# umamusume-sweepy — Session Handoff Context

> Drop this file in front of a fresh chat to pick up where the previous session
> stopped. It captures repo layout, what the original bot does, what we have
> been adding on top, the current bug state, and the next concrete steps.

---

## 1. Repo Location & How To Run

- **Repo root (Windows)**: `C:\Users\Computer\Documents\GitHub\umamusume-sweepy`
- **OS / shell**: Windows 10/11, PowerShell. The Cursor terminal does NOT
  accept cmd-style flags (`dir /B`), use `Get-ChildItem` / `ls`.
- **Stack**: Python (FastAPI + Uvicorn) backend + static HTML/CSS/JS frontend.
- **Bootstrap (from README.md)**:
  1. `winget install -e --id OpenJS.NodeJS`
  2. `npm i`
  3. `pip install -r requirements.txt`
- **Server entrypoint**: `main.py` (FastAPI app). Default port is `1616`,
  served at `http://127.0.0.1:1616`. (User has also been hitting
  `http://localhost:1616/api/...`.)
- **Game hook**: `frida-server-17.9.11-windows-x86_64.exe` lives at repo root,
  used by `uma_api/client.py` to intercept the official Uma Musume client
  traffic via Frida.

### Required dependencies (`requirements.txt`)

```
fastapi==0.136.1
frida==17.9.1
msgpack==1.1.0
pycryptodome==3.14.1
pydantic==2.13.4
Requests==2.33.1
uvicorn==0.18.2
curl_cffi==0.7.4
```

---

## 2. Original Script Objectives (what the bot was)

`umamusume-sweepy` ("Sweepy / UAT rehashed") is a /vg/-flavored career mode
automation bot for the mobile game **Uma Musume Pretty Derby (DMM/Steam
client)**. From the README:

- It hooks the game with Frida, decodes the msgpack/protobuf traffic, and
  drives the career UI (training / races / events) using a "lobotomized,
  half-ported sweepy decision engine."
- The original heuristic engine just picks the highest-scoring training each
  turn until a career finishes — no looping, no "tempt fate" mode (deliberately
  removed by upstream to avoid drama with Cygames).
- Configuration lived in JSON **presets** under `data/presets/*.json` describing:
  desired running style, learn-skill list, learn-skill blacklist, mandatory
  race schedule (`extra_race_list`), and per-stat scoring weights.
- A small web dashboard (`public/`) was the only UI: pick a preset, click
  start, watch logs.

It supported the URA/Aoharu/Make a New Track ("mant" / Trailblazer) scenarios
through `career_bot/scenarios/*.py`, with `mant.py` being the focus.

---

## 3. What We're Building On Top (this project's targets)

Goal: **grind blue-factor parents in Trailblazer ("mant", scenario_id=4) for
breeding, with a target rank of UG (Ultimate-G, rank id 19) on every run.**
A "blue factor" requires a final stat ≥ 1200; UG is the inheritance threshold
where the trainee enters Ultimate-tier breeding utility. Good runs need ≥ 3★
blue factors with strong skill/white sparks AND a UG rating.

### 3.0 UG strategy (NEW — see `data/uma_guides/UG_STRATEGY.md`)

The canonical knowledge base for what UG actually requires lives at
`data/uma_guides/UG_STRATEGY.md`. It was synthesised from four
auto-captioned English YouTube guides (JackieX strategy guide, MaybeVoid's
UG3→UG4 Taiki Shuttle run, MaybeVoid's first-UG Seiun Sky stream, markillus'
UG Oguri Cap run). Raw transcripts and meta sit under `data/uma_guides/<id>/`.

Five pillars of UG: stat sum (with near-1000 scaling bonus + soft cap at
1200), skill points spent (~2.7 k → 8–10 skills), race wins (34–37 races,
must-win G1s for set bonuses), set bonuses (mile / Triple Crown / etc.), and
aptitudes (B floor, A ideal — fix gaps with parent sparks).

Helper script `scripts/transcribe_uma_guide.py` (`captions` / `run` /
`probe` / `local` subcommands) pulls auto-captions (or Whisper-transcribes
when captions are missing) without touching `mandarin/tools`. It uses
`G:\yt-dlp\yt-dlp.exe` and falls back to `cookies-from-browser firefox`.

### 3.1 `uma.moe` import (DONE — backend wired, UI present)
Pull a public trainer's loadout from <https://uma.moe/trainer/{id}> and turn
it into a Sweepy preset patch:

