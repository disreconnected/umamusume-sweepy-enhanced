"""Credential and local-boundary proof (Approach §6, verification #4)."""

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["UMA_TEST_MODE"] = "1"
os.environ.setdefault("UMA_FIXTURE_SCENARIO", "trackblazer")

from fastapi.testclient import TestClient  # noqa: E402

import main as main_module  # noqa: E402

LOOPBACK_CLIENT = ("127.0.0.1", 51234)
LOCAL_ORIGIN = "http://127.0.0.1:1616"
FOREIGN_ORIGIN = "http://evil.example"


class TestLocalSecurity(unittest.TestCase):
    def setUp(self):
        main_module.career_session.raw_state = None
        main_module.career_session.normalized = None
        main_module.career_session.revision = 0
        main_module.active_client = None
        main_module.active_account = None

    def test_non_loopback_client_rejected(self):
        client = TestClient(main_module.app)  # default client host: testclient
        res = client.get("/api/session")
        self.assertEqual(res.status_code, 403)

    def test_foreign_origin_rejected_on_mutation(self):
        client = TestClient(main_module.app, client=LOOPBACK_CLIENT)
        res = client.post(
            "/api/session-cache",
            json={"steam_username": "u"},
            headers={"Origin": FOREIGN_ORIGIN},
        )
        self.assertEqual(res.status_code, 403)

    def test_localhost_origin_and_missing_origin_allowed(self):
        client = TestClient(main_module.app, client=LOOPBACK_CLIENT)
        ok = client.post(
            "/api/session-cache",
            json={"steam_username": "u"},
            headers={"Origin": LOCAL_ORIGIN},
        )
        self.assertEqual(ok.status_code, 200)
        no_origin = client.post("/api/session-cache", json={"steam_username": "u"})
        self.assertEqual(no_origin.status_code, 200)

    def test_legacy_cache_password_removed_on_load(self):
        path = main_module.SESSION_CACHE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "viewer_id": 1,
            "steam_username": "user",
            "steam_password": "super-secret",
            "saved_password": "also-secret",
            "proxy_url": "",
        }), encoding="utf-8")
        cache = main_module._load_session_cache()
        self.assertNotIn("steam_password", cache)
        self.assertNotIn("saved_password", cache)
        persisted = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("steam_password", persisted)
        self.assertNotIn("saved_password", persisted)
        path.unlink(missing_ok=True)

    def test_session_cache_never_accepts_password(self):
        client = TestClient(main_module.app, client=LOOPBACK_CLIENT)
        res = client.post(
            "/api/session-cache",
            json={"steam_username": "u", "steam_password": "hunter2", "proxy_url": ""},
            headers={"Origin": LOCAL_ORIGIN},
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("steam_password", json.dumps(res.json()))
        dumped = json.dumps(res.json())
        self.assertNotIn("hunter2", dumped)

    def test_login_and_play_responses_no_secret_and_no_store(self):
        client = TestClient(main_module.app, client=LOOPBACK_CLIENT)
        login = client.post("/api/login", json={"username": "u", "password": "hunter2-secret"})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.headers.get("cache-control"), "no-store")
        dumped = json.dumps(login.json())
        for secret in ("hunter2-secret", "hunter2", "steam_password"):
            self.assertNotIn(secret, dumped)
        state = client.get("/api/play/state")
        self.assertEqual(state.headers.get("cache-control"), "no-store")

    def test_diagnostics_redaction(self):
        from uma_api.client import redact_for_console
        payload = {"auth_key": "abc", "data": {"chara_info": {"turn": 3}}}
        out = redact_for_console(payload)
        self.assertEqual(out["auth_key"], "<redacted>")
        self.assertEqual(out["data"]["chara_info"]["turn"], 3)


if __name__ == "__main__":
    unittest.main()
