from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models
from facenet_pytorch import MTCNN

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "weights" / "best_deepfake_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f" Target Model Path: {WEIGHTS_PATH}")
if WEIGHTS_PATH.exists():
    file_size_mb = WEIGHTS_PATH.stat().st_size / (1024 * 1024)
    print(f" Weights File Size: {file_size_mb:.2f} MB")
else:
    print(" Weights file not found!")

# Keep MTCNN but filter out tiny background faces later
mtcnn = MTCNN(
    image_size=224,
    margin=20,
    keep_all=True,
    post_process=False,
    device=DEVICE
)

def load_model():
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4, inplace=False),
        nn.Linear(in_features, 256),
        nn.ReLU(inplace=False),
        nn.Dropout(p=0.2, inplace=False),
        nn.Linear(256, 1)
    )
    state_dict = torch.load(WEIGHTS_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict, strict=True)
    model.to(DEVICE)
    model.eval()
    print(f"Successfully loaded Kaggle weights on {DEVICE} with strict=True!")
    return model

model = load_model()

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess_face_exact(face_rgb: np.ndarray) -> torch.Tensor:
    # Exact Kaggle preprocessing so your model understands the image
    face_resized = cv2.resize(face_rgb, (224, 224))
    face_bgr = cv2.cvtColor(face_resized, cv2.COLOR_RGB2BGR)
    _, enc = cv2.imencode(".jpg", face_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    dec_bgr = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    dec_rgb = cv2.cvtColor(dec_bgr, cv2.COLOR_BGR2RGB)

    img_float = dec_rgb.astype(np.float32) / 255.0
    img_norm = (img_float - IMAGENET_MEAN) / IMAGENET_STD
    return torch.from_numpy(img_norm.transpose(2, 0, 1)).float()

def score_face_crop(face_rgb: np.ndarray) -> float:
    t_orig = preprocess_face_exact(face_rgb)
    t_flip = preprocess_face_exact(cv2.flip(face_rgb, 1))
    pair = torch.stack([t_orig, t_flip]).to(DEVICE)
    with torch.no_grad():
        logits = model(pair).squeeze(1)
        probs = torch.sigmoid(logits).cpu().numpy()
    return float(np.mean(probs))

def analyze_video(video_path: str, num_frames: int = 20) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    total_frames = min(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 300)
    if total_frames <= 0:
        cap.release()
        return {"error": "Could not read video frames"}

    target_set = set(np.linspace(0, total_frames - 1, num_frames, dtype=int))
    max_target = max(target_set)

    frames_rgb = []
    for f_idx in range(max_target + 1):
        if not cap.grab():
            break
        if f_idx in target_set:
            ret, frame = cap.retrieve()
            if ret and frame is not None:
                small_rgb = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.5, fy=0.5), cv2.COLOR_BGR2RGB)
                frames_rgb.append(small_rgb)
    cap.release()

    if not frames_rgb:
        return {"error": "No valid frames extracted"}

    with torch.no_grad():
        boxes_batch, probs_batch = mtcnn.detect(frames_rgb)

    frame_fake_probs = []
    faces_detected_count = 0

    for frame_rgb, boxes, det_probs in zip(frames_rgb, boxes_batch, probs_batch):
        h, w, _ = frame_rgb.shape
        frame_face_scores = []

        if boxes is not None and len(boxes) > 0:
            # Only look at faces with 95%+ confidence that are decently sized
            valid_boxes = [
                b for b, p in zip(boxes, det_probs)
                if p is not None and p >= 0.95 and (b[2] - b[0]) >= 30 and (b[3] - b[1]) >= 30
            ]
            valid_boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)

            if valid_boxes:
                largest_area = (valid_boxes[0][2] - valid_boxes[0][0]) * (valid_boxes[0][3] - valid_boxes[0][1])
                # Ignore random background faces (must be at least 40% the size of the main face)
                filtered_boxes = [
                    b for b in valid_boxes[:2]
                    if ((b[2] - b[0]) * (b[3] - b[1])) >= 0.40 * largest_area
                ]

                for box in filtered_boxes:
                    x1, y1, x2, y2 = [int(v) for v in box]
                    pw, ph = int((x2 - x1) * 0.15), int((y2 - y1) * 0.15)
                    x1, y1 = max(0, x1 - pw), max(0, y1 - ph)
                    x2, y2 = min(w, x2 + pw), min(h, y2 + ph)
                    face_crop = frame_rgb[y1:y2, x1:x2]
                    if face_crop.size > 0:
                        frame_face_scores.append(score_face_crop(face_crop))

        if frame_face_scores:
            faces_detected_count += 1
            frame_fake_probs.append(max(frame_face_scores))

    if not frame_fake_probs:
        for frame_rgb in frames_rgb:
            h, w, _ = frame_rgb.shape
            center_crop = frame_rgb[h//4:3*h//4, w//4:3*w//4]
            frame_fake_probs.append(score_face_crop(center_crop))

    frame_fake_probs = np.array(frame_fake_probs, dtype=np.float32)
    sorted_probs = np.sort(frame_fake_probs)[::-1]

    # Drop the absolute highest score to ignore 1-frame camera glitches in real videos
    if len(sorted_probs) >= 6:
        top_k_slice = sorted_probs[1:5]
    else:
        top_k_slice = sorted_probs[:min(4, len(sorted_probs))]

    top_k_fake_prob = float(np.mean(top_k_slice))
    mean_fake_prob = float(np.mean(frame_fake_probs))
    
    # Count how many frames look clearly fake
    suspicious_frame_count = int(np.sum(frame_fake_probs >= 0.45))

    # Calculate final score
    final_fake_score = (0.60 * top_k_fake_prob) + (0.40 * mean_fake_prob)

    # STRICT RULE: Score must be >= 0.45 AND at least 3 frames must cross the line
    THRESHOLD = 0.45
    is_fake = (final_fake_score >= THRESHOLD and suspicious_frame_count >= 3)
    
    label = "FAKE" if is_fake else "REAL"
    clean_frame_scores = [round(float(p), 3) for p in frame_fake_probs]

    print(
        f" Analysis -> Faces: {faces_detected_count}/{len(frames_rgb)} | "
        f"Mean: {mean_fake_prob:.3f} | Top-4: {top_k_fake_prob:.3f} | "
        f"Frames>=0.45: {suspicious_frame_count} | Final: {final_fake_score:.3f} => {label}"
    )

    return {
        "status": "success",
        "prediction": label,
        "label": label,
        "verdict": label,
        "result": label,
        "is_fake": bool(is_fake),
        "fake_probability": round(final_fake_score, 4),
        "real_probability": round(1.0 - final_fake_score, 4),
        "frames_analyzed": len(frame_fake_probs),
        "faces_detected": faces_detected_count,
        "frame_scores": clean_frame_scores,
        "per_frame_scores": clean_frame_scores,
        "frame_probabilities": clean_frame_scores
    }

predict_video = analyze_video
