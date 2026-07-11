import io
import re

import httpx
import numpy as np
import soundfile as sf

from app.config import settings


def _clean_for_fish(text: str) -> str:
    text = re.sub(r"[*_#`~]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _polish_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32, copy=False)
    if len(audio) == 0:
        return audio

    audio = audio - float(np.mean(audio))
    peak = float(np.max(np.abs(audio)))
    if peak > 1e-6:
        audio = audio * min(0.92 / peak, 1.0)

    fade_len = min(int(sample_rate * 0.015), len(audio) // 2)
    if fade_len > 1:
        fade = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        audio[:fade_len] *= fade
        audio[-fade_len:] *= fade[::-1]

    return np.clip(audio, -1.0, 1.0)


class TextToSpeech:
    def __init__(self) -> None:
        if not settings.fish_api_key or settings.fish_api_key == "your_actual_key_here":
            raise RuntimeError(
                "FISH_API_KEY is missing. Put your real Fish Audio API key in .env."
            )

        self._sample_rate = 44_100
        self._client = httpx.Client(timeout=120.0)
        print(f"Using Fish Audio TTS ({settings.fish_model})...")

    def synthesize(self, text: str, emotion: str | None = None) -> tuple[np.ndarray, int]:
        text = _clean_for_fish(text)
        if not text:
            return np.array([], dtype=np.float32), self._sample_rate

        url = f"{settings.fish_base_url.rstrip('/')}/v1/tts"
        headers = {
            "Authorization": f"Bearer {settings.fish_api_key}",
            "Content-Type": "application/json",
            "model": settings.fish_model,
        }
        payload = {
            "text": text,
            "reference_id": settings.fish_reference_id,
            "format": "wav",
        }

        response = self._client.post(url, headers=headers, json=payload)
        if response.status_code == 401:
            raise RuntimeError(
                "Fish Audio rejected FISH_API_KEY. Check that .env contains your real "
                "API key from https://fish.audio/app/api-keys/ and restart the app."
            )
        response.raise_for_status()

        audio, sr = sf.read(io.BytesIO(response.content), dtype="float32")
        return _polish_audio(audio, sr), sr
