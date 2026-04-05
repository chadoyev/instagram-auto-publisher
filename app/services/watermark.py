from __future__ import annotations

import asyncio
import logging
import os
import shutil

from app.settings import settings

logger = logging.getLogger(__name__)

_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}

# Logo size relative to the shorter side of the image/frame
_WM_RATIO = 0.30   # 30 % of short side, min 200 px, max 800 px
_WM_OPACITY = 0.70  # 70 % opacity
_WM_MARGIN = 20    # px from edges (bottom-right)


def get_watermark_path() -> str | None:
    """Return active watermark path: dynamic upload takes priority over env var."""
    dynamic = str(settings.media_root / "logo.png")
    if os.path.exists(dynamic):
        return dynamic
    if settings.watermark_path and os.path.exists(str(settings.watermark_path)):
        return str(settings.watermark_path)
    return None


def _is_photo(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in _PHOTO_EXTS


# ── Photo watermark (Pillow) ──────────────────────────────────────────────────

def _apply_watermark_photo_sync(input_path: str, wm_path: str, output_path: str) -> None:
    from PIL import Image

    with Image.open(input_path).convert("RGBA") as base:
        with Image.open(wm_path).convert("RGBA") as logo:
            # Scale logo relative to image short side
            short = min(base.width, base.height)
            wm_size = max(200, min(800, int(short * _WM_RATIO)))
            ratio = wm_size / max(logo.width, logo.height)
            logo = logo.resize(
                (int(logo.width * ratio), int(logo.height * ratio)),
                Image.LANCZOS,
            )

            # Apply opacity
            r, g, b, a = logo.split()
            a = a.point(lambda x: int(x * _WM_OPACITY))
            logo.putalpha(a)

            # Bottom-right corner
            x = base.width - logo.width - _WM_MARGIN
            y = base.height - logo.height - _WM_MARGIN
            layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
            layer.paste(logo, (x, y), logo)
            composited = Image.alpha_composite(base, layer)

        # Save as original format; JPEG doesn't support RGBA
        ext = os.path.splitext(output_path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            composited = composited.convert("RGB")
            composited.save(output_path, "JPEG", quality=95)
        else:
            composited.save(output_path)


# ── Video watermark (ffmpeg) ──────────────────────────────────────────────────

async def _apply_watermark_video(input_path: str, wm_path: str, output_path: str) -> bool:
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", wm_path,
        "-filter_complex",
        "[1:v]scale=150:-1,format=rgba,colorchannelmixer=aa=0.3[wm];"
        "[0:v][wm]overlay=W-w-20:H-h-20",
        "-codec:a", "copy",
        "-preset", "fast",
        output_path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0:
            logger.error("ffmpeg error: %s", stderr.decode(errors="replace"))
            return False
        return True
    except asyncio.TimeoutError:
        logger.error("ffmpeg timed out for %s", input_path)
        return False
    except FileNotFoundError:
        logger.warning("ffmpeg not found, skipping watermark")
        return False


# ── Public API ────────────────────────────────────────────────────────────────

async def apply_watermark(input_path: str) -> str:
    """Apply watermark to a photo (Pillow) or video (ffmpeg).
    Returns path to the watermarked file, or original if watermark is not configured / fails."""
    wm = get_watermark_path()
    if not wm:
        return input_path

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_wm{ext}"

    if _is_photo(input_path):
        try:
            await asyncio.to_thread(_apply_watermark_photo_sync, input_path, wm, output_path)
            return output_path
        except Exception:
            logger.exception("Pillow watermark failed for %s", input_path)
            return input_path
    else:
        ok = await _apply_watermark_video(input_path, wm, output_path)
        return output_path if ok else input_path


async def apply_watermark_to_dir(dir_path: str) -> tuple[str, list[str]]:
    """Apply watermark to every file in an album directory.

    Returns (temp_dir_path, list_of_watermarked_paths).
    The temp dir is a sibling named <dir>_wm/ and must be cleaned up after upload.
    """
    wm = get_watermark_path()
    wm_dir = dir_path.rstrip("/\\") + "_wm"
    os.makedirs(wm_dir, exist_ok=True)

    files = sorted(f for f in os.listdir(dir_path) if not f.startswith("."))
    result_paths: list[str] = []

    for fname in files:
        src = os.path.join(dir_path, fname)
        dst = os.path.join(wm_dir, fname)
        ext = os.path.splitext(fname)[1].lower()

        if not wm:
            shutil.copy2(src, dst)
            result_paths.append(dst)
            continue

        if ext in _PHOTO_EXTS:
            try:
                await asyncio.to_thread(_apply_watermark_photo_sync, src, wm, dst)
                result_paths.append(dst)
                continue
            except Exception:
                logger.exception("Photo watermark failed for %s", src)
        elif ext in _VIDEO_EXTS:
            ok = await _apply_watermark_video(src, wm, dst)
            if ok:
                result_paths.append(dst)
                continue

        # Fallback — use original file unchanged
        shutil.copy2(src, dst)
        result_paths.append(dst)

    return wm_dir, result_paths


async def cleanup_watermark(watermarked_path: str, original_path: str) -> None:
    if watermarked_path != original_path and os.path.exists(watermarked_path):
        try:
            await asyncio.to_thread(os.remove, watermarked_path)
        except OSError:
            pass


async def cleanup_watermark_dir(wm_dir: str, original_dir: str) -> None:
    """Remove the temporary watermarked album directory."""
    if wm_dir != original_dir and os.path.isdir(wm_dir):
        try:
            await asyncio.to_thread(shutil.rmtree, wm_dir)
        except OSError:
            pass
