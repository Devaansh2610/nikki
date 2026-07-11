import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import settings


class SpeechToText:
    def __init__(self) -> None:
        device = settings.whisper_device
        if device == "auto":
            device = "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                settings.whisper_model,
                device=device,
                compute_type=compute_type,
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not load the Whisper speech-recognition model. "
                "On first run, faster-whisper needs to download model files from "
                "Hugging Face; run `python main.py` with an internet connection, "
                "or set WHISPER_MODEL to a local CTranslate2 Whisper model path."
            ) from exc

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) == 0:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
            sf.write(path, audio, settings.sample_rate)

        try:
            return self.transcribe_file(path)
        finally:
            path.unlink(missing_ok=True)

    def transcribe_file(self, path: Path) -> str:
        segments, _ = self._model.transcribe(
            str(path),
            language="en",
            vad_filter=True,
            beam_size=1,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