- `career_bot/uma_moe_importer.py`
  - Fetches via the in-process Cursor browser (CDP) because `uma.moe`'s
    public JSON probe returns 503/404 from random clients.
  - Decodes: running style, trainee `card_id`, support deck, factor
    skill IDs, blue/pink/white star counts, win count, and race plan
    (`programId / 100 → race_id`).
  - Auto-pre-fills `min_stats` / `max_stats` from `STYLE_STAT_PROFILES`
    in `career_bot/presets.py` (see section 4.1).
- Endpoints in `main.py`:
  - `GET /api/uma-moe/trainer/{trainer_id}` — preview patch, no write.
  - `POST /api/uma-moe/import` — preview + merge into preset (create
    new preset if missing). Body: `UmaMoeImportRequest`.
- UI panel exists in `public/index.html` ("uma.moe import"), wired in
  `public/app.js`. Cache-bust is `?v=14`.

### 3.2 Style-aware stat targets (DONE — refined for UG)
Added to `career_bot/presets.py`:

- `STAT_VECTOR_LEN = 5` ordering `[SPD, STA, PWR, GUT, WIT]`.
- `STYLE_STAT_PROFILES` for styles `1=Front Runner`, `2=Pace Chaser`,
  `3=Late Surger`, `4=End Closer`. Each entry is `{"min": [...], "max": [...]}`.
  `min` boosts training of stats below the floor; `max` is the soft cap.
- WIT floors bumped from 400/400/500/500 → 500/500/600/500 to reflect the
  20-energy race cost in Trailblazer and JackieX's "prioritize wit on tight
  energy turns" rule.
- Helper `stat_profile_for_style(style, kind)`.
- `merge_into_preset(..., overwrite_stats=False)` re-seeds stats when running
  style changes, otherwise preserves user-tuned values.
- `career_bot/scenarios/mant.py::_score_command` consumes `min_stats` (bonus
  to under-floor stats) and `max_stats` (penalty / soft-cap once exceeded),
  plus a NEW **+8% near-1000 scaling bonus** when current stat ∈ [820, 1060]
  (per MaybeVoid: "stats closer to 1,000 have more scaling").

### 3.2b UG-targeting preset fields (NEW)
Added to `serialize_preset` (with defaults) in `career_bot/presets.py`:

- `target_rank` (default `RANK_ID_UG = 19`) — rank ladder constant.
- `race_count_target = 36`, `min_races = 30`, `max_races = 40` — race-budget
  knobs (JackieX 34–37 usual, 40–41 aggressive).
- `train_min_total_stat_gain = 40` — "+40 stats per training" rule baseline.
  Drop to 28–32 for low-bonus umas so they actually train their primary stat.
- `reserve_master_hammer_final3 = 3` — keep 3 Master Cleat Hammers for
  turns 70–72 (implemented in `career_bot/items.py`).
- `reserve_megaphone_summer = 2` — keep 2 Empowering Megaphones for each
  summer camp window (implemented in `career_bot/items.py`).
- Default `learn_skill_threshold` lowered `888 → 720` (Trailblazer rank score
  scales hard with number of skills learned). Existing presets keep their
  explicit values; only new presets pick up 720.

`career_bot/scenarios/mant.py::_best_command` now also has a UG guard: when
the best training is meaningfully below `train_min_total_stat_gain * 0.55`
AND `best_score < 0.12` AND we're not in summer camp / final stretch AND a
rest command is available, the bot rests through the junk training. Prevents
burning a turn on +12-stat noise.

### 3.2c Companion presets (NEW — per running style)
Four UG-tuned templates under `data/presets/`, one per running style, each
seeded with `STYLE_STAT_PROFILES` floors + the full UG knob set
(`target_rank = 19`, `race_count_target = 36`, `min_races/max_races`,
`train_min_total_stat_gain`, hammer/megaphone reserves, lowered
`learn_skill_threshold = 720`):

- `top_UG_FR_template.json` — Front Runner (style 1), `min_stats = [1200, 1100, 600, 0, 500]`
- `top_UG_PC_template.json` — Pace Chaser  (style 2), `min_stats = [1200, 900, 1100, 0, 500]`
- `top_UG_LS_template.json` — Late Surger  (style 3), `min_stats = [1200, 700, 1100, 0, 600]`
- `top_UG_EC_template.json` — End Closer   (style 4), `min_stats = [1200, 1100, 1100, 0, 500]`

