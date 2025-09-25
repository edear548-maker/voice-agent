# Voice Agent

Simple cross-platform voice agent powered by OpenAI.

## Setup & Run

### Windows
1. Double-click `run-windows.bat`.
2. When prompted, edit the generated `.env` with your OpenAI API key.
3. The agent starts listening.

### macOS
1. Make `run-macos.sh` executable and run it:
   ```bash
   chmod +x run-macos.sh
   ./run-macos.sh
   ```
2. When prompted, edit the generated `.env` with your OpenAI API key.
3. The agent starts listening.

Both scripts create a virtual environment, install dependencies, copy `.env.example` to `.env`, and run `main.py`.

If PortAudio or other audio dependencies are unavailable, the agent automatically falls back to text input mode so it can still run in environments without microphone access.
