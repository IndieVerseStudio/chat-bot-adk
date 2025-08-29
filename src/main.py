import json
import os
import uuid
from typing import Dict, Any

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google_custom_agent.agent import root_agent
from google.genai import types

from google.genai.types import (
    Part,
    Content,
)

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import speech
from google.cloud import texttospeech
import io
import tempfile
import base64

# Initialize FastAPI app
app = FastAPI(title="Birla Opus KYC Chat Bot", description="ADK-powered chat bot for KYC customer care")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for the frontend)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

os.environ["GOOGLE_API_KEY"] = "AIzaSyCaXAvvcyyGaMsmLJHA0Uo0vq4U6guUe-Q"

# Initialize Google Speech-to-Text client
speech_client = speech.SpeechClient()

# Initialize Google Text-to-Speech client
tts_client = texttospeech.TextToSpeechClient()

active_sessions = {}

# Request/Response models
class SessionRequest(BaseModel):
    user_id: str = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    audio_data: str = ""
    audio_format: str = "mp3"
    status: str

class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"

async def start_agent_session(user_id: str, session_id: str):
    """Create a new agent session and return the runner"""
    try:
        session_service = InMemorySessionService()
        APP_NAME = 'chat_bot_adk'

        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        return runner
    except Exception as e:
        print(f"Error creating session: {e}")
        raise e

async def call_agent_async(query: str, runner, user_id: str, session_id: str):
    """Send a message to the agent and get response"""
    try:
        content = types.Content(role='user', parts=[types.Part(text=query)])
        final_response_text = "Agent did not produce a final response"

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break

        print(f"<<< Agent Response: {final_response_text}")
        return final_response_text
    except Exception as e:
        print(f"Error calling agent: {e}")
        raise e

async def generate_tts_audio(text: str):
    """Generate TTS audio for given text"""
    try:
        # Configure the TTS request for natural Hindi voice
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Choose voice - using WaveNet for most human-like sound
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN",
            name="hi-IN-Wavenet-A",  # WaveNet female voice (most human-like)
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # Configure audio format for natural human-like quality
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Normal conversational rate
            pitch=0.0,  # Natural pitch
            volume_gain_db=0.0,  # Normal volume
            effects_profile_id=["headphone-class-device"]  # Natural audio for speakers/headphones
        )
        
        # Perform TTS
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Convert audio to base64 for easy transport
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        print(f"TTS generation error: {e}")
        return ""

# Frontend route
@app.get("/")
async def get_frontend():
    """Serve the frontend HTML"""
    html_path = os.path.join(static_dir, "index.html")
    return FileResponse(html_path)

