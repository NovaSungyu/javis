#!/usr/bin/bash

echo "=========================================="
echo "    J.A.R.V.I.S. Ultra-Light Installer   "
echo "=========================================="

# 1. Update packages & install python, git, mpv player
echo "[1/3] Installing Python, Git, and MPV..."
pkg update -y
pkg install -y python git mpv

# 2. Install lightweight Python dependencies (Installs in 3 seconds!)
echo "[2/3] Installing lightweight Python libraries..."
pip install requests python-dotenv rich gTTS

# 3. Create .env configuration file
if [ ! -f .env ]; then
    echo "[3/3] Creating .env template..."
    echo "GEMINI_API_KEY=" > .env
    echo "JARVIS_MODEL=gemini-2.5-flash" >> .env
fi

echo "=========================================="
echo " Setup complete!                          "
echo " Run:                                     "
echo "   echo \"GEMINI_API_KEY=your_key\" > .env   "
echo "   python main.py                         "
echo "=========================================="
