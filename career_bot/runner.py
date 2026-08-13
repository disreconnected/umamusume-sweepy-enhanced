"""One serialized, manual "fast mode" career session.

Replaces the autonomous ``CareerRunner`` thread loop. A single
``threading.Lock`` covers load -> validate -> API call(s) -> normalize ->
publish. Exactly one meaningful user decision executes per ``act()`` plus
transport-only follow-through (forced events, noninteractive race
presentation); any response presenting two or more choices, a shop/lesson/
roster selection, clock use, or another resource-spending decision stops and
returns control to the user. There is no background thread, no autoplay, and
no dev/burn-clock mode.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from career_bot.items import MantItemManager
from career_bot.races import RacePlanner
from career_bot.scenarios import base as scenario_base
from career_bot.scenarios import grand_concert, trackblazer, unity, ura  # noqa: F401  import for adapter registration
from career_bot.scenarios.base import has_multi_choice_event, is_unrecognized_blocking_state, parse_race_rank
from career_bot.scenarios.registry import adapter_for_scenario
from career_bot.scenarios.registry import registry as scenario_registry
from career_bot.skills import SkillBuyer


def runtime_output_root(base_dir):
    override = os.environ.get("UMA_RUNTIME_DIR")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(base_dir).resolve()
    for candidate in (base, *base.parents):
        if (candidate / ".git").exists():
            return candidate / "uma_runtime"
    return base.parent / "uma_runtime"


class UpstreamGameError(Exception):
    """A mutating call failed at the game server. The session reconciles via
    load_career() and never blindly retries the mutation."""


class ActionValidationError(Exception):
    """Action absent or disabled in the authoritative catalog."""


class ScenarioEndpointMissing(Exception):
    """The captured manifest does not describe this scenario action; the
    adapter fails closed."""


class CareerSession:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.lock = threading.Lock()
        self.raw_state = None
        self.normalized = None
        self.revision = 0
        self.preset = None
        self.race_planner = RacePlanner(base_dir)
        self.skill_buyer = SkillBuyer(base_dir)
        self.item_manager = MantItemManager()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def reset(self):
        """Drop all session state (called on login/logout; a session belongs
        to one account)."""
        with self.lock:
            self.raw_state = None
            self.normalized = None
            self.revision = 0
            self.preset = None

    def load(self, client, preset=None):
        """load_career(), recover blocked/minigame/race-running states,
        normalize, and increment the revision once."""
        with self.lock:
            self.preset = preset
            try:
                raw = client.load_career()
            except Exception as exc:
                raise UpstreamGameError(f"load_career failed: {exc}") from exc
            raw = self._settle_transport(client, raw)
            self._publish(raw, preset)
            return self._snapshot_locked()

    def snapshot(self):
        with self.lock:
            return self._snapshot_locked()

    def act(self, client, action, expected_revision, selection=None):
        """Execute exactly one meaningful decision plus transport-only
        follow-through. Rejects stale revisions with a typed conflict."""
        with self.lock:
            if expected_revision is None or int(expected_revision) != self.revision:
                return {
                    "success": False,
                    "error": "stale_revision",
                    "state": self._snapshot_locked(),
                }
            catalog = {a["id"]: a for a in (self.normalized or {}).get("actions") or []}
            entry = catalog.get(action.get("id") or "")
            if entry is None:
                return {"success": False, "error": "unknown_action", "detail": f"action {action.get('id')!r} not in the current catalog", "state": self._snapshot_locked()}
            if not entry.get("enabled"):
                return {"success": False, "error": "action_disabled", "detail": entry.get("disabled_reason") or "action disabled", "state": self._snapshot_locked()}

            adapter = self._current_adapter()
            before = self._fingerprint(self.raw_state)
            try:
                raw = adapter.execute(self, client, entry, selection=selection)
            except ActionValidationError as exc:
                return {"success": False, "error": "invalid_selection", "detail": str(exc), "state": self._snapshot_locked()}
            except ScenarioEndpointMissing as exc:
                return {"success": False, "error": "not_captured", "detail": str(exc), "state": self._snapshot_locked()}
            except Exception as exc:
                # upstream failure: reconcile, never blindly retry a mutation
                return self._reconcile_failure(client, before, exc)

            raw = self._settle_transport(client, raw)
            self._publish(raw, self.preset)
            return {"success": True, "state": self._snapshot_locked()}

    def finish(self, client, expected_revision):
        with self.lock:
            if expected_revision is None or int(expected_revision) != self.revision:
                return {"success": False, "error": "stale_revision", "state": self._snapshot_locked()}
            if (self.normalized or {}).get("phase") != "finish" and not (self.normalized or {}).get("can_finish"):
                return {"success": False, "error": "not_finishable", "state": self._snapshot_locked()}
            before = self._fingerprint(self.raw_state)
            try:
                raw = self.finish_career(client)
            except Exception as exc:
                return self._reconcile_failure(client, before, exc)
            raw = self._settle_transport(client, raw)
            self._publish(raw, self.preset)
            return {"success": True, "state": self._snapshot_locked()}

    def delete(self, client, expected_revision):
        with self.lock:
            if expected_revision is None or int(expected_revision) != self.revision:
                return {"success": False, "error": "stale_revision", "state": self._snapshot_locked()}
            before = self._fingerprint(self.raw_state)
            try:
                current_turn = self._turn_of(self.raw_state)
                client.finish_career(current_turn=current_turn, is_force_delete=True)
            except Exception as exc:
                return self._reconcile_failure(client, before, exc)
            try:
                raw = client.load_career()
            except Exception as exc:
                raise UpstreamGameError(f"load_career after delete failed: {exc}") from exc
            raw = self._settle_transport(client, raw)
            self._publish(raw, self.preset)
            return {"success": True, "state": self._snapshot_locked()}

    # ------------------------------------------------------------------
    # transitions (called by adapters; transport-only follow-through allowed)
    # ------------------------------------------------------------------
    def exec_command(self, client, payload):
        payload = dict(payload or {})
        if "current_vital" not in payload:
            payload["current_vital"] = self._vital_of(self.raw_state)
        if "current_turn" not in payload:
            payload["current_turn"] = self._turn_of(self.raw_state)
        try:
            raw = client.exec_command(**payload)
        except Exception as exc:
            if any(err in str(exc) for err in ("102", "1503")):
                raw = self._fresh_career_state(client)
            else:
                raise
        return self.drain_forced_events(client, raw)

    def submit_event(self, client, action):
        payload = dict(action.get("payload") or {})
        event_id = int(payload.get("event_id") or 0)
        current_turn = int(payload.get("current_turn") or 0) or self._turn_of(self.raw_state)
        try:
            raw = client.check_event(
                event_id=event_id,
                chara_id=int(payload.get("chara_id") or 0),
                choice_number=int(payload.get("choice_number") or 0),
                current_turn=current_turn,
            )
        except Exception as exc:
            if any(err in str(exc) for err in ("Network error", "201", "205", "208")):
                raw = self._fresh_career_state(client)
            else:
                raise
        return self.drain_forced_events(client, raw)

    def drain_forced_events(self, client, state):
        """Resolve zero/one-choice events automatically. A multi-choice event
        stops the chain and returns control."""
        current = state
        for _ in range(20):
            data = (current or {}).get("data") or {}
            events = data.get("unchecked_event_array") or []
            if not events:
                return current
            if has_multi_choice_event(events):
                return current
            event = events[0] or {}
            choice = 0
            try:
                current = client.check_event(
                    event_id=int(event.get("event_id") or 0),
                    chara_id=int(event.get("chara_id") or 0),
                    choice_number=choice,
                    current_turn=int((data.get("chara_info") or {}).get("turn") or 0),
                )
            except Exception as exc:
                if any(err in str(exc) for err in ("Network error", "201", "205", "208")):
                    return self._fresh_career_state(client)
                raise
        return current

    def run_race(self, client, program_id, preset):
        """race_entry -> (style fix) -> race_start -> rank. Rank 1 (or no
        continue offered) chains race_end -> race_out; rank > 1 with a
        continue offered stops in race_continue for the user."""
        current_turn = self._turn_of(self.raw_state)
        preset = preset or {}
        try:
            entry = client.race_entry(program_id=program_id, current_turn=current_turn)
        except Exception as exc:
            if any(err in str(exc) for err in ("205", "208")):
                self.race_planner.reject(current_turn, program_id)
                return self._fresh_career_state(client)
            raise
        entry = self.drain_forced_events(client, entry)
        self._apply_running_style(client, entry, program_id, preset)
        res = client.race_start(is_short=1, current_turn=current_turn)
        rank = parse_race_rank(res)
        if rank > 1 and self._continue_offered(res) > 0:
            res = self.drain_forced_events(client, res)
            return res
        return self._finish_race_transport(client, res, current_turn)

    def race_continue(self, client, preset):
        current_turn = self._turn_of(self.raw_state)
        res = self.raw_state or {}
        free = int(((res.get("data") or {}).get("home_info") or {}).get("available_free_continue_num") or 0)
        std = int(((res.get("data") or {}).get("home_info") or {}).get("available_continue_num") or 0)
        continue_type = 1 if free > 0 else 2
        try:
            cont = client.race_continue(current_turn=current_turn, continue_type=continue_type)
        except Exception as exc:
            if any(err in str(exc) for err in ("102", "1503", "201")):
                return self._finish_race_transport(client, res, current_turn)
            raise
        cont = self.drain_forced_events(client, cont)
        res2 = client.race_start(is_short=1, current_turn=current_turn)
        rank = parse_race_rank(res2)
        if rank > 1 and self._continue_offered(res2) > 0:
            return self.drain_forced_events(client, res2)
        return self._finish_race_transport(client, res2, current_turn)

    def accept_race(self, client, preset):
        current_turn = self._turn_of(self.raw_state)
        return self._finish_race_transport(client, self.raw_state or {}, current_turn)

    def resume_race(self, client, preset):
        """Transport-only follow-through for a career that was loaded while a
        race was already running (playing_state 2/3/4)."""
        current_turn = self._turn_of(self.raw_state)
        state = self.raw_state or {}
        data = state.get("data") or {}
        chara = data.get("chara_info") or {}
        playing_state = int(chara.get("playing_state") or 1)
        race = data.get("race_start_info") or {}
        program_id = int(race.get("program_id") or 0)
        preset = preset or {}
        if playing_state in {2, 4} and program_id:
            self._apply_running_style(client, state, program_id, preset)
        res = client.race_start(is_short=1, current_turn=current_turn)
        rank = parse_race_rank(res)
        if rank > 1 and self._continue_offered(res) > 0:
            return self.drain_forced_events(client, res)
        return self._finish_race_transport(client, res, current_turn)

    def exchange_items(self, client, payloads, current_turn):
        state = self.raw_state or {}
        current, bought, result = self._exchange(client, state, payloads, current_turn)
        if not result.get("result") == "ok":
            raise UpstreamGameError(f"item exchange rejected: {result.get('error') or result.get('skip')}")
        return current

    def use_items(self, client, payloads, current_turn):
        state = self.raw_state or {}
        current, used, result = self.item_manager.execute_use(client, state, payloads, current_turn)
        if not result.get("result") == "ok":
            raise UpstreamGameError(f"item use rejected: {result.get('error') or result.get('skip')}")
        return current

    def purchase_skills(self, client, selected_action_ids, current_turn):
        if not selected_action_ids:
            raise ActionValidationError("no skills selected")
        skill_ids = []
        for aid in selected_action_ids:
            if not str(aid).startswith("skill:"):
                raise ActionValidationError(f"not a skill action: {aid!r}")
            skill_ids.append(int(str(aid).split(":", 1)[1]))
        state = self.raw_state or {}
        candidates = self.skill_buyer.candidates_for_ids(state, skill_ids, self.preset or {})
        if len(candidates) != len(set(skill_ids)):
            missing = set(skill_ids) - {c["skill_id"] for c in candidates}
            raise ActionValidationError(f"skills not purchasable in current state: {sorted(missing)}")
        new_state, bought = self.skill_buyer._buy_batch(client, state, candidates, current_turn)
        if bought <= 0:
            result = self.skill_buyer.last_result or {}
            if result.get("result") == "failed":
                raise UpstreamGameError(f"skill purchase failed: {result.get('error')}")
            raise ActionValidationError(f"skill purchase rejected: {result.get('skip') or result}")
        return new_state

    def scenario_call(self, client, action_kind, payload, current_turn):
        adapter = self._current_adapter()
        endpoint = scenario_registry.endpoint_for(adapter.slug, action_kind)
        if not endpoint:
            raise ScenarioEndpointMissing(
                f"{adapter.slug}/{action_kind} not captured in scenario-manifest.json"
            )
        call_payload = dict(payload or {})
        call_payload["current_turn"] = current_turn
        return client.call(endpoint, call_payload)

    def finish_career(self, client):
        current_turn = self._turn_of(self.raw_state)
        state = self.raw_state or {}
        data = (state or {}).get("data") or {}
        if data.get("race_start_info"):
            try:
                client.race_out(current_turn=current_turn)
            except Exception as exc:
                if not any(err in str(exc) for err in ("102", "201", "StateRecoveryError")):
                    raise
        state = self.drain_forced_events(client, state)
        if has_multi_choice_event(((state or {}).get("data") or {}).get("unchecked_event_array") or []):
            return state
        client.finish_career(current_turn=current_turn, is_force_delete=False)
        return state

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _current_adapter(self):
        adapter = None
        if self.raw_state is not None:
            adapter = self._adapter_for(self.raw_state)
        if adapter is None:
            from career_bot.scenarios.base import UnsupportedAdapter
            adapter = UnsupportedAdapter()
        return adapter

    def _adapter_for(self, raw):
        data = (raw or {}).get("data") or {}
        chara = data.get("chara_info") or data.get("single_mode_chara_light") or {}
        scenario_id = int(chara.get("scenario_id") or 0)
        return adapter_for_scenario(scenario_id)

    def _publish(self, raw, preset):
        adapter = self._adapter_for(raw)
        context = {
            "session": self,
            "preset": preset,
            "skill_buyer": self.skill_buyer,
            "race_planner": self.race_planner,
            "item_manager": self.item_manager,
        }
        if adapter is None:
            from career_bot.scenarios.base import UnsupportedAdapter
            adapter = UnsupportedAdapter()
        normalized = adapter.normalize(raw, context)
        self.revision += 1
        normalized["revision"] = self.revision
        normalized["actions"] = adapter.actions(raw, normalized)
        normalized["recommendation"] = adapter.recommend(normalized, preset)
        normalized.setdefault("scenario", {"id": 0, "slug": "unsupported", "name": "Unsupported"})
        self.raw_state = raw
        self.normalized = normalized
        self.adapter = adapter

    def _snapshot_locked(self):
        import copy
        snapshot = copy.deepcopy(self.normalized or {})
        snapshot["revision"] = self.revision
        return snapshot

    def _settle_transport(self, client, raw):
        """Auto-resolve transport-only states: minigame, blocked state, and a
        race already running on load. Stops at continue-offered / multi-choice
        events / finish."""
        data = (raw or {}).get("data") or {}
        chara = data.get("chara_info") or {}
        playing_state = int(chara.get("playing_state") or 1)
        for _ in range(4):
            data = (raw or {}).get("data") or {}
            chara = data.get("chara_info") or {}
            playing_state = int(chara.get("playing_state") or 1)
            events = data.get("unchecked_event_array") or []
            if events and has_multi_choice_event(events):
                return raw
            if "single_mode_finish_common" in data or int(chara.get("state") or 0) == 3:
                return raw
            if playing_state == 6:
                raw = self._minigame_end(client, raw)
                continue
            if is_unrecognized_blocking_state(chara):
                raw = self._fresh_career_state(client)
                continue
            if playing_state in {2, 3, 4}:
                home_info = data.get("home_info") or {}
                race = data.get("race_start_info") or {}
                offered = int(home_info.get("available_continue_num") or 0) + int(home_info.get("available_free_continue_num") or 0)
                if offered <= 0:
                    offered = int(race.get("available_continue_num") or 0) + int(race.get("available_free_continue_num") or 0)
                if offered > 0 and parse_race_rank(raw) > 1:
                    # a continue decision belongs to the user, never to transport
                    return raw
                raw = self.resume_race(client, None)
                continue
            if events:
                raw = self.drain_forced_events(client, raw)
                continue
            return raw
        return raw

    def _minigame_end(self, client, state):
        current_turn = self._turn_of(state)
        try:
            state = client.minigame_end(current_turn=current_turn)
        except Exception:
            state = client.call("single_mode_free/minigame_end", {
                "result": {"result_state": 1, "result_value": 0, "result_detail_array": None},
                "current_turn": current_turn,
            })
        return self.drain_forced_events(client, state)

    def _fresh_career_state(self, client):
        """load_career with bounded relogin retries; used for blocked-state
        recovery and upstream reconciliation."""
        errors = []
        for attempt in range(4):
            try:
                return client.load_career()
            except Exception as exc:
                err = str(exc)
                errors.append(err)
                if any(code in err for code in ("102", "201", "208", "Network error")):
                    if attempt < 3:
                        try:
                            client.login()
                        except Exception:
                            pass
                        continue
                if attempt < 3:
                    time.sleep(1.0)
                    continue
                break
        raise UpstreamGameError("career recovery failed: " + " | ".join(errors[-2:]))

    def _reconcile_failure(self, client, before, exc):
        """After an upstream mutation failure, load the fresh career state. If
        the action committed, publish it; otherwise publish the refreshed old
        state with a typed error. Never blindly retry the mutation."""
        try:
            fresh = client.load_career()
        except Exception:
            fresh = None
        if fresh is not None and self._fingerprint(fresh) != before:
            fresh = self._settle_transport(client, fresh)
            self._publish(fresh, self.preset)
            return {"success": False, "error": "upstream_failed_committed", "detail": str(exc), "state": self._snapshot_locked()}
        if fresh is not None:
            try:
                fresh = self._settle_transport(client, fresh)
                self._publish(fresh, self.preset)
            except Exception:
                pass
        return {"success": False, "error": "upstream_failed", "detail": str(exc), "state": self._snapshot_locked()}

    def _apply_running_style(self, client, state, program_id, preset):
        running_style = preset.get("running_style")
        try:
            running_style = int(running_style)
        except (TypeError, ValueError):
            running_style = 0
        if running_style not in (1, 2, 3, 4):
            return
        chara = ((state or {}).get("data") or {}).get("chara_info") or {}
        horse = ((((state or {}).get("data") or {}).get("race_start_info") or {}).get("race_horse_data") or [{}])[0]
        try:
            current = int(chara.get("race_running_style") or horse.get("running_style") or 0)
        except (TypeError, ValueError):
            current = 0
        if current != running_style:
            client.race_entry(program_id=program_id, current_turn=self._turn_of(state), running_style=running_style, retry_208=0, retry_205=0)

    def _finish_race_transport(self, client, res, current_turn):
        try:
            client.race_end(current_turn=current_turn)
        except Exception as exc:
            if not any(err in str(exc) for err in ("102", "1503")):
                raise
        out = res
        try:
            out = client.race_out(current_turn=current_turn)
        except Exception as exc:
            if not any(err in str(exc) for err in ("102", "1503", "201")):
                raise
        return self.drain_forced_events(client, out)

    def _continue_offered(self, res):
        data = (res or {}).get("data") or {}
        home = data.get("home_info") or {}
        std = int(home.get("available_continue_num") or 0)
        free = int(home.get("available_free_continue_num") or 0)
        if std + free > 0:
            return std + free
        race = data.get("race_start_info") or {}
        return int(race.get("available_continue_num") or 0) + int(race.get("available_free_continue_num") or 0)

    def _exchange(self, client, state, payloads, current_turn):
        data = state.get("data") or {}
        free = data.get("free_data_set") or {}
        budget = int(free.get("coin_num") or free.get("gained_coin_num") or 0)
        valid_rows = {int(row.get("shop_item_id") or 0): row for row in free.get("pick_up_item_info_array") or []}
        owned_by_id = {}
        for row in free.get("user_item_info_array") or []:
            owned_by_id[int(row.get("item_id") or 0)] = int(row.get("num") or row.get("current_num") or row.get("item_num") or 0)
        payload = []
        total_cost = 0
        for item in payloads or []:
            shop_item_id = int(item.get("shop_item_id") or 0)
            if shop_item_id <= 0:
                continue
            row = valid_rows.get(shop_item_id)
            if not row:
                continue
            cost = int(row.get("coin_num") or 0)
            limit_turn = int(row.get("limit_turn") or 0)
            if limit_turn > 0 and limit_turn < current_turn:
                continue
            if int(row.get("item_buy_num") or 0) >= int(row.get("limit_buy_count") or 1):
                continue
            if total_cost + cost > budget:
                continue
            total_cost += cost
            payload.append({
                "shop_item_id": shop_item_id,
                "current_num": owned_by_id.get(int(row.get("item_id") or 0), 0),
            })
        if not payload:
            return state, 0, {"result": "skip", "skip": "preflight_failed"}
        try:
            result = client.exchange_items(payload, current_turn)
        except Exception as exc:
            return state, 0, {"result": "failed", "error": str(exc), "payload": payload}
        merged = self._merge_raw(state, result)
        return merged, len(payload), {"result": "ok", "payload": payload}

    def _merge_raw(self, state, res):
        if not res or not isinstance(res, dict) or "data" not in res:
            return state
        merged = dict(state or {})
        merged["data"] = dict((state or {}).get("data") or {})
        for k, v in (res.get("data") or {}).items():
            if isinstance(v, dict) and isinstance(merged["data"].get(k), dict):
                merged_sub = dict(merged["data"][k])
                for sub_k, sub_v in v.items():
                    if sub_v is not None:
                        merged_sub[sub_k] = sub_v
                merged["data"][k] = merged_sub
            else:
                merged["data"][k] = v
        return merged

    def _fingerprint(self, raw):
        data = (raw or {}).get("data") or {}
        chara = data.get("chara_info") or {}
        return json.dumps({
            "turn": int(chara.get("turn") or 0),
            "playing_state": int(chara.get("playing_state") or 1),
            "vital": int(chara.get("vital") or 0),
            "skill_point": int(chara.get("skill_point") or 0),
            "fans": int(chara.get("fans") or 0),
            "motivation": int(chara.get("motivation") or 0),
        }, sort_keys=True)

    def _turn_of(self, raw):
        data = (raw or {}).get("data") or {}
        chara = data.get("chara_info") or data.get("single_mode_chara_light") or {}
        return int(chara.get("turn") or 0)

    def _vital_of(self, raw):
        data = (raw or {}).get("data") or {}
        chara = data.get("chara_info") or {}
        return int(chara.get("vital") or 0)
