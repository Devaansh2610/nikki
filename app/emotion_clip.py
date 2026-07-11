import numpy as np
import soundfile as sf

from app.config import ROOT, settings


DEFAULT_CLIPS = {
    "dramatic": ROOT / "nice-date.mp3",
    "horrifying": ROOT / "i-feel-like-you-dont-love-me-as-much-as-i-do.mp3",
}


def load_direct_emotion_clip(emotion: str) -> tuple[np.ndarray, int] | None:
    if emotion not in DEFAULT_CLIPS:
        return None

    path = settings.emotion_voice_path(emotion)
    if not path.exists():
        path = DEFAULT_CLIPS[emotion]
    if not path.exists():
        return None

    audio, sample_rate = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return np.asarray(audio, dtype=np.float32), sample_rate
