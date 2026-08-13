"""Unity Cup adapter replay + recommendation coverage."""

import unittest

from tests._scenario_harness import ScenarioReplayTestCase


class TestUnityScenario(ScenarioReplayTestCase):
    slug = "unity"

    replay_cases = [
        # roster assignment advances to the opponent decision screen
        ("002_roster_decision", "unity:roster:1:100001", ["003_opponent_decision"], "phase", "scenario"),
        # opponent selection advances to a home state
        ("003_opponent_decision", "unity:opponent:20101", ["004_spirit_burst"], "phase", "home"),
        # multi-choice event stops; the choice resolves to home
        ("005_event_multi", "event:701:1", ["001_load_career"], "phase", "home"),
    ]

    recommendation_cases = [
        # multi-teammate training wins at home
        ("001_load_career", "command:1:101"),
        # roster decision: strongest member to slot 1
        ("002_roster_decision", "unity:roster:1:100001"),
        # opponent decision: category covered by a filled roster slot
        ("003_opponent_decision", "unity:opponent:20101"),
        # spirit burst ready: burst training wins
        ("004_spirit_burst", "command:1:101"),
    ]

    forced_event_fixture = ""
    forced_event_resolution = ""


if __name__ == "__main__":
    unittest.main()
