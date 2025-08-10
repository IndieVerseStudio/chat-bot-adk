#!/usr/bin/env bash
set -euo pipefail

# ========= Config (edit if needed) =========
APP_USER="chatbot"
APP_DIR="/opt/chat-bot-adk"
REPO_URL="https://github.com/IndieVerseStudio/chat-bot-adk.git"
APP_MODULE="main:app"           # change if your FastAPI app isn't main:app
HOST="0.0.0.0"
PORT="8000"
WORKERS="2"
# ==========================================

echo "[1/6] Install OS deps"
sudo apt-get update -y
sudo apt-get install -y git python3-venv python3-pip

echo "[2/6] Create service user and app directory"
if ! id -u "$APP_USER" >/dev/null 2>&1; then
  sudo useradd -r -s /usr/sbin/nologin "$APP_USER"
fi
sudo mkdir -p "$APP_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "[3/6] Fetch or update source"
if [ ! -d "$APP_DIR/.git" ]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
else
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only || true
fi

echo "[4/6] Create venv and install Python deps"
if [ ! -x "$APP_DIR/venv/bin/python" ]; then
  sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi
# sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
# requirements first (if present), then ensure uvicorn is installed
if [ -f "$APP_DIR/requirements.txt" ]; then
  sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip3" install -r "$APP_DIR/requirements.txt"
fi
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install "uvicorn[standard]"

echo "[5/6] Create env file (edit with real secrets)"
if [ ! -f "$APP_DIR/.env" ]; then
  sudo bash -c "cat > '$APP_DIR/.env' <<'ENV'
# Put your config here (key=value). Example:
# GOOGLE_API_KEY=replace_me
# GOOGLE_GENAI_USE_VERTEXAI=false
ENV"
  sudo chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
  sudo chmod 600 "$APP_DIR/.env"
fi

echo "[6/6] Install systemd unit"
sudo tee /etc/systemd/system/chatbot.service >/dev/null <<EOF
[Unit]
Description=FastAPI Chatbot (Uvicorn)
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=-$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python -m uvicorn $APP_MODULE --host $HOST --port $PORT --workers $WORKERS --proxy-headers
Restart=always
RestartSec=3
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now chatbot.service

echo "-----"
echo "Deployed. Quick checks:"
echo " systemctl status chatbot.service -l --no-pager"
echo " sudo journalctl -u chatbot.service -e -n 100"
echo " ss -ltnp | grep :$PORT   # should show LISTEN on 0.0.0.0:$PORT"
