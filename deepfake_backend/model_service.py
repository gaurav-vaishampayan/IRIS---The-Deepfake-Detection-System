from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "weights" / "best_deepfake_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"🔍 Target Model Path: {WEIGHTS_PATH}")
if WEIGHTS_PATH.exists():
    file_size_mb = WEIGHTS_PATH.stat().st_size / (1024 * 1024)
    print(f" Weights File Size: {file_size_mb:.2f} MB")
else:
    print(" Weights file not found!")


class EfficientNetDeepfakeDetector(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = models.efficientnet_b0(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features, 1)
        )

    def forward(self, x):
        return self.backbone(x)


model = EfficientNetDeepfakeDetector().to(DEVICE)

if WEIGHTS_PATH.exists() and WEIGHTS_PATH.stat().st_size > 1000000:
    try:
        checkpoint = torch.load(WEIGHTS_PATH, map_location=DEVICE, weights_only=False)
        state_dict = (
            checkpoint.get("model_state_dict")
            or checkpoint.get("state_dict")
            or checkpoint
        )
        
        model_dict = model.state_dict()
        matched_dict = {}
        for k, v in state_dict.items():
            clean_k = k.replace("backbone.", "").replace("module.", "")
            for m_key in model_dict:
                if m_key == clean_k or m_key.endswith(clean_k):
                    if v.shape == model_dict[m_key].shape:
                        matched_dict[m_key] = v
                        break

        model_dict.update(matched_dict)
        model.load_state_dict(model_dict, strict=False)
        print(f" Successfully loaded checkpoint weights ({len(matched_dict)} layers matched)!")
    except Exception as e:
        print(f" Error loading PyTorch weights: {e}")
else:
    print("WARNING: Weights file missing or invalid!")

model.eval()

preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def extract_frames_and_faces(video_path: str, num_frames: int = 10):
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    tensors_list = []

    if total_frames > 0:
        indices = np.linspace(0, max(total_frames - 1, 0), num_frames, dtype=int)
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if not ret:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
                crop = rgb[y : y + h, x : x + w]
                if crop.size > 0:
                    rgb = crop
            else:
                h_img, w_img, _ = rgb.shape
                min_dim = min(h_img, w_img)
                start_y = (h_img - min_dim) // 2
                start_x = (w_img - min_dim) // 2
                rgb = rgb[start_y:start_y+min_dim, start_x:start_x+min_dim]

            tensors_list.append(preprocess(rgb))
    cap.release()
    return tensors_list


def analyze_video(video_path: str) -> dict:
    tensors = extract_frames_and_faces(video_path, num_frames=10)
    if not tensors:
        return {"verdict": "UNKNOWN", "prediction": "UNKNOWN"}

    frame_probs = []
    with torch.no_grad():
        for t_tensor in tensors:
            tensor_in = t_tensor.unsqueeze(0).to(DEVICE)
            logit = model(tensor_in)
            prob = float(torch.sigmoid(logit).item())
            frame_probs.append(prob)

    avg_prob = sum(frame_probs) / len(frame_probs) if frame_probs else 0.0
    is_fake = avg_prob >= 0.5
    verdict = "FAKE" if is_fake else "REAL"

    # Returns strictly the label with zero confidence scores or numbers
    return {
        "verdict": verdict,
        "prediction": verdict,
        "label": verdict
    }


predict_video = analyze_video
