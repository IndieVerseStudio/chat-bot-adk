import json
import asyncio
import base64

from google.genai.types import (
    Part,
    Blob,
)

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig

from google_custom_agent.agent import root_agent

class SessionManager:
    def __init__(self):
        self.sessions = {}

    async def start_session(self, websocket, user_id, app_name):
        if user_id in self.sessions:
            print(f"Session for user #{user_id} is already active.")
            # End existing session first
            await self.end_session(user_id)

        try:
            user_session = UserSession(app_name, user_id)
            self.sessions[user_id] = user_session
            await user_session.start_session(websocket)

        except Exception as e:
            # Remove session on error
            if user_id in self.sessions:
                del self.sessions[user_id]
            raise e

    async def end_session(self, user_id):
        """Properly cleanup a user session"""
        if user_id in self.sessions:
            try:
                user_session = self.sessions[user_id]
                # await user_session.cleanup()
            except Exception as e:
                print(f"Error during cleanup for user #{user_id}: {e}")
            finally:
                del self.sessions[user_id]
                print(f"Session removed for user #{user_id}")

class UserSession:
    def __init__(self, app_name, user_id):
        self.app_name = app_name
        self.user_id = user_id
        self.live_request_queue = None
        self.tasks = []

    async def start_agent_session(self):
        """Starts an agent session"""
        
        # Create a Runner
        runner = InMemoryRunner(
            app_name=self.app_name,
            agent=root_agent,
        )
        
        # Create a Session
        session = await runner.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
        )

        # Set response modality
        run_config = RunConfig(response_modalities=["Audio"])

        # Create a LiveRequestQueue for this session
        live_request_queue = LiveRequestQueue()
        self.live_request_queue = live_request_queue

        # Start agent session
        live_events = runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )
        return live_events, live_request_queue

    async def agent_to_client_messaging(self, websocket, live_events):
        """Agent to client communication"""
        try:
            async for event in live_events:
                # If the turn complete or interrupted, send it
                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT #{self.user_id}]: {message}")
                    continue

                # Read the Content and its first Part
                part: Part = (
                    event.content and event.content.parts and event.content.parts[0]
                )
                if not part:
                    continue

                # If it's audio, send Base64 encoded audio data
                is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        message = {
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii")
                        }
                        await websocket.send_text(json.dumps(message))
                        print(f"[AGENT TO CLIENT #{self.user_id}]: audio/pcm: {len(audio_data)} bytes.")
                        continue
        except Exception as e:
            print(f"Agent to client messaging error for user #{self.user_id}: {e}")
            raise

    async def client_to_agent_messaging(self, websocket, live_request_queue):
        """Client to agent communication"""
        try:
            while True:
                # Decode JSON message
                message_json = await websocket.receive_text()
                message = json.loads(message_json)
                mime_type = message["mime_type"]
                data = message["data"]

                if message.get("type") == "update_instruction":
                    instruction = message.get("instruction")
                    if instruction:
                        response = {
                            "type": "instruction_updated",
                            "message": "Agent instruction updated successfully"
                        }
                        await websocket.send_text(json.dumps(response))
                    continue

                # Send the message to the agent
                if mime_type == "audio/pcm":
                    # Send an audio data
                    decoded_data = base64.b64decode(data)
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                else:
                    raise ValueError(f"Mime type not supported: {mime_type}")
        except Exception as e:
            print(f"Client to agent messaging error for user #{self.user_id}: {e}")
            raise

    async def start_session(self, websocket):
        live_events, live_request_queue = await self.start_agent_session()

        # Start tasks
        agent_to_client_task = asyncio.create_task(
            self.agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            self.client_to_agent_messaging(websocket, live_request_queue)
        )

        self.tasks = [agent_to_client_task, client_to_agent_task]

        try:
            # Wait until the websocket is disconnected or an error occurs
            done, pending = await asyncio.wait(
                self.tasks, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check if any task raised an exception (but ignore CancelledError)
            for task in done:
                if not task.cancelled():  # Only check non-cancelled tasks
                    exception = task.exception()
                    if exception:
                        raise exception
                        
        except Exception as e:
            print(f"Session error for user #{self.user_id}: {e}")
            raise

