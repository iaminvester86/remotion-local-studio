# Adding your own tools

The toolkit is extensible without touching the core. Any local tool that runs on
your machine can be added as an extension, with its dependencies managed the same
way the built-in tools are.

## The contract
Create a file in `extensions/`, e.g. `extensions/my_upscaler.py`, that defines:

```python
REQUIREMENTS = ["realesrgan>=0.3"]   # pip packages your tool needs (optional)
NEEDS_TORCH = True                    # set True if those deps need PyTorch (optional)

def register(subparsers):
    p = subparsers.add_parser("upscale", help="upscale an image 4x")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=_run)

def _run(args):
    # import heavy deps lazily, inside the handler, so `rls --help` stays fast
    ...
    return 0
```

That's it. The file is auto-discovered. `rls --help` will list `upscale`.

## Managed dependencies
Do not `pip install` by hand. Declare deps in `REQUIREMENTS` and install them with:

```
rls ext install my_upscaler
```

This installs into the same `.venv` and records a marker so it never reinstalls.
If your deps need PyTorch, set `NEEDS_TORCH = True` and the correct build for the
machine's accelerator (CUDA / MPS / CPU) is installed first.

## Rules that keep things working
- Import heavy libraries inside the handler, never at module top level. The CLI
  must keep running on a bare interpreter.
- Pick a unique subcommand name. A clash will shadow another tool.
- If your extension is broken, the CLI skips it and prints a note rather than
  failing. Run `rls ext list` to see what was found.
- Keep outputs under `public/...` if Remotion needs to read them.

See `extensions/example_silence.py` for a working template.
