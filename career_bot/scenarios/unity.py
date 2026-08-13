"""Unity Cup adapter (scenario id from the captured manifest).

Normalizes team members, team ranks, Spirit gauges/bursts, the Cup schedule,
roster slots, and opponent choices from captures. Recommends multi-teammate
Unity/Friendship training, efficient Spirit Burst timing, energy-safe Wit/rest,
and a roster/opponent plan targeting at least three favorable race categories.
Every roster and opponent selection remains an explicit user click.
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

#: race categories the Cup asks a team to cover well
FAVORABLE_CATEGORIES = {"short", "mile", "middle", "long", "turf", "dirt"}


class UnityAdapter(ScenarioAdapter):
    slug = "unity"
    name = "Unity Cup"
    scenario_id = 2

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

        team = data.get("unity_team_info") or {}
        cup = data.get("unity_cup_info") or {}
        spirit = data.get("unity_spirit_info") or {}

        common["scenario_state"] = {
            "team_members": [
                {
                    "trained_chara_id": int(m.get("trained_chara_id") or 0),
                    "card_id": int(m.get("card_id") or 0),
                    "name": str(m.get("name") or ""),
                    "position": int(m.get("position") or 0),
                    "rank": int(m.get("rank") or 0),
                }
                for m in (team.get("team_member_array") or [])
            ],
            "team_rank": int(team.get("team_rank") or 0),
            "roster_slots": [
                {
                    "slot": int(s.get("slot") or 0),
                    "category": str(s.get("category") or ""),
                    "filled": bool(s.get("filled")),
                }
                for s in (team.get("roster_slot_array") or [])
            ],
            "cup": {
                "round": int(cup.get("round") or 0),
                "phase": str(cup.get("phase") or ""),
                "opponent_program_id": int(cup.get("opponent_program_id") or 0),
                "category": str(cup.get("category") or ""),
                "result": int(cup.get("result") or 0),
                "is_final": bool(cup.get("is_final")),
            },
            "spirit": {
                "gauge_array": [
                    {"category": str(g.get("category") or ""), "value": int(g.get("value") or 0)}
                    for g in (spirit.get("gauge_array") or [])
                ],
                "burst_array": [
                    str(b) if isinstance(b, str) else str((b or {}).get("category") or "")
                    for b in (spirit.get("burst_array") or [])
                ],
                "burst_ready": bool(spirit.get("burst_ready")),
            },
            "roster_decision_required": bool(team.get("roster_decision_required")),
            "opponent_decision_required": bool(cup.get("opponent_decision_required")),
        }

        if is_unrecognized_blocking_state(chara):
            common["phase"] = "unsupported"
            common["error"] = f"unrecognized playing_state {common['playing_state']}"
            return common

        common["phase"] = derive_common_phase(common, data)
        ss = common["scenario_state"]
        if ss.get("roster_decision_required") or ss.get("opponent_decision_required"):
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

        if ss.get("roster_decision_required"):
            for slot in ss.get("roster_slots") or []:
                if slot.get("filled"):
                    continue
                for member in ss.get("team_members") or []:
                    actions.append(action_dict(
                        f"unity:roster:{slot['slot']}:{member['trained_chara_id']}",
                        "scenario",
                        f"Assign {member.get('name') or member['trained_chara_id']} to slot {slot['slot']} ({slot.get('category') or '?'})",
                        {
                            "slot": slot["slot"],
                            "trained_chara_id": member["trained_chara_id"],
                            "current_turn": common.get("turn") or 0,
                        },
                    ))
            actions.sort(key=lambda a: a["id"])
            return actions

        if ss.get("opponent_decision_required"):
            opponents = (data.get("unity_opponent_array") or [])
            for opponent in opponents:
                actions.append(action_dict(
                    f"unity:opponent:{int(opponent.get('program_id') or 0)}",
                    "scenario",
                    f"Race {opponent.get('category') or '?'} opponent (program {opponent.get('program_id')})",
                    {
                        "program_id": int(opponent.get("program_id") or 0),
                        "category": str(opponent.get("category") or ""),
                        "current_turn": common.get("turn") or 0,
                    },
                ))
            actions.sort(key=lambda a: a["id"])
            return actions

        # team commands arrive through the same command_info_array contract
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
            if action["id"].startswith("unity:roster"):
                return session.scenario_call(client, "unity_roster", payload, current_turn)
            if action["id"].startswith("unity:opponent"):
                return session.scenario_call(client, "unity_opponent", payload, current_turn)
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

        if ss.get("roster_decision_required"):
            for action in actions:
                aid = action["id"]
                slot = int((action.get("payload") or {}).get("slot") or 0)
                member_id = int((action.get("payload") or {}).get("trained_chara_id") or 0)
                member = next((m for m in ss.get("team_members") or [] if int(m.get("trained_chara_id") or 0) == member_id), {})
                # prefer high-rank members; slot 1 gets the strongest
                vectors[aid] = (float(int(member.get("rank") or 0)) + (1.0 if slot == 1 else 0.0), 0.0, 0.0, 0.0, 0.0)
                reasons[aid] = "strongest member for open slot"
                factors_by_id[aid] = [
                    {"label": "member rank", "value": str(member.get("rank") or "?")},
                    {"label": "slot", "value": str(slot)},
                ]
            return rank_recommendation(actions, vectors, reasons, factors_by_id)

        if ss.get("opponent_decision_required"):
            categories = {s.get("category") for s in ss.get("roster_slots") or [] if s.get("filled")}
            for action in actions:
                aid = action["id"]
                category = str((action.get("payload") or {}).get("category") or "")
                favorable = 1.0 if category in categories and category in FAVORABLE_CATEGORIES else 0.2
                vectors[aid] = (favorable, 0.0, 0.0, 0.0, 0.0)
                reasons[aid] = "category covered by filled roster slot" if favorable > 0.5 else "category uncovered"
                factors_by_id[aid] = [
                    {"label": "category", "value": category},
                    {"label": "roster covers", "value": "yes" if favorable > 0.5 else "no"},
                ]
            return rank_recommendation(actions, vectors, reasons, factors_by_id)

        chara = data.get("chara_info") or {}
        vital = int(chara.get("vital") or 0)
        max_vital = int(chara.get("max_vital") or 100)
        burst_ready = bool(ss.get("spirit", {}).get("burst_ready"))
        bonds = {row.get("target_id", 0): int(row.get("evaluation") or 0) for row in chara.get("evaluation_info_array") or []}
        cup = ss.get("cup") or {}
        required_cup = bool(cup.get("opponent_decision_required")) or bool(cup.get("round"))

        for action in actions:
            aid = action["id"]
            if not action.get("enabled"):
                continue
            if action["kind"] == "race":
                program_id = int((action.get("payload") or {}).get("program_id") or 0)
                is_goal = required_cup and program_id and program_id == int(cup.get("opponent_program_id") or 0)
                vectors[aid] = (1.0 if is_goal else 0.0, 0.0, 0.0, 0.0, 0.0)
                reasons[aid] = "required Cup race" if is_goal else "race"
            elif action["kind"] == "command":
                cmd_type = int((action.get("payload") or {}).get("command_type") or 0)
                if cmd_type == 1:
                    command = self._command_for_action(common, action)
                    idx = TRAINING_COMMANDS.get(int(command.get("command_id") or 0))
                    friendship = sum(1 for p in (command.get("training_partner_array") or []) if int(bonds.get(p, 0) or 0) >= 60)
                    teammates = len(command.get("training_partner_array") or [])
                    score = score_command(command, data, chara, preset)
                    spirit_burst = 1.0 if burst_ready else 0.0
                    vectors[aid] = (0.0, spirit_burst, float(friendship > 0), float(teammates), float(score), -float(command.get("failure_rate") or 0))
                    reasons[aid] = "Spirit Burst training" if burst_ready else ("friendship training" if friendship else "training by score")
                    factors_by_id[aid] = [
                        {"label": "spirit burst", "value": "ready" if burst_ready else "no"},
                        {"label": "friends", "value": str(friendship)},
                        {"label": "teammates", "value": str(teammates)},
                        {"label": "failure", "value": f"{int(command.get('failure_rate') or 0)}%"},
                        {"label": "stat", "value": ["Speed", "Stamina", "Power", "Guts", "Wit"][idx] if idx is not None else "?"},
                    ]
                elif cmd_type == 7:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.0, 0.3 if vital <= 40 else 0.05, 0.0)
                    reasons[aid] = "rest — energy low" if vital <= 40 else "rest"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 8:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.0, 0.8 if vital <= 85 else 0.05, 0.0)
                    reasons[aid] = "doctor — energy critical" if vital <= 85 else "doctor"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 3:
                    vectors[aid] = (0.0, 0.0, 0.0, 0.0, 0.15, 0.0)
                    reasons[aid] = "outing"
                    factors_by_id[aid] = [{"label": "mood", "value": str(int(chara.get("motivation") or 3))}]
            elif action["kind"] == "skill_purchase":
                vectors[aid] = (0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
                reasons[aid] = "skill purchase — user confirmed"

        return rank_recommendation(actions, vectors, reasons, factors_by_id)

    def _command_for_action(self, common, action):
        payload = action.get("payload") or {}
        for cmd in common.get("commands") or []:
            if (int(cmd.get("command_type") or 0) == int(payload.get("command_type") or 0)
                    and int(cmd.get("command_id") or 0) == int(payload.get("command_id") or 0)):
                return cmd
        return payload


register_adapter(UnityAdapter())
