import os
import warnings
from pathlib import Path
# from dotenv import load_dotenv

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

from session_manager import SessionManager

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# load_dotenv()

APP_NAME = "ADK Streaming example"

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example session service URI (e.g., SQLite)
# SESSION_SERVICE_URI = "sqlite:///./sessions.db"
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["https://localhost", "https://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = False

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    # session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Create a global session manager instance
session_manager = SessionManager()

@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Client websocket endpoint"""
    
    await websocket.accept()
    print(f"Client #{user_id} connected")
    
    user_id_str = str(user_id)
    
    try:
        await session_manager.start_session(websocket, user_id_str, APP_NAME)
    except WebSocketDisconnect:
        print(f"Client #{user_id} disconnected normally")
    except Exception as e:
        print(f"Error occurred for client #{user_id}: {e}")
    finally:
        # Always cleanup the session when client disconnects
        await session_manager.end_session(user_id_str)
        print(f"Session cleanup completed for client #{user_id}")

BASE_DIR = Path(__file__).resolve().parent
CERT_PATH = BASE_DIR.parent / "secrets" / "cert.pem"
KEY_PATH = BASE_DIR.parent / "secrets" / "key.pem"

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=int(os.environ.get("PORT", 8000)),  # Use 443 for production
        ssl_certfile=CERT_PATH,
        ssl_keyfile=KEY_PATH
    )