# Bot Shorts

Bot Discord untuk mengubah URL video YouTube menjadi video vertikal Shorts berisi komentar/narasi berbahasa Indonesia. Runner dijalankan manual melalui GitHub Actions dan otomatis berhenti setelah maksimal 6 jam.

## Alur

1. Slash command `/short <url>` membuat satu embed progres dan memperbarui pesan yang sama.
2. Download sumber YouTube (maksimum 30 menit dan 500 MB secara default).
3. AI Director mengirim URL YouTube sebagai input video Gemini. Jika gagal, file MP4 yang sudah diunduh diunggah ke Files API dan dianalisis dengan prompt yang sama.
4. Timeline memvalidasi klip sumber dan durasi hasil 20-180 detik. Target sekitar 60 detik, tidak wajib tepat 60.
5. Voice Engine membuat seluruh narasi dalam satu permintaan TTS.
6. FFmpeg menyusun klip, crop 9:16 1080x1920, efek zoom/slow, subtitle, dan audio narasi. Musik latar opsional dibaca dari `assets/music.mp3`.
7. MP4 dikirim ke Discord jika ukurannya sesuai batas upload. Jika terlalu besar (atau Discord menolak upload), MP4 otomatis diunggah ke Google Drive dan tautan akses ditambahkan ke embed progres yang sama.

## Status dan batasan

- [x] Workflow GitHub Actions manual, maksimum 360 menit
- [x] Automated syntax check dan unit tests saat push/pull request
- [x] Bot Discord dan slash command
- [x] Download YouTube dengan validasi host, durasi, dan ukuran
- [x] AI Director: URL video dahulu, fallback upload file
- [x] Timeline fleksibel, target 60 detik, maksimum 180 detik
- [x] TTS satu permintaan per video melalui GenerateContent
- [x] FFmpeg render vertikal, subtitle, zoom/slow, audio narasi
- [x] Musik latar opsional melalui file lokal
- [x] Google Drive OAuth 2.0 upload dan tautan viewer untuk fallback file besar
- [ ] Pemetaan efek SFX otomatis; field SFX dari Director belum diproses oleh renderer
- [ ] Transisi antar-klip lanjutan

**Belum diuji end-to-end.** Unit tests dan pemeriksaan sintaks berjalan di GitHub Actions, tetapi pengujian runtime masih memerlukan secret aktif, akses model TTS, izin Google Drive, dan satu video uji.

## Tiga GitHub Secrets

Buka **Settings → Secrets and variables → Actions → New repository secret**. Tambahkan:

1. `DISCORD_TOKEN` — token bot Discord.
2. `GEMINI_API_KEY` — API key Gemini untuk analisis video dan TTS.
3. `GOOGLE_DRIVE_CREDENTIALS` — satu JSON berisi OAuth client ID, client secret, dan refresh token Google Drive. Jangan menaruh JSON ini di repository atau membagikannya.

Contoh bentuk nilai secret ketiga (gunakan nilai asli dari file hasil otorisasi, bukan contoh ini):

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "refresh_token": "YOUR_REFRESH_TOKEN",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

Opsional: tambahkan Repository Variable `GOOGLE_DRIVE_FOLDER_ID` berisi ID folder Drive tujuan. Jika kosong, file masuk ke My Drive utama.

## Menyiapkan OAuth Google Drive

Gunakan akun Google yang memiliki Drive tujuan. Service Account tidak dipakai karena tidak bisa memiliki file di My Drive pribadi; OAuth mengunggah atas nama akun Google yang memberi izin.

1. Buka Google Cloud Console dan buat/pilih project.
2. Aktifkan **Google Drive API**.
3. Konfigurasikan Google Auth Platform / OAuth consent. Untuk aplikasi External dalam status Testing, tambahkan akun Google yang akan dipakai sebagai Test user.
4. Buat OAuth Client ID dengan tipe **Desktop app**, lalu unduh JSON-nya.
5. Di komputer lokal, pasang dependency: `pip install -r requirements.txt`.
6. Simpan file unduhan sebagai `client_secret.json` di root repository lokal (jangan commit).
7. Jalankan `python scripts/authorize_google_drive.py`. Browser akan meminta izin akses Drive. Script menghasilkan `google_drive_credentials.json`.
8. Salin seluruh isi file tersebut ke GitHub Secret bernama `GOOGLE_DRIVE_CREDENTIALS`, lalu hapus salinan lokal jika sudah tidak diperlukan.
9. Untuk penggunaan berkelanjutan, perhatikan status publikasi OAuth. Refresh token untuk aplikasi External yang masih Testing akan kedaluwarsa setelah 7 hari; ubah status ke In production jika sesuai kebutuhan dan kebijakan Google.

**Catatan akses tautan:** agar penerima Discord dapat membuka video, integrasi membuat izin **Anyone with the link — Viewer** untuk file hasil. Artinya siapa pun yang memperoleh tautannya dapat melihat video tersebut. Jangan gunakan untuk video privat/sensitif. File yang sudah diunggah tetapi gagal diberi izin tautan akan dihapus oleh integrasi.

Referensi resmi:
- [Google Drive API — Quickstart Python](https://developers.google.com/workspace/drive/api/quickstart/python)
- [Google Drive API — Create and manage files](https://developers.google.com/workspace/drive/api/guides/create-file)
- [Google OAuth 2.0 — Refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration)

## Menjalankan bot

1. Pastikan tiga GitHub Secrets sudah diisi.
2. Buka tab **Actions**.
3. Pilih **Run Discord Shorts Bot**.
4. Tekan **Run workflow**.
5. Bot aktif selama job berjalan, maksimal 6 jam. Setelah itu GitHub Actions menghentikan runner dan bot offline.

Workflow memakai concurrency agar sesi bot tidak berjalan paralel.

## Pengembangan lokal

Python 3.11 dan FFmpeg dengan filter subtitles/libass diperlukan.

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Untuk fitur Google Drive, jalankan proses OAuth di atas dan masukkan nilai JSON ke `GOOGLE_DRIVE_CREDENTIALS` di file `.env` lokal. Jangan commit `.env`.

Opsional: letakkan musik yang memang boleh digunakan di `assets/music.mp3`. Renderer mencampurnya pada volume rendah.
