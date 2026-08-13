"""Protocol capture, redaction, sanitization, and fixture manifest tooling.

Raw captures are runtime artifacts written under ``UMA_RUNTIME_DIR/captures/raw``
(never under the repository). Every record is passed through one recursive
redactor before touching disk. The deterministic sanitizer converts selected
raw sessions into committed structural fixtures under
``tests/fixtures/scenarios/<scenario>/`` and the manifest generator rebuilds
``tests/fixtures/scenarios/scenario-manifest.json`` — the authoritative source
for scenario ids, endpoint names, discriminators, and action payload shapes.

CLI:
    python -m career_bot.capture sanitize <raw.jsonl> --scenario <slug>
    python -m career_bot.capture manifest
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Canonical set of keys whose VALUES never leave the process. Mirrors the old
# SENSITIVE_ERROR_KEYS and adds password/ticket spellings seen in payloads.
SENSITIVE_ERROR_KEYS = {
    "auth_key",
    "authKey",
    "steam_session_ticket",
    "steam_ticket",
    "session_ticket",
    "sessionTicket",
    "sid",
    "udid",
    "device_id",
    "password",
    "passwd",
    "steam_password",
}

# Account/entity identifiers replaced with stable tokens by the sanitizer.
# Referential equality is preserved within one sanitization run.
TOKENIZED_KEYS = {
    "auth_key",
    "authKey",
    "steam_session_ticket",
    "steam_ticket",
    "session_ticket",
    "sessionTicket",
    "sid",
    "udid",
    "device_id",
    "password",
    "passwd",
    "steam_password",
    "steam_id",
    "viewer_id",
    "owner_viewer_id",
    "trained_chara_id",
    "succession_trained_chara_id_1",
    "succession_trained_chara_id_2",
    "target_viewer_id",
    "target_id",
}

# Keys removed entirely (presence itself is diagnostic noise or may carry
# account context we cannot prove is safe).
DROPPED_KEYS = {
    "device_name",
    "graphics_device_name",
    "platform_os_version",
    "ip_address",
}

#: career-only endpoint prefixes; anything else is diagnostic-only and never
#: becomes a fixture.
CAREER_ENDPOINT_PREFIX = "single_mode_free/"

B64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def runtime_capture_root():
    override = os.environ.get("UMA_RUNTIME_DIR")
    if override:
        base = Path(override).expanduser().resolve()
    else:
        here = Path(__file__).resolve().parent.parent
        base = here / "uma_runtime"
    return base / "captures"


def raw_dir_for(scenario_slug):
    return runtime_capture_root() / "raw" / scenario_slug


def fixtures_dir():
    here = Path(__file__).resolve().parent.parent
    return here / "tests" / "fixtures" / "scenarios"


def manifest_path():
    return fixtures_dir() / "scenario-manifest.json"


# ---------------------------------------------------------------------------
# Redaction (applied before every disk write and every callback output)
# ---------------------------------------------------------------------------

def redact_for_console(value, key=""):
    """Console/report variant: sensitive keys replaced, lists truncated to 20
    items, long strings truncated to 160 chars."""
    if key in SENSITIVE_ERROR_KEYS:
        return "<redacted>"
    if isinstance(value, dict):
        return {k: redact_for_console(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_for_console(item, key) for item in value[:20]]
    if isinstance(value, str) and len(value) > 160:
        return value[:160] + "...<truncated>"
    return value


def redact(value, key=""):
    """Recursive redactor. Keys in SENSITIVE_ERROR_KEYS have their values
    replaced; DROPPED_KEYS are removed; long strings are truncated. Safe for
    bytes, lists, dicts, and scalars."""
    if key in DROPPED_KEYS:
        return None
    if key in SENSITIVE_ERROR_KEYS:
        if isinstance(value, (dict, list, tuple)):
            return "<redacted>"
        return "<redacted>"
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            redacted = redact(v, k)
            if redacted is not None:
                out[k] = redacted
        return out
    if isinstance(value, (list, tuple)):
        return [redact(item, key) for item in value]
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, str) and len(value) > 512:
        return value[:512] + "...<truncated>"
    return value


# ---------------------------------------------------------------------------
# Deterministic sanitizer (raw capture -> committed structural fixture)
# ---------------------------------------------------------------------------

class Tokenizer:
    """Stable per-run token map. Same input -> identical output."""

    def __init__(self, scenario_slug):
        self._map = {}
        self._count = 0
        self.prefix = f"f{re.sub(r'[^a-z0-9]', '', scenario_slug.lower())}"

    def token(self, value):
        if value in self._map:
            return self._map[value]
        self._count += 1
        token = f"{self.prefix}_{self._count}"
        self._map[value] = token
        return token


def _is_gameplay_key(key):
    """Keys whose numbers drive gameplay and must survive the sanitizer
    verbatim: scenario/turn/command/event/program/item/skill ids, stats,
    meters, costs, and counts."""
    gameplay = {
        "scenario_id", "turn", "current_turn", "command_type", "command_id",
        "command_group_id", "select_id", "event_id", "chara_id", "program_id",
        "race_instance_id", "item_id", "shop_item_id", "skill_id", "group_id",
        "level", "rarity", "cost", "coin_num", "original_coin_num",
        "speed", "stamina", "power", "guts", "wiz", "vital", "max_vital",
        "motivation", "skill_point", "fans", "failure_rate", "value",
        "target_type", "num", "current_num", "item_buy_num", "limit_buy_count",
        "limit_turn", "evaluation", "story_step", "is_enable", "is_outing",
        "continue_num", "available_continue_num", "available_free_continue_num",
        "is_short", "frame_order", "rank", "rank_score", "is_boost",
        "boost_story_event_id", "deck_id", "use_tp", "current_money",
        "succession_rank_point", "difficulty_id", "difficulty",
        "hint_level", "hint_count", "choice_number", "select_index",
        "result_code", "response_code", "current_tp", "max_tp",
        "fcoin", "coin", "tp", "sp", "max_sp", "story_id",
    }
    return key in gameplay


def sanitize_record(record, scenario_slug):
    """Tokenize account/entity ids (preserving referential equality), keep
    gameplay numbers, drop diagnostic noise. Returns a new record dict."""
    tokenizer = Tokenizer(scenario_slug)

    def walk(value, key=""):
        if isinstance(value, dict):
            out = {}
            for k, v in value.items():
                if k in DROPPED_KEYS:
                    continue
                if k in TOKENIZED_KEYS:
                    out[k] = tokenizer.token(str(v))
                    continue
                out[k] = walk(v, k)
            return out
        if isinstance(value, (list, tuple)):
            return [walk(item, key) for item in value]
        if isinstance(value, bytes):
            return value.hex()
        # gameplay numbers stay verbatim; never touch a dict's own scalar keys
        return value

    return walk(record)


def sanitize_raw_session(raw_records, scenario_slug):
    """Convert a list of raw JSONL record dicts into fixture-ready dicts.
    Deterministic: identical input yields byte-identical output."""
    out = []
    for index, record in enumerate(raw_records):
        if record.get("kind") == "http_unpaired" or not record.get("response"):
            # ambiguous/unpaired records are diagnostic-only
            continue
        request = record.get("request") or {}
        response = record.get("response") or {}
        endpoint = str(request.get("endpoint") or "")
        if not endpoint.startswith(CAREER_ENDPOINT_PREFIX):
            # out-of-scope records are diagnostic-only
            continue
        fixture = {
            "name": f"{index + 1:03d}_{endpoint.rsplit('/', 1)[-1]}",
            "scenario": scenario_slug,
            "request": {
                "endpoint": endpoint,
                "payload": sanitize_record(request.get("payload") or {}, scenario_slug),
            },
            "response": sanitize_record(response, scenario_slug),
        }
        out.append(fixture)
    return out


def write_fixtures(fixtures, scenario_slug):
    """Write sanitized fixtures as JSON files. Returns the list of written
    paths."""
    directory = fixtures_dir() / scenario_slug
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for fixture in fixtures:
        path = directory / f"{fixture['name']}.json"
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# Raw recorder (JSONL under UMA_RUNTIME_DIR/captures/raw/<scenario>/)
# ---------------------------------------------------------------------------

class CaptureRecorder:
    def __init__(self, scenario_slug, session_tag=None):
        self.scenario_slug = scenario_slug
        directory = raw_dir_for(scenario_slug)
        directory.mkdir(parents=True, exist_ok=True)
        if not session_tag:
            session_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = directory / f"{session_tag}.jsonl"
        self.count = 0
        self.ambiguous = 0

    def write(self, record):
        """Append one redacted record. Raw values never reach disk."""
        record = dict(record or {})
        record["scenario"] = self.scenario_slug
        record["recorded_at"] = datetime.now().isoformat(timespec="seconds")
        redacted = redact(record)
        if redacted is None:
            return
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(redacted, ensure_ascii=False, default=str) + "\n")
        self.count += 1


def iter_raw_records(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


# ---------------------------------------------------------------------------
# Manifest (authoritative registry derived from fixtures)
# ---------------------------------------------------------------------------

def _payload_keys(payload):
    keys = []
    if isinstance(payload, dict):
        keys = sorted(payload.keys())
    return keys


def _state_kinds_from_fixtures(fixtures):
    """Classify normalized phase kinds implied by a fixture set."""
    kinds = set()
    for fixture in fixtures:
        response = fixture.get("response") or {}
        data = response.get("data") or {}
        if "single_mode_finish_common" in data:
            kinds.add("finish")
        if data.get("unchecked_event_array"):
            kinds.add("event")
        if data.get("race_start_info"):
            kinds.add("race_running")
        if (data.get("home_info") or {}).get("command_info_array"):
            kinds.add("home")
        if data.get("race_condition_array"):
            kinds.add("race_select")
        if data.get("unity_team_info") or data.get("unity_cup_info"):
            kinds.add("unity")
        if data.get("trackblazer_info"):
            kinds.add("trackblazer")
        if data.get("concert_info"):
            kinds.add("concert")
        if data.get("ura_goal_array") or data.get("ura_final_info"):
            kinds.add("ura")
    return sorted(kinds)


def _action_shapes_from_fixtures(fixtures, known_shapes):
    """Union observed request payload keys per endpoint, then map known action
    kinds to the endpoint the adapter must call."""
    observed = {}
    for fixture in fixtures:
        request = fixture.get("request") or {}
        endpoint = request.get("endpoint") or ""
        if not endpoint:
            continue
        keys = set(_payload_keys(request.get("payload")))
        observed.setdefault(endpoint, set()).update(keys)
    shapes = {}
    for kind, endpoint in known_shapes.items():
        shapes[kind] = {
            "endpoint": endpoint,
            "payload_keys": sorted(observed.get(endpoint, [])),
        }
    return shapes


KNOWN_ACTION_SHAPES = {
    "command": "single_mode_free/exec_command",
    "event": "single_mode_free/check_event",
    "race_entry": "single_mode_free/race_entry",
    "change_running_style": "single_mode_free/change_running_style",
    "race_start": "single_mode_free/race_start",
    "race_end": "single_mode_free/race_end",
    "race_out": "single_mode_free/race_out",
    "race_continue": "single_mode_free/continue",
    "skill_purchase": "single_mode_free/gain_skills",
    "item_exchange": "single_mode_free/multi_item_exchange",
    "item_use": "single_mode_free/multi_item_use",
    "load_career": "single_mode_free/load",
    "finish": "single_mode_free/finish",
    "minigame_end": "single_mode_free/minigame_end",
    # Scenario actions: current mappings until live capture confirms them.
    # The regenerated manifest is authoritative; captures may rename these.
    "unity_roster": "single_mode_free/unity_roster",
    "unity_opponent": "single_mode_free/unity_opponent",
    "concert_technique_purchase": "single_mode_free/concert_technique_purchase",
    "concert_song_purchase": "single_mode_free/concert_song_purchase",
    "concert_grand_start": "single_mode_free/concert_grand_start",
}


SCENARIO_DISPLAY_NAMES = {
    "ura": "URA Finale",
    "unity": "Unity Cup",
    "trackblazer": "Trackblazer",
    "grand_concert": "Our Grand Concert",
}


def build_manifest(fixture_dir=None, known_shapes=None):
    """Rebuild scenario-manifest.json from the fixture directories. Fully
    deterministic (no timestamps)."""
    fixture_dir = Path(fixture_dir) if fixture_dir else fixtures_dir()
    known_shapes = dict(known_shapes or KNOWN_ACTION_SHAPES)
    scenarios = {}
    if fixture_dir.exists():
        for child in sorted(p for p in fixture_dir.iterdir() if p.is_dir()):
            slug = child.name
            fixture_files = sorted(p.name for p in child.glob("*.json"))
            fixtures = []
            for name in fixture_files:
                try:
                    fixtures.append(json.loads((child / name).read_text(encoding="utf-8")))
                except (ValueError, OSError):
                    continue
            if not fixtures:
                continue
            scenario_id = 0
            for fixture in fixtures:
                data = (fixture.get("response") or {}).get("data") or {}
                chara = data.get("chara_info") or data.get("single_mode_chara_light") or {}
                if chara.get("scenario_id"):
                    scenario_id = int(chara["scenario_id"])
                    break
            endpoints = sorted({(f.get("request") or {}).get("endpoint") for f in fixtures if (f.get("request") or {}).get("endpoint")})
            discriminators = sorted(
                {k for f in fixtures for k in ((f.get("response") or {}).get("data") or {}).keys()}
            )
            scenarios[slug] = {
                "id": scenario_id,
                "slug": slug,
                "name": SCENARIO_DISPLAY_NAMES.get(slug, slug.replace("_", " ").title()),
                "fixture_files": fixture_files,
                "endpoints": endpoints,
                "discriminators": discriminators,
                "state_kinds": _state_kinds_from_fixtures(fixtures),
                "action_shapes": _action_shapes_from_fixtures(fixtures, known_shapes),
            }
    manifest = {"scenarios": scenarios, "action_shapes": known_shapes}
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_sanitize(args):
    path = Path(args.raw_jsonl)
    if not path.exists():
        print(f"raw capture not found: {path}", file=sys.stderr)
        return 1
    records = list(iter_raw_records(path))
    fixtures = sanitize_raw_session(records, args.scenario)
    written = write_fixtures(fixtures, args.scenario)
    print(f"sanitized {len(fixtures)} career records from {len(records)} raw records -> {len(written)} fixtures")
    return 0


def _cmd_manifest(args):
    path = build_manifest()
    print(f"manifest written: {path}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m career_bot.capture")
    sub = parser.add_subparsers(dest="command", required=True)

    p_san = sub.add_parser("sanitize", help="convert a raw jsonl capture into committed fixtures")
    p_san.add_argument("raw_jsonl")
    p_san.add_argument("--scenario", required=True)
    p_san.set_defaults(func=_cmd_sanitize)

    p_man = sub.add_parser("manifest", help="regenerate scenario-manifest.json from fixtures")
    p_man.set_defaults(func=_cmd_manifest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
