import io
import os
import sys
import wave

import numpy as np
import sounddevice as sd
import pyttsx3
from dotenv import load_dotenv
from openai import OpenAI


def roast(msg: str):
    print(f"🔥 {msg} — you're really trying your best, huh?")


def record_audio(seconds=8, rate=16000):
    try:
        audio = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="float32")
        sd.wait()
        return np.squeeze(audio)
    except Exception as e:
        roast(f"Mic failed: {e}")
        return None


def transcribe(client, audio, rate=16000):
    try:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        buf.seek(0)
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", buf.read())
        )
        return transcript.text.strip()
    except Exception as e:
        roast(f"Transcription blew up: {e}")
        return ""


def chat(client, messages, model):
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        full = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.get("content", "")
            print(delta, end="", flush=True)
            full += delta
        print()
        return full
    except Exception as e:
        roast(f"GPT couldn't handle it: {e}")
        return ""


_tts_engine = None


def speak(text):
    global _tts_engine

    if not text:
        return

    if _tts_engine is None:
        try:
            _tts_engine = pyttsx3.init()
        except Exception as e:
            roast(f"TTS refused to boot: {e}")
            return

    try:
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception as e:
        roast(f"TTS is toast: {e}")


def shutdown_speech():
    global _tts_engine

    if _tts_engine is None:
        return

    try:
        _tts_engine.stop()
    except Exception as e:
        roast(f"TTS wouldn't quit: {e}")
    finally:
        _tts_engine = None


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    text_only = os.getenv("TEXT_ONLY", "0") == "1"
    system_prompt = os.getenv("SYSTEM_PROMPT", "").strip()

    try:
        record_seconds = float(os.getenv("RECORD_SECONDS", "8"))
        if record_seconds <= 0:
            raise ValueError
    except ValueError:
        roast("RECORD_SECONDS was nonsense, falling back to 8")
        record_seconds = 8.0

    if not api_key:
        roast("No API key. Did you think this was magic?")
        return

    client = OpenAI(api_key=api_key)
    history = []
    if system_prompt:
        history.append({"role": "system", "content": system_prompt})

    exit_phrases = {"exit", "quit", "goodbye", "bye"}
    print("Voice agent ready. Press Ctrl+C or say 'exit' to bail out.")

    try:
        while True:
            if text_only:
                try:
                    user_text = input("You: ").strip()
                except EOFError:
                    print()
                    break
                except Exception as e:
                    roast(f"Input exploded: {e}")
                    break
            else:
                print("🎤 Speak now (Ctrl+C to exit)...")
                audio = record_audio(seconds=record_seconds)
                if audio is None:
                    continue
                user_text = transcribe(client, audio)
                if not user_text:
                    roast("Heard nothing useful. Try again.")
                    continue
                print(f"You said: {user_text}")

            if not user_text:
                continue

            if user_text.strip().lower() in exit_phrases:
                print("👋 See you next time.")
                break

            history.append({"role": "user", "content": user_text})
            print("Assistant:", end=" ", flush=True)
            reply = chat(client, history, model)
            if not reply:
                history.pop()
                continue

            history.append({"role": "assistant", "content": reply})

            if not text_only:
                speak(reply)
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Later!")
    finally:
        shutdown_speech()
        try:
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()
