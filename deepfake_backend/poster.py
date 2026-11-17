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


def _extract_first_frame(video_path: str, thumb_path: Path, size=(420, 240)) -> Image.Image:
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img.save(thumb_path, format="JPEG", quality=90)
        return img.resize(size, Image.Resampling.LANCZOS)

    fallback = Image.new("RGB", size, (30, 41, 59))
    fallback.save(thumb_path, format="JPEG")
    return fallback


def generate_poster(video_path: str, analysis_result: dict, video_url: str, unique_id: str) -> dict:
    width, height = 1080, 1350
    bg_color = (11, 15, 25)
    card_color = (22, 30, 46)
    text_white = (248, 250, 252)
    text_muted = (148, 163, 184)

    verdict = str(analysis_result.get("prediction", "REAL")).upper()
    is_fake = verdict == "FAKE"
    accent_color = (239, 68, 68) if is_fake else (16, 185, 129)
    badge_bg = (69, 18, 26) if is_fake else (6, 55, 42)

    poster_filename = f"poster_{unique_id}.png"
    thumb_filename = f"thumb_{unique_id}.jpg"
    qr_filename = f"qr_{unique_id}.png"

    poster_path = POSTER_DIR / poster_filename
    thumb_path = POSTER_DIR / thumb_filename
    qr_path = POSTER_DIR / qr_filename

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
    timestamp_str = analysis_result.get("checked_on") or datetime.now().strftime("%d %b %Y | %I:%M %p")
    draw.text((60, 110), f"Forensic Media Verification Report  •  {timestamp_str}", font=f_sub, fill=text_muted)

    # Video First Frame Thumbnail (Left)
    draw.rounded_rectangle([60, 180, 520, 500], radius=18, fill=card_color, outline=(45, 55, 72), width=2)
    poster.paste(_extract_first_frame(video_path, thumb_path), (80, 200))
    display_name = analysis_result.get("original_filename", Path(video_path).name)
    draw.text((80, 455), f"File: {display_name[:32]}", font=f_small, fill=text_muted)

    # Model Result Card (Right)
    draw.rounded_rectangle([550, 180, width - 60, 500], radius=18, fill=badge_bg, outline=accent_color, width=3)
    draw.text((590, 215), "MODEL VERDICT", font=f_section, fill=text_muted)
    draw.text((590, 265), verdict, font=f_verdict, fill=accent_color)

    fake_prob = float(analysis_result.get("fake_probability", 0.0))
    real_prob = float(analysis_result.get("real_probability", 1.0 - fake_prob))
    frames_analyzed = analysis_result.get("frames_analyzed", 30)

    draw.text((590, 370), f"Frames Analyzed : {frames_analyzed}", font=f_body, fill=text_white)
    draw.text((590, 415), f"Fake Score: {fake_prob:.2f} | Real Score: {real_prob:.2f}", font=f_body, fill=text_muted)

    # QR Code Section
    draw.rounded_rectangle([60, 540, width - 60, 1250], radius=18, fill=card_color, outline=(45, 55, 72), width=2)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(video_url)
    qr.make(fit=True)
    qr_raw = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_raw.save(qr_path, format="PNG")
    poster.paste(qr_raw.resize((420, 420), Image.Resampling.LANCZOS), (330, 600))

    draw.text((280, 1060), "SCAN QR CODE TO WATCH & VERIFY VIDEO", font=f_section, fill=text_white)
    draw.text((310, 1110), f"Result Verified by IRIS Model: {verdict}", font=f_body, fill=accent_color)

    poster.save(poster_path, format="PNG")
    return {
        "poster_url": f"/posters/{poster_filename}",
        "thumbnail_url": f"/posters/{thumb_filename}",
        "qr_url": f"/posters/{qr_filename}",
        "watch_url": video_url,
    }