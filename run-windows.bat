@echo off
python -m venv .venv
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo Add your OPENAI_API_KEY to .env then press any key...
pause >nul
python main.py
