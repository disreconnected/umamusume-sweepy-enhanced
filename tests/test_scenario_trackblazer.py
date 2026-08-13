"""Trackblazer adapter replay + recommendation coverage."""

import unittest

from tests._scenario_harness import ScenarioReplayTestCase


class TestTrackblazerScenario(ScenarioReplayTestCase):
    slug = "trackblazer"

    replay_cases = [
        # home command chains to the next turn
        ("001_load_career", "command:1:101:0:0", ["002_train_speed"], "turn", 13),
        # multi-choice event stops; the event choice resolves to home
        ("003_event_multi", "event:501:1", ["004_event_choice"], "phase", "home"),
        # race entry flows through entry/start/end/out to a home state
        ("005_race_select", "race:10101",
         ["006_race_entry", "007_race_start", "008_race_end", "009_race_out"],
         "phase", "home"),
        # explicit skill purchase resolves to a home state
        ("012_skills", "skill:200012", ["002_train_speed"], "turn", 13),
    ]

    recommendation_cases = [
        ("016_low_energy", "command:7:701"),          # rest on critical energy
        ("017_friendship", "command:1:101"),          # friendship training wins
        ("005_race_select", "race:10101", {"extra_race_list": [10101]}),  # planned race wins
        ("013_finish", "finish"),
    ]

    forced_event_fixture = "015_event_forced"
    forced_event_resolution = "004_event_choice"


if __name__ == "__main__":
    unittest.main()
