"""
env.py — paths, platform detection, and shared helpers.

No heavy imports here. Everything in this module must work on a bare Python
install so that `rls --help` and `rls doctor` run before any ML dependency exists.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

# Repo root: this file is at <repo>/rls/env.py
REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.environ.get("RLS_CACHE", REPO_ROOT / ".cache"))
STATE_DIR = CACHE_DIR / "state"          # markers recording installed features
MODELS_DIR = CACHE_DIR / "models"        # piper voices etc.
EXTENSIONS_DIR = REPO_ROOT / "extensions"

for _d in (CACHE_DIR, STATE_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def detect_os() -> str:
    s = platform.system()
    return {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(s, "unknown")


def detect_accelerator() -> str:
    """Return 'cuda', 'mps', or 'cpu' without importing torch."""
    if shutil.which("nvidia-smi"):
        try:
            subprocess.run(["nvidia-smi"], capture_output=True, check=True)
            return "cuda"
        except Exception:
            pass
    if detect_os() == "macos" and platform.machine() == "arm64":
        return "mps"
    return "cpu"


def has(binary: str) -> bool:
    return shutil.which(binary) is not None


def require_ffmpeg() -> None:
    if has("ffmpeg"):
        return
    hints = {
        "macos": "brew install ffmpeg",
        "linux": "sudo apt-get install -y ffmpeg   (or your distro's package manager)",
        "windows": "winget install Gyan.FFmpeg   (or choco install ffmpeg)",
    }
    os_name = detect_os()
    raise SystemExit(
        "ffmpeg is required but was not found.\n"
        f"Install it with: {hints.get(os_name, 'see https://ffmpeg.org/download.html')}"
    )


def outdir(sub: str) -> Path:
    """public/<sub> under the CURRENT working directory (the Remotion project)."""
    d = Path("public") / sub
    d.mkdir(parents=True, exist_ok=True)
    return d
