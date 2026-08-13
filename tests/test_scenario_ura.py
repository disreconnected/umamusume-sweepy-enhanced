"""URA Finale adapter replay + recommendation coverage."""

import unittest

from tests._scenario_harness import ScenarioReplayTestCase


class TestUraScenario(ScenarioReplayTestCase):
    slug = "ura"

    replay_cases = [
        # required goal race chains entry/start/end/out to the post-race state
        ("001_load_career", "race:10101",
         ["002_race_entry", "003_race_start", "004_race_end", "005_race_out"],
         "goal_cleared", True),
        # multi-choice event stops; the choice resolves to home
        ("006_event_multi", "event:601:1", ["007_event_choice"], "phase", "home"),
        # skills purchase resolves to a home state
        ("010_skills", "skill:200012", ["008_friendship_train"], "phase", "home"),
    ]

    recommendation_cases = [
        # required goal race beats training on the goal turn
        ("001_load_career", "race:10101"),
        # friendship training beats plain training
        ("008_friendship_train", "command:1:101"),
        # continue offered stops for the user (clock decision)
        ("009_race_continue", "race:continue"),
    ]

    forced_event_fixture = ""
    forced_event_resolution = ""


if __name__ == "__main__":
    unittest.main()
