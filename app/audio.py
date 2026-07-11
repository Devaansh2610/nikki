import queue
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf

from app.config import settings


def record_until_silence(
    silence_threshold: float = 0.015,
    silence_duration: float = 1.2,
    max_duration: float = 30.0,
    min_duration: float = 0.5,
) -> np.ndarray:
    """Record from mic; stop after sustained silence or max duration."""
    frames: list[np.ndarray] = []
    silent_chunks = 0
    started = False
    chunk_duration = 0.1
    chunk_samples = int(settings.sample_rate * chunk_duration)
    max_chunks = int(max_duration / chunk_duration)
    silence_chunks_needed = int(silence_duration / chunk_duration)

    with sd.InputStream(
        samplerate=settings.sample_rate,
        channels=1,
        dtype="float32",
        blocksize=chunk_samples,
    ) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_samples)
            chunk = chunk.flatten()
            energy = float(np.sqrt(np.mean(chunk**2)))

            if energy > silence_threshold:
                started = True
                silent_chunks = 0
                frames.append(chunk.copy())
            elif started:
                silent_chunks += 1
                frames.append(chunk.copy())
                if silent_chunks >= silence_chunks_needed:
                    break

    if not frames:
        return np.array([], dtype=np.float32)

    audio = np.concatenate(frames)
    min_samples = int(min_duration * settings.sample_rate)
    if len(audio) < min_samples:
        return np.array([], dtype=np.float32)
    return audio


def save_wav(audio: np.ndarray, path: str) -> None:
    sf.write(path, audio, settings.sample_rate)


class AudioPlayer:
    """Thread-safe queue player so TTS can generate while previous audio plays."""

    def __init__(self) -> None:
        self._queue: queue.Queue[np.ndarray | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def play(self, audio: np.ndarray, sample_rate: int) -> None:
        self._queue.put((audio, sample_rate))

    def wait_until_done(self) -> None:
        while not self._queue.empty():
            time.sleep(0.05)
        time.sleep(0.1)

    def stop(self) -> None:
        self._queue.put(None)

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                break
            audio, sample_rate = item
            sd.play(audio, sample_rate)
            sd.wait()