`data/presets/skygunner_test.json` (Late Surger) was also updated to the
new UG defaults (`learn_skill_threshold = 720`, WIT floor 600, full UG knob
set written out).

### 3.2d Auto-skill-buy disabled (TEMP)
All three skill auto-buy call sites in `career_bot/runner.py` are commented
out with the marker `# UG-AUTO-SKILL-BUY DISABLED`:

- Line ~295: end-of-career force buy
- Line ~313: post-finish retry when SP > 200 (now prints a manual prompt instead)
- Line ~332: mid-career opportunistic buy (now a `pass`)

The `_buy_skills(...)` helper itself (around line 1084) is **kept** so
re-enabling is a 3-line uncomment once `career_bot/skills.py` selection
logic is tightened. Tracked in §6.8.

### 3.2e UG item reserves (DONE)
`career_bot/items.py` now consumes the UG preset reserve fields:

- `reserve_master_hammer_final3`: before senior final-3 it avoids spending
  reserved Master Cleat Hammers, prefers spare Artisan hammers when available,
  and uses Master hammers on pre-race turns 70–72.
- `reserve_megaphone_summer`: before each summer-camp window it holds back
  Empowering Megaphones instead of dumping the last reserved copies on ordinary
  trainings.

### 3.5 TP refill + local Sweepy deck editor (NEW)
- Backend:
  - `POST /api/tp/refill` calls `UmaClient.recovery_tp(...)` and refreshes
    account status.
  - `GET/POST /api/local-decks` stores local deck definitions in
    `data/decks.json`.
- UI:
  - The TP pill has a **REFILL** action when TP is below max.
  - The Decks section has a local-only **Sweepy deck editor**. It shows owned
    support cards with rarity/type/LB/EXP, lets the user save exactly five
    owned supports as a local deck, and uses that deck for Start. This does
    **not** upload or edit in-game deck slots; the friend support remains
    selected separately.
  - uma.moe trainer search now has sort controls for score, G1 wins, and
    career/update date, with ASC/DESC toggle.
  - Imported race schedules are sourced from the selected uma.moe trainer's
    `inheritance.race_results`; the importer replaces `extra_race_list` with
    matching local program IDs, drops any race ids missing from `race_map`, and
    now prunes lower-priority donor races to ~33 pre-finals races so total
    career count lands near 36 after Twinkle Star finals.
  - After a failed Mejiro Dober copy route (A+ / 13,404 / 42 races), the local
    `top_UG_LS_Mejiro_Dober.json` preset was trimmed from 40 listed races to
    33 and `max_races` lowered to 37.
  - `career_bot/items.py` item heuristics were tightened: fewer Reset Whistles
    hoarded, higher energy recovery threshold, Royal Kale used after normal
    energy items, lower megaphone use thresholds, late Empowering Megaphone
    spending, and pre-summer Empowering Megaphone purchase priority.

### 3.3 Friend Veteran "borrow as parent" + Runtime Advisor (DONE)
Game mechanic: alongside support-card borrowing, you can borrow a friend's
*finished veteran trainee* as a rental parent for inheritance. The data comes
back in the `pre_single_mode/index` API response.

