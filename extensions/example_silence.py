"""
example_silence.py — a tiny reference extension.

It generates N seconds of silent audio with FFmpeg. It needs no extra Python
packages, so REQUIREMENTS is empty. Use it as a template for your own tools.

Copy this file, rename it, declare REQUIREMENTS for any pip deps you need, and
implement `register`. Install its deps with:  rls ext install <name>
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REQUIREMENTS: list[str] = []      # pip packages your tool needs (installed on demand)
NEEDS_TORCH = False               # set True if your deps require PyTorch


def _handler(args) -> int:
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=stereo", "-t", str(args.seconds), str(out)],
        check=True,
    )
    print(str(out))
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser("silence", help="[example ext] generate N seconds of silent audio")
    p.add_argument("--seconds", type=float, default=3.0)
    p.add_argument("--out", required=True)
    p.set_defaults(func=_handler)
