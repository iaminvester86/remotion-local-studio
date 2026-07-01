#!/usr/bin/env bash
# install.sh — one-shot local setup for macOS / Linux.
# Creates a project venv, installs the CLI + CPU-friendly core tools, and checks
# system binaries. Heavy GPU tools install later, on first use.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> remotion-local-studio installer"

# --- system binaries -------------------------------------------------------
need() { command -v "$1" >/dev/null 2>&1; }
os="$(uname -s)"
miss=0
need python3 || { echo "  MISSING python3  -> install Python 3.10+ from https://python.org"; miss=1; }
if ! need ffmpeg; then
  case "$os" in
    Darwin) echo "  MISSING ffmpeg   -> brew install ffmpeg" ;;
    Linux)  echo "  MISSING ffmpeg   -> sudo apt-get install -y ffmpeg" ;;
    *)      echo "  MISSING ffmpeg   -> https://ffmpeg.org/download.html" ;;
  esac
  miss=1
fi
need node || echo "  NOTE: Node.js not found. Needed only for Remotion rendering (https://nodejs.org)."
[ "$miss" -eq 1 ] && { echo "Install the missing required tools above, then re-run ./install.sh"; exit 1; }

# --- venv + package --------------------------------------------------------
if [ ! -d ".venv" ]; then
  echo "==> Creating virtualenv at .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip wheel >/dev/null
echo "==> Installing the rls CLI (editable) + CPU-friendly core tools"
pip install -e .
pip install -r requirements.txt

echo
echo "==> Done. Activate the environment with:  source .venv/bin/activate"
echo "    Then check everything with:           rls doctor"
echo
echo "Heavy GPU tools install on demand:"
echo "    rls install image    # FLUX / SDXL  (GPU recommended)"
echo "    rls install music    # MusicGen     (GPU recommended)"
echo "    rls install video    # CogVideoX    (CUDA only, experimental)"
