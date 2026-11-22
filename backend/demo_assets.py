import io
import base64
from typing import Dict, Any, List
from PIL import Image, ImageDraw


def _create_sidewalk_eydap_scene() -> bytes:
    img = Image.new("RGB", (800, 520), color=(185, 185, 180))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 360), (800, 520)], fill=(70, 72, 78))
    draw.ellipse([(450, 190), (765, 465)], fill=(65, 135, 185), outline=(45, 105, 155), width=3)
    draw.ellipse([(510, 225), (710, 415)], fill=(65, 60, 58), outline=(30, 28, 25), width=6)
    draw.text((255, 220), "ΕΥΔΑΠ - ΣΠΑΣΜΕΝΟ ΦΡΕΑΤΙΟ & ΠΕΖΟΔΡΟΜΙΟ", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def get_demo_presets_with_images() -> List[Dict[str, Any]]:
    img_bytes = _create_sidewalk_eydap_scene()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return [
        {
            "id": "flagship_sidewalk_eydap",
            "badge_el": "FLAGSHIP DEMO (Split Ticket: Δήμος + ΕΥΔΑΠ)",
            "title_el": "Σπασμένο Πεζοδρόμιο & Φρεάτιο ΕΥΔΑΠ με Διαρροή",
            "citizen_comment": "Εδώ στη φωτογραφία, βλέπετε πως έχει σπάσει το καπάκι του φρεατίου και τρέχει νερό!",
            "latitude": 37.981969,
            "longitude": 23.732121,
            "location_label_el": "Πανεπιστημίου 42, 1η Δημοτική Κοινότητα",
            "image_data_url": f"data:image/jpeg;base64,{b64}",
        }
    ]


def get_preset_image_bytes(preset_id: str) -> bytes:
    return _create_sidewalk_eydap_scene()
