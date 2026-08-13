"""Normalized player contract for the manual fast-mode career player.

An adapter turns one raw protocol response (as returned by
``UmaClient.call`` / ``unpack``) into the stable normalized ``PlayState``
dict the dashboard renders, exposes the exact set of legal actions, executes
exactly one meaningful user decision plus transport-only follow-through, and
optionally recommends an enabled action with an explainable rule vector.

The release gate for a scenario is its captured, sanitized fixture matrix
(see ``tests/fixtures/scenarios/scenario-manifest.json``); anything the
manifest does not describe fails closed (``phase == "unsupported"`` with zero
mutating actions).
"""

from __future__ import annotations

from typing import Optional

from career_bot.items import BAD_EFFECT_NAMES, ITEM_NAMES

#: action kinds allowed on the wire
ACTION_KINDS = {
    "command",
    "event",
    "race",
    "race_continue",
    "item_exchange",
    "item_use",
    "skill_purchase",
    "scenario",
}

PHASES = {
    "home",
    "event",
    "race_select",
    "race_running",
    "race_continue",
    "skill_purchase",
    "scenario",
    "finish",
    "unsupported",
}

TRAINING_COMMANDS = {101: 0, 105: 1, 102: 2, 103: 3, 106: 4, 601: 0, 602: 1, 603: 2, 604: 3, 605: 4}
TRAINING_NAMES = ["Speed", "Stamina", "Power", "Guts", "Wit"]
RACE_COMMAND_TYPE = 4
RACE_COMMAND_ID = 401
REST_COMMAND = (7, 701)


class UnknownScenarioError(Exception):
    """Raised when a response carries a scenario discriminator the registry
    does not know. The session fails closed with phase=unsupported."""


class ActionCatalogError(Exception):
    """Raised when an action id is absent or disabled in the authoritative
    catalog."""


def action_dict(id_, kind, label, payload, enabled=True, disabled_reason=None, destructive=False):
    """Build one wire Action object. Shapes exactly:

    {"id": str, "kind": str, "label": str, "payload": dict,
     "enabled": bool, "disabled_reason": str | None, "destructive": bool}
    """
    if kind not in ACTION_KINDS:
        raise ValueError(f"unknown action kind {kind!r}")
    return {
        "id": id_,
        "kind": kind,
        "label": label,
        "payload": dict(payload or {}),
        "enabled": bool(enabled),
        "disabled_reason": disabled_reason,
        "destructive": bool(destructive),
    }


def recommendation_dict(action_id, score, reason, factors):
    """One recommendation object:

    {"action_id": str, "score": float, "reason": str,
     "factors": [{"label": str, "value": str}]}
    """
    return {
        "action_id": action_id,
        "score": float(score),
        "reason": str(reason or ""),
        "factors": [{"label": str(f.get("label")), "value": str(f.get("value"))} for f in (factors or [])],
    }


def command_action_id(cmd):
    return "command:{type}:{id}:{group}:{select}".format(
        type=int(cmd.get("command_type") or 0),
        id=int(cmd.get("command_id") or 0),
        group=int(cmd.get("command_group_id") or 0),
        select=int(cmd.get("select_id") or 0),
    )


def command_label(cmd):
    command_type = int(cmd.get("command_type") or 0)
    command_id = int(cmd.get("command_id") or 0)
    if command_id in TRAINING_COMMANDS:
        return f"Train {TRAINING_NAMES[TRAINING_COMMANDS.get(command_id, 0)]}"
    if command_type == 7 and command_id == 701:
        return "Rest"
    if command_type == 3:
        return "Recreation (outing)"
    if command_type == 8 and command_id == 801:
        return "Doctor (medic)"
    if command_type == 4:
        return "Race"
    return f"Command {command_type}:{command_id}"


def event_action_id(event, select_index):
    return f"event:{int(event.get('event_id') or 0)}:{int(select_index or 0)}"


def skill_action_id(skill_id):
    return f"skill:{int(skill_id or 0)}"


def item_exchange_action_id(shop_item_id):
    return f"item:exchange:{int(shop_item_id or 0)}"


def item_use_action_id(item_id):
    return f"item:use:{int(item_id or 0)}"


def race_action_id(program_id):
    return f"race:{int(program_id or 0)}"


# ---------------------------------------------------------------------------
# Common normalization helpers (scenario-neutral). Missing optional arrays
# normalize to empty arrays; a missing scenario discriminator or an
# unrecognized blocking playing state yields phase="unsupported".
# ---------------------------------------------------------------------------

