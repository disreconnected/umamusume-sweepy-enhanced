"""Pure, explainable scoring helpers shared by adapters.

The Trackblazer command scorer is the existing MANT strategy calculation
moved verbatim from ``MantStrategy._score_command`` into pure functions so
recommendations never mutate state and other scenarios can reuse the pieces.
"""

from __future__ import annotations

STAT_TARGETS = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 30: 5}
TRAINING_COMMANDS = {101: 0, 105: 1, 102: 2, 103: 3, 106: 4, 601: 0, 602: 1, 603: 2, 604: 3, 605: 4}
TRAINING_NAMES = ["Speed", "Stamina", "Power", "Guts", "Wit"]
SUMMER_CAMP_TURNS = {36, 37, 38, 39, 40, 60, 61, 62, 63, 64}
SUMMER_CONSERVE_TURNS = {34, 35, 58, 59}
SUMMER_CONSERVE_ENERGY = 60
ENERGY_FAST_MEDIC = 80
ENERGY_MEDIC_GENERAL = 85
DECK_PARTNERS = {1, 2, 3, 4, 5, 6}
BAD_EFFECT_NAMES = {
    1: "Night Owl",
    2: "Slacker",
    3: "Skin Outbreak",
    4: "Slow Metabolism",
    5: "Migraine",
    6: "Practice Poor",
}


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def bond_map(chara):
    result = {}
    for row in (chara or {}).get("evaluation_info_array") or []:
        result[_int(row.get("target_id"))] = _int(row.get("evaluation"))
    return result


def current_stat(chara, target):
    keys = ["speed", "stamina", "power", "guts", "wiz", "skill_point"]
    return _float((chara or {}).get(keys[target], 0))


def period_index(turn):
    if turn <= 24:
        return 0
    if turn <= 48:
        return 1
    if turn <= 60:
        return 2
    if turn <= 72:
        return 3
    return 4


def period_row(rows, turn, fallback):
    if not isinstance(rows, list) or not rows:
        return fallback
    idx = min(period_index(turn), len(rows) - 1)
    row = rows[idx]
    return row if isinstance(row, list) else fallback


def extra_weight(idx, turn, preset):
    rows = (preset or {}).get("extra_weight") or [[0, 0, 0, 0, 0]] * 4
    if turn <= 24:
        row_idx = 0
    elif turn <= 48:
        row_idx = 1
    elif turn in SUMMER_CAMP_TURNS and len(rows) >= 4:
        row_idx = 3
    else:
        row_idx = 2
    if row_idx >= len(rows) or not isinstance(rows[row_idx], list) or idx >= len(rows[row_idx]):
        return 0.0
    return _float(rows[row_idx][idx])


def npc_score(bond, turn, preset):
    if bond >= 80:
        return 0.0
    row = period_row((preset or {}).get("npc_score_value"), turn, [0.05, 0.05, 0.05])
    v1 = _float(row[0] if len(row) > 0 else 0.05)
    v2 = _float(row[1] if len(row) > 1 else v1)
    ratio = min(1.0, bond / 80.0)
    return v1 + (v2 - v1) * ratio


def pal_score(bond, preset):
    if bond >= 80:
        return 0.0
    scores = (preset or {}).get("pal_friendship_score") or [0.08, 0.057, 0.018]
    v1 = _float(scores[0] if len(scores) > 0 else 0.08)
    v2 = _float(scores[1] if len(scores) > 1 else v1)
    ratio = min(1.0, bond / 80.0)
    return v1 + (v2 - v1) * ratio


def total_stat_gain(command):
    """Sum the positive stat deltas a training would produce, ignoring
    energy/skill-point side effects."""
    total = 0.0
    for item in (command or {}).get("params_inc_dec_info_array") or []:
        target = STAT_TARGETS.get(_int(item.get("target_type")))
        if target is None or target >= 5:
            continue
        value = _float(item.get("value"))
        if value > 0:
            total += value
    return total


def command_stat_gain(command, sp_weight=0):
    if not command:
        return 0
    total = 0
    for item in command.get("params_inc_dec_info_array") or []:
        tt = _int(item.get("target_type"))
        if tt in (1, 2, 3, 4, 5):
            total += _int(item.get("value") or 0)
        elif (tt == 6 or tt == 30) and sp_weight > 0:
            total += _int(item.get("value") or 0) * sp_weight
    if total == 0:
        for field in ["speed", "stamina", "power", "guts", "wiz"]:
            total += _int(command.get(field))
        if sp_weight > 0:
            total += _int(command.get("lp") or command.get("skill_point")) * sp_weight
    return total


