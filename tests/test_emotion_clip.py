import numpy as np
import soundfile as sf

from app import emotion_clip


def _write_wav(path, seconds=0.05, sample_rate=8000):
    samples = np.zeros(int(seconds * sample_rate), dtype=np.float32)
    sf.write(path, samples, sample_rate)


def test_non_clip_emotion_returns_none():
    assert emotion_clip.load_direct_emotion_clip("normal") is None
    assert emotion_clip.load_direct_emotion_clip("flirting") is None


def test_prefers_env_override_path_when_present(tmp_path, monkeypatch):
    override = tmp_path / "custom_dramatic.wav"
    _write_wav(override, sample_rate=16000)
    monkeypatch.setenv("REFERENCE_VOICE_DRAMATIC", str(override))

    result = emotion_clip.load_direct_emotion_clip("dramatic")

    assert result is not None
    audio, sample_rate = result
    assert isinstance(audio, np.ndarray)
    assert sample_rate == 16000


def test_falls_back_to_default_clip_when_override_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("REFERENCE_VOICE_HORRIFYING", str(tmp_path / "does_not_exist.wav"))
    default_clip = tmp_path / "default_horrifying.wav"
    _write_wav(default_clip, sample_rate=22050)
    monkeypatch.setitem(emotion_clip.DEFAULT_CLIPS, "horrifying", default_clip)

    result = emotion_clip.load_direct_emotion_clip("horrifying")

    assert result is not None
    _, sample_rate = result
    assert sample_rate == 22050


def test_returns_none_when_neither_override_nor_default_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("REFERENCE_VOICE_DRAMATIC", str(tmp_path / "missing.wav"))
    monkeypatch.setitem(emotion_clip.DEFAULT_CLIPS, "dramatic", tmp_path / "also_missing.wav")

    assert emotion_clip.load_direct_emotion_clip("dramatic") is None
