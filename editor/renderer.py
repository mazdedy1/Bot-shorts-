import subprocess
from pathlib import Path

from editor.timeline import Clip

def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or "FFmpeg gagal.")[-2500:])

def _stamp(value: float) -> str:
    ms = int(value * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def render_short(source: Path, clips: list[Clip], narration: Path, output: Path, work_dir: Path, plan: dict) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    segments = []
    for index, clip in enumerate(clips):
        segment = work_dir / f"clip_{index:02d}.mp4"
        duration = clip.end - clip.start
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1"
        if clip.effect == "zoom_in":
            vf += ",zoompan=z='min(zoom+0.0015,1.12)':d=1:s=1080x1920:fps=30"
        elif clip.effect == "zoom_out":
            vf += ",zoompan=z='if(eq(on,1),1.12,max(1.0,zoom-0.0015))':d=1:s=1080x1920:fps=30"
        elif clip.effect == "slow":
            vf += ",setpts=1.08*PTS"
        _run([
            "ffmpeg", "-y", "-ss", str(clip.start), "-i", str(source),
            "-t", str(duration), "-an", "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", str(segment),
        ])
        segments.append(segment)

    concat_file = work_dir / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in segments),
        encoding="utf-8",
    )
    joined = work_dir / "joined.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(joined)])

    subtitle_file = work_dir / "captions.srt"
    cursor = 0.0
    entries = []
    for index, clip in enumerate(clips, 1):
        duration = clip.end - clip.start
        if clip.caption:
            entries.append(
                f"{index}\n{_stamp(cursor)} --> {_stamp(cursor + duration)}\n{clip.caption}\n"
            )
        cursor += duration
    subtitle_file.write_text("\n".join(entries), encoding="utf-8")
    final_video = work_dir / "video_only.mp4"
    escaped_sub = str(subtitle_file.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles='{escaped_sub}':force_style='FontName=Arial,FontSize=18,Outline=2,Shadow=1,Alignment=2,MarginV=120'"
    _run([
        "ffmpeg", "-y", "-i", str(joined), "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an", str(final_video),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    music = Path("assets/music.mp3")
    if music.exists():
        _run([
            "ffmpeg", "-y", "-i", str(final_video), "-i", str(narration),
            "-stream_loop", "-1", "-i", str(music),
            "-filter_complex", "[1:a]volume=1.0[voice];[2:a]volume=0.12[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v:0", "-map", "[aout]", "-vf", "tpad=stop_mode=clone:stop_duration=30",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output),
        ])
    else:
        _run([
            "ffmpeg", "-y", "-i", str(final_video), "-i", str(narration),
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", "tpad=stop_mode=clone:stop_duration=30",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", str(output),
        ])
    return output
