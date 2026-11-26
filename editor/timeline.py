from dataclasses import dataclass

MAX_OUTPUT_SECONDS = 180
MIN_OUTPUT_SECONDS = 20
ALLOWED_SFX = {"none", "whoosh", "impact", "ding", "pop"}


@dataclass
class Clip:
    start: float
    end: float
    caption: str
    effect: str = "none"
    sfx: str = "none"

    @property
    def output_duration(self) -> float:
        duration = self.end - self.start
        return duration * 1.08 if self.effect == "slow" else duration


def validate_plan(plan: dict, source_duration: float) -> tuple[list[Clip], str]:
    if not isinstance(plan, dict):
        raise ValueError("Format timeline AI tidak valid.")
    narration = str(plan.get("narration", "")).strip()
    if not narration:
        raise ValueError("Naskah narasi kosong.")
    raw_clips = plan.get("clips")
    if not isinstance(raw_clips, list) or not 1 <= len(raw_clips) <= 12:
        raise ValueError("AI Director harus menghasilkan 1-12 klip.")
    clips: list[Clip] = []
    for item in raw_clips:
        if not isinstance(item, dict):
            raise ValueError("Format klip AI tidak valid.")
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Timestamp klip AI tidak valid.") from None
        if start < 0 or end <= start or end > source_duration + 0.25:
            raise ValueError("Rentang klip AI berada di luar durasi sumber.")
        effect = str(item.get("effect", "none")).lower()
        if effect not in {"none", "zoom_in", "zoom_out", "slow"}:
            effect = "none"
        sfx = str(item.get("sfx", "none")).strip().lower()
        if sfx not in ALLOWED_SFX:
            sfx = "none"
        clips.append(Clip(
            start=start,
            end=min(end, source_duration),
            caption=str(item.get("caption", "")).strip()[:180],
            effect=effect,
            sfx=sfx,
        ))
    total = sum(c.output_duration for c in clips)
    if not MIN_OUTPUT_SECONDS <= total <= MAX_OUTPUT_SECONDS:
        raise ValueError(
            f"Durasi timeline {total:.1f} detik di luar batas "
            f"{MIN_OUTPUT_SECONDS}-{MAX_OUTPUT_SECONDS} detik."
        )
    return clips, narration
