import json
import re
from pathlib import Path


EXCLUDED_KEYS = {
    "facility_period_configs",
    "facility_ratios",
}

RENAMES = {
    "race_list": "extra_race_list",
    "skill_priority_list": "learn_skill_list",
    "skill_blacklist": "learn_skill_blacklist",
    "blacklistedSkills": "learn_skill_blacklist",
    "extraWeight": "extra_weight",
    "scoreValue": "score_value",
    "baseScore": "base_score",
    "statValueMultiplier": "stat_value_multiplier",
    "witSpecialMultiplier": "wit_special_multiplier",
    "cureAsapConditions": "cure_asap_conditions",
}

MANT_SCENARIO_ID = 4


def slugify(value):
    text = re.sub(r"[^a-zA-Z0-9._ -]+", "", str(value or "").strip())
    text = re.sub(r"\s+", " ", text).strip()
    return text or "preset"


def split_csv(value):
    if isinstance(value, list):
        return value
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def normalize_skill_list(value):
    rows = value if isinstance(value, list) else []
    result = []
    for row in rows:
        if isinstance(row, list):
            parts = []
            for item in row:
                parts.extend(split_csv(item))
        else:
            parts = split_csv(row)
        if parts:
            result.append(parts)
    return result


def as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_race_list(value):
    result = []
    for item in value if isinstance(value, list) else []:
        race_id = as_int(item, None)
        if race_id is not None:
            result.append(race_id)
    return result


STAT_VECTOR_LEN = 5
DEFAULT_MIN_STATS = [0, 0, 0, 0, 0]
DEFAULT_MAX_STATS = [1200, 1200, 1200, 1200, 1200]

# Trainee rank ladder (mirrors the in-game evaluation tier and the dashboard's
# `VET_RANK_LABELS` in public/app.js). UG (rank id 19) is the entry threshold
# into the Ultimate ("U*") tiers — that's what we tune presets to target by
# default for parent-breeding runs. See data/uma_guides/UG_STRATEGY.md for
# rank_score samples we observed (UG4 ~= 21,320 from MaybeVoid Taiki Shuttle).
RANK_ID_SSP = 18
RANK_ID_UG = 19
RANK_ID_UG_PLUS = 20
RANK_ID_US = 33
RANK_ID_US_PLUS = 34

# Default UG-targeted training budget (mile/medium/long uma).
# Source: JackieX "Trackblazer Career Guide" 04:14 — usual range 34-37 races.
# The 40+ routes are whale/luck routes and starve training on normal decks.
DEFAULT_RACE_COUNT_TARGET = 36
DEFAULT_MIN_RACES = 30
DEFAULT_MAX_RACES = 37

# "+40 total stats per training" rule of thumb. Scale this down toward 28-32
# for low-stat-bonus umas so they actually train their primary stat instead
# of racing every turn.
DEFAULT_TRAIN_MIN_GAIN = 40

# Per-running-style "parent breeding" stat profiles. Vectors are
# [SPD, STA, PWR, GUT, WIT] in sweepy ordering.
#
# The MIN profile is what we want the bot to push toward (boosts training of
# any stat currently below its floor). The MAX profile is the hard scoring cap
# (Trailblazer/URA can't exceed 1200 base anyway, so we leave them at 1200).
#
# Targets are tuned for the inheritance "blue (★3) factor" threshold of 1200
# in the priority stat, and ★2 (orange, 1100+) or ★3 in secondaries. Numbers
# below 600 give white sparks at best, so we keep tertiary floors low.
#
# WIT floors bumped vs the old profile to reflect JackieX's
# "prioritize wit on tight energy turns" rule + Trailblazer's higher 20-energy
# race cost. See data/uma_guides/UG_STRATEGY.md §4.
#
# Style ids: 1 = Front Runner, 2 = Pace Chaser, 3 = Late Surger, 4 = End Closer.
STYLE_STAT_PROFILES = {
    # Front Runner: SPD + STA matter most. Power coasts. Wit covers late-start.
    1: {"min": [1200, 1100,  600,    0,  500],
        "max": [1200, 1200, 1200, 1200, 1200]},
    # Pace Chaser: SPD + PWR primary, decent STA for medium distance.
    2: {"min": [1200,  900, 1100,    0,  500],
        "max": [1200, 1200, 1200, 1200, 1200]},
    # Late Surger: SPD + PWR + WIT (for skill procs in final stretch).
    3: {"min": [1200,  700, 1100,    0,  600],
        "max": [1200, 1200, 1200, 1200, 1200]},
    # End Closer: highest stat demand. SPD + STA + PWR all in blue range.
    4: {"min": [1200, 1100, 1100,    0,  500],
        "max": [1200, 1200, 1200, 1200, 1200]},
}


