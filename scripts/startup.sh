#!/bin/bash
# Update packages and install dependencies
echo "Updating packages and installing dependencies..."
sudo apt-get update -y
sudo apt-get -y install git
sudo apt-get install -y python3-pip python3-venv

# Clone the repository
echo "Cloning the chat-bot-adk repository..."
git clone https://github.com/IndieVerseStudio/chat-bot-adk.git /opt/chat-bot-adk

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv /opt/chat-bot-adk/venv

# Install python dependencies inside the venv
echo "Installing python dependencies..."
/opt/chat-bot-adk/venv/bin/pip install -r /opt/chat-bot-adk/requirements.txt

echo "Setting up the chatbot service..."
cat <<'EOF' | sudo tee /etc/systemd/system/chatbot.service > /dev/null
[Unit]
Description=FastAPI Chatbot (Uvicorn)
After=network.target

[Service]
User=chatbot
WorkingDirectory=/opt/chat-bot-adk
# Environment=GOOGLE_API_KEY=test
ExecStart=/opt/chat-bot-adk/venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers
Restart=always
RestartSec=3
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

echo "Starting the chatbot service..."
sudo systemctl daemon-reload
sudo systemctl enable --now chatbot.service