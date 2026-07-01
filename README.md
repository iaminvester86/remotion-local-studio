# 🎬 Remotion Local Studio

A fully local, **no-API** video production toolkit for [Remotion](https://www.remotion.dev).
Voiceovers, captions, music, images, transitions, and footage analysis run on your
own machine. You clone the repo, run one installer, and use the `rls` command. No
marketplace, no plugin system, no API keys.

This is an independent, local-first re-implementation of the idea behind
[remotion-superpowers](https://github.com/DojoCodingLabs/remotion-superpowers) by
Dojo Coding Labs (which uses hosted paid APIs). Credit to them for the concept;
this version swaps every hosted service for an open local tool. MIT licensed with
attribution retained.

> Status: **early (v0.2.0).** The CLI wiring, install-on-demand logic, FFmpeg
> assembly, and the extension system are tested in this repo. The ML model
> pipelines (Whisper, Piper, MusicGen, diffusers, CogVideoX) are written to each
> library's standard usage but have **not** been run on every hardware setup.
> Validate on your machine. See "Honesty notes" at the bottom.

## What you get

| Capability | Local tool | Command | GPU? |
| --- | --- | --- | --- |
| Transcription / captions | faster-whisper | `rls transcribe` | optional |
| Voiceover | Piper | `rls tts` | optional |
| Footage analysis / review | PySceneDetect + FFmpeg | `rls analyze` | no |
| Assembly (Ken Burns, crossfade, mix, concat, burn subs) | FFmpeg | `rls ff ...` | no |
| Music bed | MusicGen | `rls music` | recommended |
| Image generation | FLUX schnell / SDXL | `rls image` | strongly recommended |
| Text-to-video (experimental) | CogVideoX | `rls video` | CUDA only |
| Your own tools | anything | `extensions/` + `rls ext` | up to you |

## Easiest way to use it: the web UI

After installing (below), run:
```
rls ui
```
This opens a local web page in your browser with a numbered, step-by-step interface:
voiceover, captions, image, motion clip, music, and analysis, each with simple forms,
drag-and-drop file pickers, and a preview of the result. A "Start here" screen checks
your hardware and tells you exactly what (if anything) to install. The page runs the
same tools as the command line, so nothing can drift. Full details in
[docs/UI.md](docs/UI.md).

For non-technical users, double-click `start-ui.sh` (macOS/Linux) or run
`start-ui.ps1` (Windows). On first run it installs everything, then opens the UI.

## Requirements
- **Python 3.10+** and **FFmpeg** (always).
- **Node.js 18+** for Remotion rendering.
- A **CUDA GPU** is strongly recommended for image/music/video. CPU-only still
  gives you transcription, captions, voiceover, analysis, and all assembly.

## Install (clone + one script)

macOS / Linux:
```bash
git clone https://github.com/iaminvester86/remotion-local-studio.git
cd remotion-local-studio
./install.sh
source .venv/bin/activate
rls doctor
```

Windows (PowerShell):
```powershell
git clone https://github.com/iaminvester86/remotion-local-studio.git
cd remotion-local-studio
.\install.ps1
.\.venv\Scripts\Activate.ps1
rls doctor
```

`install.sh` / `install.ps1` create a project virtualenv at `.venv`, install the
`rls` CLI plus the CPU-friendly core tools, and check your system binaries.
`rls doctor` then reports your OS, accelerator, binaries, and which features are
installed.

## Install the heavy tools when you want them
These are kept out of the base install so nothing huge downloads until you ask:
```bash
rls install image    # FLUX / SDXL  (+ correct PyTorch build for your hardware)
rls install music    # MusicGen
rls install video    # CogVideoX  (CUDA only, experimental)
rls install all      # everything
```
Each installs once and records a marker, so it never reinstalls.

## Use it
Run commands from inside your Remotion project (so `public/` resolves). Full
recipes are in [docs/WORKFLOWS.md](docs/WORKFLOWS.md); per-tool flags in
[docs/TOOLS.md](docs/TOOLS.md). Quick taste:
```bash
rls tts --text-file script.txt --out public/audio/vo.wav
rls transcribe --input public/audio/vo.wav --out public/captions/vo
rls image --prompt "cinematic skyline at dusk" --out public/images/sky.png
rls ff kenburns public/images/sky.png public/clips/sky.mp4 6
```
Setting up the Remotion project itself: [remotion/README.md](remotion/README.md).

## Add your own tools
Anything that runs locally can be added without touching the core. Drop a file in
`extensions/`, declare its pip `REQUIREMENTS`, implement `register(subparsers)`,
and install its deps with `rls ext install <name>`. The dependency management is
the same marker-guarded venv system the built-ins use. See
[docs/ADDING-TOOLS.md](docs/ADDING-TOOLS.md) and the working template at
`extensions/example_silence.py`.

## Dependency map (the correlations, so nothing dangles)

| Feature | System dep | Python deps | Installed by | Writes to | Consumed by |
| --- | --- | --- | --- | --- | --- |
| CLI itself | python3 | none | `pip install -e .` (installer) | — | you / Remotion |
| web UI | python3 | fastapi, uvicorn, python-multipart | `requirements.txt` (core) | serves the above | your browser |
| `transcribe` | ffmpeg | faster-whisper | `requirements.txt` (core) | `*.srt`, `*.json` | captions component |
| `tts` | — | piper-tts (+ voice download) | `requirements.txt` (core) | `public/audio/*.wav` | Remotion `<Audio>`, `transcribe` |
| `analyze` | ffmpeg | scenedetect[opencv] | `requirements.txt` (core) | `.rls/.../scenes.json`, frames | your review |
| `ff *` | ffmpeg | none | nothing extra | `public/clips/*`, etc. | Remotion |
| `music` | ffmpeg | torch + audiocraft | `rls install music` | `public/music/*.wav` | Remotion, `ff mixaudio` |
| `image` | — | torch + diffusers stack | `rls install image` | `public/images/*.png` | Remotion, `ff kenburns` |
| `video` | ffmpeg | torch + diffusers stack | `rls install video` | `public/clips/*.mp4` | Remotion |
| extensions | yours | declared `REQUIREMENTS` | `rls ext install <name>` | yours | yours |

Notes that prevent the usual breakages:
- **PyTorch is never installed by `requirements.txt`.**
- **Windows + NVIDIA GPU note.** On Windows the default PyTorch is CPU-only; `rls install` automatically uses the CUDA wheel index (cu124) when a CUDA GPU is detected. Override the index with the `RLS_TORCH_INDEX` environment variable if you need a different CUDA version. It needs a hardware-specific
  index, so `rls install` handles it: CPU wheels from the PyTorch CPU index, default
  wheels for CUDA/MPS. This is the single most common source of "it won't install"
  pain, handled in one place (`rls/deps.py`).
- **Heavy imports are lazy.** `rls --help` and `rls doctor` run before any ML
  library exists, so a fresh clone is never in a broken state.
- **One venv, one marker store.** Everything (core, on-demand features, extensions)
  installs into `.venv` and is tracked under `.cache/state/`. Delete `.cache/` to
  force re-detection; delete `.venv/` to start clean.
- **Working directory matters.** Tools resolve `public/...` relative to where you
  run them. Run inside the Remotion project.

## Honesty notes
- **Not yet battle-tested.** v0.2.0. The plumbing is verified; the model outputs are
  not validated on all hardware. Expect to debug specifics on your machine.
- **Local generation has real limits.** Music and especially text-to-video are
  below hosted-service quality and demand a strong GPU. The toolkit steers you
  toward footage and Ken Burns stills for good reason.
- **Model names drift.** The open-model landscape moves fast; the defaults here are
  representative, not permanent best picks. Swapping them is a small edit in the
  relevant `rls/tools/*.py`.
- **"Free" means no API fees**, not zero cost: model downloads are large and GPU
  time and electricity are real.

## Credit & license
Concept inspired by **remotion-superpowers** by
[Dojo Coding Labs](https://dojocoding.io) (MIT). This local-first re-implementation
is also MIT. See [LICENSE](LICENSE).