- Confirmed live shape (after instrumenting `/api/friends/raw`):
  - Container keys: `succession_trained_chara_data` and
    `event_succession_trained_chara_data`.
  - Array inside each: `succession_trained_chara_array` (35 items on the
    user's account).
  - Each row exposes: `viewer_id`, `trained_chara_id`, `card_id`, `rank`,
    `rank_score`, `scenario_id`, `running_style`, `talent_level`,
    final stats, `factor_id_array`, `succession_chara_array` (parent
    lineage with `position_id` 10/20 = direct parents), `support_card_list`
    (deck used for that veteran), and `win_saddle_id_array` (race wins).
- Implemented in `main.py`:
  - `FRIEND_VETERAN_KEYS = ("succession_trained_chara_array",)`
  - `FRIEND_VETERAN_CONTAINER_KEYS = ("succession_trained_chara_data",
    "event_succession_trained_chara_data")`
  - `_extract_veteran_rows(data)` — walks both containers + defensive top-level.
  - `normalize_friend_veterans(data)` — joins each veteran with its owner's
    `summary_user_info_array`, decodes factors via `data/factor_map.json`,
    extracts direct-parent `card_id`s and the support deck used to raise the
    veteran, computes deck type counts/archetype (`Guts meta`, `Speed/Power`,
    etc.), then sorts by `rank_score`. Returns `(list, source_tag)`.
- Endpoints:
  - `POST /api/career/friends` — primary fetch (also seeds support cards).
  - `GET  /api/friends/raw` — debug dump: top-level keys, shape, raw sample
    of first 6 keys, `veterans_found`, `veterans_source`,
    `veteran_field_candidates_tried`.
  - `GET  /api/friends/veterans` — normalized list only.
  - `GET  /api/friends/manage`, `POST /api/friends/follow`,
    `POST /api/friends/unfollow` — relationship management from the dashboard.
    The follow/unfollow client wrappers try known likely game endpoint names and
    surface any live API failure in the UI.
  - `POST /api/advisor/recommendations` — scores owned + borrowable parents for
    the selected trainee/running style without auto-picking.
- Preset schema (in `career_bot/presets.py`) gained:
  - `rental_chara_viewer_id` — friend's `viewer_id`.
  - `rental_chara_id` — the game's `trained_chara_id` of the veteran.
- API request models (in `main.py`): `StartCareerRequest` and
  `RunCareerRequest` carry `rental_viewer_id` / `rental_chara_id` and are
  forwarded into `start_career`'s `pre_single_mode/start` payload.
- UI: `public/index.html` has a "FRIEND PARENTS (BORROW)" section,
  `public/app.js` shows stats, rank, factors, parent lineage, and now the
  support deck used to raise that veteran. Friend support cards show
  following/follower badges plus follow/unfollow actions. The start panel shows
  a Runtime Advisor that highlights strong parent candidates and selected-parent
  warnings, but the user still picks manually.
- New runtime-only script behavior:
  - `career_bot/advisor.py` centralizes deck archetype detection, parent scoring,
    and `prepare_runtime_preset(...)`.
  - `main.py::run_career` copies the hydrated preset, applies deck type counts,
    then applies the runtime advisor overlay before starting `CareerRunner`.
    Existing preset JSON is not rewritten for deck/parent/meta experiments.
  - Guts-heavy decks raise the in-memory GUT floor and relax the junk-training
    threshold; low-speed decks also relax that threshold.
  - `career_bot/races.py` now respects an in-memory `max_races` pre-finals
    budget so over-dense imported donor routes stop crowding late training.

### 3.4 New presets shipped
Created under `data/presets/`:

- `skygunner_test.json` — Late Surger (style 3) tuned to push 1200 SPD +
  ★3 blue factor in Trailblazer.
- `tokai_teio.json` — Tokai Teio (original card).
- Plus reference templates: `top_FR_template.json`, `top_PC_Zoi.json`,
  `top_LS_hinacorn.json`, `top_EC_Newbielol2.json`, `TEST.json`, `1.json`,
  `xguri parent.json`.

---

## 4. File Map (only the files this project touches)

### Backend (Python)

| File | Role | Notes |
|---|---|---|
| `main.py` | FastAPI app, all HTTP routes, in-memory session state | Added uma.moe + friends-veterans endpoints, rental fields in start/run models, relationship endpoints, advisor endpoint, runtime preset overlay |
| `career_bot/advisor.py` | Runtime deck/parent advisor | Scores parent candidates, labels deck archetypes, and prepares in-memory preset overlays without writing JSON |
| `career_bot/presets.py` | Preset schema, normalization, merge logic | Added `STYLE_STAT_PROFILES`, `stat_profile_for_style`, `rental_chara_viewer_id`, `rental_chara_id`, stat re-seed rules |
| `career_bot/uma_moe_importer.py` | Pull trainer JSON from uma.moe and build a preset patch | Uses CDP browser fetch; auto-seeds stat profile; **needs fix at L348–349** (see §6) |
| `career_bot/scenarios/mant.py` | Trailblazer (mant) training decision logic | `_score_command` now reads `min_stats`/`max_stats` |
| `career_bot/scenarios/base.py` | Scenario base interface | Untouched (for reference) |
| `career_bot/runner.py` | Orchestrator that drives a career turn-by-turn | Receives rental params from `main.py` |
| `career_bot/races.py`, `events.py`, `skills.py`, `items.py`, `report.py`, `delay.py`, `master_data.py` | Domain helpers | `races.py` now observes runtime max-race budget before taking optional donor races |
| `uma_api/client.py` | Frida-backed HTTP client into the live game | Added follow/unfollow wrapper candidates |
| `scripts/generate_master_data.py` | One-shot dumper for master data tables | Untouched |

### Frontend (`public/`)

| File | Role | Notes |
|---|---|---|
| `public/index.html` | Dashboard layout | Added min/max stat editors, uma.moe import panel, "FRIEND PARENTS (BORROW)" picker, Runtime Advisor panel. Cache-bust `?v=25` |
| `public/app.js` | All dashboard JS | Added stat editor read/write, uma.moe import flow, friend-veteran deck strips, follow/unfollow UI, Runtime Advisor recommendations |
| `public/styles.css` | Styles for new editors / panels | Includes relationship badges, deck strips, advisor panel |
| `public/assets/data/uma_race_data.json`, `uma_character_data.json` | Static lookup tables surfaced to the UI | |

### Data / config (`data/`)

| Path | Role |
|---|---|
| `data/presets/*.json` | Per-build configs (see §3.4) |
| `data/chara_list.json` | `card_id → chara name` map. **It's a dict, not a list** — earlier scripts assumed list and broke |
| `data/factor_map.json` | Factor IDs → human names (skill / blue / pink). Needed for `get_factors()` in `main.py` |
| `data/race_map.json` | `program_id / race_id → race name` |
| `data/skill_data.json` | Skill metadata for scoring |
| `data/support_list.json` | Support card metadata |
| `data/event_outcomes.json` | Event branch outcomes |

### Root-level

| File | Role |
|---|---|
| `requirements.txt` | Python deps (pinned, see §1) |
| `package.json`, `package-lock.json` | Node deps (frontend only) |
| `frida-server-17.9.11-windows-x86_64.exe` | Frida server binary for hooking the game on Windows |
| `settings.json` | Local dashboard prefs |
| `README.md` | Upstream notes + screenshots |
| `context.md` | **This file** |

---

## 5. API Surface (what the dashboard / external scripts call)

Selected endpoints (full list in `main.py`):

- `GET  /api/master-data/status`, `POST /api/master-data/path`, `POST /api/master-data/generate`
- `GET  /api/presets`, `POST /api/presets`, `POST /api/presets/delete`, `POST /api/presets/save_races`
- `GET  /api/skills`
- `GET  /api/uma-moe/trainer/{trainer_id}` — preview uma.moe import
- `POST /api/uma-moe/import` — merge uma.moe into a preset
- `POST /api/login`, `GET /api/session`, `POST /api/selection`, `POST /api/logout`
- `POST /api/career/start`, `POST /api/career/run`
- `GET  /api/career/runner`, `POST /api/career/runner/stop`, `POST /api/career/runner/burn_clocks`
- `POST /api/career/friends` — refresh support + veterans cache from live game
- `GET  /api/friends/raw` — **debug** dump of cached `pre_single_mode/index`
- `GET  /api/friends/veterans` — normalized veterans list
- `GET  /api/friends/manage`, `POST /api/friends/follow`, `POST /api/friends/unfollow`
- `POST /api/advisor/recommendations`
- `POST /api/career/action`, `POST /api/career/delete`
- `GET  /api/debug/start_state`, `GET /api/debug/raw_load`
- Static: `GET /`, `/styles.css`, `/app.js`, `/sweep.png`, `/broom.png`,
  `/assets/data/{file_name}`, `/races/{file_name}`, `/api/images/{image_name}`

---

## 6. Known Issues & Pending Tasks (start here next session)

### 6.1 ~~Verify the friend-veteran extractor loads veterans~~ DONE
User restarted uvicorn and re-hit `POST /api/career/friends` then
`GET /api/friends/raw`. Response now reports
`veterans_found: 35` and `veterans_source = "succession_trained_chara_array"`.
So the backend extractor (`_extract_veteran_rows` +
`normalize_friend_veterans`) is working correctly.

### 6.2 ~~Don't prefill `rental_chara_id` from `uma.moe`~~ DONE
Fixed in `career_bot/uma_moe_importer.py::build_preset_patch`:

- `rental_chara_id` is now hard-coded to `0` in the patch (was
  `inheritance_id`, which is **not** the game's `trained_chara_id`).
- The inheritance_id is preserved as `uma_moe_inheritance_id` for
  informational use.
- `rental_chara_card_id` is now also propagated through `merge_into_preset`
  so the UI has a hint to auto-resolve the matching veteran.
- The merge function's `if patch[key]` truthiness check leaves any
  user-set `rental_chara_id` untouched when the patch carries `0`.

### 6.3 ~~UI: surface the rich veteran info in the picker~~ DONE
`public/app.js::renderFriendVeterans` now draws each borrowable veteran
with:

- A **stat strip** (`vet-stat`) color-coded by blue-factor tier:
  `blue3` (≥1200, ★3 candidate), `blue2` (≥1100), `blue1` (≥600), `white`.
- A **rank badge** in the top-right (`G..UG+..US+`) tier-tinted
  (`vet-rank-low/mid/high/ex`).
- **Direct-parent portraits** in the top-left via `parent_card_ids` →
  `/api/images/{card_id}.png`.
- A **factor chip row** (`vet-factor`) covering stat / aptitude / unique /
  skill factors with star count, max 5 chips.
- Kicker line shows trainer name · scenario · running style · rank score.

Styles live in `public/styles.css` under `/* === Friend Veteran ... ===` */`,
the grid is widened via `#friend-vet-grid { --grid-min: 14rem }` and the
card aspect ratio is `3 / 4` to fit the new content.

`applyPresetRentalSelection` is now a 3-tier resolver:
1. exact `(viewer_id, trained_chara_id)`,
2. `(viewer_id, card_id hint)` for fresh uma.moe imports — picks the
   trainer's highest `rank_score` veteran on that card,
3. `card_id` only — picks any friend running that chara.
When it resolves a match via tier 2/3 it auto-writes the real
`trained_chara_id` back into the preset.

Cache-bust was bumped to `?v=15` for both `app.js` and `styles.css`.

### 6.4 🔴 ACTIVE BUG — Friend veterans disappear after a browser refresh
**Symptom (user words)**: *"It works when it first load, but when you
refresh it, it wont show again."*

**Confirmed via JSON dump**: `GET /api/friends/raw` after the refresh still
returns `veterans_found: 35`, so the **backend has the data**. The veterans
just never make it into the second-load response.

**Root cause** — caching short-circuit in
`main.py::get_friend_list` (`POST /api/career/friends`, lines **1607–1655**):

```python
# main.py L1621-1627 — the offending early-return:
if not req.exclude_viewer_ids and active_dashboard_data is not None \
        and "friends" in active_dashboard_data:
    return {
        "success": True,
        "friends": active_dashboard_data["friends"],
        "exclude_viewer_ids": active_dashboard_data.get("friendExcludeIds", []),
        "source": "cache",
    }
    # ❌ no "veterans" / "veterans_source" — frontend then nukes the picker
```

The frontend at `public/app.js::loadFriendVeterans` L2253–L2260 calls
this endpoint on every page load:

```js
const data = await apiJson('/api/career/friends', {
    method: 'POST',
    body: JSON.stringify({ exclude_viewer_ids: [] })  // ← triggers cache path
});
dashData.friendVeterans = data.veterans || [];        // ← becomes []
```

Because the cached response omits `veterans`, `dashData.friendVeterans`
gets wiped to `[]` and the picker renders empty even though
`active_dashboard_data["friendVeterans"]` on the server is populated.

**Fix plan (do this next session)**:

1. **`main.py`** — extend the cache early-return to also surface
   veterans from `active_dashboard_data`:

   ```python
   if not req.exclude_viewer_ids and not req.force_refresh \
           and active_dashboard_data is not None \
           and "friends" in active_dashboard_data:
       return {
           "success": True,
           "friends": active_dashboard_data["friends"],
           "exclude_viewer_ids": active_dashboard_data.get("friendExcludeIds", []),
           "source": "cache",
           "veterans": active_dashboard_data.get("friendVeterans", []),
           "veterans_source": active_dashboard_data.get(
               "friendVeteransSource", "cache"
           ),
       }
   ```

2. **`main.py::FriendListRequest`** (L905–906) — add an opt-in bypass:

   ```python
   class FriendListRequest(BaseModel):
       exclude_viewer_ids: list[int] = []
       force_refresh: bool = False
   ```

3. **`public/app.js::loadFriendVeterans`** (L2253) — pass
   `force_refresh: refresh` so the "REFRESH" button hits the live
   `pre_single_mode/index` while initial loads keep using the cache:

   ```js
   const data = await apiJson('/api/career/friends', {
       method: 'POST',
       body: JSON.stringify({ exclude_viewer_ids: [], force_refresh: refresh })
   });
   ```

4. Bump cache-bust to `?v=16` in `public/index.html` for `app.js` /
   `styles.css` so the browser actually picks up the new JS.

5. **Verify**:
   - Hard-refresh dashboard → veterans show on first load.
   - Soft-refresh (F5) → veterans STILL show, response `source: "cache"`
     with non-empty `veterans`.
   - Click REFRESH → backend logs a fresh `pre_single_mode/index` call,
     response `source` is *not* `"cache"`.

### 6.5 Pending — end-to-end borrow test
After 6.4 lands, run a full smoke test:

- Pick a veteran in the new rich picker.
- Confirm `selection.rentalParent` is set and written back into the active
  preset's `rental_chara_viewer_id` + `rental_chara_id`.
- Start a Trailblazer career and inspect the request body that hits
  `pre_single_mode/start` — it must carry
  `rental_trained_chara_id` + `rental_viewer_id` matching the selected
  veteran (logged from `start_career` in `main.py` L1137).
- Confirm the in-game inheritance screen actually shows the borrowed
  parent slotted in.

### 6.8 Pending — re-enable auto-skill-buy after tightening selection
Skill auto-buy was disabled in `career_bot/runner.py` (3 call sites, marker
`UG-AUTO-SKILL-BUY DISABLED`) because the picker was buying suboptimal
skills. To bring it back without regression:

1. Read `career_bot/skills.py::SkillBuyer.buy` + helpers. Identify the
   ranking step that decides which skills land in `last_selected`.
2. Add a guard so only skills from the preset's `learn_skill_list` are
   *ever* bought when `force=False` (mid-career); for `force=True`
   (end-of-career) allow the picker to expand into rainbow/inheritable
   skills but still honour `learn_skill_blacklist` strictly.
3. Verify the candidate scoring uses `learn_skill_threshold` (lowered to
   720 in this session) as a *minimum* SP-per-skill bar — anything below
   that gets dropped.
4. Then uncomment the three lines marked `# state = self._buy_skills(...)`
   in `runner.py` (around L295, L313, L332). Delete the explanatory
   comment block when re-enabling.

While auto-buy is off, the runner will leave SP unspent and the user has
to buy skills manually before pressing the finish-confirm in-game.

### 6.7 ~~items.py reserve enforcement (UG strategy follow-up)~~ DONE
`career_bot/items.py` now respects `reserve_master_hammer_final3` and
`reserve_megaphone_summer`. The remaining validation is empirical: run a
Trailblazer career and watch item logs to confirm hammers are saved for
turns 70–72 and Empowering Megaphones are still available entering summer camp.

### 6.6 Pending (low priority) — auth persistence across server restarts
User asked: *"can we make it so the AUTH persist after the server is
restarted somehow?"* — flagged as nice-to-have, not blocking.

**Feasibility snapshot (from reading `main.py::login` L1183–L1244 and
`uma_api/client.py`)**:

- Login currently requires *fresh in-game auth* captured by Frida every
  time (`has_fresh_auth_config(cfg)` is enforced and raises if stale).
- The Steam session ticket (`steam_session_ticket`) is acquired via
  `get_ticket(username, password, code)`. Steam app tickets are valid
  only for a short window (minutes, not hours) and consumed on first use.
- `pending_game_auth_config` is rebuilt by the Frida hook on each
  game launch.

So **full unattended persistence is not realistic** without re-architecting
auth (would need re-issuing Steam tickets server-side and re-hooking
Frida on game cold start). What we *could* do incrementally:

- **(easy)** Persist the last `active_account` summary + last picked
  preset to a `data/.session_cache.json` so the dashboard re-opens with
  the right context on restart, even though `active_client` is `None`
  until the user re-logs.
- **(medium)** Cache the in-game `viewer_id → account` mapping so the
  user doesn't have to re-select a target account.
- **(out of scope for now)** Real auto-relogin would need:
  refresh Steam ticket → re-trigger Frida capture → call
  `/api/login` headlessly. Not worth the complexity until the rest of
  the loop is stable.

Recommend keeping this parked until §6.4 + §6.5 are green.

---

## 7. Next Steps (concrete TODO for the next session, in order)

1. **Fix the cache-omits-veterans bug** in `main.py::get_friend_list` —
   add `veterans` / `veterans_source` to the cached early-return.
   (§6.4 step 1)
2. **Add `force_refresh`** to `FriendListRequest` and wire the
   "REFRESH" button to send it. (§6.4 steps 2–3)
3. **Bump frontend cache-bust** to `?v=16` and reload the dashboard.
   (§6.4 step 4)
4. **Smoke-test refresh persistence** (§6.4 step 5).
5. **End-to-end borrow test** — pick a veteran, start a Trailblazer
   career, confirm rental fields land in `pre_single_mode/start`.
   (§6.5)
6. **(stretch)** Add a tiny `data/.session_cache.json` that remembers
   last selected preset + last `viewer_id`, so a restart at least
   preserves UI context. (§6.6 easy bullet)
7. **Run an actual Trailblazer career** with `skygunner_test.json` (now
   UG-tuned), one of the four `top_UG_<style>_template.json` files, and
   the picked veteran. Validate end stats land near `min_stats` (SPD ≥ 1200
   for the ★3 blue), that the final `rank_score` clears ~20,500 (UG
   threshold), and that the picker resolution logic stays stable across
   the run. **Remember to manually buy skills before the finish-confirm
   while §6.8 is active.**
8. **Tighten skills.py selection logic and re-enable auto-buy** per §6.8.
9. **Validate item reserves in a real Trailblazer career** — confirm hammers
   are saved for turns 70–72 and Empowering Megaphones survive into summer camp.
10. **(stretch)** Capture observed `rank_score` per finished run into a small
    `data/career_results.jsonl` so we can correlate `rank_score → rank_id`
    thresholds empirically and tighten `RANK_ID_*` constants in
    `career_bot/presets.py`.

---

## 8. Important Gotchas / Lessons Learned

- **`chara_list.json` is a dict** keyed by stringified `card_id`. Treating
  it as a list (as `scan_uma_moe_trainers.py` originally did) crashes.
- **`uma.moe` requires browser-style fetch** (CDP). Direct `requests.get`
  returns 503/404. Already wired via Cursor MCP browser.
- **`programId / 100 → race_id`**: when decoding uma.moe race plans, cast
  `programId` to `int` first or `dict.get` lookup misses.
- **PowerShell vs cmd**: don't use `dir /B`; use `Get-ChildItem` or the
  Glob tool. PowerShell also needs `sys.stdout.reconfigure(encoding="utf-8")`
  before printing Unicode trainer names.
- **`STAT_VECTOR_LEN = 5`** order is `[SPD, STA, PWR, GUT, WIT]`. Don't
  reorder — `mant.py::_score_command` and the JSON presets all assume this.
- **Game thresholds for blue factors**: ≥1200 stat = ★3 blue,
  1100–1199 = ★2, 600–1099 = ★1, <600 = white spark only. This is why
  `STYLE_STAT_PROFILES` floors are set the way they are.
- **The user runs the server locally** at `127.0.0.1:1616` /
  `localhost:1616`. If output looks stale, suspect that the server wasn't
  restarted after a code change.

---

## 9. Useful Links

- Game: <https://umamusume.com/>
- Public trainer DB used for imports: <https://uma.moe/>
  - Trainer page pattern: `https://uma.moe/trainer/<trainer_id>`
- GameTora (skills / events reference): <https://gametora.com/umamusume>
- Sweepy upstream / inspiration: see screenshots in `README.md`
- Frida: <https://frida.re/> (Frida server binary in repo root)
- FastAPI: <https://fastapi.tiangolo.com/>

---

## 10. Quick "where do I look" cheat sheet

- "How does a turn get scored?" → `career_bot/scenarios/mant.py::_score_command`
- "Where's the UG-targeted strategy synthesis?" →
  `data/uma_guides/UG_STRATEGY.md` (transcripts: `data/uma_guides/<vid>/`)
- "How do I transcribe a new guide video?" →
  `python scripts/transcribe_uma_guide.py captions <url>` (fast — uses
  YouTube auto-CC; falls back to faster-whisper via `run` subcommand)
- "What does the dashboard send when I press Start?" →
  `main.py::StartCareerRequest` + `POST /api/career/start` →
  `career_bot/runner.py`
- "Where do I add a new preset field?" →
  `career_bot/presets.py` (normalize + merge) and the matching reader in
  `public/app.js`
- "Why do veterans vanish after a refresh?" → §6.4 (cache early-return
  in `main.py::get_friend_list` L1621–1627 omits `veterans`).
- "Where's the live veteran extractor logic?" → `main.py::_extract_veteran_rows`
  + `normalize_friend_veterans`.
- "How is uma.moe data converted?" →
  `career_bot/uma_moe_importer.py::build_preset_patch`
- "Where's the friend-veteran raw shape?" →
  `GET /api/friends/raw` after `POST /api/career/friends`
- "Why can't I make auth survive a restart?" → §6.6 (Steam ticket TTL +
  Frida-captured config are both one-shot).

