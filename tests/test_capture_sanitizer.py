"""Redaction + sanitizer contract (Approach §1, verification #1)."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from career_bot.capture import (
    SENSITIVE_ERROR_KEYS,
    TOKENIZED_KEYS,
    redact,
    redact_for_console,
    sanitize_raw_session,
    sanitize_record,
)


class TestRedactor(unittest.TestCase):
    def test_sensitive_keys_replaced_everywhere(self):
        nested = {
            "auth_key": "deadbeef",
            "data": {
                "chara_info": {"turn": 12, "udid": "11111111-2222-3333-4444-555555555555"},
                "nested_list": [{"sid": "abc", "value": 1}, {"device_id": "xyz"}],
            },
        }
        out = redact(nested)
        assert "deadbeef" not in json.dumps(out)
        assert "11111111-2222-3333-4444-555555555555" not in json.dumps(out)
        assert "abc" not in json.dumps(out)
        assert "xyz" not in json.dumps(out)
        # gameplay numbers survive
        self.assertEqual(out["data"]["chara_info"]["turn"], 12)

    def test_bytes_and_nested_lists(self):
        payload = {"blob": b"\x00\x01\x02", "rows": [{"viewer_id": 42, "value": 7}]}
        out = redact(payload)
        self.assertIsInstance(out["blob"], str)
        self.assertEqual(out["rows"][0]["value"], 7)

    def test_console_variant_truncates(self):
        out = redact_for_console({"long": "x" * 500, "steam_session_ticket": "t" * 200})
        self.assertEqual(len(out["long"]), 160 + len("...<truncated>"))
        self.assertEqual(out["steam_session_ticket"], "<redacted>")


class TestSanitizer(unittest.TestCase):
    def _raw_session(self):
        return [
            {
                "kind": "http",
                "request": {
                    "endpoint": "single_mode_free/exec_command",
                    "request_id": "req_1",
                    "viewer_id": 12345,
                },
                "response": {
                    "data": {
                        "chara_info": {
                            "turn": 13,
                            "viewer_id": 12345,
                            "scenario_id": 4,
                            "speed": 145,
                            "skill_point": 340,
                        },
                        "home_info": {"command_info_array": [{"command_type": 1, "command_id": 101, "failure_rate": 15}]},
                    },
                    "data_headers": {"result_code": 1, "viewer_id": 12345},
                },
            },
            {
                "kind": "http",
                "request": {"endpoint": "load/index", "request_id": "req_2", "viewer_id": 12345},
                "response": {"data": {"tp_info": {"current_tp": 30}}, "data_headers": {"result_code": 1}},
            },
            {
                "kind": "http_unpaired",
                "request": {"endpoint": "single_mode_free/race_start", "viewer_id": 12345},
                "response": {},
            },
        ]

    def test_two_sanitizations_byte_identical(self):
        raw = self._raw_session()
        a = sanitize_raw_session(raw, "trackblazer")
        b = sanitize_raw_session(raw, "trackblazer")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_referential_equality_and_gameplay_ids_preserved(self):
        raw = self._raw_session()
        out = sanitize_raw_session(raw, "trackblazer")
        self.assertEqual(len(out), 1)  # load/index is not a career endpoint; unpaired is diagnostic-only
        fixture = out[0]
        chara = fixture["response"]["data"]["chara_info"]
        headers = fixture["response"]["data_headers"]
        # same viewer_id maps to the same token everywhere
        self.assertEqual(chara["viewer_id"], headers["viewer_id"])
        self.assertNotEqual(chara["viewer_id"], 12345)
        # gameplay numbers survive verbatim
        self.assertEqual(chara["turn"], 13)
        self.assertEqual(chara["scenario_id"], 4)
        self.assertEqual(chara["speed"], 145)
        self.assertEqual(chara["skill_point"], 340)
        self.assertEqual(fixture["response"]["data"]["home_info"]["command_info_array"][0]["command_id"], 101)

    def test_no_forbidden_key_or_value_survives(self):
        raw = [{
            "kind": "http",
            "request": {"endpoint": "single_mode_free/load", "request_id": "r", "viewer_id": 9},
            "response": {"data": {"chara_info": {
                "turn": 1, "scenario_id": 4, "udid": "u-secret", "auth_key": "k-secret",
                "steam_session_ticket": "t-secret", "password": "p-secret", "device_id": "d-secret",
            }}, "data_headers": {"viewer_id": 9}},
        }]
        out = sanitize_raw_session(raw, "trackblazer")
        dumped = json.dumps(out)
        for secret in ("u-secret", "k-secret", "t-secret", "p-secret", "d-secret"):
            self.assertNotIn(secret, dumped)

    def test_sanitize_record_equality_preserved_across_records(self):
        raw = [
            {"kind": "http", "request": {"endpoint": "single_mode_free/load", "viewer_id": 77}, "response": {"data": {"chara_info": {"turn": 1, "viewer_id": 77}}}},
            {"kind": "http", "request": {"endpoint": "single_mode_free/exec_command", "viewer_id": 77}, "response": {"data": {"chara_info": {"turn": 2, "viewer_id": 77}}}},
        ]
        out = sanitize_raw_session(raw, "trackblazer")
        token_a = out[0]["response"]["data"]["chara_info"]["viewer_id"]
        token_b = out[1]["response"]["data"]["chara_info"]["viewer_id"]
        self.assertEqual(token_a, token_b)


if __name__ == "__main__":
    unittest.main()
