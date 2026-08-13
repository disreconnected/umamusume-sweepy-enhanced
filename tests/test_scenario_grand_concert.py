"""Our Grand Concert adapter replay + recommendation coverage."""

import unittest

from tests._scenario_harness import ScenarioReplayTestCase


class TestGrandConcertScenario(ScenarioReplayTestCase):
    slug = "grand_concert"

    replay_cases = [
        # technique purchase advances to the next home state
        ("001_load_career", "concert:buy:technique:1", ["002_technique_offer"], "turn", 16),
        # promo concert entry is a race flow (entry/start/end/out) ending home
        ("004_promo_ready", "concert:promo:30101",
         ["002_technique_offer", "002_technique_offer", "002_technique_offer", "002_technique_offer"],
         "phase", "home"),
    ]

    recommendation_cases = [
        # energy-recovery technique timed when energy is critical
        ("002_technique_offer", "concert:buy:technique:1"),
        # song pacing: four per half-year
        ("003_song_pacing", "concert:buy:song:2"),
        # promo schedule wins while offered
        ("004_promo_ready", "concert:promo:30101"),
        # grand concert wins when ready
        ("005_grand_ready", "concert:grand"),
    ]

    forced_event_fixture = ""
    forced_event_resolution = ""


if __name__ == "__main__":
    unittest.main()
