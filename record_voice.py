#!/usr/bin/env python3
"""Record a local reference voice clip."""

import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from rich.console import Console

from app.audio import record_until_silence
from app.config import settings

console = Console()

SAMPLE_LINES = [
    "Hey, I'm here for you. Whatever you're feeling right now, that's completely okay.",
    "You don't have to have it all figured out. We can just talk, no pressure at all.",
    "I really mean it when I say I'm listening. Tell me what's on your mind.",
]


def main() -> None:
    out = settings.reference_voice_path
    out.parent.mkdir(parents=True, exist_ok=True)

    console.print("[bold]Record Nikki's voice[/]")
    console.print("Read one of these lines naturally (5–15 seconds):\n")
    for i, line in enumerate(SAMPLE_LINES, 1):
        console.print(f"  [cyan]{i}.[/] {line}")
    console.print()

    input("Press Enter when ready, then start speaking…")
    console.print("[yellow]🎤 Recording… pause for 1.2s to finish[/]")

    audio = record_until_silence(max_duration=20.0)
    duration = len(audio) / settings.sample_rate

    if duration < 3.0:
        console.print("[red]Too short — aim for at least 5 seconds. Try again.[/]")
        sys.exit(1)

    sf.write(out, audio, settings.sample_rate)
    console.print(f"[green]Saved {duration:.1f}s clip → {out}[/]")


if __name__ == "__main__":
    main()
