# ADK Streaming Chat Bot

A real-time voice chat application powered by Google's Agent Development Kit (ADK) and Gemini 2.0 Flash, featuring live audio streaming and web-based interface.

## Local Setup

Follow these steps to get the project running on your local machine:

### Prerequisites

- Python 3.8 or higher
- Google ADK API access and credentials
- Modern web browser with microphone support

### Installation Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/IndieVerseStudio/chat-bot-adk.git
   cd chat-bot-adk
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv

   # On Windows
   .venv\Scripts\Activate.ps1

   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   Create a `.env` file in the project root directory:

   ```env
   # Google ADK Configuration (required)
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=your_api_key

   > **Note**: You'll need to obtain these credentials from the Google Cloud Console with ADK access enabled.

   ```

5. **Start the development server**:

   ```bash
   python -m uvicorn main:app --reload
   ```

6. **Open your browser** and navigate to:

   ```
   http://localhost:8000
   ```

7. **Test the application**:
   - Click "Talk with Gemini" to start a voice conversation
   - Allow microphone permissions when prompted
   - Speak your question and listen to Gemini's audio response
