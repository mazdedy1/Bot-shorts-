# Bot Shorts

Bot Discord untuk mengubah URL video YouTube menjadi video vertikal Shorts berisi komentar/narasi berbahasa Indonesia. Runner dijalankan manual melalui GitHub Actions dan otomatis berhenti setelah maksimal 6 jam.

## Alur

1. Slash command `/short <url>` membuat satu embed progres dan memperbarui pesan yang sama.
2. Download sumber YouTube menggunakan pytubefix 11.2.2 dengan client WEB dan pembuatan PO Token otomatis via BotGuard/Node.js, memilih stream MP4 hingga 1080p dan menggabungkan audio/video adaptif dengan FFmpeg (maksimum 30 menit dan 500 MB secara default).
3. AI Director mengirim URL YouTube sebagai input video Gemini. Jika gagal, file MP4 yang sudah diunduh diunggah ke Files API dan dianalisis dengan prompt yang sama.
4. Timeline memvalidasi klip sumber dan durasi hasil 20-180 detik. Target sekitar 60 detik, tidak wajib tepat 60.
5. Voice Engine membuat seluruh narasi dalam satu permintaan TTS.
6. FFmpeg menyusun klip, crop 9:16 1080x1920, efek zoom/slow, subtitle, transisi dip-to-black, SFX sintetis, musik opsional, dan narasi.
7. MP4 dikirim langsung ke Discord jika ukurannya sesuai batas upload. Jika terlalu besar atau Discord menolak lampiran, file tetap disimpan di folder kerja runner dan diunggah sebagai GitHub Actions Artifact saat workflow menyelesaikan langkah terakhir.

## Penyimpanan video besar

- Tidak menggunakan Google Drive dan tidak membutuhkan OAuth, refresh token, atau secret Google Drive.
- Video hasil render disimpan sementara di `work/<interaction-id>/short.mp4`.
- Setelah proses bot berhenti, workflow mengunggah semua hasil `work/**/short.mp4` sebagai artifact bernama `shorts-<run-id>`.
- Artifact disimpan selama 7 hari. Unduh dari **GitHub → Actions → pilih workflow run → Artifacts**.
- Karena bot tetap aktif untuk menerima beberapa perintah, artifact baru tersedia setelah sesi bot dihentikan atau workflow berakhir. Setelah selesai membuat Shorts, hentikan workflow run dari tab Actions agar langkah upload artifact berjalan.
- Artifact adalah penyimpanan sementara untuk hasil unduhan, bukan file permanen di repository. Batas penyimpanan artifact mengikuti kuota GitHub akun/repository.

## Status dan batasan

- [x] Workflow GitHub Actions manual, maksimum 360 menit
- [x] Automated syntax check dan unit tests saat push/pull request
- [x] Bot Discord dan slash command dengan satu embed progres
- [x] Download YouTube menggunakan pytubefix dengan validasi host, durasi, dan ukuran
- [x] AI Director: URL video dahulu, fallback upload file
- [x] Timeline fleksibel, target 60 detik, maksimum 180 detik
- [x] TTS satu permintaan per video melalui GenerateContent
- [x] FFmpeg render vertikal, subtitle, zoom/slow, audio narasi
- [x] Transisi dip-to-black singkat antar-klip
- [x] SFX sintetis whoosh, impact, ding, dan pop berdasarkan label AI
- [x] Musik latar opsional melalui file lokal
- [x] GitHub Actions Artifact untuk menyimpan MP4 hasil render

**Belum diuji end-to-end.** Unit tests dan pemeriksaan sintaks berjalan di GitHub Actions, tetapi pengujian runtime masih memerlukan secret aktif, akses model TTS, dan satu video uji. SFX adalah efek sintetis sederhana, bukan rekaman audio profesional; transisi saat ini berupa dip-to-black singkat, bukan cross-dissolve.

## GitHub Actions Secrets

Buka **Settings → Secrets and variables → Actions → New repository secret**. Cukup buat dua secrets:

1. `DISCORD_TOKEN` — token bot Discord.
2. `GEMINI_API_KEY` — API key Gemini untuk analisis video dan TTS.

Tidak perlu membuat `GDrive_Auto`, `GOOGLE_DRIVE_CREDENTIALS`, atau `GOOGLE_DRIVE_FOLDER_ID`.

## Menjalankan bot

1. Pastikan dua GitHub Secrets di atas sudah diisi.
2. Buka tab **Actions**.
3. Pilih **Run Discord Shorts Bot**.
4. Tekan **Run workflow**.
5. Gunakan perintah `/short <url>` di Discord.
6. Jika semua video sudah selesai diproses, hentikan workflow run. Langkah terakhir akan mengunggah MP4 ke Artifacts.
7. Buka halaman run yang sama dan unduh artifact `shorts-<run-id>`.

Workflow memakai concurrency agar sesi bot tidak berjalan paralel.

## Pengembangan lokal

Python 3.11 dan FFmpeg dengan filter subtitles/libass diperlukan.

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Opsional: letakkan musik yang memang boleh digunakan di `assets/music.mp3`. Renderer mencampurnya pada volume rendah.
