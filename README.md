# Voice Agent

A cross-platform OpenAI-powered voice agent that records an 8 second audio clip, sends it to Whisper for speech-to-text, streams GPT responses, speaks them back with `pyttsx3`, and keeps the whole conversation in memory for follow-up questions.

## Features
- 8 second / 16 kHz microphone capture with automatic fallback to manual text input if audio fails
- Whisper-powered transcription (`whisper-1`)
- Streaming GPT responses (default `gpt-5`) with persistent in-session memory
- Text-to-speech via `pyttsx3` when voice output is enabled
- Roast-style error feedback so you know exactly how spectacularly something failed

## Quick Start
The repo ships with one-shot scripts that handle everything: create a virtual environment, install dependencies (including platform extras), copy `.env.example` to `.env`, and launch the agent.

### Windows
1. Double-click `run-windows.bat`.
2. When prompted, open the generated `.env` file and paste your `OPENAI_API_KEY` (or paste it directly into the console prompt).
3. Return to the terminal window and press any key to continue.
4. The agent launches and prints `Listening`. Say something or type `quit` to exit.

### macOS
1. Make the script executable (first run only) and launch it:
   ```bash
   chmod +x run-macos.sh
   ./run-macos.sh
   ```
2. When prompted, update `.env` with your `OPENAI_API_KEY` (or paste it into the console prompt) and press **Enter**.
3. The script reruns automatically until the agent starts cleanly and prints `Listening`.

### Text-only mode
If you can't or don't want to use a microphone, set `TEXT_ONLY=1` in `.env`. The agent will prompt you for text input each turn but still speak responses if TTS is available.

### Stopping the agent
- Say "quit" or "exit" (in text or voice) to end the session politely.
- Hit `Ctrl+C` if you want to bail immediately; the agent will roast you on the way out.

## Configuration
Copy `.env.example` to `.env` (the scripts already do this) and tweak the values:

```env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5
TEXT_ONLY=0
```

Change `OPENAI_MODEL` to any GPT model you prefer (e.g., `gpt-4o-mini`) and flip `TEXT_ONLY` to `1` to disable microphone capture entirely.

## Troubleshooting
- **Missing audio device** – the agent will fall back to manual input automatically and keep running.
- **TTS errors** – failures downgrade to silent mode; the conversation continues in the console.
- **API key issues** – if `.env` is empty, the agent prompts you to paste a key when it launches.

Need to reset? Delete `.venv/` and run the platform script again.
