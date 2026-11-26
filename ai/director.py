import json
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai import types

DIRECTOR_PROMPT = """
Kamu adalah AI video director untuk membuat YouTube Shorts review/komentar berbahasa Indonesia.
Analisis video yang diberikan, lalu keluarkan JSON valid sesuai schema.
Pilih momen visual yang relevan, runtut, menarik, dan bisa dipotong dari video sumber.
Buat narasi komentar orisinal berbahasa Indonesia, bukan menyalin dialog panjang dari video.
Target durasi hasil sekitar 60 detik, tetapi fleksibel mengikuti materi dan narasi; batas keras 180 detik.
Jangan memaksakan tepat 60 detik. Buat 4-12 klip, masing-masing punya start dan end dalam detik sumber.
Setiap klip harus punya caption singkat Bahasa Indonesia. Narasi final harus menyatu sebagai satu naskah.
Jangan mengarang peristiwa yang tidak terlihat/terdengar. Bila konteks tidak jelas, gunakan deskripsi netral.
Tambahkan effects hanya dari: none, zoom_in, zoom_out, slow. SFX hanya label deskriptif pendek atau none.
Output JSON saja, tanpa markdown.
Schema:
{
 "title": "judul pendek",
 "narration": "naskah voice-over lengkap",
 "style": "gaya pembacaan TTS singkat",
 "clips": [{"start":0.0,"end":5.0,"caption":"teks subtitle","effect":"none","sfx":"none"}],
 "music_mood":"none atau deskripsi singkat",
 "notes":"catatan editing singkat"
}
Pastikan start >= 0, end > start, klip berada dalam durasi video sumber, dan total durasi gabungan 20-180 detik.
"""

def _client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^`{3}(?:json)?s*|s*`{3}$", "", cleaned, flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI Director tidak mengembalikan JSON yang valid.")
    return json.loads(cleaned[start:end + 1])

def _generate(client, model: str, video_part, prompt: str) -> dict:
    response = client.models.generate_content(
        model=model,
        contents=[video_part, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.35,
            max_output_tokens=8192,
        ),
    )
    if not response.text:
        raise RuntimeError("AI Director mengembalikan respons kosong.")
    return _extract_json(response.text)

def analyze_video(youtube_url: str, video_path: Path, source_duration: float) -> tuple[dict, str]:
    client = _client()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = DIRECTOR_PROMPT + f"\nDurasi sumber video: {source_duration:.1f} detik."
    # Route 1: the YouTube URL is sent as file_data, not plain prompt text.
    try:
        part = types.Part(file_data=types.FileData(file_uri=youtube_url, mime_type="video/*"))
        plan = _generate(client, model, part, prompt)
        return plan, "URL video"
    except Exception:
        # Route 2: upload the existing MP4 and submit the exact same prompt.
        uploaded = client.files.upload(
            file=str(video_path),
            config=types.UploadFileConfig(mime_type="video/mp4"),
        )
        deadline = time.monotonic() + 300
        while True:
            state = getattr(uploaded, "state", None)
            state_name = getattr(state, "name", str(state)).upper() if state else ""
            if state_name == "ACTIVE":
                break
            if state_name in {"FAILED", "CANCELLED"}:
                raise RuntimeError("Pemrosesan file video oleh AI gagal.")
            if time.monotonic() >= deadline:
                raise TimeoutError("Waktu tunggu pemrosesan video AI habis.")
            time.sleep(5)
            uploaded = client.files.get(name=uploaded.name)
        uploaded_part = types.Part.from_uri(
            file_uri=uploaded.uri,
            mime_type=uploaded.mime_type or "video/mp4",
        )
        plan = _generate(client, model, uploaded_part, prompt)
        return plan, "Upload alternatif"
