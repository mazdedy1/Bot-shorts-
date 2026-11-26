# Bot Shorts

Bot Discord untuk membuat video Shorts dari URL YouTube. Runner dijalankan manual melalui GitHub Actions dan otomatis berhenti setelah maksimal 6 jam.

## Status pembangunan

- [x] Workflow GitHub Actions manual, maksimum 360 menit
- [x] Bot Discord dan slash command `/short`
- [x] Download video YouTube dengan batas durasi dan ukuran
- [ ] AI Director: analisis URL Gemini dengan fallback upload file
- [ ] Timeline fleksibel, target sekitar 60 detik (bukan durasi wajib)
- [ ] Voice Engine: satu permintaan TTS per video
- [ ] FFmpeg Editor: klip, subtitle, overlay, SFX, musik, mixing, render 9:16
- [ ] Pengiriman MP4 atau tautan alternatif ke Discord

**Catatan:** repository ini baru berisi fondasi awal. Bot belum menghasilkan MP4 sampai seluruh tahap AI, TTS, dan editor selesai diimplementasikan.

## GitHub Secrets

Tambahkan melalui **Settings → Secrets and variables → Actions → New repository secret**:

- `DISCORD_TOKEN`: token bot Discord
- `GEMINI_API_KEY`: API key Gemini

Opsional: tambahkan repository variable `GEMINI_MODEL`.

Jangan commit file `.env` atau token ke repository.

## Menjalankan bot

1. Buka tab **Actions**.
2. Pilih **Run Discord Shorts Bot**.
3. Tekan **Run workflow**.
4. Bot aktif selama job berjalan, maksimal 6 jam.
5. Setelah 6 jam GitHub Actions menghentikan runner.

Workflow memakai concurrency agar workflow bot tidak berjalan paralel. GitHub Actions bukan hosting permanen; setelah job selesai bot offline.

## Pengembangan lokal

Python 3.11 dan FFmpeg diperlukan.

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```