def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def chara_of(data):
    chara = data.get("chara_info") or {}
    if not chara:
        chara = data.get("single_mode_chara_light") or {}
    return chara or {}


def parse_race_rank(res):
    """Finish rank (1-based) of the player's horse from the race_scenario
    blob, or 99 when it cannot be parsed. Copied from the old CareerRunner."""
    import base64
    import gzip
    import struct

    data = (res or {}).get("data", {})
    headers = (res or {}).get("data_headers", {})
    viewer_id = _int(headers.get("viewer_id"))

    race_start_info = data.get("race_start_info", {})
    horses = race_start_info.get("race_horse_data", [])

    player = next((horse for horse in horses if _int(horse.get("viewer_id")) == viewer_id), None)
    if not player:
        return 99
    frame_order = player.get("frame_order")
    if not frame_order:
        return 99
    result_index = _int(frame_order) - 1

    scenario_b64 = data.get("race_scenario")
    if not scenario_b64:
        return 99
    try:
        blob = gzip.decompress(base64.b64decode(scenario_b64))
    except Exception:
        return 99

    offset = 0
    if len(blob) < offset + 4:
        return 99
    header_len = struct.unpack_from("<i", blob, offset)[0]
    offset += 4 + header_len
    if len(blob) < offset + 16:
        return 99
    _, horse_num, _, horse_result_size = struct.unpack_from("<fiii", blob, offset)
    offset += 16
    if len(blob) < offset + 4:
        return 99
    pad_len = struct.unpack_from("<i", blob, offset)[0]
    offset += 4 + pad_len
    if len(blob) < offset + 8:
        return 99
    frame_count, frame_size = struct.unpack_from("<ii", blob, offset)
    offset += 8 + frame_count * frame_size
    if len(blob) < offset + 4:
        return 99
    pad_len = struct.unpack_from("<i", blob, offset)[0]
    offset += 4 + pad_len
    if not (0 <= result_index < horse_num):
        return 99
    if len(blob) < offset + (result_index + 1) * horse_result_size:
        return 99
    finish_order = struct.unpack_from("<i", blob, offset + result_index * horse_result_size)[0]
    return finish_order + 1


def normalize_common(raw_state):
    data = (raw_state or {}).get("data") or {}
    chara = chara_of(data)
    home = data.get("home_info") or {}
    free = data.get("free_data_set") or {}
    race = data.get("race_start_info") or {}
    race_rank = parse_race_rank(raw_state)
    continue_offered = _int(home.get("available_continue_num")) + _int(home.get("available_free_continue_num"))
    if continue_offered <= 0:
        continue_offered = _int(race.get("available_continue_num")) + _int(race.get("available_free_continue_num"))
    common = {
        "turn": _int(chara.get("turn")),
        "playing_state": _int(chara.get("playing_state") or 1),
        "trainee": {
            "card_id": _int(chara.get("card_id")),
            "name": str(chara.get("chara_name") or ""),
            "scenario_id": _int(chara.get("scenario_id")),
        },
        "stats": {
            "speed": _int(chara.get("speed")),
            "stamina": _int(chara.get("stamina")),
            "power": _int(chara.get("power")),
            "guts": _int(chara.get("guts")),
            "wit": _int(chara.get("wiz")),
        },
        "energy": {"current": _int(chara.get("vital")), "max": _int(chara.get("max_vital") or 100)},
        "motivation": _int(chara.get("motivation") or 3),
        "skill_points": _int(chara.get("skill_point")),
        "fans": _int(chara.get("fans")),
        "conditions": [_int(e) for e in (chara.get("chara_effect_id_array") or [])],
        "support_bonds": [
            {
                "target_id": _int(row.get("target_id")),
                "evaluation": _int(row.get("evaluation")),
                "is_outing": _int(row.get("is_outing") or 0),
                "story_step": _int(row.get("story_step") or 0),
            }
            for row in (chara.get("evaluation_info_array") or [])
        ],
        "commands": normalize_commands(home),
        "events": normalize_events(data),
        "race": normalize_race(race, rank=race_rank, continue_offered=continue_offered),
        "inventory": normalize_inventory(free),
        "scenario_state": {},
        "phase": "unsupported",
        "can_finish": False,
        "error": None,
    }
    return common


