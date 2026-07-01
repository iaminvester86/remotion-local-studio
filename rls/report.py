"""Shared environment/status report, consumed by `rls doctor` and the web UI."""
from __future__ import annotations

from . import __version__
from . import env, deps

# Plain-language metadata for each tool, used to drive the UI.
TOOLS = {
    "transcribe": {"label": "Captions & transcript", "gpu": "optional",
                   "feature": "transcribe",
                   "blurb": "Turn speech in an audio or video file into subtitles."},
    "tts":        {"label": "Voiceover", "gpu": "optional", "feature": "tts",
                   "blurb": "Read a script aloud in a synthetic voice."},
    "image":      {"label": "Image", "gpu": "recommended", "feature": "image",
                   "blurb": "Create a still image from a text description."},
    "music":      {"label": "Music", "gpu": "recommended", "feature": "music",
                   "blurb": "Generate a background music bed from a description."},
    "video":      {"label": "Video clip (experimental)", "gpu": "required", "feature": "video",
                   "blurb": "Create a short moving clip from text. Slow; needs a strong GPU."},
    "analyze":    {"label": "Analyze footage", "gpu": "no", "feature": "analyze",
                   "blurb": "Find scene cuts in a video and pull one frame per scene."},
}


def report() -> dict:
    feats = deps.installed_features()
    binaries = {b: env.has(b) for b in ("node", "npm", "python3", "ffmpeg")}
    return {
        "version": __version__,
        "os": env.detect_os(),
        "accelerator": env.detect_accelerator(),
        "binaries": binaries,
        "features": feats,
        "tools": TOOLS,
    }