def stat_profile_for_style(style_id, key="min"):
    """Return the recommended stat vector for a running style, or a flat
    default if the style id isn't recognised."""
    profile = STYLE_STAT_PROFILES.get(int(style_id or 0))
    if not profile:
        return list(DEFAULT_MIN_STATS if key == "min" else DEFAULT_MAX_STATS)
    return list(profile.get(key) or (DEFAULT_MIN_STATS if key == "min" else DEFAULT_MAX_STATS))


def normalize_stat_vector(value, fallback):
    """Coerce an array/dict into a 5-int vector [SPD, STA, PWR, GUT, WIT]."""
    base = list(fallback) if fallback else [0] * STAT_VECTOR_LEN
    if isinstance(value, dict):
        keys = ("speed", "stamina", "power", "guts", "wit")
        for idx, key in enumerate(keys):
            base[idx] = as_int(value.get(key, base[idx]), base[idx])
        return base[:STAT_VECTOR_LEN]
    if isinstance(value, list):
        for idx in range(STAT_VECTOR_LEN):
            if idx < len(value):
                base[idx] = as_int(value[idx], base[idx])
        return base[:STAT_VECTOR_LEN]
    return base[:STAT_VECTOR_LEN]


def normalize_card_id_list(value, max_len=5):
    """Coerce a card list (typically the deck) into a list of positive ints."""
    out = []
    if not isinstance(value, list):
        return out
    for item in value:
        cid = as_int(item, 0)
        if cid > 0:
            out.append(cid)
        if len(out) >= max_len:
            break
    return out


def serialize_preset(raw):
    data = dict(raw or {})
    serialized = {}

    serialized["name"] = slugify(data.get("name") or "preset")
    serialized["running_style"] = as_int(data.get("running_style"), 1)
    serialized["learn_skill_list"] = normalize_skill_list(data.get("learn_skill_list"))

    blacklist = []
    blacklist.extend(split_csv(data.get("blacklistedSkills")))
    blacklist.extend(split_csv(data.get("skill_blacklist")))
    blacklist.extend(split_csv(data.get("learn_skill_blacklist")))
    serialized["learn_skill_blacklist"] = list(dict.fromkeys(blacklist))

    serialized["extra_race_list"] = normalize_race_list(data.get("extra_race_list", data.get("race_list", [])))
    # Lower default skill-buy threshold (was 888). Trailblazer rank_score scales
    # heavily with number of skills learned, so we want to buy more aggressively.
    # See data/uma_guides/UG_STRATEGY.md §5.7.
    serialized["learn_skill_threshold"] = as_int(data.get("learn_skill_threshold"), 720)

    serialized["min_stats"] = normalize_stat_vector(data.get("min_stats"), DEFAULT_MIN_STATS)
    serialized["max_stats"] = normalize_stat_vector(data.get("max_stats"), DEFAULT_MAX_STATS)

    # UG-targeting knobs. Defaults assume a mile/medium/long uma aiming for
    # the Ultimate (UG) inheritance threshold. Drop `train_min_total_stat_gain`
    # to ~28-32 for umas with no speed-bonus support cards.
    serialized["target_rank"] = as_int(data.get("target_rank"), RANK_ID_UG)
    serialized["race_count_target"] = as_int(data.get("race_count_target"), DEFAULT_RACE_COUNT_TARGET)
    serialized["min_races"] = as_int(data.get("min_races"), DEFAULT_MIN_RACES)
    serialized["max_races"] = as_int(data.get("max_races"), DEFAULT_MAX_RACES)
    serialized["train_min_total_stat_gain"] = as_int(
        data.get("train_min_total_stat_gain"), DEFAULT_TRAIN_MIN_GAIN
    )
    # Reserves the bot must respect (consumed by items.py / mant.py in future).
    serialized["reserve_master_hammer_final3"] = as_int(
        data.get("reserve_master_hammer_final3"), 3
    )
    serialized["reserve_megaphone_summer"] = as_int(
        data.get("reserve_megaphone_summer"), 2
    )

    serialized["support_card_ids"] = normalize_card_id_list(data.get("support_card_ids"))
    serialized["friend_card_id"] = as_int(data.get("friend_card_id"), 0)
    serialized["friend_viewer_id"] = as_int(data.get("friend_viewer_id"), 0)
    serialized["trainee_card_id"] = as_int(data.get("trainee_card_id"), 0)
    serialized["parent_id_1"] = as_int(data.get("parent_id_1"), 0)
    serialized["parent_id_2"] = as_int(data.get("parent_id_2"), 0)
    # Rental veteran (friend's borrowable uma used as a 3rd inheritance slot).
    # rental_chara_viewer_id == the friend's viewer id (matches uma.moe account_id)
    # rental_chara_id == that friend's trained_chara_id for the specific veteran
    serialized["rental_chara_viewer_id"] = as_int(data.get("rental_chara_viewer_id"), 0)
    serialized["rental_chara_id"] = as_int(data.get("rental_chara_id"), 0)

    # Provenance fields, written when the preset was created by an importer.
    for key in ("imported_from_trainer_id", "imported_trainer_name", "imported_at"):
        val = data.get(key)
        if val:
            serialized[key] = str(val)

    return serialized

