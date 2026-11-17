import os
import sys
import shutil
import socket
import uuid
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Folders to store uploaded videos (for the QR code) and generated posters
UPLOAD_DIR = CURRENT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

        # Save a copy of the video in /uploads so the QR code link can play it
        unique_id = uuid.uuid4().hex[:8]
        saved_video_name = f"vid_{unique_id}{suffix}"
        saved_video_path = UPLOAD_DIR / saved_video_name
        shutil.copy2(tmp_path, saved_video_path)

        host_ip = get_local_ip()
        video_qr_url = f"http://{host_ip}:8000/uploads/{saved_video_name}"
        poster_filename = f"poster_{unique_id}.png"

        # Generate the poster with the QR code and model verdict
        generate_poster(
            video_path=str(saved_video_path),
            analysis_result=result,
            video_url=video_qr_url,
            output_filename=poster_filename
        )

       #ui for poster
        result["video_url"] = f"/uploads/{saved_video_name}"
        result["poster_url"] = f"/posters/{poster_filename}"
        result["poster_full_url"] = f"http://{host_ip}:8000/posters/{poster_filename}"

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# Directly land on frontend/index.html when visiting http://127.0.0.1:8000/
@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/index.html")
async def serve_index_explicit():
    return FileResponse(FRONTEND_DIR / "index.html")


# Serve uploaded videos and generated posters (must be mounted BEFORE "/")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/posters", StaticFiles(directory=str(POSTER_DIR)), name="posters")

# Serve all static frontend files (/pages/main.html, /css/*, /js/*, /assets/*)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
