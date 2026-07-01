# The web interface

The UI is the easiest way to use the toolkit. It is a local web page that runs the
same tools as the `rls` command, with forms instead of typed flags.

## Start it

Easiest (non-technical):
- macOS/Linux: double-click `start-ui.sh` (or run `./start-ui.sh`).
- Windows: right-click `start-ui.ps1` and "Run with PowerShell".

On first run it installs everything, then opens your browser automatically. After
that it opens in a second or two.

If you already installed and activated the venv, just run:
```
rls ui
```
Options: `rls ui --port 9000`, `rls ui --no-browser`. It binds to `127.0.0.1`
(your machine only); nothing is exposed to the network.

## What you see

- A numbered list of steps down the left, in the order you'd usually do them:
  Voiceover, Captions, Image, Motion clip, Music, Video, Analyze.
- A "Start here" screen showing whether FFmpeg and a GPU are present, with the
  exact install command if something is missing, plus buttons to install the
  optional heavy tools (image, music, video) only if you want them.
- A working panel for each step with plain-language fields, file drag-and-drop,
  and a preview of the result (play the audio, view the image, watch the clip).
- An activity panel on the right showing each job's live progress and log.

## How it relates to the command line

Every button runs the matching `rls` command as a background job and streams its
output to the page. The command it ran is shown under each job, so the UI doubles
as a way to learn the CLI. There is one code path: the UI cannot do anything the
CLI can't, and they never drift apart.

## Honest limits

- The first time you use Image, Music, or Video, it downloads large model files.
  The progress appears in the activity log; it can take a while.
- On a machine with no GPU, Image and Music are slow and Video is not practical.
  The Start-here screen tells you this based on your actual hardware.
- The UI does not yet assemble the final Remotion composition for you. It produces
  the assets; you place them in your Remotion project and render. See
  `docs/WORKFLOWS.md` and `remotion/README.md`.
