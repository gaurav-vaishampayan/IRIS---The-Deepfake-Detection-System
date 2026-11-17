import os
import sys
import json
import shutil
import socket
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"

UPLOAD_DIR = CURRENT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

RECORDS_DIR = CURRENT_DIR / "records"
RECORDS_DIR.mkdir(parents=True, exist_ok=True)

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_service import analyze_video
from poster import generate_poster, POSTER_DIR

app = FastAPI(title="IRIS Deepfake Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PosterRequest(BaseModel):
    analysis_id: str


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@app.post("/predict")
@app.post("/analyze")
async def predict_endpoint(video: UploadFile = File(...)):
    if not video.filename:
        raise HTTPException(status_code=400, detail="No video file uploaded.")

    suffix = Path(video.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        result = analyze_video(tmp_path)

        unique_id = uuid.uuid4().hex[:8]
        saved_video_name = f"vid_{unique_id}{suffix}"
        saved_video_path = UPLOAD_DIR / saved_video_name
        shutil.copy2(tmp_path, saved_video_path)

        prediction = str(result.get("prediction") or result.get("verdict") or "REAL").upper()
        fake_prob = float(result.get("fake_probability", 0.0))
        real_prob = float(result.get("real_probability", 1.0 - fake_prob))

        record = {
            **result,
            "analysis_id": unique_id,
            "prediction": prediction,
            "fake_probability": round(fake_prob, 4),
            "real_probability": round(real_prob, 4),
            "frames_analyzed": result.get("frames_analyzed", 30),
            "original_filename": video.filename,
            "saved_video_name": saved_video_name,
            "video_url": f"/uploads/{saved_video_name}",
            "checked_on": datetime.now().strftime("%d %b %Y"),
        }

        (RECORDS_DIR / f"{unique_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/generate-poster")
async def generate_poster_endpoint(payload: PosterRequest):
    record_path = RECORDS_DIR / f"{payload.analysis_id}.json"
    if not record_path.exists():
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    record = json.loads(record_path.read_text(encoding="utf-8"))
    saved_video_path = UPLOAD_DIR / record["saved_video_name"]
    if not saved_video_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded video file not found.")

    host_ip = get_local_ip()
    watch_url = f"http://{host_ip}:8000/pages/watch.html?id={payload.analysis_id}"

    assets = generate_poster(
        video_path=str(saved_video_path),
        analysis_result=record,
        video_url=watch_url,
        unique_id=payload.analysis_id,
    )

    record.update(assets)
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


@app.get("/analysis/{analysis_id}")
async def get_analysis_endpoint(analysis_id: str):
    record_path = RECORDS_DIR / f"{analysis_id}.json"
    if not record_path.exists():
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return json.loads(record_path.read_text(encoding="utf-8"))


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/index.html")
async def serve_index_explicit():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/posters", StaticFiles(directory=str(POSTER_DIR)), name="posters")
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")