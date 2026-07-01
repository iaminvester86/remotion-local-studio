#!/usr/bin/env bash
# Double-click friendly launcher (macOS/Linux). Runs setup if needed, then opens the UI.
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo "First run: installing. This can take a few minutes..."
  ./install.sh || { echo "Install failed. See messages above."; read -p "Press Enter to close"; exit 1; }
fi
# shellcheck disable=SC1091
. .venv/bin/activate
rls ui
