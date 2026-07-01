"""Local music generation via MusicGen (audiocraft)."""
from __future__ import annotations
from pathlib import Path
from ..deps import ensure_feature


def run(args) -> int:
    ensure_feature("music")
    from audiocraft.models import MusicGen          # lazy
    from audiocraft.data.audio import audio_write

    model = MusicGen.get_pretrained(f"facebook/musicgen-{args.model}")
    model.set_generation_params(duration=args.duration)
    print(f"[rls] Generating {args.duration:.0f}s of music...")
    wav = model.generate([args.prompt])

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    stem = str(out.with_suffix(""))
    audio_write(stem, wav[0].cpu(), model.sample_rate,
                strategy="loudness", loudness_compressor=True)
    print(stem + ".wav")
    return 0
