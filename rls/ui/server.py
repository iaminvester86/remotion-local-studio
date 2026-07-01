"""
server.py — local web UI backend.

The UI is a thin front-end over the same `rls` CLI: each generate action spawns
`python -m rls <subcommand>` as a background job and streams its output to the
browser. One code path, so the UI never drifts from the CLI.

Adds: a configurable output folder (where public/ and .rls/ live), reveal-in-
file-manager, and an analysis-results endpoint that turns scene detection into a
viewable gallery. Binds to 127.0.0.1 only.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..report import report, TOOLS

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"

app = FastAPI(title="Remotion Local Studio")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# Where generated assets and uploads go. Defaults to the launch directory.
OUTPUT_ROOT = Path.cwd().resolve()

JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


# ---- helpers ---------------------------------------------------------------

def _abs_under_root(p: str) -> str:
    """Resolve a (possibly relative) output path against OUTPUT_ROOT, absolute."""
    pp = Path(p)
    return str(pp if pp.is_absolute() else (OUTPUT_ROOT / pp))


def _safe(path: str) -> Path:
    root = OUTPUT_ROOT
    target = Path(path) if os.path.isabs(path) else (root / path)
    target = target.resolve()
    if root != target and root not in target.parents:
        raise HTTPException(403, "path outside the output folder")
    return target


# ---- jobs ------------------------------------------------------------------

def _new_job(label: str, argv: list[str], result_kind: str = "file",
             result_hint: str | None = None) -> str:
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        JOBS[jid] = {"id": jid, "label": label, "argv": argv, "status": "running",
                     "log": [], "output": None, "error": None, "started": time.time(),
                     "result_kind": result_kind, "result_hint": result_hint}
    threading.Thread(target=_run_job, args=(jid,), daemon=True).start()
    return jid


def _run_job(jid: str) -> None:
    job = JOBS[jid]
    cmd = [sys.executable, "-m", "rls", *job["argv"]]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, bufsize=1, cwd=str(OUTPUT_ROOT))
        last = ""
        for line in proc.stdout:  # type: ignore
            line = line.rstrip("\n")
            last = line or last
            with _LOCK:
                job["log"].append(line)
                job["log"] = job["log"][-600:]
        proc.wait()
        if proc.returncode == 0:
            job["status"] = "done"
            job["output"] = last
        else:
            job["status"] = "error"
            job["error"] = f"exited with code {proc.returncode}"
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
    finally:
        job["finished"] = time.time()


# ---- argv builder (whitelisted) -------------------------------------------

def _build_argv(tool: str, p: dict) -> tuple[list[str], str, str | None]:
    def need(k):
        if not p.get(k):
            raise HTTPException(400, f"missing '{k}'")
        return p[k]

    if tool == "transcribe":
        out = _abs_under_root(p.get("out") or "public/captions/captions")
        a = ["transcribe", "--input", need("input"), "--out", out,
             "--model", p.get("model", "base")]
        if p.get("lang"): a += ["--lang", p["lang"]]
        return a, "captions", out + ".srt"
    if tool == "tts":
        out = _abs_under_root(p.get("out") or "public/audio/voiceover.wav")
        a = ["tts", "--out", out, "--voice", p.get("voice", "en_US-amy-medium")]
        if p.get("text"): a += ["--text", p["text"]]
        return a, "audio", out
    if tool == "music":
        out = _abs_under_root(p.get("out") or "public/music/bed.wav")
        return (["music", "--prompt", need("prompt"), "--duration",
                 str(p.get("duration", 15)), "--out", out, "--model",
                 p.get("model", "small")], "audio", out)
    if tool == "image":
        out = _abs_under_root(p.get("out") or "public/images/image.png")
        a = ["image", "--prompt", need("prompt"), "--out", out,
             "--width", str(p.get("width", 1024)), "--height", str(p.get("height", 1024)),
             "--model", p.get("model", "sdxl")]
        if p.get("seed"): a += ["--seed", str(p["seed"])]
        return a, "image", out
    if tool == "video":
        out = _abs_under_root(p.get("out") or "public/clips/generated.mp4")
        return (["video", "--prompt", need("prompt"), "--out", out,
                 "--frames", str(p.get("frames", 49)), "--fps", str(p.get("fps", 8))],
                "video", out)
    if tool == "analyze":
        outdir = p.get("outdir") or "analysis"
        return (["analyze", "--input", need("input"),
                 "--outdir", _abs_under_root(outdir)], "analysis", outdir)
    if tool == "kenburns":
        out = _abs_under_root(p.get("out") or "public/clips/clip.mp4")
        return (["ff", "kenburns", need("image"), out, str(p.get("seconds", 6))],
                "video", out)
    if tool == "install":
        return ["install", need("feature")], "install", None
    raise HTTPException(400, f"unknown tool '{tool}'")


# ---- routes ----------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/api/status")
def api_status():
    r = report()
    r["output_root"] = str(OUTPUT_ROOT)
    return JSONResponse(r)


@app.get("/api/config")
def api_config():
    return {"output_root": str(OUTPUT_ROOT)}


@app.post("/api/config")
def api_set_config(body: dict):
    global OUTPUT_ROOT
    p = body.get("output_root", "").strip()
    if not p:
        raise HTTPException(400, "output_root required")
    root = Path(p).expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(400, f"cannot use folder: {e}")
    OUTPUT_ROOT = root.resolve()
    return {"output_root": str(OUTPUT_ROOT)}


@app.post("/api/reveal")
def api_reveal(body: dict):
    target = _safe(body.get("path", "."))
    folder = target if target.is_dir() else target.parent
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(folder)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"opened": str(folder)}


@app.post("/api/run")
async def api_run(body: dict):
    tool = body.get("tool")
    if tool not in (set(TOOLS) | {"kenburns", "install"}):
        raise HTTPException(400, f"unknown tool '{tool}'")
    argv, kind, hint = _build_argv(tool, body.get("params", {}))
    jid = _new_job(body.get("label", tool), argv, kind, hint)
    return {"job": jid, "command": "rls " + " ".join(shlex.quote(x) for x in argv)}


@app.get("/api/jobs/{jid}")
def api_job(jid: str):
    job = JOBS.get(jid)
    if not job:
        raise HTTPException(404, "no such job")
    return job


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    updir = OUTPUT_ROOT / ".rls" / "uploads"
    updir.mkdir(parents=True, exist_ok=True)
    dest = updir / Path(file.filename).name
    dest.write_bytes(await file.read())
    return {"path": str(dest)}


@app.get("/api/analysis")
def api_analysis(path: str):
    """Return scene-detection results with web paths to each frame."""
    outdir = _safe(path)
    scenes_file = outdir / "scenes.json"
    if not scenes_file.is_file():
        raise HTTPException(404, "no scenes.json in that folder")
    data = json.loads(scenes_file.read_text(encoding="utf-8"))
    for s in data:
        fr = Path(s.get("frame", ""))
        try:
            rel = fr.resolve().relative_to(OUTPUT_ROOT)
            s["frame_url"] = "/api/file?path=" + str(rel).replace("\\", "/")
        except Exception:
            s["frame_url"] = None
    return {"scenes": data, "count": len(data)}


@app.get("/api/file")
def api_file(path: str):
    return FileResponse(_safe(path))


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    import uvicorn
    if open_browser:
        import webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    print(f"[rls] UI running at http://{host}:{port}  (output folder: {OUTPUT_ROOT})")
    uvicorn.run(app, host=host, port=port, log_level="warning")
