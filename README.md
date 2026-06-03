# umamusume-sweepy-enhanced

> Enhanced fork of [SweepTosher/umamusume-sweepy](https://github.com/SweepTosher/umamusume-sweepy)
> focused on grinding stable **S-Rank minimum / stable high stats** Trailblazer ("mant") careers for blue-factor
> parents, with a much richer dashboard for deck/parent management.

The original upstream is a `/vg/` Sweepy bot that drives Uma Musume Pretty
Derby careers via a Frida hook + msgpack/protobuf intercept. This fork keeps
that engine intact and layers on a calibrated decision/preset stack plus a
heavily expanded web UI.

---

## What's new in this fork

### 1. High-Stat & S-Rank Targeting (UG is current aspirational ceiling)

> [!NOTE]
> **Realistic Calibration Target**: While the presets and strategy support pushing towards the Ultimate (UG) tier, achieving UG reliably is far-fetched for the current version without maxed setups. The realistic, stable focus is calibrated for **S-Rank minimum** and high stats to build solid parent grids.

- Strategy framework at [`data/uma_guides/UG_STRATEGY.md`](data/uma_guides/UG_STRATEGY.md),
  synthesised from public English guides. Documents the rank ladder
  (UG = rank id `19`, US+ = `34`), the five `rank_score` pillars
  (stats, skills, race wins, set bonuses, aptitudes), and the cadences
  the bot now follows.
- New UG preset fields in `career_bot/presets.py`:
  - `target_rank` (default `RANK_ID_UG = 19`)
  - `race_count_target = 36`, `min_races = 30`, `max_races = 40`
  - `train_min_total_stat_gain = 40` (+40-stats-per-training rule)
  - `reserve_master_hammer_final3 = 3` (hold hammers for turns 70–72)
  - `reserve_megaphone_summer = 2` (hold megaphones for each summer camp)
  - `learn_skill_threshold` default lowered `888 → 720`.
- Style-aware stat targets (`STYLE_STAT_PROFILES` for Front Runner / Pace
  Chaser / Late Surger / End Closer) with bumped WIT floors and a
  near-1000 scaling bonus in the trainer scoring inside
  `career_bot/scenarios/mant.py`.
- UG-tuned per-style templates under `data/presets/`:
  - `top_UG_FR_template.json`, `top_UG_PC_template.json`,
    `top_UG_LS_template.json`, `top_UG_EC_template.json`,
    `top_FR_template.json`.
- UG item reserves implemented in `career_bot/items.py` (Master Cleat
  Hammers reserved for final 3, Empowering Megaphones reserved for summer
  camps, smarter Vita/Royal-Kale ordering, fewer hoarded Reset Whistles,
  pre-summer Empowering Megaphone purchase priority).
- Race-budget enforcement in `career_bot/races.py` so imported donor routes
  cannot crowd out late-game training.

### 2. Runtime advisor (no preset rewrites needed)

- New `career_bot/advisor.py` module centralises:
  - Deck-archetype detection (e.g. "Guts meta", "Speed/Power").
  - Parent candidate scoring (blue stars, rank score, lineage legality).
  - `prepare_runtime_preset(...)` — in-memory overlay that tunes
    `min_stats` and `train_min_total_stat_gain` per run.
- `main.py::run_career` deep-copies the hydrated preset, applies the
  advisor overlay, and only the in-memory copy is mutated — your JSON
  presets stay clean.
- New API: `POST /api/advisor/recommendations` exposes the parent
  scoring to the dashboard so you can see _why_ a given parent helps or
  hurts a given trainee + style.

### 3. uma.moe trainer import

- `career_bot/uma_moe_importer.py` pulls a public trainer's loadout from
  `https://uma.moe/trainer/{id}` via the in-process Cursor CDP browser
  (the public JSON endpoint 503s most of the time).
- Decodes running style, trainee `card_id`, support deck, factor sparks,
  blue/pink/white star counts, win count, and the race plan
  (`programId / 100 → race_id`). Auto-seeds `min_stats` / `max_stats`
  from `STYLE_STAT_PROFILES`.
- `prune_race_plan_for_ug(...)` trims donor race lists to ≈33 pre-finals
  races (preserving every G1 and the chronological order of others) so
  the bot doesn't lose training turns to over-dense schedules.
- Endpoints:
  - `GET /api/uma-moe/trainer/{trainer_id}` — preview patch, no write.
  - `POST /api/uma-moe/import` — preview + merge. Defaults to
    `create_only=true` so trainer imports never silently overwrite an
    existing template; the dashboard suggests a timestamped preset name.
- UI: dedicated "uma.moe import" panel with search-by-character, sort
  controls (score / G1 wins / career date) and ASC/DESC toggle.

### 4. Friend veteran "borrow as parent" + relationship management

- `main.py::normalize_friend_veterans(...)` now also returns each
  veteran's full **support deck used to raise that trainee** and a
  computed deck-type archetype.
- Endpoints:
  - `POST /api/career/friends` — primary fetch (also seeds support cards).
  - `GET /api/friends/raw`, `GET /api/friends/veterans` — debug + clean
    veteran list.
  - `GET /api/friends/manage`, `POST /api/friends/follow`,
    `POST /api/friends/unfollow` — relationship management from the
    dashboard. The follow/unfollow client wrappers in `uma_api/client.py`
    probe known game endpoint names and surface live API failures.
- Preset schema gained `rental_chara_viewer_id` + `rental_chara_id`, and
  the start-career requests forward them into the
  `pre_single_mode/start` payload so you actually inherit from the
  rented veteran.
- UI: "FRIEND PARENTS (BORROW)" + "FRIEND SUPPORTS" panels show stats,
  rank, factors, parent lineage and the deck used to raise each veteran,
  plus relationship badges (mutual / following / follower / not followed)
  with follow/unfollow buttons directly on each card.
- New **Friend Manage** panel: paste any trainer/friend ID, hit
  **Preview** (checks local cache first, then uma.moe), then
  **Follow**, and see your loaded relationships with one-click unfollow.

### 5. Local Sweepy deck editor + TP refill

- `POST /api/tp/refill` calls `UmaClient.recovery_tp(...)` and refreshes
  account status. A **REFILL** button appears on the TP pill whenever
  TP is below max.
- `GET/POST /api/local-decks` stores local deck definitions in
  `data/decks.json` (untracked — see `.gitignore`).
- UI: the Decks section gets a **LOCAL** badge + **EDIT** button per
  local deck. The editor lists every owned support card with
  rarity / type / LB / EXP and lets you snapshot any five owned cards
  into a re-usable Sweepy deck. This does **not** touch in-game deck
  slots; friend support is still selected separately.

### 6. Auto-skill-buy temporarily disabled ( maybe will implement a UI for buying skills similar to the game version, not a priority )

All three skill auto-buy call sites in `career_bot/runner.py` are
commented out with the marker `# UG-AUTO-SKILL-BUY DISABLED`. The
underlying `_buy_skills(...)` helper is kept so re-enabling is a
3-line uncomment once selection logic is tightened.

### 7. New strategy / handoff docs ( will be updated ) 

- [`data/uma_guides/UG_STRATEGY.md`](data/uma_guides/UG_STRATEGY.md) —
  calibration strategy framework for high stats and S-Rank targeting.
- [`context.md`](context.md) — full session handoff context covering
  repo layout, current bug state, and pending work.
- [`scripts/transcribe_uma_guide.py`](scripts/transcribe_uma_guide.py) —
  helper to pull auto-captions / Whisper transcripts from YouTube guides
  (used to build `UG_STRATEGY.md`).

---

## Requirements

### Native / OS
- Windows 10/11 (the upstream's Frida hook + paths assume Windows).
- The DMM/Steam Uma Musume client installed and running while the bot
  works. `frida-server-17.9.11-windows-x86_64.exe` (NOT shipped in this
  repo — drop your own copy at the repo root, see `.gitignore`).
- PowerShell or cmd for bootstrap.

### Tooling
- **Node.js** — `winget install -e --id OpenJS.NodeJS`, then `npm i`.
- **Python 3.11+** — `pip install -r requirements.txt`.
- Optional, only if you want to (re)build the UG guide transcripts:
  - `yt-dlp` (the script defaults to `G:\yt-dlp\yt-dlp.exe`, override
    via `--yt-dlp PATH`).
  - `ffmpeg` on `PATH` (for Whisper fallback).
  - `faster-whisper` for local transcription when YouTube auto-captions
    are missing.

### Python deps (see `requirements.txt`)

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

### Runtime config
- `settings.json` — turn delay, `master_data.master_mdb_path`
  (point this at your local
  `…\AppData\LocalLow\Cygames\Umamusume\master\master.mdb`), and
  `event_boost`.
- Game master data + cached lookups live under `data/`
  (`chara_list.json`, `factor_map.json`, `race_map.json`,
  `skill_data.json`, `support_list.json`). The bot writes
  `data/.session_cache.json` and `data/decks.json`; both are gitignored.

### How to Setup and Run

#### 1. Prepare Frida Server
You must download and place the Frida server executable matching the version in `requirements.txt` (`frida==17.9.1`) into the repository root.
- Download `frida-server-17.9.1-windows-x86_64.exe.xz` (or similar 17.9.x version) from the [Frida Releases](https://github.com/frida/frida/releases).
- Extract it and place the `.exe` file directly in the project root directory.

#### 2. Directory Structure
Ensure your project folder tree matches the following:
```text
umamusume-sweepy-enhanced/
├── career_bot/
├── data/
├── node_modules/
├── public/
├── uma_api/
├── main.py
├── frida-server-17.9.1-windows-x86_64.exe  <-- Place the frida server exe here
├── requirements.txt
└── ...
```

#### 3. Running
1. Run `npm i` to install Node dependencies.
2. Run `pip install -r requirements.txt` to install Python dependencies.
3. Run `python main.py` — access the dashboard Web UI at: `http://127.0.0.1:1616`.
4. Login & 2FA.

---

## API surface (new in this fork)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/tp/refill` | Refill TP via `UmaClient.recovery_tp`. |
| `GET` / `POST` | `/api/local-decks` | List / save local Sweepy decks. |
| `GET` | `/api/uma-moe/trainer/{id}` | Preview uma.moe trainer patch. |
| `POST` | `/api/uma-moe/import` | Preview + import uma.moe trainer (defaults `create_only=true`). |
| `POST` | `/api/career/friends` | Primary friends fetch (seeds supports + veterans). |
| `GET` | `/api/friends/raw` | Debug dump of raw `pre_single_mode/index`. |
| `GET` | `/api/friends/veterans` | Normalised veteran list with deck/archetype. |
| `GET` | `/api/friends/manage` | Friend/following counts + cached list. |
| `POST` | `/api/friends/follow` | Follow a viewer id. |
| `POST` | `/api/friends/unfollow` | Unfollow a viewer id. |
| `POST` | `/api/advisor/recommendations` | Parent scoring for selected trainee + style. |

Existing upstream endpoints (`/api/career/start`, `/api/career/run`,
`/api/account/status`, …) are unchanged; `run_career` now applies the
runtime advisor overlay before handing off to `CareerRunner`.

---

# Upstream Sweepy README (preserved)

i've made a terrible mistake

<img width="1080" height="262" alt="image" src="https://github.com/user-attachments/assets/ec2b366c-2ad9-4e2c-852c-384d4ac9ef43" />
Need I remind you that networking of uma will change eventually, bricking this repo. If this keeps up I assue you that version would not be made public. Should've expected less from low trust societies.

fuck you


# Sweepy — /vg/'s Uma Musume Bot (UAT REHASHED)

> [!IMPORTANT]
> **Install Node with `winget install -e --id OpenJS.NodeJS`, then run `npm i` first.**
> **Then go install requirements.txt**

---

## click this button for comedic effect (8mins mant lmao)

<img width="471" height="53" alt="image" src="https://github.com/user-attachments/assets/a2dbe989-f001-4e41-a5b3-1c01c287b97f" />

---
Looping/ending careers was intentionally removed to prevent another Twitter drama and to avoid aggravating Cygames. I think it’s very clear what “tempt fate” mode + looping can do. I don’t want that to be publicly accessible. Do not ask me for this.

Furthermore, this takes <3 mins to figure out, so to those who already did: loose lips sink ships. Keep it zipped.

uses lobotobized/halfported sweepy decision engine, no intention of fully porting/upgrading it as I will be migrating to MCTS soon (ts gonna take months given my hardware [nvm that architecture is straight up not realistic for mant]).



<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/a376b9e0-832e-45ea-add4-499a9f76a284" />
<img width="190" height="158" alt="image" src="https://github.com/user-attachments/assets/428a7704-0729-4dc3-890f-246fb0a94774" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/65edac1a-91c0-4559-8393-7432418afa18" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/3193d3ce-2a3a-4a77-9ed6-c04702083b60" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/d58f6376-76c7-455e-a16d-9bb9d92db969" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/d097751f-966f-4f3f-ba5b-3608cac6bdbe" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/671eb304-cb0b-4f02-9023-ea313df2f987" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/f1ecf7d6-1e18-45d6-8143-66b877d9c786" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/94ea9609-54db-4322-a0f3-9168a70932e0" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/d64d2197-217f-40c5-a57e-3ccd5c868e2d" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/cacd2cf3-b880-4b1e-8818-af33a30bcf38" />
<img width="190" height="140" alt="image" src="https://github.com/user-attachments/assets/3bdd80ec-cb77-4637-9f61-e3f8fab8d85d" />
<img width="235" height="226" alt="image" src="https://github.com/user-attachments/assets/ffb9960a-347d-4d7f-8c0d-57ff96f72b6a" />
<img width="317" height="317" alt="image" src="https://github.com/user-attachments/assets/61c4c0dd-85bc-4517-84c1-021fcf5d47fa" />
<img width="428" height="605" alt="image" src="https://github.com/user-attachments/assets/07ca8a7f-3f89-4667-a5c6-d50ab5b10fe3" />
