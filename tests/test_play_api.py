"""Play API status policy with the fixture transport (verification #3/#7)."""

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


def reset_session_state():
    main_module.career_session.reset()
    main_module.active_client = None
    main_module.active_account = None
    main_module.active_dashboard_data = None


class TestPlayApi(unittest.TestCase):
    def setUp(self):
        reset_session_state()
        self.client = TestClient(main_module.app, client=LOOPBACK_CLIENT)

    def test_play_scenarios_from_captured_registry(self):
        res = self.client.get("/api/play/scenarios")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        slugs = {s["slug"] for s in data["scenarios"]}
        self.assertEqual(slugs, {"ura", "unity", "trackblazer", "grand_concert"})

    def test_play_requires_login(self):
        res = self.client.get("/api/play/state")
        self.assertEqual(res.status_code, 401)

    def test_login_then_state_then_action_then_stale(self):
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.json().get("success"))
        self.assertEqual(login.headers.get("cache-control"), "no-store")

        state = self.client.get("/api/play/state")
        self.assertEqual(state.status_code, 200)
        play_state = state.json()["state"]
        self.assertEqual(play_state["scenario"]["slug"], "trackblazer")
        revision = play_state["revision"]

        act = self.client.post("/api/play/action", json={"action_id": "command:1:101:0:0", "expected_revision": revision})
        self.assertEqual(act.status_code, 200)
        self.assertEqual(act.json()["state"]["revision"], revision + 1)

        # deliberately stale second tab
        stale = self.client.post("/api/play/action", json={"action_id": "command:1:101:0:0", "expected_revision": revision})
        self.assertEqual(stale.status_code, 409)
        body = stale.json()
        self.assertEqual(body["error"], "stale_revision")
        self.assertEqual(body["state"]["revision"], revision + 1)

    def test_unknown_action_422_and_upstream_502(self):
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertTrue(login.json().get("success"))
        state = self.client.get("/api/play/state").json()["state"]

        bad = self.client.post("/api/play/action", json={"action_id": "no:such:action", "expected_revision": state["revision"]})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"], "unknown_action")

    def test_finish_stale_revision_returns_409_not_500(self):
        """_play_result JSONResponse errors must pass through finish/delete
        unchanged (review finding: stale/upstream errors became 500s)."""
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertTrue(login.json().get("success"))
        state = self.client.get("/api/play/state").json()["state"]
        stale = self.client.post("/api/career/finish", json={"expected_revision": state["revision"] + 9})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["error"], "stale_revision")
        self.assertEqual(stale.json()["state"]["revision"], state["revision"])

    def test_delete_stale_revision_returns_409_not_500(self):
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertTrue(login.json().get("success"))
        state = self.client.get("/api/play/state").json()["state"]
        stale = self.client.post("/api/career/delete", json={"expected_revision": state["revision"] + 9})
        self.assertEqual(stale.status_code, 409)

    def test_finish_action_refreshes_account(self):
        """The grid finish action is terminal: account refresh + new-career
        availability, no relogin needed."""
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertTrue(login.json().get("success"))
        st = self.client.get("/api/play/state").json()["state"]
        # drive to the finish state (013)
        for aid in ["command:1:101:0:0", "command:7:701:0:0", "event:501:1",
                    "command:1:101:0:0", "race:10101", "command:1:101:0:0", "race:accept",
                    "command:1:101:0:0"]:
            r = self.client.post("/api/play/action", json={"action_id": aid, "expected_revision": st["revision"]})
            st = r.json()["state"]
        self.assertEqual(st["phase"], "finish")
        r = self.client.post("/api/play/action", json={"action_id": "finish", "expected_revision": st["revision"]})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body.get("success"))
        self.assertIn("account", body)
        self.assertIsNone(body["account"]["career"])

    def test_no_store_on_session_and_play(self):
        res = self.client.get("/api/session")
        self.assertEqual(res.headers.get("cache-control"), None)  # non-mutating GET
        login = self.client.post("/api/login", json={"username": "u", "password": "p"})
        self.assertEqual(login.headers.get("cache-control"), "no-store")
        state = self.client.get("/api/play/state")
        self.assertEqual(state.headers.get("cache-control"), "no-store")


if __name__ == "__main__":
    unittest.main()
