import os
import wave
from pathlib import Path

from google import genai
from google.genai import types

def synthesize_narration(text: str, output_path: Path, style: str = "natural, clear Indonesian narrator") -> Path:
    """One TTS request for the complete narration; style metadata is not spoken."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("TTS_MODEL", "gemini-3.8-flash-tts")
    contents = [{
        "role": "user",
        "parts": [{
            "text": text,
            "speech_metadata": {"style": style},
        }],
    }]
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=os.getenv("TTS_VOICE", "Kore")
                    )
                )
            ),
        ),
    )
    audio_parts = [
        part.inline_data for part in (response.parts or [])
        if getattr(part, "inline_data", None) and part.inline_data.data
    ]
    if not audio_parts:
        raise RuntimeError("TTS tidak menghasilkan audio.")
    data = b"".join(part.data for part in audio_parts)
    mime = (audio_parts[0].mime_type or "audio/wav").lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if mime == "audio/wav" or data[:4] == b"RIFF":
        output_path.write_bytes(data)
    elif mime in {"audio/l16", "audio/pcm"}:
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(data)
    else:
        raise RuntimeError(f"Format audio TTS tidak didukung: {mime}")
    return output_path
