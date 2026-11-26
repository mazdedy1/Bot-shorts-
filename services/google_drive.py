import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _credentials_from_secret(raw: str) -> Credentials:
    """Build OAuth credentials from the single GOOGLE_DRIVE_CREDENTIALS secret."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS harus berisi JSON OAuth yang valid.") from exc

    client_config = payload.get("installed") or payload.get("web") or payload
    client_id = client_config.get("client_id")
    client_secret = client_config.get("client_secret")
    refresh_token = payload.get("refresh_token")
    token_uri = client_config.get("token_uri") or payload.get("token_uri") or TOKEN_URI
    if not all((client_id, client_secret, refresh_token)):
        raise ValueError(
            "GOOGLE_DRIVE_CREDENTIALS harus memuat client_id, client_secret, dan refresh_token."
        )

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=[DRIVE_SCOPE],
    )


def upload_video_to_drive(video_path: Path, filename: str = "short.mp4") -> dict[str, Any]:
    """Upload an MP4 and create an anyone-with-the-link viewer permission."""
    raw = os.getenv("GOOGLE_DRIVE_CREDENTIALS", "").strip()
    if not raw:
        raise RuntimeError("GOOGLE_DRIVE_CREDENTIALS belum diatur.")

    credentials = _credentials_from_secret(raw)
    # Refresh explicitly so credential failures are reported before the upload starts.
    credentials.refresh(Request())
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    metadata: dict[str, Any] = {"name": filename, "mimeType": "video/mp4"}
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    created = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,size,webViewLink",
        supportsAllDrives=True,
    ).execute()

    file_id = created.get("id")
    if not file_id:
        raise RuntimeError("Google Drive tidak mengembalikan ID file setelah upload.")

    try:
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
            supportsAllDrives=True,
        ).execute()
    except Exception as exc:
        # Do not leave an uploaded but unusable private file behind.
        try:
            service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        except Exception:
            pass
        raise RuntimeError(
            "Video terunggah, tetapi izin tautan publik gagal dibuat. "
            "Periksa izin folder Google Drive dan coba lagi."
        ) from exc

    link = created.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
    return {
        "id": file_id,
        "name": created.get("name", filename),
        "size": int(created.get("size") or video_path.stat().st_size),
        "url": link,
    }
