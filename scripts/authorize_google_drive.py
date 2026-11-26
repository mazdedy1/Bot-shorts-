#!/usr/bin/env python3
"""Create the OAuth JSON value used by the GOOGLE_DRIVE_CREDENTIALS GitHub Secret."""

import argparse
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE = "https://www.googleapis.com/auth/drive.file"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Authorize this bot to upload generated MP4 files to your Google Drive."
    )
    parser.add_argument(
        "--client-secrets",
        default="client_secret.json",
        help="OAuth Desktop App JSON downloaded from Google Cloud Console.",
    )
    parser.add_argument(
        "--output",
        default="google_drive_credentials.json",
        help="Local output file. Do not commit or share this file.",
    )
    args = parser.parse_args()

    client_path = Path(args.client_secrets)
    if not client_path.is_file():
        raise SystemExit(f"File OAuth tidak ditemukan: {client_path}")

    config = json.loads(client_path.read_text(encoding="utf-8"))
    client = config.get("installed") or config.get("web") or config
    if not client.get("client_id") or not client.get("client_secret"):
        raise SystemExit("JSON OAuth tidak memuat client_id dan client_secret.")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), [SCOPE])
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        success_message="Google Drive berhasil dihubungkan. Anda boleh menutup tab ini.",
    )
    if not credentials.refresh_token:
        raise SystemExit(
            "Google tidak memberikan refresh token. Jalankan ulang otorisasi dengan prompt consent."
        )

    secret_value = {
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri or "https://oauth2.googleapis.com/token",
    }
    output = Path(args.output)
    output.write_text(json.dumps(secret_value, indent=2), encoding="utf-8")
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    print(f"OAuth selesai. Simpan isi file {output} ke GitHub Secret GOOGLE_DRIVE_CREDENTIALS.")
    print("Jangan commit, upload ke chat, atau membagikan file kredensial ini.")


if __name__ == "__main__":
    main()