def normalize_commands(home):
    rows = []
    for cmd in home.get("command_info_array") or []:
        if int(cmd.get("command_type") or 0) not in (1, 3, 4, 7, 8):
            continue
        rows.append({
            "command_type": _int(cmd.get("command_type")),
            "command_id": _int(cmd.get("command_id")),
            "command_group_id": _int(cmd.get("command_group_id") or 0),
            "select_id": _int(cmd.get("select_id") or 0),
            "is_enable": bool(cmd.get("is_enable", 1)),
            "failure_rate": _int(cmd.get("failure_rate")),
            "params_inc_dec_info_array": [
                {
                    "target_type": _int(p.get("target_type")),
                    "value": _int(p.get("value")),
                }
                for p in (cmd.get("params_inc_dec_info_array") or [])
            ],
            "training_partner_array": [int(p) for p in (cmd.get("training_partner_array") or [])],
            "tips_event_partner_array": [int(p) for p in (cmd.get("tips_event_partner_array") or [])],
            "label": command_label(cmd),
        })
    return rows


def normalize_events(data):
    rows = []
    for event in data.get("unchecked_event_array") or []:
        contents = event.get("event_contents_info") or {}
        choices = [
            {
                "select_index": _int(c.get("select_index")),
                "title": str(c.get("choice_title") or c.get("title") or ""),
            }
            for c in (contents.get("choice_array") or [])
        ]
        rows.append({
            "event_id": _int(event.get("event_id")),
            "chara_id": _int(event.get("chara_id") or 0),
            "story_id": str(event.get("story_id") or ""),
            "choice_array": choices,
            "is_forced": len(choices) <= 1,
        })
    return rows


def normalize_race(race, rank=99, continue_offered=0):
    if not race:
        return None
    return {
        "program_id": _int(race.get("program_id")),
        "race_instance_id": str(race.get("race_instance_id") or ""),
        "is_short": _int(race.get("is_short") or 0),
        "continue_num": _int(race.get("continue_num") or 0),
        "available_continue_num": _int(race.get("available_continue_num") or 0),
        "available_free_continue_num": _int(race.get("available_free_continue_num") or 0),
        "horse_count": len(race.get("race_horse_data") or []),
        "viewer_id": _int(race.get("viewer_id")),
        "rank": int(rank),
        "continue_offered": int(continue_offered or 0),
    }


def normalize_inventory(free):
    rows = []
    for row in free.get("user_item_info_array") or []:
        item_id = _int(row.get("item_id"))
        rows.append({
            "item_id": item_id,
            "name": ITEM_NAMES.get(item_id, f"Item {item_id}"),
            "num": _int(row.get("num") or row.get("current_num") or row.get("item_num")),
        })
    return rows


def condition_names(condition_ids):
    return [BAD_EFFECT_NAMES.get(cid, f"effect {cid}") for cid in condition_ids]


def has_multi_choice_event(events):
    """True when any event offers two or more choices. Works on both raw
    server events (event_contents_info.choice_array) and normalized event
    rows (top-level choice_array)."""
    for event in events or []:
        event = event or {}
        choices = event.get("choice_array") or []
        if not choices:
            choices = ((event.get("event_contents_info") or {}).get("choice_array") or [])
        if len(choices) > 1:
            return True
    return False


def derive_common_phase(common, data, scenario_state=None):
    """Common phase derivation shared by adapters. Scenario adapters may
    override afterwards for scenario-specific blocking screens."""
    if "single_mode_finish_common" in data:
        return "finish"
    if has_multi_choice_event(common.get("events") or []):
        return "event"
    playing_state = common.get("playing_state") or 1
    if playing_state == 5:
        return "finish"
    if playing_state in {2, 3, 4}:
        race = common.get("race") or {}
        if int(race.get("continue_offered") or 0) > 0 and int(race.get("rank") or 99) > 1:
            return "race_continue"
        return "race_running"
    commands = common.get("commands") or []
    race_enabled = any(
        c.get("command_type") == RACE_COMMAND_TYPE and c.get("is_enable")
        for c in commands
    )
    if race_enabled:
        return "race_select"
    return "home"


def is_unrecognized_blocking_state(chara):
    playing_state = _int((chara or {}).get("playing_state") or 1)
    return playing_state not in {1, 2, 3, 4, 5}


# ---------------------------------------------------------------------------
# Recommendation scoring helpers (pure, explainable)
# ---------------------------------------------------------------------------

