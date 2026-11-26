import json
import unittest

from services.google_drive import DRIVE_SCOPE, _credentials_from_secret


class GoogleDriveCredentialTests(unittest.TestCase):
    def test_builds_credentials_from_flat_secret(self):
        payload = {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "refresh_token": "refresh-token",
        }
        credentials = _credentials_from_secret(json.dumps(payload))
        self.assertEqual(credentials.client_id, "client-id")
        self.assertEqual(credentials.client_secret, "client-secret")
        self.assertEqual(credentials.refresh_token, "refresh-token")
        self.assertEqual(credentials.scopes, [DRIVE_SCOPE])

    def test_accepts_downloaded_oauth_client_shape(self):
        payload = {
            "installed": {
                "client_id": "client-id",
                "client_secret": "client-secret",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
            "refresh_token": "refresh-token",
        }
        credentials = _credentials_from_secret(json.dumps(payload))
        self.assertEqual(credentials.client_id, "client-id")

    def test_rejects_invalid_json(self):
        with self.assertRaises(ValueError):
            _credentials_from_secret("not-json")

    def test_rejects_missing_refresh_token(self):
        with self.assertRaises(ValueError):
            _credentials_from_secret(json.dumps({"client_id": "x", "client_secret": "y"}))


if __name__ == "__main__":
    unittest.main()
