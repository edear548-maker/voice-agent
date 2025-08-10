#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
fi
echo "Add your OPENAI_API_KEY to .env then press enter to continue..."
read
python main.py
