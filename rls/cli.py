"""
cli.py — the `rls` command. Lightweight: heavy libraries are imported only inside
the handler that needs them, so `rls --help` and `rls doctor` work on a bare venv.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from . import env, deps, extensions


# ---- meta commands ---------------------------------------------------------

def cmd_doctor(args) -> int:
    from .report import report
    r = report()
    print(f"remotion-local-studio {r['version']}")
    print(f"OS           : {r['os']}")
    print(f"Accelerator  : {r['accelerator']}  (cuda=GPU, mps=Apple Silicon, cpu=none)")
    hints = {"node": "https://nodejs.org (Remotion)", "npm": "ships with Node.js",
             "python3": "https://python.org", "ffmpeg": "brew/apt/winget install ffmpeg"}
    print("System binaries:")
    for b, ok in r["binaries"].items():
        print(f"  {'ok  ' if ok else 'MISS'} {b:8} {'' if ok else '-> ' + hints.get(b, '')}")
    print("Feature dependencies (installed on first use):")
    for name, ok in r["features"].items():
        print(f"  {'ok' if ok else '--'} {name}")
    exts = extensions.list_extensions()
    print(f"Extensions   : {', '.join(exts) if exts else '(none)'}")
    if r["accelerator"] == "cpu":
        print("\nNote: no GPU. Transcription, voiceover, captions, analysis and assembly work.")
        print("Image generation will be slow; local text-to-video is impractical.")
    print("\nTip: run `rls ui` for a beginner-friendly web interface.")
    return 0


def cmd_install(args) -> int:
    targets = list(deps.FEATURES) if args.feature == "all" else [args.feature]
    for t in targets:
        deps.ensure_feature(t)
    print("[rls] done.")
    return 0


def cmd_ui(args) -> int:
    # Ensure UI deps exist, installing on first use so a fresh clone "just works".
    try:
        import fastapi, uvicorn  # noqa: F401
    except ImportError:
        deps.ensure_packages("ui", ["fastapi>=0.110", "uvicorn[standard]>=0.27",
                                    "python-multipart>=0.0.9"])
    from .ui.server import serve
    serve(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def cmd_ext(args) -> int:
    if args.ext_cmd == "list":
        for e in extensions.list_extensions():
            print(e)
        return 0
    if args.ext_cmd == "install":
        return extensions.install_extension(args.name)
    return 1


# ---- tool handlers (lazy module import) ------------------------------------

def _lazy(modname, args):
    from importlib import import_module
    return import_module(f".tools.{modname}", package="rls").run(args)


# ---- parser ----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rls", description="Local, no-API video production toolkit.")
    p.add_argument("--version", action="version", version=f"rls {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Report environment, binaries, and installed features").set_defaults(func=cmd_doctor)

    pui = sub.add_parser("ui", help="Launch the beginner-friendly web interface")
    pui.add_argument("--host", default="127.0.0.1")
    pui.add_argument("--port", type=int, default=8765)
    pui.add_argument("--no-browser", action="store_true", help="don't auto-open the browser")
    pui.set_defaults(func=cmd_ui)

    pi = sub.add_parser("install", help="Install a feature's dependencies now")
    pi.add_argument("feature", choices=list(deps.FEATURES) + ["all"])
    pi.set_defaults(func=cmd_install)

    pt = sub.add_parser("transcribe", help="Audio/video -> SRT + word-level JSON (Whisper)")
    pt.add_argument("--input", required=True)
    pt.add_argument("--out", required=True, help="output path WITHOUT extension")
    pt.add_argument("--model", default="base", help="tiny|base|small|medium|large-v3")
    pt.add_argument("--lang", default=None)
    pt.set_defaults(func=lambda a: _lazy("transcribe", a))

    pv = sub.add_parser("tts", help="Narration from text (Piper)")
    pv.add_argument("--text", default="")
    pv.add_argument("--text-file", default="")
    pv.add_argument("--out", required=True)
    pv.add_argument("--voice", default="en_US-amy-medium")
    pv.set_defaults(func=lambda a: _lazy("tts", a))

    pm = sub.add_parser("music", help="Background music bed (MusicGen)")
    pm.add_argument("--prompt", required=True)
    pm.add_argument("--duration", type=float, default=15.0)
    pm.add_argument("--out", required=True)
    pm.add_argument("--model", default="small", choices=["small", "medium", "large"])
    pm.set_defaults(func=lambda a: _lazy("music", a))

    pim = sub.add_parser("image", help="Image generation (FLUX schnell / SDXL)")
    pim.add_argument("--prompt", required=True)
    pim.add_argument("--out", required=True)
    pim.add_argument("--width", type=int, default=1024)
    pim.add_argument("--height", type=int, default=1024)
    pim.add_argument("--model", default="flux-schnell", choices=["flux-schnell", "sdxl"])
    pim.add_argument("--steps", type=int, default=None)
    pim.add_argument("--seed", type=int, default=None)
    pim.set_defaults(func=lambda a: _lazy("image", a))

    pvid = sub.add_parser("video", help="EXPERIMENTAL text-to-video (CogVideoX, CUDA only)")
    pvid.add_argument("--prompt", required=True)
    pvid.add_argument("--out", required=True)
    pvid.add_argument("--frames", type=int, default=49)
    pvid.add_argument("--fps", type=int, default=8)
    pvid.add_argument("--steps", type=int, default=50)
    pvid.set_defaults(func=lambda a: _lazy("video", a))

    pa = sub.add_parser("analyze", help="Scene cuts + frames (PySceneDetect)")
    pa.add_argument("--input", required=True)
    pa.add_argument("--outdir", default=".rls/analysis")
    pa.add_argument("--threshold", type=float, default=27.0)
    pa.set_defaults(func=lambda a: _lazy("analyze", a))

    # ffmpeg assembly ops grouped under `rls ff <op>`
    pf = sub.add_parser("ff", help="FFmpeg assembly ops (no models)")
    ff = pf.add_subparsers(dest="ff_cmd", required=True)
    from .tools import ffmpeg_ops as F
    k = ff.add_parser("kenburns"); k.add_argument("image"); k.add_argument("out")
    k.add_argument("seconds", type=float, nargs="?", default=6.0)
    k.add_argument("--width", type=int, default=1920); k.add_argument("--height", type=int, default=1080)
    k.set_defaults(func=F.kenburns)
    c = ff.add_parser("crossfade"); c.add_argument("a"); c.add_argument("b"); c.add_argument("out")
    c.add_argument("dur", type=float, nargs="?", default=1.0); c.set_defaults(func=F.crossfade)
    cc = ff.add_parser("concat"); cc.add_argument("out"); cc.add_argument("clips", nargs="+")
    cc.set_defaults(func=F.concat)
    mx = ff.add_parser("mixaudio"); mx.add_argument("video"); mx.add_argument("audio"); mx.add_argument("out")
    mx.add_argument("vol", type=float, nargs="?", default=0.3); mx.set_defaults(func=F.mixaudio)
    bs = ff.add_parser("burnsubs"); bs.add_argument("video"); bs.add_argument("subs"); bs.add_argument("out")
    bs.set_defaults(func=F.burnsubs)

    pe = sub.add_parser("ext", help="Manage user extensions in extensions/")
    es = pe.add_subparsers(dest="ext_cmd", required=True)
    es.add_parser("list")
    ei = es.add_parser("install"); ei.add_argument("name")
    pe.set_defaults(func=cmd_ext)

    # let extensions add their own top-level subcommands
    extensions.load_into(sub)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
