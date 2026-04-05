from __future__ import annotations

import os

from PIL import Image


def convert_webp_to_jpeg(input_path: str) -> str:
    if not input_path.lower().endswith(".webp"):
        return input_path
    output_path = os.path.splitext(input_path)[0] + ".jpg"
    with Image.open(input_path) as img:
        img.convert("RGB").save(output_path, "JPEG", quality=95)
    try:
        os.remove(input_path)
    except OSError:
        pass
    return output_path


def is_video(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in {".mp4", ".mov", ".avi", ".mkv"}


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in {
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
    }
