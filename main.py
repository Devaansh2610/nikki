#!/usr/bin/env python3
"""Nikki — voice companion chatbot with speech in / speech out."""

import sys

from app.chat import NikkiChat


def main() -> int:
    try:
        NikkiChat().run()
    except RuntimeError as exc:
        print(f"\nStartup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