# API Endpoints
@app.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest = SessionRequest()):
    """Create a new chat session"""
    try:
        # Generate IDs - session_id is always server-generated
        user_id = request.user_id or str(uuid.uuid4())
        session_id = str(uuid.uuid4())  # Always generate session_id on server
        
        # Create the agent session
        runner = await start_agent_session(user_id, session_id)
        
        # Store the session
        active_sessions[session_id] = {
            "runner": runner,
            "user_id": user_id,
            "session_id": session_id
        }
        
        return SessionResponse(
            session_id=session_id,
            user_id=user_id,
            status="success",
            message="Session created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the agent"""
    try:
        # Check if session exists
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please create a session first using POST /")
        
        session_data = active_sessions[request.session_id]
        runner = session_data["runner"]
        user_id = session_data["user_id"]
        
        # Send message to agent
        response = await call_agent_async(request.message, runner, user_id, request.session_id)
        
        # Generate TTS audio for the response
        audio_data = await generate_tts_audio(response)
        
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            audio_data=audio_data,
            audio_format="mp3",
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/sessions")
async def get_active_sessions():
    """Get list of active sessions (for debugging)"""
    return {
        "active_sessions": list(active_sessions.keys()),
        "total_sessions": len(active_sessions)
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Health check endpoint
@app.get("/complaints")
async def get_complaints():
    """Get all complaints from the data file"""
    try:
        complaints_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "complaints.json")
        if os.path.exists(complaints_path):
            with open(complaints_path, 'r') as f:
                complaints_data = json.load(f)
            return {"complaints": complaints_data, "total": len(complaints_data)}
        else:
            return {"complaints": [], "total": 0, "message": "No complaints file found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch complaints: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio file to text using Google Speech-to-Text API"""
    try:
        # Read the uploaded audio file
        audio_data = await file.read()
        
        # Configure recognition config for Hindi-English mix
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # Common web format
            sample_rate_hertz=48000,  # Standard web audio sample rate
            language_code="hi-IN",  # Hindi (India)
            alternative_language_codes=["en-IN"],  # English (India) as alternative
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            model="latest_long",  # Best model for longer audio
        )
        
        # Create audio object
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Perform speech recognition
        response = speech_client.recognize(config=config, audio=audio)
        
        if response.results:
            # Get the most confident result
            result = response.results[0]
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
            return {
                "transcription": transcript,
                "confidence": confidence,
                "language": "hi-IN",
                "status": "success"
            }
        else:
            return {
                "transcription": "",
                "error": "No speech detected in audio",
                "status": "error"
            }
            
    except Exception as e:
        print(f"Speech-to-Text error: {e}")
        return {
            "transcription": "",
            "error": f"Speech recognition failed: {str(e)}",
            "status": "error"
        }

@app.post("/audio-chat")
async def audio_chat(session_id: str, file: UploadFile = File(...)):
    """Process audio input and return chat response using Google Speech-to-Text API"""
    try:
        # Check if session exists first
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please create a session first.")
        
        # Read the uploaded audio file
        audio_data = await file.read()
        
        # Configure recognition config for Hindi-English mix
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="hi-IN",
            alternative_language_codes=["en-IN"],
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            model="latest_long",
        )
        
        # Create audio object
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Perform speech recognition
        response = speech_client.recognize(config=config, audio=audio)
        
        if response.results:
            # Get the transcribed text
            result = response.results[0]
            transcribed_text = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
            # Get session data and send to agent
            session_data = active_sessions[session_id]
            runner = session_data["runner"]
            user_id = session_data["user_id"]
            
            # Send transcribed text to agent
            agent_response = await call_agent_async(transcribed_text, runner, user_id, session_id)
            
            # Generate TTS audio for the response
            audio_data = await generate_tts_audio(agent_response)
            
            return {
                "transcription": transcribed_text,
                "confidence": confidence,
                "response": agent_response,
                "audio_data": audio_data,
                "audio_format": "mp3",
                "session_id": session_id,
                "status": "success"
            }
        else:
            return {
                "transcription": "",
                "response": "Sorry, I couldn't hear any speech in your message. Please try again or type your message.",
                "error": "No speech detected",
                "status": "error"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Audio chat error: {e}")
        return {
            "transcription": "",
            "response": "Sorry, there was an issue processing your voice message. Please try typing your message instead.",
            "error": f"Audio processing failed: {str(e)}",
            "status": "error"
        }

@app.post("/text-to-speech")
async def convert_text_to_speech(request: TTSRequest):
    """Convert text to speech using Google Text-to-Speech API"""
    try:
        # Configure the TTS request for natural Hindi voice
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        
        # Choose voice - using WaveNet for most human-like sound
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN",  # Hindi (India)
            name="hi-IN-Wavenet-A",  # WaveNet female voice (most human-like)
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # Configure audio format for natural human-like quality
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Normal conversational rate
            pitch=0.0,  # Natural pitch
            volume_gain_db=0.0,  # Normal volume
            effects_profile_id=["headphone-class-device"]  # Natural audio for speakers/headphones
        )
        
        # Perform TTS
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Convert audio to base64 for easy transport
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "audio_format": "mp3",
            "text": request.text,
            "language": request.language,
            "voice": "hi-IN-Neural2-A",
            "status": "success"
        }
        
    except Exception as e:
        print(f"TTS error: {e}")
        return {
            "audio_data": "",
            "error": f"Text-to-speech conversion failed: {str(e)}",
            "status": "error"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Chat Bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)