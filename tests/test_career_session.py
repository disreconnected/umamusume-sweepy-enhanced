"""Serialized transition / stale-tab proof (Approach §2, verification #3)."""

import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests._scenario_harness import FixtureQueueClient, fresh_session, raw_for  # noqa: E402


class BarrierClient(FixtureQueueClient):
    """FixtureQueueClient that parks inside exec_command until two threads
    arrive, so the session lock is genuinely contended."""

    def __init__(self, current=None, responses=None):
        super().__init__(current=current, responses=responses)
        self.barrier = threading.Barrier(2)
        self.in_call = threading.Event()

    def exec_command(self, **kwargs):
        self.in_call.set()
        try:
            self.barrier.wait(timeout=5)
        except threading.BrokenBarrierError:
            pass
        return self._next("exec_command", **kwargs)


class TestCareerSessionSerialization(unittest.TestCase):
    def setUp(self):
        self.session = fresh_session()

    def test_two_concurrent_actions_one_mutation(self):
        client = BarrierClient(
            current=raw_for("trackblazer", "001_load_career"),
            responses=[raw_for("trackblazer", "002_train_speed")] * 4,
        )
        state = self.session.load(client, {})
        revision = state["revision"]
        action = {"id": "command:1:101:0:0"}

        results = {}
        errors = []

        def worker():
            try:
                results[threading.get_ident()] = self.session.act(client, action, revision)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertFalse(errors)
        outcomes = list(results.values())
        self.assertEqual(len(outcomes), 2)
        winners = [r for r in outcomes if r.get("success")]
        losers = [r for r in outcomes if not r.get("success")]
        self.assertEqual(len(winners), 1, "exactly one mutation must win")
        self.assertEqual(len(losers), 1)
        self.assertEqual(winners[0]["state"]["revision"], revision + 1)
        self.assertEqual(losers[0]["error"], "stale_revision")
        self.assertEqual(losers[0]["state"]["revision"], revision + 1, "loser sees the winner's snapshot")
        # exactly one exec_command reached the transport
        mutations = [c for c in client.calls if c[0] == "exec_command"]
        self.assertEqual(len(mutations), 1)

    def test_multi_choice_event_stops_before_mutation(self):
        client = FixtureQueueClient(current=raw_for("trackblazer", "003_event_multi"))
        state = self.session.load(client, {})
        self.assertEqual(state["phase"], "event")
        # a command cannot be smuggled through while an event blocks
        result = self.session.act(client, {"id": "command:1:101:0:0"}, state["revision"])
        self.assertEqual(result["error"], "unknown_action")
        self.assertEqual([c for c in client.calls if c[0] == "exec_command"], [])

    def test_spending_state_requires_explicit_action(self):
        """Shop rows appear as actions but never execute autonomously."""
        client = FixtureQueueClient(current=raw_for("trackblazer", "011_shop"))
        state = self.session.load(client, {})
        exchange = [a for a in state["actions"] if a["kind"] == "item_exchange"]
        self.assertTrue(exchange)
        for action in exchange:
            self.assertTrue(action["destructive"], "shop spending must be flagged consequential")

    def test_forced_plumbing_chains_inside_one_act(self):
        """A command whose response carries forced events resolves them in the
        same act without a second user decision."""
        client = FixtureQueueClient(
            current=raw_for("trackblazer", "001_load_career"),
            responses=[raw_for("trackblazer", "015_event_forced"), raw_for("trackblazer", "004_event_choice")],
        )
        state = self.session.load(client, {})
        result = self.session.act(client, {"id": "command:1:101:0:0"}, state["revision"])
        self.assertTrue(result["success"])
        self.assertEqual(result["state"]["phase"], "home")
        events = [c[0] for c in client.calls]
        self.assertIn("check_event", events, "forced event drained inside the same act")


if __name__ == "__main__":
    unittest.main()
