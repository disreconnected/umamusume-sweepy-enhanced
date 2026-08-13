"""URA Finale adapter (scenario id from the captured manifest).

Exposes character goals / required races, ordinary commands, events, optional
races, skills, and the URA final sequence. Recommendation priority:
required-goal safety first, then strong friendship / multi-support training,
then stat deficits, then summer preparation, then energy/failure/mood safety,
then fan thresholds / optional races only when training is weak.
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
    race_action_id,
    race_continue_actions,
    race_running_actions,
    race_select_actions,
    rank_recommendation,
    skill_purchase_actions,
)
from career_bot.scenarios.registry import register_adapter
from career_bot.scoring import TRAINING_COMMANDS, TRAINING_NAMES, score_command

GOAL_FAN_THRESHOLDS = {12: 350, 24: 1500, 36: 3500, 48: 7000, 60: 15000, 72: 30000}


class UraAdapter(ScenarioAdapter):
    slug = "ura"
    name = "URA Finale"
    scenario_id = 1

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

        goals = []
        for goal in data.get("ura_goal_array") or []:
            goals.append({
                "program_id": int(goal.get("program_id") or 0),
                "turn": int(goal.get("turn") or 0),
                "title": str(goal.get("goal_title") or goal.get("title") or ""),
                "cleared": bool(goal.get("cleared")),
                "required_fans": int(goal.get("required_fans") or 0),
            })
        final_info = data.get("ura_final_info") or {}
        common["scenario_state"] = {
            "goals": goals,
            "final": {
                "is_final": bool(final_info.get("is_final")),
                "final_program_id": int(final_info.get("final_program_id") or 0),
                "result": int(final_info.get("result") or 0),
            },
        }

        if is_unrecognized_blocking_state(chara):
            common["phase"] = "unsupported"
            common["error"] = f"unrecognized playing_state {common['playing_state']}"
            return common

        common["phase"] = derive_common_phase(common, data)
        if "single_mode_finish_common" in data or int(chara.get("state") or 0) == 3:
            common["phase"] = "finish"
            common["can_finish"] = True
        return common

    def actions(self, raw_state, normalized_state):
        data = (raw_state or {}).get("data") or {}
        common = normalized_state
        actions = []

        if has_multi_choice_event(common.get("events") or []):
            return event_actions(common.get("events") or [])

        if common.get("phase") == "race_running":
            return race_running_actions(common)

        if common.get("phase") == "race_continue":
            return race_continue_actions(common)

        if common.get("phase") == "finish":
            return [action_dict("finish", "scenario", "Finish and save career", {"is_force_delete": False}, destructive=True)]

        actions.extend(command_actions(common))
        actions.extend(race_select_actions(data, common))
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
        turn = int(chara.get("turn") or 0)
        vital = int(chara.get("vital") or 0)
        max_vital = int(chara.get("max_vital") or 100)
        motivation = int(chara.get("motivation") or 3)
        goals = (common.get("scenario_state") or {}).get("goals") or []
        required_this_turn = [
            g for g in goals
            if int(g.get("turn") or 0) == turn and not g.get("cleared") and (g.get("program_id") or 0)
        ]
        required_ids = {int(g.get("program_id") or 0) for g in required_this_turn}
        required_ids.update(int(g.get("program_id") or 0) for g in goals if int(g.get("turn") or 0) <= turn and not g.get("cleared") and (g.get("program_id") or 0) and int(g.get("turn") or 0) > 0 and turn >= int(g.get("turn") or 0))
        bonds = {row.get("target_id", 0): int(row.get("evaluation") or 0) for row in chara.get("evaluation_info_array") or []}

        for action in actions:
            aid = action["id"]
            if not action.get("enabled"):
                continue
            if action["kind"] == "race":
                program_id = int((action.get("payload") or {}).get("program_id") or 0)
                if program_id in required_ids:
                    vectors[aid] = (1.0, 0.0, 0.0, 0.0, 0.0)
                    reasons[aid] = "required goal race"
                    factors_by_id[aid] = [{"label": "rule", "value": "required goal"}]
                else:
                    fans = int(chara.get("fans") or 0)
                    threshold = GOAL_FAN_THRESHOLDS.get(turn)
                    fan_pressure = 1.0 if (threshold and fans < threshold) else 0.2
                    training_score = self._best_training_score(common, data, chara, preset)
                    weak_training = 1.0 if training_score < 0.25 else 0.0
                    vectors[aid] = (0.0, 0.0, 0.0, fan_pressure * weak_training, 0.0)
                    reasons[aid] = "fan threshold — training weak" if (fan_pressure and weak_training) else "optional race"
                    factors_by_id[aid] = [
                        {"label": "fans", "value": f"{fans}/{threshold or '?'}"},
                        {"label": "best training", "value": f"{training_score:.2f}"},
                    ]
            elif action["kind"] == "command":
                cmd_type = int((action.get("payload") or {}).get("command_type") or 0)
                if cmd_type == 1:
                    command = self._command_for_action(common, action)
                    idx = TRAINING_COMMANDS.get(int(command.get("command_id") or 0))
                    friendship = sum(1 for p in (command.get("training_partner_array") or []) if int(bonds.get(p, 0) or 0) >= 60)
                    partners = len(command.get("training_partner_array") or [])
                    score = score_command(command, data, chara, preset)
                    vectors[aid] = (0.0, float(friendship > 0), float(partners), float(score), -float(command.get("failure_rate") or 0))
                    reasons[aid] = "friendship training" if friendship else "training by score"
                    factors_by_id[aid] = [
                        {"label": "friends", "value": str(friendship)},
                        {"label": "partners", "value": str(partners)},
                        {"label": "failure", "value": f"{int(command.get('failure_rate') or 0)}%"},
                        {"label": "stat", "value": TRAINING_NAMES[idx] if idx is not None and 0 <= idx < len(TRAINING_NAMES) else "?"},
                    ]
                elif cmd_type == 7:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.3 if vital <= 40 else 0.05, 0.0)
                    reasons[aid] = "rest — energy low" if vital <= 40 else "rest"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 8:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.8 if vital <= 85 else 0.05, 0.0)
                    reasons[aid] = "doctor — energy critical" if vital <= 85 else "doctor"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 3:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.15 if motivation < 4 else 0.03, 0.0)
                    reasons[aid] = "outing — mood low" if motivation < 4 else "outing"
                    factors_by_id[aid] = [{"label": "mood", "value": str(motivation)}]
            elif action["kind"] == "skill_purchase":
                vectors[aid] = (0.0, 0.0, 0.0, 0.0, 1.0)
                reasons[aid] = "skill purchase — user confirmed"

        return rank_recommendation(actions, vectors, reasons, factors_by_id)

    def _command_for_action(self, common, action):
        payload = action.get("payload") or {}
        for cmd in common.get("commands") or []:
            if (int(cmd.get("command_type") or 0) == int(payload.get("command_type") or 0)
                    and int(cmd.get("command_id") or 0) == int(payload.get("command_id") or 0)):
                return cmd
        return payload

    def _best_training_score(self, common, data, chara, preset):
        best = 0.0
        for cmd in common.get("commands") or []:
            if int(cmd.get("command_type") or 0) != 1:
                continue
            best = max(best, float(score_command(cmd, data, chara, preset)))
        return best


register_adapter(UraAdapter())