def friendship_bond_count(common, command):
    """Number of deck partners with a strong bond on this command (>= 60).
    Pal (target_id 6) counts too; outing commands count one."""
    bonds = {row["target_id"]: row["evaluation"] for row in (common or {}).get("support_bonds") or []}
    partners = command.get("training_partner_array") or []
    return sum(1 for p in partners if int(bonds.get(int(p), 0) or 0) >= 60)


def support_count(command):
    return len(command.get("training_partner_array") or [])


def is_friendship_training(common, command):
    if command.get("command_type") != 1:
        return False
    return friendship_bond_count(common, command) >= 1


def reward_score(reward):
    """Numeric value of an event reward block. Scenario-neutral; moved from
    the old MantStrategy._reward_score so every adapter can reuse it."""
    score = 0.0
    for item in (reward or {}).get("params_inc_dec_info_array") or (reward or {}).get("effected_parameter_array") or []:
        target = _int(item.get("target_type"))
        value = _float(item.get("value"))
        if target == 10:
            score += value * 0.03
        elif 1 <= target <= 5:
            score += value * (0.02 if target < 5 else 0.01)
        elif target == 30:
            score += value * 0.01
    score += _float(reward.get("skill_point")) * 0.01
    score += _float(reward.get("vital")) * 0.03
    return score


def event_choice_score(event, select_index):
    """Score an event choice by its reward block (when present) plus index
    tiebreak. Choices without reward blocks default to the reward score of
    the first choice so ordering stays deterministic."""
    contents = (event or {}).get("event_contents_info") or {}
    choices = contents.get("choice_array") or []
    for choice in choices:
        if _int(choice.get("select_index")) != _int(select_index or 0):
            continue
        rewards = choice.get("reward_array") or choice.get("rewards") or []
        total = sum(reward_score(r) for r in rewards)
        return total if total else _float(choice.get("score"))
    return 0.0


def rank_recommendation(actions, rule_vectors, reasons, factors_by_id=None):
    """Rank enabled actions by an exact lexicographic rule vector (descending)
    then ascending deterministic action id; wire score =
    enabled_action_count - zero_based_rank. Returns the top recommendation or
    None when there are no enabled actions."""
    enabled = [a for a in (actions or []) if a.get("enabled")]
    if not enabled:
        return None
    keyed = []
    for a in enabled:
        vector = tuple(rule_vectors.get(a["id"]) or ())
        keyed.append((vector, a["id"], a))
    keyed.sort(key=lambda row: (row[0], row[1]), reverse=True)
    best_vector, best_id, best_action = keyed[0]
    rank = next(i for i, row in enumerate(keyed) if row[1] == best_id)
    score = float(len(enabled) - rank)
    factors = factors_by_id.get(best_id) if factors_by_id else None
    if not factors:
        factors = [{"label": "action", "value": best_action.get("label") or best_id}]
    return recommendation_dict(
        best_id,
        score,
        reasons.get(best_id) or best_action.get("label", ""),
        factors,
    )


