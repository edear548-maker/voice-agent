import io
import os
import random
import sys
import wave
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pyttsx3
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI


ROASTS = [
    "{detail}. Bold strategy, Cotton.",
    "{detail}. Even my toaster could do better.",
    "{detail}. Did you try turning your brain on?",
    "{detail}. That's one way to speedrun failure.",
    "{detail}. You're keeping the chaos interesting at least.",
]


def roast(detail: str) -> None:
    """Print a delightfully mean error message."""
    zinger = random.choice(ROASTS)
    print(f"🔥 {zinger.format(detail=detail)}")


@dataclass
class AgentConfig:
    api_key: str
    model: str = "gpt-5"
    text_only: bool = False
    sample_rate: int = 16_000
    duration_seconds: int = 8


class VoiceAgent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.history: List[dict[str, str]] = []
        self.tts_engine: Optional[pyttsx3.Engine] = None
        self._init_tts()

    def _init_tts(self) -> None:
        if self.config.text_only:
            return
        try:
            self.tts_engine = pyttsx3.init()
        except Exception as exc:  # pragma: no cover - platform specific failure handling
            roast(f"TTS initialization faceplanted: {exc}")
            self.tts_engine = None

    def speak(self, text: str) -> None:
        if not self.tts_engine:
            return
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as exc:  # pragma: no cover - platform specific failure handling
            roast(f"TTS choked mid-sentence: {exc}")
            self.tts_engine = None

    def record_audio(self) -> Optional[np.ndarray]:
        try:
            frames = int(self.config.duration_seconds * self.config.sample_rate)
            recording = sd.rec(
                frames,
                samplerate=self.config.sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            return np.squeeze(recording)
        except Exception as exc:  # pragma: no cover - relies on hardware
            roast(f"Mic threw a tantrum: {exc}")
            return None

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.config.sample_rate)
                wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())
            buffer.seek(0)
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("speech.wav", buffer.read()),
            )
            return transcript.text.strip()
        except Exception as exc:
            roast(f"Transcription imploded: {exc}")
            return ""

    def _prompt_for_text(self) -> Optional[str]:
        try:
            return input("You: ")
        except EOFError:
            roast("Input stream tapped out. Guess we're done here.")
        except Exception as exc:
            roast(f"Keyboard input went kaboom: {exc}")
        return None

    def _fallback_to_text(self) -> Optional[str]:
        roast("Voice failed, so type like it's 1999.")
        return self._prompt_for_text()

    def capture_user_message(self) -> Optional[str]:
        if self.config.text_only:
            return self._prompt_for_text()
        audio = self.record_audio()
        if audio is None:
            return self._fallback_to_text()
        text = self.transcribe(audio)
        if not text:
            return self._fallback_to_text()
        print(f"You said: {text}")
        return text

    def stream_reply(self) -> str:
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=self.history,
                stream=True,
            )
        except Exception as exc:
            roast(f"GPT rage quit before responding: {exc}")
            return ""

        response_fragments: List[str] = []
        try:
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.get("content")
                if not delta:
                    continue
                print(delta, end="", flush=True)
                response_fragments.append(delta)
        except Exception as exc:
            roast(f"Streaming response blew up: {exc}")
            return ""
        finally:
            print()
        return "".join(response_fragments).strip()

    def run(self) -> None:
        print("Listening")
        while True:
            try:
                message = self.capture_user_message()
            except KeyboardInterrupt:
                print("\n🔥 Fine, storm out then. Bye!")
                break

            if message is None:
                continue
            message = message.strip()
            if not message:
                roast("Blank message? Bold move.")
                continue
            if message.lower() in {"quit", "exit"}:
                print("🔥 Rage quitting already? Conversation over.")
                break

            self.history.append({"role": "user", "content": message})
            reply = self.stream_reply()
            if not reply:
                continue
            self.history.append({"role": "assistant", "content": reply})
            self.speak(reply)


def ensure_api_key() -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    roast("No OPENAI_API_KEY found. Paste it or we stare at each other.")
    try:
        api_key = input("OPENAI_API_KEY: ").strip()
    except EOFError:
        api_key = ""
    if not api_key:
        roast("Still no key. I'm just going to nap.")
        return None
    os.environ["OPENAI_API_KEY"] = api_key
    return api_key


def build_config() -> Optional[AgentConfig]:
    load_dotenv()
    api_key = ensure_api_key()
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-5")
    text_only = os.getenv("TEXT_ONLY", "0") == "1"
    return AgentConfig(api_key=api_key, model=model, text_only=text_only)


def main() -> int:
    config = build_config()
    if not config:
        return 1
    agent = VoiceAgent(config)
    agent.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
