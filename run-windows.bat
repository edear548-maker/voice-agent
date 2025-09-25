@echo off
setlocal enabledelayedexpansion

python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist .env copy .env.example .env

echo Paste your OPENAI_API_KEY when prompted. Leave blank to edit .env manually.
set "OPENAI_KEY="
set /p OPENAI_KEY=OPENAI_API_KEY (optional): 
if not "!OPENAI_KEY!"=="" (
    set "PYTMP=%TEMP%\set_openai_key.py"
    echo import sys>"%PYTMP%"
    echo from pathlib import Path>>"%PYTMP%"
    echo key = sys.argv[1]>>"%PYTMP%"
    echo path = Path(".env")>>"%PYTMP%"
    echo text = path.read_text(encoding="utf-8")>>"%PYTMP%"
    echo lines = text.splitlines()>>"%PYTMP%"
    echo updated = False>>"%PYTMP%"
    echo for idx, line in enumerate(lines):>>"%PYTMP%"
    echo     if line.startswith("OPENAI_API_KEY="):>>"%PYTMP%"
    echo         lines[idx] = f"OPENAI_API_KEY={key}">>"%PYTMP%"
    echo         updated = True>>"%PYTMP%"
    echo         break>>"%PYTMP%"
    echo if not updated:>>"%PYTMP%"
    echo     lines.insert(0, f"OPENAI_API_KEY={key}")>>"%PYTMP%"
    echo path.write_text("\n".join(lines) + "\n", encoding="utf-8")>>"%PYTMP%"
    python "%PYTMP%" "!OPENAI_KEY!"
    del "%PYTMP%"
)

echo Save any changes to .env, then press any key to launch the agent.
pause >nul

:loop
python main.py
if %errorlevel% equ 0 goto end
echo Agent exited with errors. Reinstalling dependencies and trying again...
pip install -r requirements.txt
echo Press any key once you've handled any issues to retry.
pause >nul
goto loop

:end
endlocal