def normalize_skills(context, raw_state, preset=None):
    """PlayState.skills: owned skills + every legal skill tip option with
    resolved tier, prerequisites, exact discounted cost, remaining SP,
    affordability, and a recommendation score. Built through the SkillBuyer's
    metadata resolution (never the auto priority list)."""
    skill_buyer = (context or {}).get("skill_buyer")
    if skill_buyer is None:
        return {"owned": [], "options": [], "remaining_sp": 0}
    data = (raw_state or {}).get("data") or {}
    chara = chara_of(data)
    points = _int(chara.get("skill_point"))
    owned = [
        {
            "skill_id": _int(row.get("skill_id")),
            "group_id": skill_buyer.skill_to_group_id.get(_int(row.get("skill_id")), _int(row.get("skill_id")) // 10),
            "name": skill_buyer.skill_names.get(_int(row.get("skill_id")), ""),
        }
        for row in (chara.get("skill_array") or [])
    ]
    owned_ids = {row["skill_id"] for row in owned}
    priority = skill_buyer._priority_context(preset or {})
    blacklist = skill_buyer._blacklist(preset or {})
    options = []
    for tip in chara.get("skill_tips_array") or []:
        resolved = skill_buyer.resolve_skill_tip(
            tip,
            owned_ids,
            {skill_buyer.skill_to_group_id.get(sid, sid // 10) for sid in owned_ids},
            priority,
            blacklist,
            preset or {},
        )
        if not resolved or resolved.get("skip_reason"):
            continue
        cost = _int(resolved.get("cost"))
        options.append({
            "skill_id": _int(resolved.get("resolved_skill_id")),
            "group_id": _int(resolved.get("group_id")),
            "name": resolved.get("resolved_name") or "",
            "tip_rarity": _int(resolved.get("tip_rarity")),
            "hint_level": _int(resolved.get("hint_level")),
            "tier": _int(resolved.get("tip_rarity")),
            "prerequisite_skill_ids": [int(s) for s in (resolved.get("bundled_skill_ids") or [])],
            "cost": cost,
            "remaining_sp": points,
            "affordable": cost <= points,
            "owned": False,
            "recommendation_score": float(_int(resolved.get("priority")) if resolved.get("priority") != 999 else 500),
        })
    return {"owned": owned, "options": options, "remaining_sp": points}


def command_actions(common):
    """All legal home commands as deterministic actions."""
    actions = []
    for cmd in (common or {}).get("commands") or []:
        if int(cmd.get("command_type") or 0) == RACE_COMMAND_TYPE:
            # the race command is expressed as race:<program_id> actions, never
            # as an exec_command
            continue
        enabled = bool(cmd.get("is_enable"))
        actions.append(action_dict(
            command_action_id(cmd),
            "command",
            cmd.get("label") or command_label(cmd),
            {
                "command_type": cmd["command_type"],
                "command_id": cmd["command_id"],
                "command_group_id": cmd["command_group_id"],
                "select_id": cmd["select_id"],
                "current_turn": (common or {}).get("turn") or 0,
            },
            enabled=enabled,
            disabled_reason=None if enabled else "command disabled by the game",
        ))
    return actions


def event_actions(events):
    """One action per event choice. Multi-choice events stop; forced events
    list their single (or zero) choice for the drain path."""
    actions = []
    for event in (events or []):
        choices = event.get("choice_array") or []
        for choice in choices:
            actions.append(action_dict(
                event_action_id(event, choice["select_index"]),
                "event",
                f"Event {event.get('event_id')} · choice {choice['select_index']}",
                {
                    "event_id": event.get("event_id"),
                    "chara_id": event.get("chara_id") or 0,
                    "choice_number": choice["select_index"],
                    "current_turn": 0,
                },
            ))
    return actions


def race_select_actions(data, common, preset=None):
    """Legal optional/required races from race_condition_array when the race
    command is enabled."""
    race_condition = data.get("race_condition_array") or []
    race_enabled = any(
        c.get("command_type") == RACE_COMMAND_TYPE and c.get("is_enable")
        for c in (common or {}).get("commands") or []
    )
    if not race_enabled:
        return []
    seen = set()
    actions = []
    for item in race_condition:
        program_id = _int(item.get("program_id"))
        if not program_id or program_id in seen:
            continue
        seen.add(program_id)
        actions.append(action_dict(
            race_action_id(program_id),
            "race",
            f"Enter race {program_id}",
            {"program_id": program_id, "current_turn": (common or {}).get("turn") or 0},
        ))
    actions.sort(key=lambda a: a["id"])
    return actions


def race_running_actions(common):
    """Transport plumbing for a race that is already running (resume path)."""
    playing_state = (common or {}).get("playing_state") or 1
    if playing_state not in {2, 3, 4, 5}:
        return []
    return [action_dict(
        "race:resume",
        "race",
        "Resume race (entry/start/end/out)",
        {"current_turn": (common or {}).get("turn") or 0},
    )]


def race_continue_actions(common):
    """Continue-offered actions after a race_start with rank > 1."""
    race = (common or {}).get("race") or {}
    offered = int((race or {}).get("continue_offered") or 0)
    if offered <= 0:
        return []
    actions = [
        action_dict(
            "race:continue",
            "race_continue",
            "Use continue (clock) and race again",
            {"current_turn": (common or {}).get("turn") or 0},
            destructive=True,
            disabled_reason=None,
        ),
        action_dict(
            "race:accept",
            "race_continue",
            "Accept current result",
            {"current_turn": (common or {}).get("turn") or 0},
        ),
    ]
    return actions


def item_exchange_actions(state, preset=None, item_manager=None):
    """Legal shop rows as item_exchange actions (one per row, buy 1)."""
    data = (state or {}).get("data") or {}
    free = data.get("free_data_set") or {}
    chara = chara_of(data)
    current_turn = _int(chara.get("turn"))
    coin_val = free.get("coin_num")
    if coin_val is None:
        coin_val = free.get("gained_coin_num")
    budget = _int(coin_val)
    actions = []
    for row in free.get("pick_up_item_info_array") or []:
        shop_item_id = _int(row.get("shop_item_id"))
        item_id = _int(row.get("item_id"))
        name = ITEM_NAMES.get(item_id, f"Item {item_id}")
        cost = _int(row.get("coin_num"))
        limit_turn = _int(row.get("limit_turn"))
        bought = _int(row.get("item_buy_num"))
        limit = _int(row.get("limit_buy_count") or 1)
        enabled = True
        reason = None
        if not shop_item_id:
            enabled, reason = False, "invalid shop row"
        elif limit_turn > 0 and limit_turn < current_turn:
            enabled, reason = False, "expired"
        elif bought >= limit:
            enabled, reason = False, "limit reached"
        elif cost <= 0 or cost > budget:
            enabled, reason = False, "unaffordable"
        actions.append(action_dict(
            item_exchange_action_id(shop_item_id),
            "item_exchange",
            f"Buy {name} ({cost} coins)",
            {"shop_item_id": shop_item_id, "current_num": _int(row.get("item_buy_num") or 0), "current_turn": current_turn},
            enabled=enabled,
            disabled_reason=reason,
            destructive=True,
        ))
    actions.sort(key=lambda a: a["id"])
    return actions


def item_use_actions(state, preset=None, item_manager=None):
    """Owned usable items as item_use actions (use 1 each click)."""
    data = (state or {}).get("data") or {}
    free = data.get("free_data_set") or {}
    actions = []
    for row in free.get("user_item_info_array") or []:
        item_id = _int(row.get("item_id"))
        num = _int(row.get("num") or row.get("current_num") or row.get("item_num"))
        if item_id <= 0 or num <= 0:
            continue
        actions.append(action_dict(
            item_use_action_id(item_id),
            "item_use",
            f"Use {ITEM_NAMES.get(item_id, f'Item {item_id}')} (x{num})",
            {"item_id": item_id, "use_num": 1, "current_num": num, "current_turn": _int((chara_of(data)).get("turn"))},
            destructive=True,
        ))
    actions.sort(key=lambda a: a["id"])
    return actions


def skill_purchase_actions(common, skills=None):
    """skill:<id> actions for every affordable option; the bulk
    `skills:purchase` action carries selected_action_ids."""
    actions = []
    for option in (skills or {}).get("options") or []:
        affordable = bool(option.get("affordable"))
        actions.append(action_dict(
            skill_action_id(option["skill_id"]),
            "skill_purchase",
            f"Learn {option.get('name') or option['skill_id']} ({option.get('cost')} SP)",
            {"skill_id": option["skill_id"], "level": 1},
            enabled=affordable,
            disabled_reason=None if affordable else "not enough skill points",
        ))
    return actions


def bulk_skill_action():
    return action_dict(
        "skills:purchase",
        "skill_purchase",
        "Purchase selected skills",
        {},
    )


class ScenarioAdapter:
    """One captured, manifest-registered scenario. Implementations are
    scenario-neutral transport wrappers; every decision belongs to the user."""

    slug = ""
    name = ""
    scenario_id = 0

    def normalize(self, raw_state, context=None):
        """Return the full normalized PlayState dict (no revision yet)."""
        raise NotImplementedError

    def actions(self, raw_state, normalized_state):
        """Return the deterministic list of Action dicts legal right now."""
        raise NotImplementedError

    def execute(self, session, client, action, selection=None):
        """Execute exactly one meaningful user decision plus transport-only
        follow-through (forced events, noninteractive race presentation).
        Returns the new raw state dict (the full API response envelope)."""
        raise NotImplementedError

    def recommend(self, normalized_state, preset):
        """Return a recommendation dict referencing an enabled action, or
        None. Never executes anything."""
        return None


class UnsupportedAdapter(ScenarioAdapter):
    """Fail-closed adapter for scenario IDs outside the captured registry."""

    slug = "unsupported"
    name = "Unsupported"
    scenario_id = 0

    def normalize(self, raw_state, context=None):
        data = (raw_state or {}).get("data") or {}
        chara = chara_of(data)
        common = normalize_common(raw_state)
        common.update({
            "scenario": {"id": _int(chara.get("scenario_id")), "slug": "unsupported", "name": "Unsupported"},
            "phase": "unsupported",
            "can_finish": False,
            "error": f"scenario {common['trainee']['scenario_id']} not in captured registry",
        })
        return common

    def actions(self, raw_state, normalized_state):
        return []
