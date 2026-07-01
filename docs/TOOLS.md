# Tools reference

Every tool is a subcommand of `rls`. Run `rls <tool> --help` for exact flags.
Output paths are yours to choose; the examples write under `public/` so Remotion's
`staticFile()` can resolve them.

## transcribe (Whisper)
```
rls transcribe --input public/audio/vo.wav --out public/captions/vo --model base
```
Produces `vo.srt` and `vo.json` (word-level tokens for animated captions).
Reliability: high. CPU is fine. Use `--model small|medium` for accents/noise.

## tts (Piper)
```
rls tts --text-file script.txt --out public/audio/vo.wav --voice en_US-amy-medium
```
Reliability: high, CPU fine. Voice is intelligible but flatter than hosted TTS.
Other voices: browse https://huggingface.co/rhasspy/piper-voices and pass the id.

## music (MusicGen)
```
rls music --prompt "warm lo-fi jazz, soft piano" --duration 20 --out public/music/bed.wav
```
Reliability: medium. GPU recommended. Good for instrumental beds, weak on full songs.

## image (FLUX schnell / SDXL)
```
rls image --prompt "cinematic skyline at dusk" --out public/images/sky.png --width 1920 --height 1080
```
Reliability: good on a GPU (>=12GB VRAM), impractical on CPU.

## video (CogVideoX) — experimental
```
rls video --prompt "a paper plane gliding" --out public/clips/plane.mp4
```
CUDA only, slow, lower quality than hosted models. Prefer a still + Ken Burns.

## analyze (PySceneDetect)
```
rls analyze --input footage.mp4 --outdir .rls/analysis
```
Writes `scenes.json` (cut timestamps) and one JPEG per scene under `frames/`.
This is the local stand-in for a video-understanding API: you read the frames.

## ff (FFmpeg assembly, no models)
```
rls ff kenburns public/images/sky.png public/clips/sky.mp4 6
rls ff crossfade a.mp4 b.mp4 out.mp4 1
rls ff concat out.mp4 a.mp4 b.mp4 c.mp4
rls ff mixaudio video.mp4 public/music/bed.wav out.mp4 0.25
rls ff burnsubs video.mp4 subs.srt out.mp4
```
Reliability: high. Runs anywhere FFmpeg is installed.
