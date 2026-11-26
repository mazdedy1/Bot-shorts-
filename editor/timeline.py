from dataclasses import dataclass

MAX_OUTPUT_SECONDS = 180
MIN_OUTPUT_SECONDS = 20

@dataclass
class Clip:
    start: float
    end: float
    caption: str
    effect: str = "none"
    sfx: str = "none"

def validate_plan(plan: dict, source_duration: float) -> tuple[list[Clip], str]:
    narration = str(plan.get("narration", "")).strip()
    if not narration:
        raise ValueError("Naskah narasi kosong.")
    raw_clips = plan.get("clips")
    if not isinstance(raw_clips, list) or not raw_clips:
        raise ValueError("AI Director tidak menghasilkan klip.")
    clips: list[Clip] = []
    for item in raw_clips:
        start = float(item["start"])
        end = float(item["end"])
        if start < 0 or end <= start or end > source_duration + 0.25:
            raise ValueError("Rentang klip AI berada di luar durasi sumber.")
        effect = str(item.get("effect", "none")).lower()
        if effect not in {"none", "zoom_in", "zoom_out", "slow"}:
            effect = "none"
        clips.append(Clip(start, end, str(item.get("caption", "")).strip(), effect, str(item.get("sfx", "none"))))
    total = sum(c.end - c.start for c in clips)
    if not MIN_OUTPUT_SECONDS <= total <= MAX_OUTPUT_SECONDS:
        raise ValueError(f"Durasi timeline {total:.1f} detik di luar batas {MIN_OUTPUT_SECONDS}-{MAX_OUTPUT_SECONDS} detik.")
    return clips, narration
