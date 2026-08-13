"""Shared harness for scenario adapter replay/recommendation tests."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from career_bot.runner import CareerSession  # noqa: E402


def load_fixtures(slug):
    directory = ROOT / "tests" / "fixtures" / "scenarios" / slug
    result = {}
    for path in sorted(directory.glob("*.json")):
        result[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return result


class FixtureQueueClient:
    """Fake UmaClient. load_career() returns the *current* state without
    consuming; every mutating call pops the next queued response and makes it
    the current state. Every call is recorded for assertion."""

    def __init__(self, current=None, responses=None):
        self.current = current if current is not None else {"data": {}, "data_headers": {"result_code": 1}}
        self.queue = list(responses or [])
        self.calls = []
        self.viewer_id = 1

    def load_career(self):
        self.calls.append(("load_career", {}))
        return self.current

    def login(self):
        self.calls.append(("login", {}))
        return self.current

    def _next(self, ep, **kwargs):
        self.calls.append((ep, kwargs))
        if self.queue:
            self.current = self.queue.pop(0)
        return self.current

    def call(self, ep, args=None):
        return self._next(ep, **(args or {}))

    def exec_command(self, **kwargs):
        return self._next("exec_command", **kwargs)

    def check_event(self, **kwargs):
        return self._next("check_event", **kwargs)

    def race_entry(self, **kwargs):
        return self._next("race_entry", **kwargs)

    def race_start(self, **kwargs):
        return self._next("race_start", **kwargs)

    def race_end(self, **kwargs):
        return self._next("race_end", **kwargs)

    def race_out(self, **kwargs):
        return self._next("race_out", **kwargs)

    def race_continue(self, **kwargs):
        return self._next("race_continue", **kwargs)

    def gain_skills(self, gain_skill_info_array, current_turn):
        return self._next("gain_skills", gain_skill_info_array=gain_skill_info_array, current_turn=current_turn)

    def use_items(self, use_item_info_array, current_turn):
        return self._next("use_items", use_item_info_array=use_item_info_array, current_turn=current_turn)

    def exchange_items(self, exchange_item_info_array, current_turn):
        return self._next("exchange_items", exchange_item_info_array=exchange_item_info_array, current_turn=current_turn)

    def minigame_end(self, current_turn, **kwargs):
        return self._next("minigame_end", current_turn=current_turn, **kwargs)

    def finish_career(self, current_turn, is_force_delete=False):
        return self._next("finish_career", current_turn=current_turn, is_force_delete=is_force_delete)


def fresh_session():
    return CareerSession(ROOT)


def fixture_response(fixture):
    return dict(fixture["response"])


def raw_for(slug, name):
    return fixture_response(load_fixtures(slug)[name])


def normalize_fixture(slug, name, session=None, preset=None):
    """Unit-level normalize (bypasses the session's transport settling)."""
    session = session or fresh_session()
    raw = raw_for(slug, name)
    adapter = session._adapter_for(raw)
    if adapter is None:
        from career_bot.scenarios.base import UnsupportedAdapter
        adapter = UnsupportedAdapter()
    context = {
        "session": session,
        "preset": preset or {},
        "skill_buyer": session.skill_buyer,
        "race_planner": session.race_planner,
        "item_manager": session.item_manager,
    }
    normalized = adapter.normalize(raw, context)
    normalized["actions"] = adapter.actions(raw, normalized)
    normalized["recommendation"] = adapter.recommend(normalized, preset or {})
    return normalized, adapter


def _value_of(state, key):
    if key == "phase":
        return state["phase"]
    if key == "turn":
        return state["turn"]
    if key == "fans":
        return state["fans"]
    if key == "revision":
        return state["revision"]
    if key == "goal_cleared":
        return any(g["cleared"] for g in state.get("scenario_state", {}).get("goals", []))
    raise KeyError(key)


class ScenarioReplayTestCase(unittest.TestCase):
    slug = ""
    #: (fixture_a, action_id, [response fixture names in order], key, value)
    replay_cases = []
    #: (fixture_name, expected_top_action_prefix, preset_override)
    recommendation_cases = []
    forced_event_fixture = ""
    forced_event_resolution = ""

    def setUp(self):
        if not self.slug:
            self.skipTest("abstract base scenario test case")
        self.session = fresh_session()
        self.fixtures = load_fixtures(self.slug)

    def test_every_fixture_recognized_with_valid_contract(self):
        from career_bot.scenarios.base import PHASES
        for name in sorted(self.fixtures):
            normalized, adapter = normalize_fixture(self.slug, name, self.session)
            self.assertIn(normalized["phase"], PHASES, name)
            self.assertEqual(normalized["scenario"]["slug"], self.slug, name)
            ids = [a["id"] for a in normalized["actions"]]
            self.assertEqual(len(ids), len(set(ids)), f"duplicate action ids in {name}")
            for action in normalized["actions"]:
                self.assertIn(action["kind"], {
                    "command", "event", "race", "race_continue",
                    "item_exchange", "item_use", "skill_purchase", "scenario",
                }, name)
                self.assertIsInstance(action["payload"], dict, name)
            rec = normalized.get("recommendation")
            if rec and rec.get("action_id"):
                action = next((a for a in normalized["actions"] if a["id"] == rec["action_id"]), None)
                self.assertIsNotNone(action, f"recommendation targets missing action in {name}")
                self.assertTrue(action["enabled"], f"recommendation targets disabled action in {name}")
                self.assertTrue(rec.get("factors"), f"recommendation lacks factors in {name}")
                self.assertIsInstance(rec["score"], (int, float), name)

    def test_curated_recommendation_cases(self):
        for row in self.recommendation_cases:
            name, expected_prefix = row[0], row[1]
            preset = row[2] if len(row) > 2 else None
            normalized, _ = normalize_fixture(self.slug, name, self.session, preset=preset)
            rec = normalized.get("recommendation")
            self.assertIsNotNone(rec, f"{name}: expected a recommendation")
            self.assertTrue(
                rec["action_id"].startswith(expected_prefix),
                f"{name}: expected top action starting with {expected_prefix!r}, got {rec['action_id']!r}",
            )

    def test_replay_cases(self):
        for a_name, action_id, response_names, key, value in self.replay_cases:
            client = FixtureQueueClient(
                current=raw_for(self.slug, a_name),
                responses=[raw_for(self.slug, b_name) for b_name in response_names],
            )
            state = self.session.load(client, {})
            catalog = {a["id"]: a for a in state["actions"]}
            self.assertIn(action_id, catalog, f"{a_name}: action {action_id} not in catalog")
            result = self.session.act(client, {"id": action_id}, state["revision"])
            self.assertTrue(result["success"], f"{a_name} -> {response_names}: {result}")
            self.assertEqual(result["state"]["revision"], state["revision"] + 1, f"{a_name} -> {response_names}")
            self.assertEqual(_value_of(result["state"], key), value, f"{a_name} -> {response_names}")

    def test_forced_event_drains_on_load(self):
        if not self.forced_event_fixture:
            self.skipTest("no forced-event fixture defined")
        client = FixtureQueueClient(
            current=raw_for(self.slug, self.forced_event_fixture),
            responses=[raw_for(self.slug, self.forced_event_resolution)],
        )
        state = self.session.load(client, {})
        self.assertEqual(state["phase"], "home")
        self.assertTrue(any(c[0] == "check_event" for c in client.calls), "forced event must auto-submit")

    def test_stale_revision_conflict(self):
        first = sorted(self.fixtures)[0]
        client = FixtureQueueClient(current=raw_for(self.slug, first))
        state = self.session.load(client, {})
        result = self.session.act(client, {"id": "nope"}, state["revision"] + 7)
        self.assertEqual(result["error"], "stale_revision")
        self.assertEqual(result["state"]["revision"], state["revision"])

    def test_unknown_scenario_fails_closed(self):
        raw = {
            "data": {"chara_info": {"turn": 1, "playing_state": 1, "scenario_id": 99999}},
            "data_headers": {"result_code": 1},
        }
        session = fresh_session()
        adapter = session._adapter_for(raw)
        self.assertIsNone(adapter)
        from career_bot.scenarios.base import UnsupportedAdapter
        unsupported = UnsupportedAdapter()
        normalized = unsupported.normalize(raw, {"session": session})
        self.assertEqual(normalized["phase"], "unsupported")
        self.assertEqual(unsupported.actions(raw, normalized), [])

    def test_act_ignores_client_supplied_numbers(self):
        """act() must use the server-built catalog payload, never client
        numbers beyond id/selection/expected_revision."""
        a_name, action_id, response_names = self.replay_cases[0][:3]
        client = FixtureQueueClient(
            current=raw_for(self.slug, a_name),
            responses=[raw_for(self.slug, b) for b in response_names],
        )
        state = self.session.load(client, {})
        tampered = {"id": action_id, "payload": {"current_turn": 999, "command_id": 999}}
        result = self.session.act(client, tampered, state["revision"])
        self.assertTrue(result["success"], result)
        self.assertTrue(client.calls, "expected at least one transport call")
        for ep, kwargs in client.calls:
            if ep in {"load_career", "login"}:
                continue
            self.assertNotEqual(kwargs.get("current_turn"), 999, ep)
            self.assertNotEqual(kwargs.get("command_id"), 999, ep)

    def test_unknown_action_is_typed_error(self):
        first = sorted(self.fixtures)[0]
        client = FixtureQueueClient(current=raw_for(self.slug, first))
        state = self.session.load(client, {})
        result = self.session.act(client, {"id": "no:such:action"}, state["revision"])
        self.assertEqual(result["error"], "unknown_action")
        self.assertEqual(result["state"]["revision"], state["revision"])
