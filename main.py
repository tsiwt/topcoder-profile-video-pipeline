import uuid, json, asyncio, shutil, traceback
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import uvicorn

from config import UPLOAD_DIR, OUTPUT_DIR, JOBS_DIR, MAX_UPLOAD_MB
from pipeline.orchestrator import run_pipeline

app = FastAPI(title="Topcoder Profile Video Pipeline", version="3.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


def job_status_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"

def save_job(job_id: str, data: dict):
    with open(job_status_path(job_id), "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_job(job_id: str) -> dict:
    p = job_status_path(job_id)
    if not p.exists():
        raise HTTPException(404, "Job not found")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


async def process_video_task(job_id: str, video_path: str, metadata: dict):
    save_job(job_id, {"status": "processing", "progress": 0})
    try:
        output_path = str(OUTPUT_DIR / f"{job_id}_final.mp4")
        await asyncio.to_thread(
            run_pipeline,
            video_path=video_path,
            metadata=metadata,
            output_path=output_path,
            progress_callback=lambda p: save_job(job_id,
                {"status": "processing", "progress": p}),
        )
        save_job(job_id, {"status": "done", "progress": 100,
                          "output": f"/api/download/{job_id}"})
    except Exception as e:
        traceback.print_exc()
        save_job(job_id, {"status": "error", "error": str(e)})


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")

@app.post("/api/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    handle: str = Form("Member"),
    rating_color: str = Form("blue"),
    tracks: str = Form("development"),
    tagline: str = Form(""),
):
    contents = await video.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB}MB limit")

    job_id = uuid.uuid4().hex[:12]
    ext = Path(video.filename).suffix or ".mp4"
    video_path = str(UPLOAD_DIR / f"{job_id}{ext}")
    with open(video_path, "wb") as f:
        f.write(contents)

    metadata = {
        "handle": handle,
        "rating_color": rating_color,
        "tracks": [t.strip() for t in tracks.split(",")],
        "tagline": tagline,
    }

    save_job(job_id, {"status": "queued", "progress": 0})
    background_tasks.add_task(process_video_task, job_id, video_path, metadata)

    return {"job_id": job_id, "status_url": f"/api/status/{job_id}"}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    return load_job(job_id)

@app.get("/api/download/{job_id}")
async def download(job_id: str):
    info = load_job(job_id)
    if info.get("status") != "done":
        raise HTTPException(400, "Video not ready")
    path = OUTPUT_DIR / f"{job_id}_final.mp4"
    if not path.exists():
        raise HTTPException(404, "File missing")
    return FileResponse(str(path), media_type="video/mp4",
                        filename=f"topcoder_profile_{job_id}.mp4")

@app.get("/api/health")
async def health():
    return {"status": "ok", "ffmpeg": shutil.which("ffmpeg") is not None}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
