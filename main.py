import io
import os
import wave

from typing import Optional

import numpy as np

SOUNDDEVICE_IMPORT_ERROR: Optional[Exception] = None
try:
    import sounddevice as sd
except Exception as err:  # pragma: no cover - best effort to capture import errors
    sd = None
    SOUNDDEVICE_IMPORT_ERROR = err

PYTTSX3_IMPORT_ERROR: Optional[Exception] = None
try:
    import pyttsx3
except Exception as err:  # pragma: no cover - best effort to capture import errors
    pyttsx3 = None
    PYTTSX3_IMPORT_ERROR = err
from dotenv import load_dotenv
from openai import OpenAI


def roast(msg: str):
    print(f"🔥 {msg} — you're really trying your best, huh?")


def record_audio(seconds=8, rate=16000):
    if sd is None:
        reason = SOUNDDEVICE_IMPORT_ERROR or "sounddevice is unavailable"
        roast(f"Mic failed: {reason}")
        return None
    try:
        audio = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype='float32')
        sd.wait()
        return np.squeeze(audio)
    except Exception as e:
        roast(f"Mic failed: {e}")
        return None


def transcribe(client, audio, rate=16000):
    try:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
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
            delta = chunk.choices[0].delta.get('content', '')
            print(delta, end='', flush=True)
            full += delta
        print()
        return full
    except Exception as e:
        roast(f"GPT couldn't handle it: {e}")
        return ""


def speak(text):
    if pyttsx3 is None:
        reason = PYTTSX3_IMPORT_ERROR or "pyttsx3 is unavailable"
        roast(f"TTS is toast: {reason}")
        return
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        roast(f"TTS is toast: {e}")


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5")
    text_only = os.getenv("TEXT_ONLY", "0") == "1"

    if not text_only and sd is None:
        reason = SOUNDDEVICE_IMPORT_ERROR or "sounddevice is unavailable"
        roast(f"Falling back to text mode: {reason}")
        text_only = True

    if not api_key:
        roast("No API key. Did you think this was magic?")
        return

    client = OpenAI(api_key=api_key)
    history = []
    print("Listening" if not text_only else "Awaiting input")

    if text_only:
        try:
            user_text = input("You: ")
        except Exception as e:
            roast(f"Input exploded: {e}")
            return
    else:
        audio = record_audio()
        if audio is None:
            return
        user_text = transcribe(client, audio)
        if not user_text:
            return
        print(f"You said: {user_text}")

    history.append({"role": "user", "content": user_text})
    reply = chat(client, history, model)
    if reply:
        history.append({"role": "assistant", "content": reply})
        if not text_only:
            speak(reply)


if __name__ == "__main__":
    main()
