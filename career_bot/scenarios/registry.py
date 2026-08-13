"""Literal scenario adapter registry keyed by the captured
scenario-manifest.json. Unknown scenario ids fail closed as unsupported rather
than falling back to any scenario.

The manifest — never guessed public mappings — decides scenario ids, names,
and per-action endpoint names. When the manifest is missing (e.g. in a fresh
checkout before fixture generation) a minimal built-in table carries the
capture-derived ids already committed; regenerating the manifest overwrites
it.
"""

from __future__ import annotations

import json
from pathlib import Path

from career_bot.capture import KNOWN_ACTION_SHAPES, manifest_path

# Fallback ids recorded from the committed fixture manifest. These are
# capture-derived, not public-map guesses: the existing Trackblazer code and
# presets already use scenario_id 4 everywhere, and the fixture files carry
# the remaining ids. `python -m career_bot.capture manifest` is authoritative
# and overrides this table at runtime.
BUILTIN_MANIFEST = {
    "ura": {"id": 1, "name": "URA Finale"},
    "unity": {"id": 2, "name": "Unity Cup"},
    "trackblazer": {"id": 4, "name": "Trackblazer"},
    "grand_concert": {"id": 3, "name": "Our Grand Concert"},
}


class _Registry:
    def __init__(self):
        self._manifest = None
        self._adapters = {}
        self._load()

    def _load(self):
        path = manifest_path()
        if path.exists():
            try:
                self._manifest = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self._manifest = None
        if self._manifest is None:
            self._manifest = {
                "scenarios": {
                    slug: {
                        "id": info["id"],
                        "slug": slug,
                        "name": info["name"],
                        "endpoints": [],
                        "discriminators": [],
                        "state_kinds": [],
                        "action_shapes": {},
                        "fixture_files": [],
                    }
                    for slug, info in BUILTIN_MANIFEST.items()
                },
                "action_shapes": dict(KNOWN_ACTION_SHAPES),
            }

    def reload(self):
        self._load()

    @property
    def scenarios(self):
        return self._manifest.get("scenarios") or {}

    def scenario_ids(self):
        return {slug: int(info.get("id") or 0) for slug, info in self.scenarios.items()}

    def id_to_slug(self):
        result = {}
        for slug, info in self.scenarios.items():
            result[int(info.get("id") or 0)] = slug
        return result

    def scenario_info(self, slug):
        info = self.scenarios.get(slug)
        if not info:
            return None
        return {
            "id": int(info.get("id") or 0),
            "slug": slug,
            "name": info.get("name") or slug.replace("_", " ").title(),
        }

    def scenario_by_id(self, scenario_id):
        for slug, info in self.scenarios.items():
            if int(info.get("id") or 0) == int(scenario_id or 0):
                return self.scenario_info(slug)
        return None

    def endpoint_for(self, slug, action_kind):
        """Manifest-authoritative endpoint for an action kind, or None when
        the fixture matrix has not captured it (adapter must fail closed)."""
        info = self.scenarios.get(slug) or {}
        shapes = info.get("action_shapes") or {}
        shape = shapes.get(action_kind)
        if shape and shape.get("endpoint"):
            return shape["endpoint"]
        return None

    def register(self, adapter):
        self._adapters[adapter.slug] = adapter

    def adapter_for(self, scenario_id):
        slug = self.id_to_slug().get(int(scenario_id or 0))
        if slug:
            return self._adapters.get(slug)
        return None


registry = _Registry()


def register_adapter(adapter):
    registry.register(adapter)


def adapter_for_scenario(scenario_id):
    return registry.adapter_for(scenario_id)


def supported_scenarios():
    """[{id, slug, name}] rows from the captured registry, sorted by id."""
    rows = []
    for slug, info in sorted(registry.scenarios.items(), key=lambda item: int((item[1] or {}).get("id") or 0)):
        rows.append({
            "id": int(info.get("id") or 0),
            "slug": slug,
            "name": info.get("name") or slug.replace("_", " ").title(),
        })
    return rows
