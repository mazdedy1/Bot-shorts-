# Bot Shorts

Bot Discord untuk mengubah URL video YouTube menjadi video vertikal Shorts berisi komentar/narasi berbahasa Indonesia. Runner dijalankan manual melalui GitHub Actions dan otomatis berhenti setelah maksimal 6 jam.

## Alur

1. Slash command `/short <url>` membuat satu embed progres dan memperbarui pesan yang sama.
2. Download sumber YouTube (maksimum 30 menit dan 500 MB secara default).
3. AI Director mengirim URL YouTube sebagai input video Gemini. Jika gagal, file MP4 yang sudah diunduh diunggah ke Files API dan dianalisis dengan prompt yang sama.
4. Timeline memvalidasi klip sumber dan durasi hasil 20-180 detik. Target sekitar 60 detik, tidak wajib tepat 60.
5. Voice Engine membuat seluruh narasi dalam satu permintaan TTS.
6. FFmpeg menyusun klip, crop 9:16 1080x1920, efek zoom/slow, subtitle, transisi dip-to-black, SFX sintetis, musik opsional, dan narasi.
7. MP4 dikirim ke Discord jika ukurannya sesuai batas upload. Jika terlalu besar (atau Discord menolak upload), MP4 otomatis diunggah ke Google Drive dan tautan akses ditambahkan ke embed progres yang sama.

## Status dan batasan

- [x] Workflow GitHub Actions manual, maksimum 360 menit
- [x] Automated syntax check dan unit tests saat push/pull request
- [x] Bot Discord dan slash command dengan satu embed progres
- [x] Download YouTube dengan validasi host, durasi, dan ukuran
- [x] AI Director: URL video dahulu, fallback upload file
- [x] Timeline fleksibel, target 60 detik, maksimum 180 detik
- [x] TTS satu permintaan per video melalui GenerateContent
- [x] FFmpeg render vertikal, subtitle, zoom/slow, audio narasi
- [x] Transisi dip-to-black singkat antar-klip
- [x] SFX sintetis whoosh, impact, ding, dan pop berdasarkan label AI
- [x] Musik latar opsional melalui file lokal
- [x] Google Drive OAuth 2.0 upload dan tautan viewer untuk fallback file besar

**Belum diuji end-to-end.** Unit tests dan pemeriksaan sintaks berjalan di GitHub Actions, tetapi pengujian runtime masih memerlukan secret aktif, akses model TTS, izin Google Drive, dan satu video uji. SFX adalah efek sintetis sederhana, bukan rekaman audio profesional; transisi saat ini berupa dip-to-black singkat, bukan cross-dissolve.

## GitHub Actions Secrets

Buka **Settings → Secrets and variables → Actions → New repository secret**. Buat tiga secrets berikut:

1. `DISCORD_TOKEN` — token bot Discord.
2. `GEMINI_API_KEY` — API key Gemini untuk analisis video dan TTS.
3. `GDrive_Auto` — satu JSON berisi OAuth client ID, client secret, dan refresh token Google Drive.

Nilai `GDrive_Auto` harus berupa **satu objek JSON valid**. Untuk OAuth Client bertipe Web application, gunakan struktur ini dan ganti setiap `xxx` dengan nilai asli:

```json
{
  "web": {
    "client_id": "xxx",
    "client_secret": "xxx",
    "token_uri": "https://oauth2.googleapis.com/token"
  },
  "refresh_token": "xxx"
}
```

Jangan menambahkan dua objek JSON secara berurutan, jangan menaruh koma setelah properti terakhir, dan jangan memasukkan tanda pagar/code fence ke nilai secret. Jangan commit atau membagikan kredensial ini. Source code membaca secret melalui environment variable `GOOGLE_DRIVE_CREDENTIALS`; kredensial tidak perlu ditulis ke file Python.

Opsional: tambahkan Repository Variable `GOOGLE_DRIVE_FOLDER_ID` berisi ID folder Drive tujuan. Jika kosong, file masuk ke My Drive utama.

## Menyiapkan OAuth Google Drive

1. Di Google Cloud Console, pilih project dan aktifkan **Google Drive API**.
2. Konfigurasikan Google Auth Platform / OAuth consent screen. Jika aplikasi External masih berstatus Testing, tambahkan akun Google yang akan memberi izin sebagai Test user.
3. Buat OAuth Client ID bertipe **Web application**.
4. Pada Authorized redirect URIs, tambahkan persis `https://developers.google.com/oauthplayground`. Authorized JavaScript origins boleh dikosongkan untuk alur ini.
5. Buka Google OAuth 2.0 Playground. Pada pengaturan (ikon roda gigi), aktifkan **Use your own OAuth credentials**, lalu masukkan Client ID dan Client Secret dari OAuth client yang sama.
6. Pada Step 1, pilih scope `https://www.googleapis.com/auth/drive.file`, lalu lakukan Authorize APIs dan setujui akses menggunakan akun Google Drive tujuan.
7. Pada Step 2, tukarkan authorization code untuk token. Ambil nilai **refresh_token** dari respons token.
8. Susun satu JSON dengan format di atas, lalu simpan langsung sebagai GitHub Secret bernama `GDrive_Auto`. Jangan kirim refresh token atau client secret ke chat, issue, log, maupun repository.

File JSON yang diunduh dari Google Cloud berisi konfigurasi OAuth client (misalnya client ID, client secret, token URI), **bukan refresh token**. Gunakan file itu sebagai sumber nilai konfigurasi; refresh token didapat setelah persetujuan OAuth. Simpan file unduhan dengan aman dan jangan commit.

Untuk penggunaan berkelanjutan, perhatikan status publikasi OAuth. Refresh token untuk aplikasi External yang masih Testing dapat kedaluwarsa setelah 7 hari. Ubah status ke In production jika sesuai kebutuhan dan kebijakan Google; Google dapat mensyaratkan verifikasi untuk scope tertentu.

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

Untuk fitur Google Drive, isi `GOOGLE_DRIVE_CREDENTIALS` di `.env` lokal dengan JSON OAuth yang sama. Jangan commit `.env`.

Opsional: letakkan musik yang memang boleh digunakan di `assets/music.mp3`. Renderer mencampurnya pada volume rendah.
```
