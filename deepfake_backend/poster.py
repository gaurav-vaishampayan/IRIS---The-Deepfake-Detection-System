from pathlib import Path
from datetime import datetime
import cv2
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
POSTER_DIR = BASE_DIR / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


def _load_font(size: int, bold: bool = False):
    candidates = (
        ["arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"]
        if bold
        else ["arial.ttf", "segoeui.ttf", "calibri.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _extract_thumbnail(video_path: str, size=(420, 240)) -> Image.Image:
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total > 5:
        cap.set(cv2.CAP_PROP_POS_FRAMES, total // 3)
    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb).resize(size, Image.Resampling.LANCZOS)

    return Image.new("RGB", size, (30, 41, 59))


def generate_poster(video_path: str, analysis_result: dict, video_url: str, output_filename: str) -> Path:
    width, height = 1080, 1350
    bg_color = (11, 15, 25)
    card_color = (22, 30, 46)
    text_white = (248, 250, 252)
    text_muted = (148, 163, 184)

    verdict = str(analysis_result.get("prediction", "REAL")).upper()
    is_fake = verdict == "FAKE"
    accent_color = (239, 68, 68) if is_fake else (16, 185, 129)
    badge_bg = (69, 18, 26) if is_fake else (6, 55, 42)

    poster = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(poster)

    f_title = _load_font(44, bold=True)
    f_sub = _load_font(22)
    f_verdict = _load_font(64, bold=True)
    f_section = _load_font(26, bold=True)
    f_body = _load_font(22)
    f_small = _load_font(18)

    # Top Header
    draw.rectangle([0, 0, width, 14], fill=accent_color)
    draw.text((60, 50), "IRIS DEEPFAKE DETECTION SYSTEM", font=f_title, fill=text_white)
    timestamp_str = datetime.now().strftime("%d %b %Y | %I:%M %p")
    draw.text((60, 110), f"Forensic Media Verification Report  •  {timestamp_str}", font=f_sub, fill=text_muted)

    # Video Thumbnail (Left)
    draw.rounded_rectangle([60, 180, 520, 500], radius=18, fill=card_color, outline=(45, 55, 72), width=2)
    poster.paste(_extract_thumbnail(video_path), (80, 200))
    draw.text((80, 455), f"File: {Path(video_path).name[:32]}", font=f_small, fill=text_muted)

    # Model Result Card (Right)
    draw.rounded_rectangle([550, 180, width - 60, 500], radius=18, fill=badge_bg, outline=accent_color, width=3)
    draw.text((590, 215), "MODEL VERDICT", font=f_section, fill=text_muted)
    draw.text((590, 265), verdict, font=f_verdict, fill=accent_color)

    fake_prob = float(analysis_result.get("fake_probability", 0.0))
    real_prob = float(analysis_result.get("real_probability", 1.0 - fake_prob))
    frames_analyzed = analysis_result.get("frames_analyzed", 20)

    draw.text((590, 370), f"Frames Analyzed : {frames_analyzed}", font=f_body, fill=text_white)
    draw.text((590, 415), f"Fake Score: {fake_prob:.2f} | Real Score: {real_prob:.2f}", font=f_body, fill=text_muted)

    # QR Code Section (Points directly to the uploaded video + result)
    draw.rounded_rectangle([60, 540, width - 60, 1250], radius=18, fill=card_color, outline=(45, 55, 72), width=2)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(video_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((420, 420))
    poster.paste(qr_img, (330, 600))

    draw.text((280, 1060), "SCAN QR CODE TO WATCH UPLOADED VIDEO", font=f_section, fill=text_white)
    draw.text((310, 1110), f"Result Verified by IRIS Model: {verdict}", font=f_body, fill=accent_color)

    output_path = POSTER_DIR / output_filename
    poster.save(output_path, format="PNG")
    return output_path