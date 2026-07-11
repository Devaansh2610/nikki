#!/usr/bin/env python3
"""
Prepare a local reference voice clip from any audio file you provide.

Use only audio you have the right to use.

Usage:
  python prepare_voice.py interview.mp3
  python prepare_voice.py clip.wav --start 12 --duration 10
  python prepare_voice.py clip.mp4 --start 0:45 --duration 8 --out voices/reference.wav
  python prepare_voice.py scream.mp3 --duration 12 --out voices/screaming.wav
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import ROOT, settings

TARGET_SR = 24_000
MIN_SEC = 5.0
MAX_SEC = 30.0


def parse_time(value: str) -> float:
    if ":" in value:
        parts = value.split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        raise ValueError(f"Bad time format: {value}")
    return float(value)


def load_with_ffmpeg(path: Path, start: float, duration: float) -> tuple[np.ndarray, int]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-i",
        str(path),
        "-t",
        str(duration),
        "-ac",
        "1",
        "-ar",
        str(TARGET_SR),
        "-f",
        "wav",
        "pipe:1",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Install with: brew install ffmpeg")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: ffmpeg failed:\n{exc.stderr.decode()}")
        sys.exit(1)

    import io

    data, sr = sf.read(io.BytesIO(proc.stdout), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


def normalize(audio: np.ndarray, peak: float = 0.9) -> np.ndarray:
    max_val = float(np.max(np.abs(audio)))
    if max_val < 1e-6:
        return audio
    return audio * (peak / max_val)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a reference voice clip")
    parser.add_argument("input", type=Path, help="Audio/video file (mp3, wav, mp4, etc.)")
    parser.add_argument("--start", type=parse_time, default=0.0, help="Start time (seconds or mm:ss)")
    parser.add_argument("--duration", type=float, default=10.0, help="Clip length in seconds")
    parser.add_argument("--out", type=Path, default=settings.reference_voice_path, help="Output WAV path")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    duration = min(max(args.duration, MIN_SEC), MAX_SEC)
    if args.duration < MIN_SEC or args.duration > MAX_SEC:
        print(f"Note: duration clamped to {duration}s")

    print(f"Extracting {duration}s from {args.input} (start={args.start}s)…")
    audio, sr = load_with_ffmpeg(args.input, args.start, duration)
    audio = normalize(audio)

    out = args.out
    if not out.is_absolute():
        out = ROOT / out

    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, audio, sr)

    secs = len(audio) / sr
    print(f"Saved {secs:.1f}s reference clip → {out}")
    print()
    print("Tips for a good clone:")
    print("  • One speaker only, no background music")
    print("  • Clear conversational speech, not whispering or shouting")
    print("  • Natural pace — interview answers work great")
    print()
    print("Set in .env if needed:")
    try:
        rel = out.relative_to(ROOT)
        print(f"  REFERENCE_VOICE={rel}")
    except ValueError:
        print(f"  REFERENCE_VOICE={out}")


if __name__ == "__main__":
    main()