def hydrate_preset(raw):
    data = serialize_preset(raw)

    data["scenario_id"] = MANT_SCENARIO_ID
    data["scenario"] = MANT_SCENARIO_ID
    data["cure_asap_conditions"] = ["Migraine", "Night Owl", "Skin Outbreak", "Slacker", "Slow Metabolism", "(Practice poor isn't worth a turn to cure)"]
    # `expect_attribute` is the per-stat cap the scoring strategy uses to
    # zero out training above the target. We feed it from max_stats so the
    # user can edit caps from the preset UI / uma.moe importer. Anything
    # >= 1200 effectively means "no cap".
    raw_caps = data.get("max_stats") or DEFAULT_MAX_STATS
    data["expect_attribute"] = [as_int(v, 9999) or 9999 for v in raw_caps][:STAT_VECTOR_LEN]
    data["score_value"] = [[0.11, 0.1, 0.006, 0.09], [0.11, 0.1, 0.006, 0.09], [0.11, 0.1, 0.006, 0.09], [0.03, 0.05, 0.006, 0.09], [0, 0, 0.006, 0]]
    data["base_score"] = [0, 0, 0, 0, 0]
    data["stat_value_multiplier"] = [0.01, 0.01, 0.01, 0.01, 0.01, 0.005]
    data["extra_weight"] = [[0, 0, 0, 0, 0]] * 4
    data["npc_score_value"] = [[0.05, 0.05, 0.05], [0.05, 0.05, 0.05], [0.05, 0.05, 0.05], [0.03, 0.05, 0.05], [0, 0, 0.05]]
    data["special_training"] = [0.095, 0.095, 0.095, 0.095, 0]
    data["spirit_explosion"] = [[0.16, 0.16, 0.16, 0.06, 0.11]] * 5
    data["wit_special_multiplier"] = [1.57, 1.37]
    data["compensate_failure"] = True
    data["summer_score_threshold"] = 0.34
    data["motivation_threshold_year1"] = 3
    data["motivation_threshold_year2"] = 4
    data["motivation_threshold_year3"] = 4
    data["prioritize_recreation"] = False
    data["pal_thresholds"] = []
    data["pal_friendship_score"] = [0.08, 0.057, 0.018]
    data["pal_card_multiplier"] = 0.1
    data["rest_threshold"] = 48
    data["manual_purchase_at_end"] = False
    data["mant_config"] = {}

    return data

class PresetStore:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.preset_dir = self.base_dir / "data" / "presets"

    def ensure(self):
        self.preset_dir.mkdir(parents=True, exist_ok=True)

    def read_all(self):
        self.ensure()
        loaded = {}
        for path in self._source_files():
            try:
                data = hydrate_preset(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            loaded[data["name"]] = data
        return sorted(loaded.values(), key=lambda item: item["name"].lower())

    def read_one(self, name):
        wanted = str(name or "").strip().lower()
        for preset in self.read_all():
            if preset["name"].lower() == wanted:
                return preset
        return None

    def write(self, preset):
        self.ensure()
        serialized_data = serialize_preset(preset)
        path = self.preset_dir / f"{slugify(serialized_data['name'])}.json"
        path.write_text(json.dumps(serialized_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return hydrate_preset(serialized_data)

    def delete(self, name):
        path = self.preset_dir / f"{slugify(name)}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def _source_files(self):
        if self.preset_dir.exists():
            return list(self.preset_dir.glob("*.json"))
        return []
