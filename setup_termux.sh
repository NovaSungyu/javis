#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if ! command -v pkg >/dev/null 2>&1; then
    echo "Run this installer inside Android Termux."
    exit 1
fi
pkg update -y
pkg install -y python termux-api
if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
fi
echo "Install the matching Termux:API Android app and grant needed permissions."
echo "Edit .env to set your API key. Local commands do not need a key."
echo "Start: bash start.sh"
