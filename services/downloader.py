import os
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}

def download_video(url: str, destination: Path) -> tuple[Path, dict]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError("URL harus berasal dari YouTube.")
    max_minutes = int(os.getenv("MAX_VIDEO_MINUTES", "30"))
    max_bytes = int(os.getenv("MAX_DOWNLOAD_MB", "500")) * 1024 * 1024
    destination.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "best[height<=1080][ext=mp4]/best[height<=1080]/best",
        "outtmpl": str(destination / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": max_bytes,
        "socket_timeout": 30,
        "retries": 2,
        "merge_output_format": "mp4",
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = float(info.get("duration") or 0)
        if duration <= 0 or duration > max_minutes * 60:
            raise ValueError(f"Durasi video harus antara 1 detik dan {max_minutes} menit.")
        ydl.download([url])
        prepared = ydl.prepare_filename(info)
    path = Path(prepared)
    if not path.exists():
        candidates = list(destination.glob("source.*"))
        if not candidates:
            raise RuntimeError("File video hasil unduhan tidak ditemukan.")
        path = candidates[0]
    if path.stat().st_size > max_bytes:
        path.unlink(missing_ok=True)
        raise ValueError("Ukuran video melewati batas unduhan.")
    return path, {
        "title": info.get("title", "Video"),
        "duration": duration,
        "filesize": path.stat().st_size,
        "webpage_url": info.get("webpage_url", url),
    }
