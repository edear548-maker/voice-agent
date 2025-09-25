import io
import logging
import os
import wave
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pyttsx3
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class AgentConfig:
    """Configuration options for the voice agent."""

    model: str
    transcription_model: str
    sample_rate: int
    record_seconds: float
    text_only: bool
    max_turns: Optional[int]
    exit_phrases: Tuple[str, ...]
    system_prompt: Optional[str]
    voice_rate: Optional[int]
    voice_volume: Optional[float]

    @classmethod
    def from_env(cls) -> Tuple[str, "AgentConfig"]:
        """Create a configuration instance from environment variables."""

        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Set OPENAI_API_KEY in your environment or .env file.")

        def _get_int(name: str, default: Optional[int]) -> Optional[int]:
            value = os.getenv(name)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                logging.warning("Invalid %s value '%s'. Using %s.", name, value, default)
                return default

        def _get_float(name: str, default: Optional[float]) -> Optional[float]:
            value = os.getenv(name)
            if value is None:
                return default
            try:
                return float(value)
            except ValueError:
                logging.warning("Invalid %s value '%s'. Using %s.", name, value, default)
                return default

        model = os.getenv("OPENAI_MODEL", "gpt-5").strip() or "gpt-5"
        transcription_model = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1").strip() or "whisper-1"
        sample_rate = _get_int("SAMPLE_RATE", 16000) or 16000
        record_seconds = _get_float("RECORD_SECONDS", 8.0) or 8.0
        text_only = os.getenv("TEXT_ONLY", "0").strip() == "1"
        max_turns = _get_int("MAX_TURNS", None)
        voice_rate = _get_int("VOICE_RATE", None)
        voice_volume = _get_float("VOICE_VOLUME", None)
        exit_raw = os.getenv("EXIT_PHRASES", "exit,quit,bye")
        exit_phrases = tuple(
            phrase.strip().lower()
            for phrase in exit_raw.split(",")
            if phrase.strip()
        ) or ("exit", "quit", "bye")
        system_prompt = os.getenv("SYSTEM_PROMPT")

        config = cls(
            model=model,
            transcription_model=transcription_model,
            sample_rate=sample_rate,
            record_seconds=record_seconds,
            text_only=text_only,
            max_turns=max_turns,
            exit_phrases=exit_phrases,
            system_prompt=system_prompt,
            voice_rate=voice_rate,
            voice_volume=voice_volume,
        )
        return api_key, config


class VoiceAgent:
    """Voice-enabled assistant backed by OpenAI models."""

    def __init__(self, api_key: str, config: AgentConfig) -> None:
        self.client = OpenAI(api_key=api_key)
        self.config = config
        self.history: List[dict[str, str]] = []
        if config.system_prompt:
            self.history.append({"role": "system", "content": config.system_prompt})
        self.engine = None if config.text_only else self._create_engine()

    def _create_engine(self):
        try:
            engine = pyttsx3.init()
            if self.config.voice_rate is not None:
                engine.setProperty("rate", self.config.voice_rate)
            if self.config.voice_volume is not None:
                engine.setProperty("volume", max(0.0, min(self.config.voice_volume, 1.0)))
            return engine
        except Exception:  # noqa: BLE001
            logging.exception("Failed to initialize text-to-speech engine.")
            return None

    def record_audio(self) -> Optional[np.ndarray]:
        frames = int(self.config.record_seconds * self.config.sample_rate)
        logging.info(
            "Recording audio for up to %.1f seconds at %d Hz.",
            self.config.record_seconds,
            self.config.sample_rate,
        )
        try:
            audio = sd.rec(
                frames,
                samplerate=self.config.sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            return np.squeeze(audio)
        except KeyboardInterrupt:
            logging.info("Recording interrupted by user.")
            raise
        except Exception:  # noqa: BLE001
            logging.exception("Microphone capture failed.")
            return None

    def transcribe(self, audio: np.ndarray) -> str:
        logging.info("Transcribing audio with %s.", self.config.transcription_model)
        try:
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.config.sample_rate)
                wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())
            buffer.seek(0)
            transcript = self.client.audio.transcriptions.create(
                model=self.config.transcription_model,
                file=("audio.wav", buffer.read()),
            )
            text = transcript.text.strip()
            if text:
                logging.info("Transcript: %s", text)
            else:
                logging.info("No speech detected in recording.")
            return text
        except Exception:  # noqa: BLE001
            logging.exception("Transcription request failed.")
            return ""

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        logging.info("Requesting response from %s.", self.config.model)
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=self.history,
                stream=True,
            )
            print("Assistant: ", end="", flush=True)
            parts: List[str] = []
            for chunk in stream:
                delta = chunk.choices[0].delta.get("content", "")
                if not delta:
                    continue
                print(delta, end="", flush=True)
                parts.append(delta)
            print()
        except Exception:  # noqa: BLE001
            logging.exception("Chat completion failed.")
            self.history.pop()  # remove user message on failure
            return ""

        reply = "".join(parts).strip()
        if reply:
            self.history.append({"role": "assistant", "content": reply})
        else:
            logging.info("Model returned an empty response.")
        return reply

    def speak(self, text: str) -> None:
        if not text or self.engine is None:
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:  # noqa: BLE001
            logging.exception("Text-to-speech playback failed.")

    def capture_user_input(self) -> Optional[str]:
        if self.config.text_only:
            try:
                return input("You: ").strip()
            except KeyboardInterrupt:
                raise
            except EOFError:
                logging.info("Input stream closed. Exiting.")
                return None
            except Exception:  # noqa: BLE001
                logging.exception("Failed to read from stdin.")
                return ""

        audio = self.record_audio()
        if audio is None:
            return ""
        text = self.transcribe(audio)
        if text:
            print(f"You said: {text}")
        return text

    def run(self) -> None:
        if self.config.text_only:
            logging.info("Text-only mode enabled. Type an exit phrase (%s) to stop.", ", ".join(self.config.exit_phrases))
        else:
            logging.info(
                "Listening... say one of (%s) to stop.",
                ", ".join(self.config.exit_phrases),
            )

        turns = 0
        while self.config.max_turns is None or turns < self.config.max_turns:
            user_text = self.capture_user_input()
            if user_text is None:
                break
            user_text = user_text.strip()
            if not user_text:
                continue
            if user_text.lower() in self.config.exit_phrases:
                logging.info("Exit phrase received. Goodbye.")
                break
            reply = self.chat(user_text)
            if not reply:
                continue
            if not self.config.text_only:
                self.speak(reply)
            turns += 1

        logging.info("Session finished after %d turn(s).", turns)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    setup_logging()
    try:
        api_key, config = AgentConfig.from_env()
    except ValueError as exc:
        logging.error("%s", exc)
        return

    agent = VoiceAgent(api_key=api_key, config=config)
    try:
        agent.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Goodbye.")


if __name__ == "__main__":
    main()
