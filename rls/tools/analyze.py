"""Local scene detection + representative frame extraction (PySceneDetect + ffmpeg)."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from ..deps import ensure_feature
from ..env import require_ffmpeg


def run(args) -> int:
    require_ffmpeg()
    ensure_feature("analyze")
    from scenedetect import detect, AdaptiveDetector  # lazy

    inp = Path(args.input)
    if not inp.is_file():
        raise SystemExit(f"input not found: {inp}")
    outdir = Path(args.outdir); frames = outdir / "frames"
    frames.mkdir(parents=True, exist_ok=True)

    scenes = detect(str(inp), AdaptiveDetector(adaptive_threshold=args.threshold))
    report = []
    for i, (start, end) in enumerate(scenes):
        a, b = start.get_seconds(), end.get_seconds()
        mid = (a + b) / 2.0
        fp = frames / f"scene_{i:03d}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{mid:.3f}",
                        "-i", str(inp), "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
        report.append({"scene": i, "start_s": round(a, 3), "end_s": round(b, 3),
                       "frame": str(fp).replace("\\", "/")})

    (outdir / "scenes.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[rls] detected {len(report)} scenes")
    print(str(outdir / "scenes.json"))
    return 0
