"""Local image generation via diffusers (FLUX schnell / SDXL)."""
from __future__ import annotations
from pathlib import Path
from ..deps import ensure_feature


def run(args) -> int:
    ensure_feature("image")
    import torch                                     # lazy
    from diffusers import FluxPipeline, StableDiffusionXLPipeline

    if torch.cuda.is_available():
        device, dtype, cuda = "cuda", torch.bfloat16, True
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device, dtype, cuda = "mps", torch.float16, False
    else:
        device, dtype, cuda = "cpu", torch.float32, False
        print("[rls] WARNING: no GPU detected; image generation on CPU is very slow.")

    gen = torch.Generator(device="cpu").manual_seed(args.seed) if args.seed is not None else None

    def place(pipe):
        # On CUDA, offload submodules to CPU and stream them in as needed, so large
        # models (e.g. FLUX) run on 12GB cards without out-of-memory errors.
        if cuda:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(device)
        return pipe

    if args.model == "flux-schnell":
        pipe = place(FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell", torch_dtype=dtype))
        steps = args.steps or 4
        img = pipe(args.prompt, width=args.width, height=args.height,
                   num_inference_steps=steps, guidance_scale=0.0, generator=gen).images[0]
    else:
        pipe = place(StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=dtype,
            use_safetensors=True))
        steps = args.steps or 30
        img = pipe(args.prompt, width=args.width, height=args.height,
                   num_inference_steps=steps, generator=gen).images[0]

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(str(out))
    return 0
