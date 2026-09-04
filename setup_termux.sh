#!/usr/bin/bash

echo "=========================================="
echo "    J.A.R.V.I.S. Termux Installer        "
echo "=========================================="

# 1. Update Termux repositories
echo "[1/4] Updating Termux packages..."
pkg update -y

# 2. Install essential packages, C/Rust compilers for wheels
echo "[2/4] Installing Python, Git, Termux-API, Clang, and Rust compilers..."
pkg install -y python git termux-api clang rust binutils libffi openssl

# 3. Install Python dependencies
echo "[3/4] Installing Python dependencies..."
pip install -r requirements.txt

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
