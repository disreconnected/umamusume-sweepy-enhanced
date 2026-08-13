"""Trackblazer adapter: migrated MANT scenario (scenario_id 4).

Recommendations reuse the existing numeric command/race scorer as pure
functions; the shop/items logic from MantItemManager is exposed as preview
methods and executes only for explicitly selected rows.
"""

from __future__ import annotations

from career_bot.items import ITEM_NAMES, MantItemManager
from career_bot.events import EventManager
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
    item_exchange_actions,
    item_use_actions,
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
from career_bot.scoring import score_command

RACE_GRADE_BONUS = {"1": 0.5, "2": 0.3, "3": 0.2}


class TrackblazerAdapter(ScenarioAdapter):
    slug = "trackblazer"
    name = "Trackblazer"
    scenario_id = 4

    def __init__(self):
        self.event_manager = None
        self.item_manager = MantItemManager()

    def _ensure_event_manager(self, context):
        if self.event_manager is None:
            base_dir = ((context or {}).get("session") or {}).base_dir
            self.event_manager = EventManager(base_dir)

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------
    def normalize(self, raw_state, context=None):
        data = (raw_state or {}).get("data") or {}
        chara = data.get("chara_info") or {}
        common = normalize_common(raw_state)
        free = data.get("free_data_set") or {}
        preset = (context or {}).get("preset") or {}
        self._ensure_event_manager(context)
        self._raw = raw_state or {}
        self._last_session = (context or {}).get("session")

        if not chara.get("scenario_id"):
            common["phase"] = "unsupported"
            common["error"] = "missing scenario discriminator"
            common["scenario"] = {"id": 0, "slug": "unsupported", "name": "Unsupported"}
            return common
        common["scenario"] = {"id": int(chara.get("scenario_id") or 0), "slug": self.slug, "name": self.name}
        common["skills"] = normalize_skills(context, raw_state, preset)

        coin_val = free.get("coin_num")
        if coin_val is None:
            coin_val = free.get("gained_coin_num")
        rival_races = []
        for row in free.get("rival_race_info_array") or []:
            rival_races.append({
                "program_id": int(row.get("program_id") or 0),
                "chara_id": int(row.get("chara_id") or 0),
            })
        tb = data.get("trackblazer_info") or {}
        common["scenario_state"] = {
            "mant_coin": int(coin_val or 0),
            "shop_rows": [
                {
                    "shop_item_id": int(row.get("shop_item_id") or 0),
                    "item_id": int(row.get("item_id") or 0),
                    "name": ITEM_NAMES.get(int(row.get("item_id") or 0), ""),
                    "cost": int(row.get("coin_num") or 0),
                    "original_cost": int(row.get("original_coin_num") or int(row.get("coin_num") or 0)),
                    "item_buy_num": int(row.get("item_buy_num") or 0),
                    "limit_buy_count": int(row.get("limit_buy_count") or 1),
                    "limit_turn": int(row.get("limit_turn") or 0),
                }
                for row in free.get("pick_up_item_info_array") or []
            ],
            "rival_races": rival_races,
            "climax_ready": bool(tb.get("climax_ready")),
            "climax_program_id": int(tb.get("climax_program_id") or 0),
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

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------
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
        actions.extend(item_exchange_actions(raw_state))
        actions.extend(item_use_actions(raw_state))
        actions.extend(skill_purchase_actions(common, common.get("skills")))
        actions.append(bulk_skill_action())

        # Twinkle Star Climax entry is a race entry for the climax program.
        ss = common.get("scenario_state") or {}
        if ss.get("climax_ready") and ss.get("climax_program_id"):
            climax_id = race_action_id(ss["climax_program_id"])
            if not any(a["id"] == climax_id for a in actions):
                actions.append(action_dict(
                    climax_id,
                    "race",
                    "Twinkle Star Climax",
                    {"program_id": ss["climax_program_id"], "current_turn": common.get("turn") or 0},
                ))
        actions.sort(key=lambda a: (a["kind"], a["id"]))
        return actions

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------
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
        if kind == "item_exchange":
            return session.exchange_items(client, [payload], current_turn)
        if kind == "item_use":
            return session.use_items(client, [payload], current_turn)
        if kind == "skill_purchase":
            if action["id"] == "skills:purchase":
                return session.purchase_skills(client, selection or [], current_turn)
            return session.purchase_skills(client, [action["id"]], current_turn)
        if kind == "scenario":
            if action["id"] == "finish":
                return session.finish_career(client)
        return session.raw_state

    # ------------------------------------------------------------------
    # recommend
    # ------------------------------------------------------------------
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
        vital = int(chara.get("vital") or 0)
        max_vital = int(chara.get("max_vital") or 100)
        motivation = int(chara.get("motivation") or 3)
        turn = int(chara.get("turn") or 0)
        bad_status = self._has_curable_bad_status(chara, preset)
        bonds = {row.get("target_id", 0): int(row.get("evaluation") or 0) for row in chara.get("evaluation_info_array") or []}

        for action in actions:
            aid = action["id"]
            if not action.get("enabled"):
                continue
            if action["kind"] == "race":
                program_id = int((action.get("payload") or {}).get("program_id") or 0)
                is_planned = program_id in self._planned_program_ids(preset, data)
                info = self._race_grade(program_id)
                fans = int(chara.get("fans") or 0)
                fan_pressure = 0.3 if (fans < 350 and turn > 11 and turn not in {12, 13, 14, 15}) else 0.0
                planned_bonus = 0.6 if is_planned else 0.0
                vectors[aid] = (planned_bonus, fan_pressure, RACE_GRADE_BONUS.get(info, 0.0), 0.0, 0.0)
                reasons[aid] = "planned race" if is_planned else ("fan threshold race" if fan_pressure else "optional race")
                factors_by_id[aid] = [
                    {"label": "planned", "value": "yes" if is_planned else "no"},
                    {"label": "grade", "value": info or "?"},
                    {"label": "fans", "value": str(fans)},
                ]
            elif action["kind"] == "command":
                cmd_type = int((action.get("payload") or {}).get("command_type") or 0)
                cmd_id = int((action.get("payload") or {}).get("command_id") or 0)
                if cmd_type == 1:
                    command = self._command_for_action(common, action)
                    score = score_command(command, data, chara, preset)
                    friendship = sum(1 for p in (command.get("training_partner_array") or []) if int(bonds.get(p, 0) or 0) >= 60)
                    partners = len(command.get("training_partner_array") or [])
                    vectors[aid] = (0.0, 0.0, float(score), -float(command.get("failure_rate") or 0), 0.0)
                    reasons[aid] = f"best training by MANT score ({score:.3f})"
                    factors_by_id[aid] = [
                        {"label": "score", "value": f"{score:.3f}"},
                        {"label": "friends", "value": str(friendship)},
                        {"label": "partners", "value": str(partners)},
                        {"label": "failure", "value": f"{int(command.get('failure_rate') or 0)}%"},
                    ]
                elif cmd_type == 7:
                    score = 0.3 if vital <= 40 else 0.1
                    vectors[aid] = (0.0, 0.0, float(score), 0.0, 0.0)
                    reasons[aid] = "rest to recover energy" if vital <= 40 else "rest"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 8:
                    score = 0.9 if bad_status and vital <= 85 else 0.05
                    vectors[aid] = (0.0, 0.0, float(score), 0.0, 0.0)
                    reasons[aid] = "cure bad status" if bad_status else "doctor"
                    factors_by_id[aid] = [{"label": "energy", "value": f"{vital}/{max_vital}"}]
                elif cmd_type == 3:
                    score = 0.2 if (motivation < 4 and vital < 90) else 0.05
                    vectors[aid] = (0.0, 0.0, float(score), 0.0, 0.0)
                    reasons[aid] = "outing to raise mood"
                    factors_by_id[aid] = [{"label": "mood", "value": str(motivation)}]
            elif action["kind"] == "item_exchange":
                vectors[aid] = (0.0, 0.0, 0.0, 0.0, 1.0)
                reasons[aid] = "shop purchase — user confirmed"
            elif action["kind"] == "skill_purchase":
                vectors[aid] = (0.0, 0.0, 0.0, 0.0, 0.5)
                reasons[aid] = "skill purchase — user confirmed"

        return rank_recommendation(actions, vectors, reasons, factors_by_id)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _command_for_action(self, common, action):
        payload = action.get("payload") or {}
        for cmd in common.get("commands") or []:
            if (int(cmd.get("command_type") or 0) == int(payload.get("command_type") or 0)
                    and int(cmd.get("command_id") or 0) == int(payload.get("command_id") or 0)
                    and int(cmd.get("command_group_id") or 0) == int(payload.get("command_group_id") or 0)):
                return cmd
        return payload

    def _planned_program_ids(self, preset, data):
        """User-authored planned races (extra_race_list) plus anything the
        planner can resolve from master data."""
        wanted = set()
        for value in (preset or {}).get("extra_race_list") or []:
            try:
                wanted.add(int(value))
            except (TypeError, ValueError):
                continue
        race_planner = getattr(getattr(self, "_last_session", None), "race_planner", None)
        if race_planner is not None:
            turn = int((data.get("chara_info") or {}).get("turn") or 0)
            wanted.update(int(pid) for pid in race_planner.wanted_programs(preset, turn))
        return wanted

    def _race_grade(self, program_id):
        race_planner = getattr(getattr(self, "_last_session", None), "race_planner", None)
        if race_planner is None:
            return ""
        info = (race_planner.program or {}).get(int(program_id or 0)) or {}
        return str(info.get("race_instance_id") or "")[:1]

    def _has_curable_bad_status(self, chara, preset):
        wanted = self._cure_condition_names(preset)
        if not wanted:
            return False
        for effect_id in chara.get("chara_effect_id_array") or []:
            try:
                effect_id = int(effect_id)
            except (TypeError, ValueError):
                continue
            name = {
                1: "Night Owl", 2: "Slacker", 3: "Skin Outbreak",
                4: "Slow Metabolism", 5: "Migraine", 6: "Practice Poor",
            }.get(effect_id)
            if name and self._condition_key(name) in wanted:
                return True
        return False

    def _cure_condition_names(self, preset):
        result = set()
        names = preset.get("cure_asap_conditions") or []
        if isinstance(names, str):
            names = names.split(",")
        for name in names:
            key = self._condition_key(name)
            if key:
                result.add(key)
        return result

    def _condition_key(self, name):
        text = str(name or "").strip()
        if not text or text.startswith("("):
            return ""
        return "".join(ch.lower() for ch in text if ch.isalnum())


register_adapter(TrackblazerAdapter())
