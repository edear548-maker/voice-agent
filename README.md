# Voice Agent

Simple cross-platform voice agent powered by OpenAI. Record a short clip, stream the model's reply back in the terminal, and optionally speak it aloud.

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

## Usage

* The agent now keeps the full conversation history so you can ask follow-up questions.
* Press `Ctrl+C` or say "exit" ("quit"/"bye" also work) to stop listening.
* Set `TEXT_ONLY=1` in `.env` if you prefer to type instead of using the microphone.

## Configuration

Update `.env` with the following options:

- `OPENAI_API_KEY` – required OpenAI API key.
- `OPENAI_MODEL` – chat model to use (defaults to `gpt-4o`).
- `TEXT_ONLY` – set to `1` for keyboard-only mode.
- `SYSTEM_PROMPT` – optional instruction that is prepended to the conversation.
- `RECORD_SECONDS` – duration of each microphone capture in seconds (defaults to `8`).
