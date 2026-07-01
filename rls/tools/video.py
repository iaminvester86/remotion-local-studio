"""EXPERIMENTAL local text-to-video via diffusers (CogVideoX). CUDA only."""
from __future__ import annotations
from pathlib import Path
from ..deps import ensure_feature


def run(args) -> int:
    ensure_feature("video")
    import torch                                     # lazy
    from diffusers import CogVideoXPipeline
    from diffusers.utils import export_to_video

    if not torch.cuda.is_available():
        raise SystemExit(
            "Local text-to-video realistically needs a CUDA GPU.\n"
            "Generate a still image and animate it with `rls ff kenburns` instead."
        )

    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2b", torch_dtype=torch.float16)
    pipe.enable_model_cpu_offload()
    print("[rls] Generating video (several minutes)...")
    frames = pipe(prompt=args.prompt, num_frames=args.frames,
                  num_inference_steps=args.steps).frames[0]

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, str(out), fps=args.fps)
    print(str(out))
    return 0
