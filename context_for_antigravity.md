# umamusume-sweepy-enhanced — Antigravity Handoff Context

> Drop this doc in front of a fresh Antigravity session to pick up the project.
> Sister to `context.md` (Cursor handoff) but reorganised around **tools, files,
> and future enhancements**. Both files are kept in sync at handoff time.

---

## 1. What this project is

- A fork of [SweepTosher/umamusume-sweepy](https://github.com/SweepTosher/umamusume-sweepy)
  living in `C:\Users\Computer\Documents\GitHub\umamusume-sweepy`.
- Public fork on GitHub: <https://github.com/disreconnected/umamusume-sweepy-enhanced>
  (remote name `enhanced`; upstream is `origin`).
- Drives **Uma Musume Pretty Derby (DMM/Steam, Windows client)** career mode
  via a Frida hook + a FastAPI/Vanilla-JS dashboard.
- This fork targets **UG-rated Trailblazer ("mant") runs** for blue-factor
  parent grinding. Scoring + decision logic lives in `career_bot/`; UI in
  `public/`.

### Quick start

1. `winget install -e --id OpenJS.NodeJS`
2. `npm i`
3. `pip install -r requirements.txt`
4. Drop `frida-server-17.9.11-windows-x86_64.exe` at the repo root (NOT in
   git — gitignored, see §5).
5. Launch the DMM/Steam Uma client, then `python main.py`.
6. Dashboard: <http://127.0.0.1:1616>.

---

## 2. Tools used

### 2.1 Runtime / language stack

| Tool | Version | Used by | Why |
|---|---|---|---|
| Python | 3.11+ | Backend, scripts | FastAPI app + career engine |
| Node.js | latest LTS | Frontend tooling | Required by upstream `npm i`. Frontend itself is plain ES modules — no bundler |
| PowerShell / cmd | Windows-default | Dev shell | Most tooling assumes Windows paths |
| Frida | 17.9.1 (Python) / 17.9.11 (server) | `uma_api/client.py` | Hooks the live game to dump msgpack/protobuf traffic |

### 2.2 Python dependencies (`requirements.txt`)

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

### 2.3 External services / APIs

- **In-game API** (Cygames servers, reached through Frida-decrypted msgpack):
  - `pre_single_mode/index` — friend list, support cards, veterans
  - `pre_single_mode/start` — start a career; carries `rental_viewer_id` +
    `rental_trained_chara_id` for inherit-from-friend
  - `recovery_tp` — TP refill
  - Follow/unfollow probes in `uma_api/client.py::follow_user/unfollow_user`
- **uma.moe** — public trainer mirror (`https://uma.moe/trainer/{id}`).
  Fetched via the **in-process Cursor CDP browser** because the public JSON
  probe 503s most of the time.

### 2.4 Dev / research tools

| Tool | Where it lives | Notes |
|---|---|---|
| `yt-dlp` | `G:\yt-dlp\yt-dlp.exe` (override with `--yt-dlp`) | Used by `scripts/transcribe_uma_guide.py` to pull metadata + auto-captions for UG strategy research |
| `ffmpeg` | `PATH` | Required by `faster-whisper` fallback |
| `faster-whisper` | `pip install faster-whisper` (optional) | Whisper transcription when YT auto-captions are missing |
| Cursor CDP browser | Cursor MCP `cursor-ide-browser` | Drives the uma.moe importer (`career_bot/uma_moe_importer.py`) |
| `gh` CLI | system PATH | Used for repo/PR plumbing |
| Git | system PATH | Remotes: `origin` = upstream, `enhanced` = this fork |
| ngrok / Cygames master.mdb | local install | `settings.json::master_data.master_mdb_path` points at `…\AppData\LocalLow\Cygames\Umamusume\master\master.mdb` |

### 2.5 Editor / agent context

- Designed to be picked up by either **Cursor** (`context.md`, this fork's
  primary IDE) or **Antigravity** (this file).
- Cursor MCP servers in use: `cursor-app-control`, `cursor-backend-control`,
  `cursor-ide-browser`. The CDP browser is **load-bearing** for the
  uma.moe importer.

---

## 3. File map (every file the fork touches)

### 3.1 Backend — `career_bot/`

| File | Role |
|---|---|
| `career_bot/advisor.py` | Runtime deck-archetype detection, parent scoring, `prepare_runtime_preset(...)` in-memory overlay. New in this fork. |
| `career_bot/delay.py` | Turn-delay pacing helpers (consumes `settings.json::turn_delay`). |
| `career_bot/events.py` | Story event branch handling. |
| `career_bot/items.py` | Item shop + consumption. Enforces `reserve_master_hammer_final3` and `reserve_megaphone_summer`, tighter buy heuristics for UG. |
| `career_bot/master_data.py` | `master.mdb` loader for static game tables. |
| `career_bot/presets.py` | Preset schema + normalization. Adds `STYLE_STAT_PROFILES`, `rental_chara_*`, UG knob set (`target_rank`, race budgets, `train_min_total_stat_gain`, hammer/megaphone reserves), lowered `learn_skill_threshold = 720`. |
| `career_bot/races.py` | Race chooser. Now respects an in-memory `max_races` pre-finals budget. |
| `career_bot/report.py` | End-of-run summary printer. |
| `career_bot/runner.py` | Turn-by-turn orchestrator. Auto-skill-buy disabled at 3 sites (`UG-AUTO-SKILL-BUY DISABLED`); `_buy_skills` helper still present. |
| `career_bot/scenarios/base.py` | Scenario base interface. Untouched. |
| `career_bot/scenarios/mant.py` | Trailblazer training scorer. Consumes `min_stats` / `max_stats`, applies near-1000 scaling bonus, UG junk-training rest guard. |
| `career_bot/skills.py` | Skill ranker / `SkillBuyer.buy(...)` (currently dormant — see §6.5). |
| `career_bot/uma_moe_importer.py` | CDP-backed `uma.moe/trainer/{id}` fetcher; builds preset patches; `prune_race_plan_for_ug(...)` trims donor races to ~33 pre-finals. |

### 3.2 Backend — root + game client

| File | Role |
|---|---|
| `main.py` | FastAPI app, all HTTP routes, in-memory session state. Big — hosts every endpoint listed in §4. |
| `uma_api/client.py` | Frida-backed HTTP client into the live game. Adds `_call_first_supported(...)`, `follow_user(...)`, `unfollow_user(...)`. |
| `scripts/generate_master_data.py` | One-shot dumper for the game's master tables. |
| `scripts/transcribe_uma_guide.py` | `captions` / `run` / `probe` / `local` subcommands for pulling YT transcripts. UTF-8-safe stdout. |

### 3.3 Frontend — `public/`

| File | Role |
|---|---|
| `public/index.html` | Dashboard layout. Cache-bust at `?v=25`. Hosts Friend Manage + Runtime Advisor panels. |
| `public/app.js` | All dashboard JS — selection state, fetchers, render loops, advisor wiring, friend management, uma.moe import + sort controls, local deck editor, TP refill. |
| `public/styles.css` | All styles (advisor panel, relationship badges, deck strips, friend-manage panel, deck editor, etc.). |
| `public/sweep.png`, `public/broom.png` | Branding assets. |
| `public/assets/data/uma_race_data.json` | Static race lookup surfaced to the UI. |
| `public/assets/data/uma_character_data.json` | Static character lookup. |
| `public/races/*.png` | Race banner art used by the dashboard. |

### 3.4 Data — `data/`

| Path | Role | Tracked in git? |
|---|---|---|
| `data/chara_list.json` | `card_id → chara name` map (a dict, **not** a list — earlier scripts assumed list and broke). | ✅ |
| `data/factor_map.json` | Factor IDs → human names. | ✅ |
| `data/race_map.json` | `program_id / race_id → race name`. | ✅ |
| `data/skill_data.json` | Skill metadata for scoring. | ✅ |
| `data/support_list.json` | Support card metadata. | ✅ |
| `data/event_outcomes.json` | Event branch outcomes. | ✅ |
| `data/.session_cache.json` | Last-session cache. | ❌ (`.gitignore`) |
| `data/.backups/` | Snapshot bundles. | ❌ |
| `data/decks.json` | Local Sweepy deck store. | ❌ (user-local) |
| `data/presets/top_UG_FR_template.json` | Front-Runner UG template. | ✅ |
| `data/presets/top_UG_PC_template.json` | Pace-Chaser UG template. | ✅ |
| `data/presets/top_UG_LS_template.json` | Late-Surger UG template. | ✅ |
| `data/presets/top_UG_EC_template.json` | End-Closer UG template. | ✅ |
| `data/presets/top_FR_template.json` | Front-Runner non-UG template. | ✅ |
| `data/presets/top_UG_LS_Mejiro_Dober.json` | Worked Dober example (37-race UG). | ✅ |
| `data/presets/top_UG_PC_Mcqueen.json` | Worked McQueen example. | ✅ |
| `data/presets/top_UG_PC_oguri.json` | Worked Oguri Cap example. | ✅ |
| `data/presets/top_EC_Newbielol2.json` | End-Closer worked preset. | ✅ |
| `data/presets/top_LS_hinacorn.json` | Late-Surger worked preset. | ✅ |
| `data/presets/top_PC_Zoi.json` | Pace-Chaser worked preset. | ✅ |
| `data/presets/tokai_teio.json` | Tokai Teio example. | ✅ |
| `data/presets/skygunner_test.json` | Late-Surger smoke preset. | ✅ |
| `data/presets/xguri parent.json` | Pre-existing example. | ✅ |
| `data/presets/1.json`, `TEST.json` | Throwaway tests. | ❌ |
| `data/presets/uma.moe*.json` | Raw uma.moe imports. | ❌ |
| `data/uma_guides/UG_STRATEGY.md` | Canonical UG rating strategy doc. | ✅ |
| `data/uma_guides/<id>/{cc.en.vtt, transcript.{json,txt}, meta.json}` | YouTube auto-caption + Whisper outputs for source guides. | ❌ (kept local — verbatim YT content) |
| `data/images/` | Cached card portraits served via `/api/images/{name}.png`. | partial |

### 3.5 Root / config

| File | Role | Tracked? |
|---|---|---|
| `README.md` | Fork overview + upstream notes (rewritten for this fork). | ✅ |
| `context.md` | Cursor session handoff (deep dive). | ✅ |
| `context_for_antigravity.md` | This file. | ✅ |
| `requirements.txt` | Pinned Python deps. | ✅ |
| `package.json`, `package-lock.json` | Node deps (frontend tooling only). | ✅ |
| `settings.json` | Local dashboard prefs (turn delay, `master.mdb` path, event boost). | ✅ |
| `.gitignore` | Excludes Frida binary, decks, transcripts, throwaway presets. | ✅ |
| `frida-server-17.9.11-windows-x86_64.exe` | Frida server binary (~68 MB). | ❌ (`.gitignore`) |

---

## 4. API surface (FastAPI routes in `main.py`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/master-data/status` | Whether `master.mdb` is loaded. |
| `POST` | `/api/master-data/path` | Set `master.mdb` path. |
| `POST` | `/api/master-data/generate` | Regenerate cached tables. |
| `GET` | `/api/presets` | List presets. |
| `POST` | `/api/presets` | Save preset. |
| `POST` | `/api/presets/delete` | Delete preset. |
| `POST` | `/api/presets/save_races` | Save race list only. |
| `GET` | `/api/skills` | Skill catalogue. |
| `GET` | `/api/uma-moe/trainer/{trainer_id}` | Preview uma.moe import. |
| `POST` | `/api/uma-moe/import` | Import (defaults `create_only=true`). |
| `POST` | `/api/login` | Login via Frida-captured ticket. |
| `GET` | `/api/session` | Session/account state. |
| `POST` | `/api/selection` | Persist current trainee/deck/parents/rental. |
| `POST` | `/api/logout` | Drop active client. |
| `POST` | `/api/career/start` | Start a career via `pre_single_mode/start`. |
| `POST` | `/api/career/run` | Drive the loop (applies runtime advisor overlay). |
| `GET` | `/api/career/runner` | Runner state. |
| `POST` | `/api/career/runner/stop` | Stop runner. |
| `POST` | `/api/career/runner/burn_clocks` | Burn idle clocks. |
| `POST` | `/api/career/friends` | Refresh support + veterans cache. |
| `GET` | `/api/friends/raw` | Debug dump of cached `pre_single_mode/index`. |
| `GET` | `/api/friends/veterans` | Normalised veteran list w/ deck + archetype. |
| `GET` | `/api/friends/manage` | Following counts + cached list. |
| `POST` | `/api/friends/follow` | Follow a viewer id. |
| `POST` | `/api/friends/unfollow` | Unfollow a viewer id. |
| `POST` | `/api/advisor/recommendations` | Parent scoring for selected trainee+style. |
| `POST` | `/api/career/action` | Free-form runner action. |
| `POST` | `/api/career/delete` | Delete the active career. |
| `POST` | `/api/tp/refill` | Refill TP via `UmaClient.recovery_tp`. |
| `GET` / `POST` | `/api/local-decks` | List / save local Sweepy decks. |
| `GET` | `/api/debug/start_state` | Debug snapshot. |
| `GET` | `/api/debug/raw_load` | Raw load endpoint dump. |
| `GET` | `/` | Dashboard HTML. |
| `GET` | `/styles.css`, `/app.js`, `/sweep.png`, `/broom.png` | Static assets. |
| `GET` | `/assets/data/{file_name}` | Lookup JSONs. |
| `GET` | `/races/{file_name}` | Race banners. |
| `GET` | `/api/images/{image_name}` | Card portrait proxy. |

---

## 5. What's already shipped in this fork (highlights)

- UG bot stack: style-aware stat targets, near-1000 scaling bonus, UG preset
  knobs, item reserves, race-budget enforcement, junk-training rest guard.
- **Runtime advisor** so JSON presets stay clean — deck/parent advice gets
  applied as an in-memory overlay in `main.py::run_career`.
- **uma.moe importer** with race-plan pruning to ~33 pre-finals races,
  `create_only` default to avoid clobbering templates.
- **Friend veteran "borrow as parent"** flow with relationship management
  (follow/unfollow) and a rich friend cards UI.
- **Local Sweepy deck editor** + **TP refill** button.
- Auto-skill-buy temporarily disabled (3 call sites in `runner.py`).

Full breakdown: see `README.md` and `context.md`.

---

## 6. Possible future enhancements

> Ordered roughly by ROI; pick whatever the next session has appetite for.
> Where a `(§…)` reference appears, it points back into `context.md`.

### 6.1 Re-enable auto-skill-buy with stricter selection (`context.md` §6.8)
- Add a hard guard in `career_bot/skills.py::SkillBuyer.buy(...)` so
  mid-career (`force=False`) only buys skills from
  `preset.learn_skill_list`, ignoring rainbow / inheritable picks.
- Honour `learn_skill_blacklist` strictly in both modes; use
  `learn_skill_threshold` (now 720) as the SP-per-skill floor.
- Once green, uncomment the three lines marked `# state = self._buy_skills(...)`
  in `career_bot/runner.py` (~L295 / L313 / L332).

### 6.2 End-to-end inheritance smoke test (`context.md` §6.5)
- Pick a friend veteran in the rich picker, start a Trailblazer career,
  inspect the actual `pre_single_mode/start` payload to confirm
  `rental_trained_chara_id` + `rental_viewer_id` match.
- Log the inheritance screen response from the live game to lock the
  behaviour down with a recorded fixture.

### 6.3 Telemetry capture for UG rank-score calibration
- After every finished run, persist final stats, race wins, skill spend,
  set bonuses, and the resulting `rank_score` (+ in-game letter) to a
  newline-delimited JSON file under `data/.runs/<timestamp>.jsonl`.
- Use that ledger to calibrate the
  `UG entry ≈ 20,500 rank_score` working baseline in
  `data/uma_guides/UG_STRATEGY.md` against real runs.

### 6.4 Advisor: archetype-conditioned race budgets
- `career_bot/advisor.py::prepare_runtime_preset(...)` currently tunes
  `min_stats` and `train_min_total_stat_gain` per archetype.
- Extend it to tune `max_races` / `race_count_target` per archetype
  too — e.g. Guts-heavy decks should generally pull `max_races` down by
  2–3 to leave more training turns; Speed/Power decks can run higher.

### 6.5 Advisor: weighted blue-factor coverage check
- When advising parents, also look at the **trainee's missing aptitude
  letters**; recommend parents whose pink (aptitude) sparks plug those
  gaps before scoring by raw blue-star count.
- Surface a "covers DIRT B → A" tooltip in the advisor panel.

### 6.6 uma.moe importer: caching + multi-source merge
- Cache fetched trainers to `data/.uma_moe_cache/<trainer_id>.json` so
  re-importing the same trainer is instant.
- Optionally merge race plans across **all** of a trainer's recent
  veterans (not just the top one) and dedupe to one canonical plan.

### 6.7 Friend management UX upgrades
- Bulk follow/unfollow from search results.
- Search-by-name across the friend list.
- A "veterans you can still borrow this week" filter that respects the
  in-game cooldown / weekly rental limit.

### 6.8 Local Sweepy deck editor 2.0
- Drag-and-drop reordering between deck slots.
- Per-deck notes (e.g. "URA SPD A+ run") stored in `data/decks.json`.
- Side-by-side compare of two local decks against the same trainee.

### 6.9 TP refill: schedule / auto-refill loop
- Add a "refill whenever TP < N" toggle so a long run can chew through
  multiple TP buckets without manual clicks.
- Surface the recovery-item inventory before each refill so the user
  knows which item (TP-recovery 50/100/All) will be consumed.

### 6.10 Session persistence (`context.md` §6.6)
- Easy: persist last active account + last picked preset + last rental
  selection to `data/.session_cache.json` so the dashboard re-opens with
  context after a restart.
- Medium: cache `viewer_id → account` mapping to skip re-selecting an
  account.
- Out of scope: re-issuing Steam tickets server-side and re-hooking
  Frida on game cold start (real unattended auto-relogin).

### 6.11 Strategy doc loop
- Auto-pull every new English UG guide via
  `scripts/transcribe_uma_guide.py`, classify them with a tiny LLM
  pass, and append confirmed numeric findings (rank_score samples,
  optimal race counts, hammer cadence) to `data/uma_guides/UG_STRATEGY.md`
  with provenance lines.

### 6.12 Frida resilience
- Detect when the in-game session token rotates mid-run and re-attempt
  the call once before failing the runner.
- Surface "ticket about to expire — re-capture from game" warnings in
  the dashboard so users can pre-empt the loss.

### 6.13 Test harness
- Add a `tests/` folder with:
  - JSON fixtures of `pre_single_mode/index` for friend extraction
    regression tests.
  - Synthetic preset + state fixtures to lock down
    `career_bot/scenarios/mant.py::_score_command` scoring against
    golden numbers.
  - Race-plan pruner unit tests for
    `career_bot/uma_moe_importer.py::prune_race_plan_for_ug`.

### 6.14 Packaging / one-click installer
- A `scripts/bootstrap.ps1` that does `winget install OpenJS.NodeJS`,
  `npm i`, `pip install -r requirements.txt`, and downloads the
  matching `frida-server-*.exe` into the repo root.
- A Windows shortcut that launches `python main.py` + opens the
  dashboard URL.

### 6.15 MCTS migration scaffolding
- Upstream README hints at migrating from the heuristic engine to
  **MCTS**. Even before a full port, we can shim a "what-if" panel that
  takes a current state snapshot and runs N rollouts with the existing
  scorer to surface ranked next-move suggestions to the user. Useful as
  a debugger and as the seed for the eventual MCTS rollout.

---

## 7. Conventions

- **No new comments narrating obvious code** (per project style).
- **Don't rewrite preset JSONs for tuning** — extend
  `career_bot/advisor.py::prepare_runtime_preset(...)` instead. JSON
  presets are loadout, not policy.
- **`?v=` cache-bust** in `public/index.html` bumps every UI session
  (currently `?v=25`); bump it whenever `app.js` or `styles.css` change.
- **`UG-AUTO-SKILL-BUY DISABLED` marker** in `career_bot/runner.py` —
  search for it when re-enabling.
- **`# UG-…` markers** elsewhere — search-tag for UG-targeted code paths.
- Long markdown reference: prefer `context.md` (Cursor) for narrative
  state; this file (Antigravity) for tools/files/future-work.

---

## 8. Where to look first when something breaks

| Symptom | First file to read |
|---|---|
| "Login fails" / "no fresh auth" | `main.py::login`, `uma_api/client.py` |
| "Veterans don't show after refresh" | `main.py::get_friend_list` (cache early-return), `public/app.js::loadFriendVeterans` |
| "Bot trains junk" | `career_bot/scenarios/mant.py::_score_command`, `career_bot/advisor.py::prepare_runtime_preset` |
| "Bot wastes items" | `career_bot/items.py` (reserve helpers + `buy_shop_items`) |
| "Races crowd out training" | `career_bot/races.py::choose`, `career_bot/uma_moe_importer.py::prune_race_plan_for_ug` |
| "uma.moe import 503s" | `career_bot/uma_moe_importer.py` (CDP fetch path) |
| "Skill auto-buy buys garbage" | `career_bot/runner.py` (call sites currently disabled) + `career_bot/skills.py` |
| "TP refill button does nothing" | `main.py::POST /api/tp/refill`, `uma_api/client.py::recovery_tp` |
