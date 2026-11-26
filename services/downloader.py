import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from pytubefix import YouTube

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def download_video(url: str, destination: Path) -> tuple[Path, dict]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError("URL harus berasal dari YouTube.")

    max_minutes = int(os.getenv("MAX_VIDEO_MINUTES", "30"))
    max_bytes = int(os.getenv("MAX_DOWNLOAD_MB", "500")) * 1024 * 1024
    destination.mkdir(parents=True, exist_ok=True)

    yt = YouTube(url.strip())
    duration = int(yt.length or 0)
    if duration <= 0 or duration > max_minutes * 60:
        raise ValueError(f"Durasi video harus antara 1 detik dan {max_minutes} menit.")

    # Prefer the highest MP4 adaptive video stream up to 1080p.
    video_streams = [
        stream for stream in yt.streams.filter(
            adaptive=True, only_video=True, file_extension="mp4"
        ).all()
        if stream.height and stream.height <= 1080
    ]
    video_streams.sort(key=lambda stream: (stream.height or 0, stream.fps or 0), reverse=True)
    video_stream = video_streams[0] if video_streams else None

    # Progressive MP4 is a fallback when an adaptive video/audio pair is unavailable.
    if video_stream is None:
        progressive = [
            stream for stream in yt.streams.filter(
                progressive=True, file_extension="mp4"
            ).all()
            if stream.height and stream.height <= 1080
        ]
        progressive.sort(key=lambda stream: (stream.height or 0, stream.fps or 0), reverse=True)
        if not progressive:
            raise RuntimeError("Tidak ditemukan stream MP4 yang sesuai (maksimum 1080p).")
        stream = progressive[0]
        estimated_size = stream.filesize or stream.filesize_approx or 0
        if estimated_size > max_bytes:
            raise ValueError("Perkiraan ukuran video melewati batas unduhan.")
        downloaded = stream.download(
            output_path=str(destination), filename="source.mp4",
            timeout=30, max_retries=2,
        )
        path = Path(downloaded)
    else:
        audio_stream = yt.streams.get_audio_only(subtype="mp4")
        if audio_stream is None:
            raise RuntimeError("Stream audio MP4 tidak tersedia.")

        estimated_size = (
            (video_stream.filesize or video_stream.filesize_approx or 0)
            + (audio_stream.filesize or audio_stream.filesize_approx or 0)
        )
        if estimated_size > max_bytes:
            raise ValueError("Perkiraan ukuran video melewati batas unduhan.")

        video_path = destination / "source_video.mp4"
        audio_path = destination / "source_audio.mp4"
        video_file = video_stream.download(
            output_path=str(destination), filename=video_path.name,
            timeout=30, max_retries=2,
        )
        audio_file = audio_stream.download(
            output_path=str(destination), filename=audio_path.name,
            timeout=30, max_retries=2,
        )
        path = destination / "source.mp4"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error",
                    "-i", video_file, "-i", audio_file,
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c", "copy", "-movflags", "+faststart", str(path),
                ],
                check=True, capture_output=True, text=True, timeout=300,
            )
        finally:
            Path(video_file).unlink(missing_ok=True)
            Path(audio_file).unlink(missing_ok=True)

    if not path.exists():
        raise RuntimeError("File video hasil unduhan tidak ditemukan.")
    if path.stat().st_size > max_bytes:
        path.unlink(missing_ok=True)
        raise ValueError("Ukuran video melewati batas unduhan.")

    return path, {
        "title": yt.title or "Video",
        "duration": float(duration),
        "filesize": path.stat().st_size,
        "webpage_url": url.strip(),
    }
