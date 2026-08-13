"""Our Grand Concert adapter (scenario id from the captured manifest).

Normalizes the five Performance Point currencies, techniques, songs,
learned-song count, Hype, the promo schedule, and concert states.
Recommends Friendship Training and deck-relevant stat gains, energy-recovery
technique timing, four songs per half-year, priority Skill Point / friendship
songs, and the 16/18-song timing gates. Every technique/song choice remains an
explicit user action.
"""

from __future__ import annotations

from career_bot.scenarios.base import (
    ScenarioAdapter,
    action_dict,
    bulk_skill_action,
    command_actions,
    derive_common_phase,
    event_action_id,
    event_actions,
    event_choice_score,
    has_multi_choice_event,
    is_unrecognized_blocking_state,
    normalize_common,
    normalize_skills,
    race_continue_actions,
    race_running_actions,
    rank_recommendation,
    skill_purchase_actions,
)
from career_bot.scenarios.registry import register_adapter
from career_bot.scoring import TRAINING_COMMANDS, score_command

SONGS_PER_HALF_YEAR = 4
SONG_GATES = {49: 12, 61: 12, 73: 16}
TURNS_PER_HALF_YEAR = 24


class GrandConcertAdapter(ScenarioAdapter):
    slug = "grand_concert"
    name = "Our Grand Concert"
    scenario_id = 3

    def normalize(self, raw_state, context=None):
        data = (raw_state or {}).get("data") or {}
        chara = data.get("chara_info") or {}
        common = normalize_common(raw_state)
        preset = (context or {}).get("preset") or {}
        self._raw = raw_state or {}
        self._last_session = (context or {}).get("session")

        if not chara.get("scenario_id"):
            common["phase"] = "unsupported"
            common["error"] = "missing scenario discriminator"
            common["scenario"] = {"id": 0, "slug": "unsupported", "name": "Unsupported"}
            return common
        common["scenario"] = {"id": int(chara.get("scenario_id") or 0), "slug": self.slug, "name": self.name}
        common["skills"] = normalize_skills(context, raw_state, preset)

        info = data.get("concert_info") or {}
        pp = info.get("performance_point_array") or []
        if isinstance(pp, dict):
            pp_rows = [{"key": str(k), "value": int(v or 0)} for k, v in pp.items()]
        else:
            pp_rows = [
                {"key": str(row.get("key") or row.get("type") or ""), "value": int(row.get("value") or 0)}
                for row in pp
            ]
        turn = int(chara.get("turn") or 0)
        half_year = max(1, (turn - 1) // TURNS_PER_HALF_YEAR + 1) if turn > 0 else 1

        common["scenario_state"] = {
            "performance_points": {row["key"]: row["value"] for row in pp_rows if row["key"]},
            "hype": int(info.get("hype") or 0),
            "learned_song_count": int(info.get("learned_song_count") or 0),
            "half_year": half_year,
            "songs_this_half": int(info.get("songs_this_half") or 0),
            "techniques": [
                {
                    "technique_id": int(t.get("technique_id") or 0),
                    "name": str(t.get("name") or ""),
                    "cost": int(t.get("cost") or 0),
                    "energy_recovery": int(t.get("energy_recovery") or 0),
                    "owned": bool(t.get("owned")),
                    "deck_relevant": bool(t.get("deck_relevant")),
                }
                for t in (info.get("technique_array") or [])
            ],
            "songs": [
                {
                    "song_id": int(s.get("song_id") or 0),
                    "name": str(s.get("name") or ""),
                    "cost": int(s.get("cost") or 0),
                    "skill_point_priority": bool(s.get("skill_point_priority")),
                    "friendship_priority": bool(s.get("friendship_priority")),
                }
                for s in (info.get("song_array") or [])
            ],
            "promo": {
                "program_id": int(info.get("promo_program_id") or 0),
                "ready": bool(info.get("promo_ready")),
                "done": bool(info.get("promo_done")),
            },
            "grand_concert_ready": bool(info.get("grand_concert_ready")),
        }

        if is_unrecognized_blocking_state(chara):
            common["phase"] = "unsupported"
            common["error"] = f"unrecognized playing_state {common['playing_state']}"
            return common

        common["phase"] = derive_common_phase(common, data)
        ss = common["scenario_state"]
        if ss.get("grand_concert_ready"):
            common["phase"] = "scenario"
        if "single_mode_finish_common" in data or int(chara.get("state") or 0) == 3:
            common["phase"] = "finish"
            common["can_finish"] = True
        return common

    def actions(self, raw_state, normalized_state):
        data = (raw_state or {}).get("data") or {}
        common = normalized_state
        actions = []
        ss = common.get("scenario_state") or {}

        if has_multi_choice_event(common.get("events") or []):
            return event_actions(common.get("events") or [])

        if common.get("phase") == "race_running":
            return race_running_actions(common)

        if common.get("phase") == "race_continue":
            return race_continue_actions(common)

        if common.get("phase") == "finish":
            return [action_dict("finish", "scenario", "Finish and save career", {"is_force_delete": False}, destructive=True)]

        for technique in ss.get("techniques") or []:
            if technique.get("owned"):
                continue
            actions.append(action_dict(
                f"concert:buy:technique:{technique['technique_id']}",
                "scenario",
                f"Learn technique {technique.get('name') or technique['technique_id']} ({technique.get('cost')} PP)",
                {"technique_id": technique["technique_id"], "cost": technique.get("cost"), "current_turn": common.get("turn") or 0},
                destructive=True,
            ))

        for song in ss.get("songs") or []:
            actions.append(action_dict(
                f"concert:buy:song:{song['song_id']}",
                "scenario",
                f"Learn song {song.get('name') or song['song_id']} ({song.get('cost')} PP)",
                {"song_id": song["song_id"], "cost": song.get("cost"), "current_turn": common.get("turn") or 0},
                destructive=True,
            ))

        promo = ss.get("promo") or {}
        if promo.get("ready") and not promo.get("done") and promo.get("program_id"):
            actions.append(action_dict(
                f"concert:promo:{promo['program_id']}",
                "scenario",
                "Enter promo concert",
                {"program_id": promo["program_id"], "current_turn": common.get("turn") or 0},
            ))

        if ss.get("grand_concert_ready"):
            actions.append(action_dict(
                "concert:grand",
                "scenario",
                "Enter Grand Concert",
                {"current_turn": common.get("turn") or 0},
            ))

        actions.extend(command_actions(common))
        for item in data.get("race_condition_array") or []:
            program_id = int(item.get("program_id") or 0)
            if not program_id:
                continue
            actions.append(action_dict(
                f"race:{program_id}",
                "race",
                f"Enter race {program_id}",
                {"program_id": program_id, "current_turn": common.get("turn") or 0},
            ))
        actions.extend(skill_purchase_actions(common, common.get("skills")))
        actions.append(bulk_skill_action())
        actions.sort(key=lambda a: (a["kind"], a["id"]))
        return actions

    def execute(self, session, client, action, selection=None):
        kind = action.get("kind")
        payload = action.get("payload") or {}
        data = (session.raw_state or {}).get("data") or {}
        current_turn = int(payload.get("current_turn") or (data.get("chara_info") or {}).get("turn") or 0)

        if kind == "command":
            return session.exec_command(client, payload)
        if kind == "event":
            return session.submit_event(client, action)
        if kind == "race":
            program_id = int(payload.get("program_id") or 0)
            if not program_id:
                return session.raw_state
            return session.run_race(client, program_id, session.preset)
        if kind == "race_continue":
            if action["id"] == "race:accept":
                return session.accept_race(client, session.preset)
            return session.race_continue(client, session.preset)
        if kind == "skill_purchase":
            if action["id"] == "skills:purchase":
                return session.purchase_skills(client, selection or [], current_turn)
            return session.purchase_skills(client, [action["id"]], current_turn)
        if kind == "scenario":
            if action["id"].startswith("concert:buy:technique"):
                return session.scenario_call(client, "concert_technique_purchase", payload, current_turn)
            if action["id"].startswith("concert:buy:song"):
                return session.scenario_call(client, "concert_song_purchase", payload, current_turn)
            if action["id"].startswith("concert:promo"):
                return session.run_race(client, int(payload.get("program_id") or 0), session.preset)
            if action["id"] == "concert:grand":
                return session.scenario_call(client, "concert_grand_start", payload, current_turn)
            if action["id"] == "finish":
                return session.finish_career(client)
        return session.raw_state

    def recommend(self, normalized_state, preset):
        common = normalized_state or {}
        data = (self._raw or {}).get("data") or {}
        actions = common.get("actions") or []
        preset = preset or {}
        vectors = {}
        reasons = {}
        factors_by_id = {}
        ss = common.get("scenario_state") or {}

        events = common.get("events") or []
        if has_multi_choice_event(events):
            for event in events:
                if event.get("is_forced"):
                    continue
                for choice in event.get("choice_array") or []:
                    aid = event_action_id(event, choice["select_index"])
                    score = event_choice_score(event, choice["select_index"])
                    vectors[aid] = (1.0, score, 0.0, 0.0, 0.0)
                    reasons[aid] = "best event outcome by reward"
                    factors_by_id[aid] = [{"label": "event reward", "value": f"{score:+.2f}"}]
            return rank_recommendation(actions, vectors, reasons, factors_by_id)

        chara = data.get("chara_info") or {}
        vital = int(chara.get("vital") or 0)
        max_vital = int(chara.get("max_vital") or 100)
        turn = int(chara.get("turn") or 0)
        bonds = {row.get("target_id", 0): int(row.get("evaluation") or 0) for row in chara.get("evaluation_info_array") or []}
        learned = int(ss.get("learned_song_count") or 0)
        songs_this_half = int(ss.get("songs_this_half") or 0)
        half = int(ss.get("half_year") or 1)

        for action in actions:
            aid = action["id"]
            if not action.get("enabled"):
                continue
            if aid == "concert:grand":
                vectors[aid] = (1.0, 0.0, 0.0, 0.0, 0.0)
                reasons[aid] = "Grand Concert available"
                factors_by_id[aid] = [{"label": "rule", "value": "grand concert"}]
            elif action["id"].startswith("concert:promo:"):
                vectors[aid] = (0.98, 0.0, 0.0, 0.0, 0.0)
                reasons[aid] = "promo concert available"
                factors_by_id[aid] = [{"label": "rule", "value": "promo schedule"}]
            elif action["id"].startswith("concert:buy:technique:"):
                technique_id = int(action["id"].rsplit(":", 1)[-1])
                technique = next((t for t in ss.get("techniques") or [] if int(t.get("technique_id") or 0) == technique_id), {})
                energy_score = 0.9 if (int(technique.get("energy_recovery") or 0) > 0 and vital <= 45) else 0.3
                vectors[aid] = (0.0, energy_score, 0.0, 0.0, 0.0)
                reasons[aid] = "energy recovery technique — energy low" if (int(technique.get("energy_recovery") or 0) > 0 and vital <= 45) else "technique purchase"
                factors_by_id[aid] = [
                    {"label": "energy", "value": f"{vital}/{max_vital}"},
                    {"label": "recovers", "value": str(technique.get("energy_recovery") or 0)},
                    {"label": "deck relevant", "value": "yes" if technique.get("deck_relevant") else "no"},
                ]
            elif action["id"].startswith("concert:buy:song:"):
                song_id = int(action["id"].rsplit(":", 1)[-1])
                song = next((s for s in ss.get("songs") or [] if int(s.get("song_id") or 0) == song_id), {})
                gate = SONG_GATES.get(turn)
                behind_gate = gate is not None and learned < gate
                pacing = songs_this_half < SONGS_PER_HALF_YEAR
                priority = 0.25 if (song.get("skill_point_priority") or song.get("friendship_priority")) else 0.0
                score = (0.7 if behind_gate else 0.0) + (0.5 if pacing else 0.0) + priority
                vectors[aid] = (0.0, score, 0.0, 0.0, 0.0)
                reasons[aid] = "song pacing: four per half-year" if pacing else "song purchase"
                factors_by_id[aid] = [
                    {"label": "songs this half", "value": f"{songs_this_half}/{SONGS_PER_HALF_YEAR}"},
                    {"label": "learned", "value": f"{learned}/{gate or '?'}"},
                    {"label": "priority", "value": "skill point/friendship" if priority else "normal"},
                ]
            elif action["kind"] == "command":
                cmd_type = int((action.get("payload") or {}).get("command_type") or 0)
                if cmd_type == 1:
                    command = self._command_for_action(common, action)
                    idx = TRAINING_COMMANDS.get(int(command.get("command_id") or 0))
                    friendship = sum(1 for p in (command.get("training_partner_array") or []) if int(bonds.get(p, 0) or 0) >= 60)
                    score = score_command(command, data, chara, preset)
                    vectors[aid] = (0.0, 0.0, float(friendship > 0), float(score), 0.0, 0.0)
                    reasons[aid] = "friendship training" if friendship else "training by score"
                    factors_by_id[aid] = [
                        {"label": "friends", "value": str(friendship)},
                        {"label": "stat", "value": ["Speed", "Stamina", "Power", "Guts", "Wit"][idx] if idx is not None else "?"},
                        {"label": "failure", "value": f"{int(command.get('failure_rate') or 0)}%"},
                    ]
                elif cmd_type == 7:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.3 if vital <= 40 else 0.05, 0.0, 0.0)
                    reasons[aid] = "rest — energy low" if vital <= 40 else "rest"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 8:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.8 if vital <= 85 else 0.05, 0.0, 0.0)
                    reasons[aid] = "doctor — energy critical" if vital <= 85 else "doctor"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
            elif action["kind"] == "skill_purchase":
                vectors[aid] = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
                reasons[aid] = "skill purchase — user confirmed"

        return rank_recommendation(actions, vectors, reasons, factors_by_id)

    def _command_for_action(self, common, action):
        payload = action.get("payload") or {}
        for cmd in common.get("commands") or []:
            if (int(cmd.get("command_type") or 0) == int(payload.get("command_type") or 0)
                    and int(cmd.get("command_id") or 0) == int(payload.get("command_id") or 0)):
                return cmd
        return payload


register_adapter(GrandConcertAdapter())
