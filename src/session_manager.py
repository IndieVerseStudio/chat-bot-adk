import json
import asyncio
import base64

from google.genai.types import (
    Part,
    Blob,
    SpeechConfig,
    PrebuiltVoiceConfig,
)

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue, Agent
from google.adk.agents.run_config import RunConfig
import logging

from google_custom_agent.agent import root_agent
from google_custom_agent.kyc_tools_wrapper import kyc_tools

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
        self.custom_instruction = None
        self.websocket = None
        self.restart_requested = False

    async def start_agent_session(self):
        """Starts an agent session"""
        logging.info(f"Starting agent session for user #{self.user_id}")
        
        # Create a Runner with custom instruction if provided
        if self.custom_instruction:
            logging.info(f"Using custom instruction for user #{self.user_id}: {self.custom_instruction}")
            # Create a custom agent with the user's instruction
            custom_agent = Agent(
                name="custom_agent",
                model="gemini-2.5-flash-preview-native-audio-dialog",
                description="Custom AI assistant based on user instructions.",
                instruction=self.custom_instruction,
                tools=kyc_tools,
            )
            agent_to_use = custom_agent
        else:
            logging.info(f"Using default instruction for user #{self.user_id}")
            # Use the default agent
            agent_to_use = root_agent
        
        # Create a Runner
        runner = InMemoryRunner(
            app_name=self.app_name,
            agent=agent_to_use,
        )
        
        # Create a Session
        session = await runner.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
        )

        # Set response modality with Hindi male voice
        # Try Hindi male voice names - if one doesn't work, fallback to next option
        hindi_male_voices = [
            "hi-IN-Wavenet-B",  # Primary Hindi male voice
            "hi-IN-Wavenet-C",  # Secondary Hindi male voice
            "hi-IN-Standard-B", # Standard Hindi male voice
            "Pogue"             # Fallback male voice
        ]
        
        run_config = None
        for voice_name in hindi_male_voices:
            try:
                print(f"Trying voice: {voice_name}")
                male_voice = PrebuiltVoiceConfig(voice_name=voice_name)
                speech_config = SpeechConfig(
                    voice_config=male_voice,
                    language_code="hi-IN"  # Hindi (India) language code
                )
                run_config = RunConfig(
                    response_modalities=["Audio"],
                    speech_config=speech_config
                )
                print(f"✓ Successfully configured Hindi male voice: {voice_name}")
                break
            except Exception as e:
                print(f"Voice {voice_name} failed: {e}")
                continue
        
        # Final fallback to default if all voice configurations fail
        if run_config is None:
            print("All voice configurations failed, using default")
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
                
                # Handle instruction updates
                if message.get("type") == "update_instruction":
                    instruction = message.get("instruction")
                    # Set custom instruction (None for default, string for custom)
                    self.custom_instruction = instruction
                    logging.info(f"Custom instruction updated for user #{self.user_id}: {self.custom_instruction}")
                    
                    # Start the agent session with the instruction
                    await self._start_agent_session()
                    
                    response = {
                        "type": "instruction_updated",
                        "message": "Agent instruction updated successfully"
                    }
                    await websocket.send_text(json.dumps(response))
                    continue

                # Handle regular messages
                mime_type = message.get("mime_type")
                data = message.get("data")
                
                if not mime_type or not data:
                    continue

                # Send the message to the agent
                if mime_type == "audio/pcm":
                    # Send an audio data
                    if self.live_request_queue is None:
                        logging.warning(f"No live_request_queue available for user #{self.user_id}, agent session not started yet")
                        continue
                    decoded_data = base64.b64decode(data)
                    self.live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                else:
                    raise ValueError(f"Mime type not supported: {mime_type}")
        except Exception as e:
            print(f"Client to agent messaging error for user #{self.user_id}: {e}")
            raise

    async def start_session(self, websocket):
        """Start the session"""
        self.websocket = websocket
        await self._run_session_without_agent()

    async def _run_session_without_agent(self):
        """Run session without agent initially, wait for instruction"""
        logging.info(f"Starting session without agent for user #{self.user_id}")
        
        # Start only the client messaging task initially
        client_to_agent_task = asyncio.create_task(
            self.client_to_agent_messaging(self.websocket, None)
        )

        self.tasks = [client_to_agent_task]

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

    async def _start_agent_session(self):
        """Start the agent session after instruction is set"""
        logging.info(f"Starting agent session for user #{self.user_id}")
        
        # Create the agent session
        live_events, live_request_queue = await self.start_agent_session()
        
        # Start agent to client messaging task
        agent_to_client_task = asyncio.create_task(
            self.agent_to_client_messaging(self.websocket, live_events)
        )
        
        # Add the new task to the list
        self.tasks.append(agent_to_client_task)
        
        # Update the client messaging to use the new queue
        self.live_request_queue = live_request_queue





