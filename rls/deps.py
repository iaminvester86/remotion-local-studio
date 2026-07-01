"""
deps.py — managed, on-demand dependency installation.

All installs target the CURRENTLY RUNNING interpreter (sys.executable), which is
the project venv when you run `rls`. A marker file per feature prevents repeat
installs. This is what keeps heavy GPU libraries out of the base install while
still making every feature work the first time it is used.
"""
from __future__ import annotations

import subprocess
import sys

from .env import STATE_DIR, detect_accelerator

# Feature -> pip packages. torch is handled separately (needs accelerator-specific index).
FEATURES: dict[str, dict] = {
    "transcribe": {"torch": False, "pkgs": ["faster-whisper>=1.0"]},
    "tts":        {"torch": False, "pkgs": ["piper-tts>=1.2"]},
    "analyze":    {"torch": False, "pkgs": ["scenedetect>=0.6", "opencv-python>=4.6"]},
    "music":      {"torch": True,  "pkgs": ["audiocraft>=1.3"]},
    "image":      {"torch": True,  "pkgs": [
        "diffusers>=0.30", "transformers>=4.44", "accelerate>=0.33",
        "safetensors", "sentencepiece", "protobuf", "pillow",
    ]},
    "video":      {"torch": True,  "pkgs": [
        "diffusers>=0.30", "transformers>=4.44", "accelerate>=0.33",
        "imageio", "imageio-ffmpeg", "sentencepiece",
    ]},
}


def _pip(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "pip", "install", *args], check=True)


def _marker(name: str):
    return STATE_DIR / f"{name}.installed"


def install_torch() -> None:
    if _marker("torch").exists():
        return
    import os
    from .env import detect_os
    acc = detect_accelerator()
    # Allow a manual override, e.g. RLS_TORCH_INDEX=https://download.pytorch.org/whl/cu121
    index = os.environ.get("RLS_TORCH_INDEX")
    print(f"[rls] Installing PyTorch for accelerator: {acc}")
    if acc == "cpu":
        index = index or "https://download.pytorch.org/whl/cpu"
        _pip("torch", "torchvision", "torchaudio", "--index-url", index)
    elif acc == "cuda":
        # IMPORTANT: on Windows the default PyPI torch wheels are CPU-only; you must
        # use the CUDA index to get GPU support. On Linux the default bundles CUDA,
        # but using the explicit CUDA index works there too, so we always set it.
        index = index or "https://download.pytorch.org/whl/cu124"
        _pip("torch", "torchvision", "torchaudio", "--index-url", index)
    else:  # mps / unknown -> default wheels (macOS arm64 wheels include MPS)
        if index:
            _pip("torch", "torchvision", "torchaudio", "--index-url", index)
        else:
            _pip("torch", "torchvision", "torchaudio")
    _marker("torch").touch()


def ensure_feature(name: str) -> None:
    """Install a known feature's dependencies once. Raises if name is unknown."""
    if name not in FEATURES:
        raise SystemExit(f"Unknown feature '{name}'. Known: {', '.join(FEATURES)}")
    if _marker(name).exists():
        return
    spec = FEATURES[name]
    if spec["torch"]:
        install_torch()
    print(f"[rls] Installing dependencies for '{name}' (first use)...")
    _pip(*spec["pkgs"])
    _marker(name).touch()


def ensure_packages(marker: str, packages: list[str], need_torch: bool = False) -> None:
    """Generic installer for extensions: managed, marker-guarded, idempotent."""
    if _marker(marker).exists():
        return
    if need_torch:
        install_torch()
    print(f"[rls] Installing extension dependencies for '{marker}'...")
    _pip(*packages)
    _marker(marker).touch()


def installed_features() -> dict[str, bool]:
    status = {"torch": _marker("torch").exists()}
    for f in FEATURES:
        status[f] = _marker(f).exists()
    return status
