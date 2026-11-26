import subprocess
from pathlib import Path

from editor.timeline import Clip

TRANSITION_SECONDS = 0.16
SFX_FILTERS = {
    "whoosh": (
        "anoisesrc=color=white:duration=0.35:sample_rate=24000,"
        "highpass=f=400,lowpass=f=5000,afade=t=in:st=0:d=0.03,"
        "afade=t=out:st=0.16:d=0.19,volume=0.22"
    ),
    "impact": (
        "sine=frequency=85:duration=0.28:sample_rate=24000,"
        "afade=t=out:st=0.03:d=0.25,volume=0.38"
    ),
    "ding": (
        "sine=frequency=880:duration=0.4:sample_rate=24000,"
        "afade=t=out:st=0.08:d=0.32,volume=0.18"
    ),
    "pop": (
        "sine=frequency=520:duration=0.14:sample_rate=24000,"
        "afade=t=out:st=0.02:d=0.12,volume=0.22"
    ),
}


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


def _make_sfx_track(clips: list[Clip], work_dir: Path) -> list[tuple[Path, int]]:
    tracks: list[tuple[Path, int]] = []
    cursor = 0.0
    for index, clip in enumerate(clips):
        expression = SFX_FILTERS.get(clip.sfx)
        if expression:
            path = work_dir / f"sfx_{index:02d}.wav"
            _run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", expression,
                "-ac", "2", "-ar", "24000", "-c:a", "pcm_s16le", str(path),
            ])
            tracks.append((path, max(0, int(cursor * 1000))))
        cursor += clip.output_duration
    return tracks


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

        rendered_duration = clip.output_duration
        fade_duration = min(TRANSITION_SECONDS, rendered_duration / 2)
        if index > 0:
            vf += f",fade=t=in:st=0:d={fade_duration:.3f}"
        if index < len(clips) - 1:
            fade_start = max(0.0, rendered_duration - fade_duration)
            vf += f",fade=t=out:st={fade_start:.3f}:d={fade_duration:.3f}"

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
        duration = clip.output_duration
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
    sfx_tracks = _make_sfx_track(clips, work_dir)
    music = Path("assets/music.mp3")
    command = ["ffmpeg", "-y", "-i", str(final_video), "-i", str(narration)]
    filters = ["[1:a]volume=1.0[voice]"]
    audio_labels = ["[voice]"]
    input_index = 2

    if music.exists():
        command.extend(["-stream_loop", "-1", "-i", str(music)])
        filters.append(f"[{input_index}:a]volume=0.12[music]")
        audio_labels.append("[music]")
        input_index += 1

    for index, (sfx_path, delay_ms) in enumerate(sfx_tracks):
        command.extend(["-i", str(sfx_path)])
        filters.append(
            f"[{input_index}:a]adelay={delay_ms}|{delay_ms},volume=0.35[sfx{index}]"
        )
        audio_labels.append(f"[sfx{index}]")
        input_index += 1

    filters.append(
        "".join(audio_labels)
        + f"amix=inputs={len(audio_labels)}:duration=first:dropout_transition=2[aout]"
    )
    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[aout]",
        "-vf", "tpad=stop_mode=clone:stop_duration=180",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(output),
    ])
    _run(command)
    return output
