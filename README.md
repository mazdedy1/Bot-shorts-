# Bot Shorts

Bot Discord untuk mengubah URL video YouTube menjadi video vertikal Shorts berisi komentar/narasi berbahasa Indonesia. Runner dijalankan manual melalui GitHub Actions dan otomatis berhenti setelah maksimal 6 jam.

## Alur yang sudah diimplementasikan

1. Slash command `/short <url>` membuat satu embed progres dan memperbarui pesan yang sama.
2. Download sumber YouTube (maksimum 30 menit dan 500 MB secara default).
3. AI Director mengirim URL YouTube sebagai input video Gemini. Jika gagal, file MP4 yang sudah diunduh diunggah ke Files API dan dianalisis dengan prompt yang sama.
4. Timeline memvalidasi klip sumber dan durasi hasil 20-180 detik. Target sekitar 60 detik, tidak wajib tepat 60.
5. Voice Engine membuat seluruh narasi dalam satu permintaan TTS.
6. FFmpeg menyusun klip, crop 9:16 1080x1920, efek zoom/slow, subtitle, dan audio narasi. Musik latar opsional dibaca dari `assets/music.mp3`.
7. MP4 dikirim sebagai attachment pada embed progres yang sama jika ukuran file tidak melewati batas upload Discord.

## Status dan batasan

- [x] Workflow GitHub Actions manual, maksimum 360 menit
- [x] Bot Discord dan slash command
- [x] Download YouTube dengan validasi host, durasi, dan ukuran
- [x] AI Director: URL video dahulu, fallback upload file
- [x] Timeline fleksibel, target 60 detik, maksimum 180 detik
- [x] TTS satu permintaan per video melalui GenerateContent
- [x] FFmpeg render vertikal, subtitle, zoom/slow, audio narasi
- [x] Musik latar opsional melalui file lokal
- [ ] Penyimpanan alternatif dan tautan download otomatis jika MP4 melewati batas upload Discord
- [ ] Pemetaan efek SFX otomatis; saat ini field SFX dari Director belum diproses oleh renderer

**Belum diuji end-to-end.** Implementasi API dan renderer sudah ditulis, tetapi validasi runtime memerlukan API key, token Discord, akses model TTS, dan satu video uji. Jangan anggap workflow sudah berjalan sebelum dijalankan dari tab Actions.

## GitHub Secrets dan Variables

Tambahkan melalui **Settings → Secrets and variables → Actions**:

Secrets wajib:
- `DISCORD_TOKEN`: token bot Discord
- `GEMINI_API_KEY`: API key Gemini

Repository variables opsional:
- `GEMINI_MODEL` (default `gemini-2.5-flash`)
- `TTS_MODEL` (default `gemini-3.8-flash-tts`)
- `TTS_VOICE` (default `Kore`)

Jangan commit file `.env` atau token ke repository.

## Menjalankan bot

1. Buka tab **Actions**.
2. Pilih **Run Discord Shorts Bot**.
3. Tekan **Run workflow**.
4. Bot aktif selama job berjalan, maksimal 6 jam.
5. Setelah 6 jam GitHub Actions menghentikan runner dan bot offline.

Workflow memakai concurrency agar sesi bot tidak berjalan paralel.

## Pengembangan lokal

Python 3.11 dan FFmpeg dengan filter subtitles/libass diperlukan.

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Opsional: letakkan musik yang memang boleh digunakan di `assets/music.mp3`. Renderer mencampurnya pada volume rendah.
