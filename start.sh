#!/usr/bin/bash
if [ ! -f .env ] || ! grep -q "GEMINI_API_KEY=AIza" .env 2>/dev/null; then
    echo "=========================================="
    echo " 🔑 J.A.R.V.I.S. API Key Setup            "
    echo "=========================================="
    read -p "Enter your Gemini API Key: " user_key
    echo "GEMINI_API_KEY=$user_key" > .env
    echo "JARVIS_MODEL=gemini-2.5-flash" >> .env
    echo "API Key Saved!"
fi
python main.py "$@"

