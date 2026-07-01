"""Deterministic local assembly via FFmpeg. No models, no APIs."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..env import require_ffmpeg


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def kenburns(args) -> int:
    require_ffmpeg()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    fps = 30; frames = int(args.seconds * fps)
    vf = (f"scale={args.width}*2:-1,"
          f"zoompan=z='min(zoom+0.0008,1.4)':d={frames}:s={args.width}x{args.height}:fps={fps},"
          f"format=yuv420p")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", args.image,
          "-vf", vf, "-t", str(args.seconds), str(out)])
    print(str(out)); return 0


def crossfade(args) -> int:
    require_ffmpeg()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", args.a], capture_output=True, text=True, check=True)
    alen = float(probe.stdout.strip())
    off = max(alen - args.dur, 0)
    fc = f"[0][1]xfade=transition=fade:duration={args.dur}:offset={off},format=yuv420p"
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.a, "-i", args.b,
          "-filter_complex", fc, str(out)])
    print(str(out)); return 0


def concat(args) -> int:
    require_ffmpeg()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    import tempfile, os
    listf = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for f in args.clips:
        listf.write(f"file '{os.path.abspath(f)}'\n")
    listf.close()
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
          "-i", listf.name, "-c:v", "libx264", "-c:a", "aac", str(out)])
    os.unlink(listf.name)
    print(str(out)); return 0


def mixaudio(args) -> int:
    require_ffmpeg()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    fc = (f"[1:a]volume={args.vol}[bed];"
          f"[0:a][bed]amix=inputs=2:duration=first:dropout_transition=2[a]")
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.video, "-i", args.audio,
          "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
          "-c:v", "copy", "-c:a", "aac", str(out)])
    print(str(out)); return 0


def burnsubs(args) -> int:
    require_ffmpeg()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.video,
          "-vf", f"subtitles='{args.subs}'", "-c:a", "copy", str(out)])
    print(str(out)); return 0
