"""Local transcription via faster-whisper. Outputs SRT + word-level JSON."""
from __future__ import annotations

import json
from pathlib import Path

from ..deps import ensure_feature


def _ts(seconds: float) -> str:
    h = int(seconds // 3600); m = int((seconds % 3600) // 60)
    s = int(seconds % 60); ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def run(args) -> int:
    ensure_feature("transcribe")
    from faster_whisper import WhisperModel  # lazy

    inp = Path(args.input)
    if not inp.is_file():
        raise SystemExit(f"input not found: {inp}")

    device, compute = "cpu", "int8"
    try:
        import torch
        if torch.cuda.is_available():
            device, compute = "cuda", "float16"
    except Exception:
        pass

    model = WhisperModel(args.model, device=device, compute_type=compute)
    segments, info = model.transcribe(str(inp), language=args.lang, word_timestamps=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    words, srt, idx = [], [], 1
    for seg in segments:
        srt += [str(idx), f"{_ts(seg.start)} --> {_ts(seg.end)}", seg.text.strip(), ""]
        idx += 1
        for w in (seg.words or []):
            a, b = int(w.start * 1000), int(w.end * 1000)
            words.append({"text": w.word, "startMs": a, "endMs": b,
                          "timestampMs": (a + b) // 2,
                          "confidence": round(float(getattr(w, "probability", 1.0)), 4)})

    Path(str(out) + ".srt").write_text("\n".join(srt), encoding="utf-8")
    Path(str(out) + ".json").write_text(json.dumps(words, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"[rls] language={info.language} prob={info.language_probability:.2f}")
    print(f"{out}.srt")
    print(f"{out}.json")
    return 0