def score_command(command, data, chara, preset):
    """The existing MANT training scorer, pure. Higher is better."""
    preset = preset or {}
    turn = _int((chara or {}).get("turn"))
    weights = period_row(preset.get("score_value"), turn, [0.11, 0.10, 0.006, 0.09])
    base = preset.get("base_score") or [0, 0, 0, 0, 0]
    targets = preset.get("expect_attribute") or [9999, 9999, 9999, 9999, 9999]
    min_stats = preset.get("min_stats") or [0, 0, 0, 0, 0]
    min_stats_boost = _float(preset.get("min_stats_boost") or 1.6)
    idx = TRAINING_COMMANDS.get(_int(command.get("command_id")), 0)
    score = _float(base[idx] if idx < len(base) else 0)
    w_lv1 = _float(weights[0] if len(weights) > 0 else 0.11)
    w_lv2 = _float(weights[1] if len(weights) > 1 else 0.10)
    w_energy = _float(weights[2] if len(weights) > 2 else 0.006)
    w_hint = _float(weights[3] if len(weights) > 3 else 0.09)
    stat_mult = preset.get("stat_value_multiplier") or [0.01, 0.01, 0.01, 0.01, 0.01, 0.005]
    bonds = bond_map(chara)
    partners = command.get("training_partner_array") or []
    hints = set(command.get("tips_event_partner_array") or [])
    pal_count = 0
    hint_count = 0
    for partner_id in partners:
        partner_id = _int(partner_id)
        bond = _int(bonds.get(partner_id, 0))
        if partner_id in hints:
            hint_count += 1
        if bond >= 80:
            continue
        time_decay = max(0.0, (72 - turn) / 72.0)
        efficiency_boost = 1.0 + (bond / 80.0) * 0.5 if bond >= 60 else 1.0
        weight = time_decay * efficiency_boost
        if partner_id not in DECK_PARTNERS:
            score += npc_score(bond, turn, preset) * weight
            continue
        if partner_id == 6:
            pal_count += 1
            score += pal_score(bond, preset) * weight
            continue
        ratio = min(1.0, bond / 80.0)
        yield_val = w_lv1 + (w_lv2 - w_lv1) * ratio
        score += yield_val * weight
    if hint_count:
        score += w_hint
    for item in command.get("params_inc_dec_info_array") or []:
        value = _float(item.get("value"))
        if _int(item.get("target_type")) == 10:
            energy_score = value * w_energy
            if _int((chara or {}).get("vital")) >= 80 and value < 0:
                energy_score *= 0.9
            score += energy_score
            continue
        target = STAT_TARGETS.get(_int(item.get("target_type")))
        if target is None or target == 5:
            continue
        stat_gain_score = value * _float(stat_mult[target] if target < len(stat_mult) else 0.01)
        cap = _float(targets[target] if target < len(targets) else 9999)
        floor = _float(min_stats[target] if target < len(min_stats) else 0)
        current_stat_value = current_stat(chara, target) if target < 5 else 0.0
        if floor > 0 and target < 5 and current_stat_value < floor and value > 0:
            stat_gain_score *= min_stats_boost
        if value > 0 and target < 5 and 820 <= current_stat_value <= 1060:
            stat_gain_score *= 1.08
        abs_cap = _float(preset.get("absolute_stat_cap") or 1100)
        eff_cap = min(abs_cap, cap)
        if value > 0 and target < 5 and current_stat_value >= eff_cap:
            stat_gain_score = 0.0
        elif cap > 0 and target < 5:
            ratio = current_stat_value / cap
            if ratio > 1.0:
                stat_gain_score *= 0.0
            elif ratio > 0.97:
                stat_gain_score *= 0.35 - ((ratio - 0.97) / 0.03) * 0.25
            elif ratio > 0.94:
                stat_gain_score *= 0.55 - ((ratio - 0.94) / 0.03) * 0.20
            elif ratio > 0.90:
                stat_gain_score *= 0.75 - ((ratio - 0.90) / 0.04) * 0.20
            elif ratio > 0.86:
                stat_gain_score *= 0.85 - ((ratio - 0.86) / 0.04) * 0.10
            elif ratio > 0.82:
                stat_gain_score *= 0.91 - ((ratio - 0.82) / 0.04) * 0.06
            elif ratio > 0.78:
                stat_gain_score *= 0.95 - ((ratio - 0.78) / 0.04) * 0.04
            elif ratio > 0.74:
                stat_gain_score *= 0.98 - ((ratio - 0.74) / 0.04) * 0.03
            elif ratio > 0.70:
                stat_gain_score *= 1.00 - ((ratio - 0.70) / 0.04) * 0.02
        score += stat_gain_score
    if pal_count:
        score *= 1.0 + max(0.0, min(1.0, _float(preset.get("pal_card_multiplier") or 0.1)))
    if preset.get("compensate_failure", True):
        score *= max(0.0, 1.0 - (_float(command.get("failure_rate")) / 50.0))
    if idx == 4:
        vital = _int((chara or {}).get("vital"))
        max_vital = _int((chara or {}).get("max_vital") or 100)
        gain = 0
        for item in command.get("params_inc_dec_info_array") or []:
            if _int(item.get("target_type")) == 10:
                gain = _float(item.get("value"))
                break
        if vital >= max_vital or (gain > 0 and vital + gain > max_vital):
            score *= 0.35 if turn > 72 else 0.75
        elif vital < 85:
            score *= 1.03
    extra = extra_weight(idx, turn, preset)
    if extra == -1:
        return -999.0
    score *= max(0.0, min(2.0, 1.0 + extra))
    if turn < 60:
        deck_mults = preset.get("_deck_multipliers")
        if deck_mults and len(deck_mults) > idx:
            score *= _float(deck_mults[idx])
    return score
