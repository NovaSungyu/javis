#!/usr/bin/bash

echo "=========================================="
echo "    J.A.R.V.I.S. Termux Installer        "
echo "=========================================="

# 1. Update Termux repositories
echo "[1/4] Updating Termux packages..."
pkg update -y

# 2. Install essential packages and pre-compiled Python binaries
echo "[2/4] Installing Python, Git, Termux-API, and binary wheels..."
pkg install -y python git termux-api python-pydantic python-rich python-requests python-dotenv

# 3. Install Python GenAI dependencies
echo "[3/4] Installing Google GenAI SDK..."
pip install google-genai

# 4. Create .env configuration file if missing
if [ ! -f .env ]; then
    echo "[4/4] Creating .env file..."
    echo "GEMINI_API_KEY=" > .env
    echo "JARVIS_MODEL=gemini-2.5-flash" >> .env
    echo "Created .env template. Please enter your GEMINI_API_KEY in .env!"
else
    echo "[4/4] .env file already exists."
fi

echo "=========================================="
echo " Setup complete!                          "
echo " 1. Edit .env file to set your API Key:  "
echo "    echo \"GEMINI_API_KEY=your_key\" > .env "
echo " 2. Run JARVIS:                           "
echo "    python main.py --voice                "
echo "=========================================="
