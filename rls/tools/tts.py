"""Local text-to-speech via Piper. Downloads the requested voice on first use."""
from __future__ import annotations

import subprocess
import sys
import urllib.request
from pathlib import Path

from ..deps import ensure_feature
from ..env import MODELS_DIR

VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def _ensure_voice(voice: str) -> Path:
    # Voice id format: LOCALE-NAME-QUALITY  (LOCALE itself contains '_'), e.g. en_US-amy-medium
    parts = voice.split("-")
    if len(parts) != 3:
        raise SystemExit(f"Voice '{voice}' must be LOCALE-NAME-QUALITY, e.g. en_US-amy-medium")
    locale, name, quality = parts
    lang = locale.split("_")[0]
    vdir = MODELS_DIR / "piper"
    vdir.mkdir(parents=True, exist_ok=True)
    onnx = vdir / f"{voice}.onnx"
    if not onnx.exists():
        url = f"{VOICE_BASE}/{lang}/{locale}/{name}/{quality}/{voice}.onnx"
        print(f"[rls] Downloading Piper voice: {voice}")
        try:
            urllib.request.urlretrieve(url, onnx)
            urllib.request.urlretrieve(url + ".json", str(onnx) + ".json")
        except Exception as e:
            raise SystemExit(
                f"Could not download voice '{voice}' ({e}).\n"
                "Check the exact id at https://huggingface.co/rhasspy/piper-voices"
            )
    return onnx


def run(args) -> int:
    ensure_feature("tts")
    text = args.text
    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    if not text:
        raise SystemExit("Provide --text or --text-file")

    onnx = _ensure_voice(args.voice)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Use the piper console script from the same venv as this interpreter.
    piper = Path(sys.executable).parent / "piper"
    cmd = [str(piper), "--model", str(onnx), "--output_file", str(out)]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    print(str(out))
    return 0
