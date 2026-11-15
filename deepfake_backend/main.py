import os
import sys
import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_service import analyze_video

app = FastAPI(title="IRIS Deepfake Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Serve all static frontend files (/pages/main.html, /css/*, /js/*, /assets/*)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")