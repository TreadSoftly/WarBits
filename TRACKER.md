# Warbits Tracker (Unified)

Purpose: single source of truth for current state, priorities, and validation.

-------------------------------------------------------------------------------
PROJECT SNAPSHOT
-------------------------------------------------------------------------------
- Core: Python + Matplotlib 3D flight/gunnery sim with precomputed flight plans.
- Current focus: SmartLib pack integration + physics accuracy (flight/ballistics) + render perf/FPS.
- Impact recognition: working and observable (bogies, ground AAA, aircraft).
- FPS: low (~16.6 avg). Render time dominates (~48ms avg).
- Latest profiling summary (single loop run):
  - render_avg_ms: 48.095
  - fps_avg: 16.59
  - interval_avg_ms: 60.26
- SmartLib packs live in `warbits/lib/` (v0-v6); docs reviewed, code integration pending.

-------------------------------------------------------------------------------
DECISIONS (RENDERER PATH)
-------------------------------------------------------------------------------
- Simulation core stays Python/NumPy; renderer consumes state.
- Default upgrade path: Panda3D for real-time rendering.
- Matplotlib remains for debug/analysis (telemetry, profiling, replay plots).
- Alternatives (not default): VisPy (fast viz, not full engine), Godot (not Python-first).

-------------------------------------------------------------------------------
PROJECT CONSTITUTION (NON-NEGOTIABLES)
-------------------------------------------------------------------------------
- Single unit system: SI internally (m, s, kg, N, rad).
- Determinism required: same seed -> same outcomes (within tolerance).
- Sim core runs headless (no renderer).
- Renderer does not own simulation truth.
- No silent physics failures in dev/test.
- Data lineage preserved (sources + hashes).
- FPS is a feature: perf budgets + regression checks.

Determinism contract:
- Discrete decisions and event ordering: exact match.
- Continuous physics: tolerance-based match.
- Single RNG source passed explicitly.

Performance budget:
- Target frame time breakdown (sim vs render).
- Allowed regressions and measurement commands.

Fresh machine checklist:
- OS + Python version + install steps + run command + success output.

-------------------------------------------------------------------------------
ADDITIONAL POLICIES / HIGH-LEVERAGE ITEMS
-------------------------------------------------------------------------------
- Data rights and licensing: document provenance; avoid copyrighted assets.
- Determinism across machines: tolerate FP variance; lock RNG usage; document policy.
- Replay + forensic debugging: event log format + replay tooling.
- Sim manifest per run: config dump, version string, data build hashes, seeds,
  determinism flags, hardware summary, and avg frame timings.

-------------------------------------------------------------------------------
PRIORITY ORDER (WHAT TO DO FIRST)
-------------------------------------------------------------------------------
P0 - Foundation and correctness (Stage 0)
- Headless sim loop + determinism tests.
- Strict physics error mode (no silent failures).
- Fix known physics bugs (argmax t=0 hit, ProjectileBuffer max_samples).
- Config dump + sim manifest.
- Profiling schema + perf regression guard.
- SmartLib integration pass (diff `warbits/lib` packs vs `warbits/simlib`, pick canonical APIs).

P1 - Data contract and ingestion (Stage 1)
- Canonical schemas + unit enforcement.
- DataStore + validation + alias resolution.
- Ingestion as deterministic build tool (diff mode, raw manifest).

P2 - Core architecture seam
- RendererAdapter split + MatplotlibRenderer cleanup.
- Typed events in runtime state + JSONL event log.
- Headless run tool.

P3 - Panda3D renderer evolution (Stage 5)
- Panda3D skeleton + terrain + minimal visuals.
- Benchmark tool comparing renderers.
- Optional pixel-art visual style.

P4 - Realism systems (Stages 2-4)
- Atmosphere/drag, weapon fuses, flight envelopes.
- Damage model + sensors + AI behavior.
- Scenario DSL + mission logic + replay/telemetry.

P5 - Distribution + multiplayer (Stage 6)
- Packaging, CI, server-authoritative sim.

Execution order (to avoid chaos):
1) Data contract + loaders + validation (Stage 1).
2) Headless engine loop + determinism tests (Stage 0).
3) Fix correctness bugs + strict physics mode (Stage 2).
4) Realism systems (Stages 2-3).
5) Renderer evolution (Stage 5).
6) Packaging/multiplayer last (Stage 6).

-------------------------------------------------------------------------------
PROMPT PACKETS (CODEX EXECUTION PLAN)
-------------------------------------------------------------------------------
PROMPT 1/13 - Repo inventory + ground-truth map (no changes) | DONE
- Print repo tree and locate key files.
- Find entrypoints and render loop dependencies.
- Run tests (if present).
- Save config dump to docs/baseline_config_dump.txt.
- Write docs/BASELINE.md (run command, perf notes, import inconsistencies).
- Results: docs/BASELINE.md and docs/baseline_config_dump.txt created.
- Tests (python -m pytest -q): 3 failed (test_aircraft_hits, test_enemy_ground, test_scenario), 26 passed.

PROMPT 2/13 - Project Constitution docs + non-negotiables | DONE
- Create docs/CONSTITUTION.md, docs/ARCHITECTURE.md, docs/DATA_CONTRACT.md.
  - Added: docs/CONSTITUTION.md, docs/ARCHITECTURE.md, docs/DATA_CONTRACT.md.

PROMPT 3/13 - Unify runtime state + typed events | DONE
- Canonical state module; other state modules re-export.
- warbits/core/events.py + event_log.py; update producers.
- Tests for roundtrip + singleton runtime.
  - Added: warbits/core/events.py, warbits/core/event_log.py, warbits/core/__init__.py.
  - Updated impact producers to emit ImpactEvent.
  - Added tests/test_events_roundtrip.py and tests/test_state_singleton.py.

PROMPT 4/13 - Split sim core from rendering | DONE
- RendererAdapter base class/protocol.
- Simulation class with step() (no renderer imports).
- Headless run tool + smoke test.
  - Added: warbits/rendering/base.py and warbits/rendering/__init__.py.
  - Added: warbits/core/sim.py with headless Simulation and determinism hash.
  - Added: warbits/tools/headless_run.py and tests/test_headless_sim.py.
  - animation.py now routes step calls through Simulation (callback wrapper).

PROMPT 5/13 - Fix known physics bugs + strict physics mode | DONE
- Fix argmax t=0 bug (ballistics, rockets).
- Replace silent exceptions with strict mode or DebugEvent.
- ProjectileBuffer max_samples guard + tests.
- Terrain collision tests for bullets/rockets/bombs.
- Update TRACKER.md statuses.
  - Results: strict physics toggle + debug-event logging, argmax fix, ProjectileBuffer guard,
    tests for terrain collisions and max_samples handling.

PROMPT 6/13 - Data layer: DataStore + schema validation | DONE
- warbits/data/schema.py, store.py, validate.py.
- CLI tool validate_data.py.
- Wire sim to use data-driven parameters.
- Tests with fixture data.
  - Results: DataStore with alias resolution, schema validation + cross-link checks,
    validate_data CLI, fixture-based tests, legacy specs loaders wired to DataStore.

PROMPT 7/13 - MatplotlibRenderer cleanup | DONE
- MatplotlibRenderer as adapter only.
- Move artists to renderer caches.
- Renderer-agnostic geometry helpers.
- Test: core sim does not import matplotlib.
  - Results: renderer-agnostic geometry helpers, MatplotlibRenderer adapter with cached artists,
    lazy config/physics imports + core-import test to keep matplotlib out of headless sim.

PROMPT 8/13 - Panda3D scaffolding | PENDING
- Optional Panda3D dependency + guard.
- Panda3DRenderer skeleton with ground plane + placeholder aircraft.
- run_panda3d tool; flags for frames/seed.

PROMPT 9/13 - Panda3D terrain port | PENDING
- Renderer-agnostic terrain grid + Panda3D heightfield.
- Visual height vs sample_height validation.

PROMPT 10/13 - Panda3D minimal gameplay visuals | PENDING
- Aircraft + projectiles + enemies + explosions/parachutes.
- Batch rendering; avoid per-projectile NodePaths.
- Benchmark tool comparing renderers.

PROMPT 11/13 - Pixel-art visual style | PENDING
- Visual style switch (realistic vs pixel).
- Nearest-neighbor filtering, low-res textures, flat shading.
- Demo assets structure.

PROMPT 12/13 - Packaging + fresh-machine bootstrap | PENDING
- pyproject.toml + console scripts.
- bootstrap_dev + smoke_test scripts.
- PyInstaller spec + docs/RUNBOOK.md.

PROMPT 13/13 - CI + regression tests + perf gates | PENDING
- Deterministic regression test with stable hash.
- Headless perf tripwire benchmark.
- GitHub Actions workflow for tests + validation + headless sim.
- Update TRACKER.md statuses.

-------------------------------------------------------------------------------
ROADMAP STATUS (CURRENT)
-------------------------------------------------------------------------------
R1  Realism scope + determinism + perf targets | DONE
R2  Scenario seed + randomness hooks | DONE
R3  Scenario variability engine | DONE
R4  Flight-path variety | DONE
R5  Terrain profiles + per-loop selection | DONE
R6  Terrain interaction | DONE
R7  Impact recognition kernel | DONE
R8  Performance smoothing/optimization | IN PROGRESS
R9  Debug/telemetry overlays | PENDING
R10 Canonical data schema + unit conventions | PENDING
R11 Excel ingestion pipeline | DONE (partial; loadouts stubbed)
R12 Damage model | PENDING
R13 Sensors/target recognition | PENDING
R14 Multi-vehicle + loadouts | PENDING
R15 Rendering upgrades | PENDING
R16 Mission logic/objectives/scoring | PENDING
R17 Replay/telemetry export + playback | PENDING
R18 Weather depth | LATER
R19 Water/aquatic environments | LATER

-------------------------------------------------------------------------------
SMARTLIB INTEGRATION STATUS (LIB FOLDER)
-------------------------------------------------------------------------------
- Source packs: `warbits/lib/warbits_smartlib_pack_v0` through `v6` (docs reviewed).
- Current `warbits/simlib`: core v0 + flight v1 + v6 ai/mission merged; v2-v5 still only in lib packs.
- Docs mismatch: pack trackers disagree on total pack count and DONE status; reconcile before wiring.
- Next actions: diff pack code vs current simlib, choose canonical APIs, merge modules, add tests.
- Review iterations target: 7 (v2-v6 packs + data pipeline + 0 TEST reference pass).
- Review progress: iteration 2 complete (v2 sensors code); iteration 3 complete (v5 terrain code); iteration 4 complete (v3 damage code); iteration 5 complete (v4 weapons code); iteration 6 complete (v6 AI/mission code); iteration 7 complete (data pipeline + 0 TEST review).
 - pytest now ignores `warbits/lib/**` (pyproject pytest config).

-------------------------------------------------------------------------------
SMARTLIB INTEGRATION RULES (PRO GUIDANCE)
-------------------------------------------------------------------------------
- One canonical SmartLib location: `warbits/simlib` only.
- `warbits/lib/warbits_smartlib_pack_*` are archives only (no runtime imports, no packaging, no tests).
- simlib must not import `warbits.logic` / `warbits.physics` / `warbits.core` (one-way deps).
- No git commands.
- Every change ends with: `python -m pytest -q` (fix failures immediately).
- No temporary hacks (no sys.path edits, no silent exception swallowing).
- Determinism preserved: seed -> same event ordering + close-enough float results.
- Integrate one subsystem at a time; each step ends with specific tests passing.
- No duplicated packages; no test discovery chaos.

-------------------------------------------------------------------------------
SMARTLIB INTEGRATION TRACKER (100% DONE DEFINITION)
-------------------------------------------------------------------------------
A) Canonicalization and safety gates
- [x] v6 ai/ and mission/ merged into `warbits/simlib/`.
- [x] v6 tests copied into `tests/` and imports updated to `warbits.simlib.*`.
- [x] pytest ignores `warbits/lib/**` completely.
- [x] packaging excludes `warbits/lib/**` completely.
- [ ] runtime imports never point into `warbits/lib/**`.

B) Integration into live sim loop (real usage, not just "library exists")
- [ ] Deterministic RNG owned by Simulation and handed to systems (no random globals).
- [x] MissionDirector runs each tick and produces directives.
- [ ] AI policies exist for at least one entity type (AAA or bogies) using simlib.ai.
- [ ] Sensors feed AI observations (no omniscience).
- [ ] Damage system consumes impacts/explosions deterministically.
- [ ] One golden scenario runs headless and produces a stable event hash.

C) Proof
- [ ] `python -m pytest -q` is green.
- [ ] Headless run prints determinism hash + mission result + event counts and writes a manifest.
- [ ] Mission win/lose computed by MissionDirector and logged.

-------------------------------------------------------------------------------
SMARTLIB PROMPT PACK (ORDERED STEPS)
-------------------------------------------------------------------------------
PROMPT 1 - Merge v6 into runtime + bring tests into root.
- Copy ai/ and mission/ from v6 pack into `warbits/simlib/`.
- Copy tests into `tests/`, fix imports to `warbits.simlib.*`.
- Run `python -m pytest -q`.
  - Status: DONE

PROMPT 2 - Lock pytest discovery so `warbits/lib` never runs.
- Set pytest testpaths to `tests` and add `warbits/lib` to `norecursedirs`.
- Add note to docs/ARCHITECTURE.md about canonical runtime vs archives.
- Run `python -m pytest -q`.
  - Status: DONE

PROMPT 3 - Lock packaging so `warbits/lib` cannot ship.
- Exclude `warbits/lib/**` from package discovery and MANIFEST.in (if present).
- Add tests/test_package_layout.py to assert `warbits.lib` is not importable.
- Run `python -m pytest -q`.
  - Status: DONE

PROMPT 4 - Create SimServices (core -> simlib glue).
- Add `warbits/core/services.py` with SimServices (rng, data, terrain queries, clock, config).
- Simulation constructs SimServices and passes to systems.
- Eliminate hidden randomness (use services.rng only).
- Run `python -m pytest -q`.
  - Status: DONE (core sim path; animation/logic RNG migration still pending)

PROMPT 5 - Integrate MissionDirector (mission runs each tick).
- Add `warbits/logic/mission_runtime.py`.
- MissionDirector tick -> directives; apply directives in Simulation.
- Add deterministic mission + mission integration smoke test.
- Run `python -m pytest -q`.
  - Status: DONE

PROMPT 6 - Integrate AI policy for one unit type (quality first).
- Add `warbits/logic/ai_policies.py` and hook into enemy_ground or enemy_bogies.
- Use simlib.ai for decisions; add deterministic tests and hysteresis/no thrash test.
- Run `python -m pytest -q`.

PROMPT 7 - Integrate sensors (no omniscience).
- Add `warbits/logic/sensor_runtime.py` using simlib.sensors.
- AI consumes tracks and confidence, not perfect positions.
- Add LOS + detection timing tests.
- Run `python -m pytest -q`.

PROMPT 8 - Headless proof run.
- Enhance headless tool to emit determinism hash + mission results + event counts + manifest.
- Add golden headless test with stable hash and mission result.
- Run `python -m pytest -q`.

-------------------------------------------------------------------------------
AI GOAP + BT INTEGRATION (AAA FIRST)
-------------------------------------------------------------------------------
Tracker:
- docs/AI_GOAP_BT_TRACKER.md (100% done definition and phase checklist).

Go-hard prompt pack (8 packets, in order):
1) AI glue contract (commands + world facts + docs).
2) Deterministic AI logging into DebugEvent + tests.
3) GOAP domain for AAA + deterministic planner tests.
4) BT executors for AAA actions + execution tests.
5) Hybrid brain (GOAP plans, BT executes, budgeted replans) + determinism tests.
6) Integrate HybridBrainAAA into enemy_ground with sensors (no omniscience) + tests.
7) GOAP/BT for bogies using autopilot/waypoints + tests.
8) Golden headless proof + planning budget tests; update tracker.

Rules to enforce:
- Deterministic and budgeted replanning (no per-frame replans by default).
- Stable tie-breaking (sort by action name; deterministic RNG substream on ties).
- All AI outputs go through a single command model (no ad-hoc dicts).

-------------------------------------------------------------------------------
SMARTLIB INTEGRATION MAP (IMPORT DIRECTION)
-------------------------------------------------------------------------------
- `warbits/core/sim.py` owns DeterministicRNG, SimServices, mission runtime, sensor runtime, AI runtime.
- `warbits/logic/enemy_ground.py` and `warbits/logic/enemy_bogies.py` ask AI policy for actions.
- `warbits/logic/scenario.py` compiles scenarios and selects missions.
- `warbits/physics/*` stays physics-only; no tactics or policy decisions.
- `warbits/simlib/*` stays pure library; no imports back into warbits.*.

-------------------------------------------------------------------------------
REVIEW & INTEGRATION PLAN (IN PROGRESS)
-------------------------------------------------------------------------------
1) Map SmartLib docs/pack contents to current simlib (gaps + duplicates) | DONE
2) Code-level diff + merge plan for v2-v6 (sensors/damage/weapons/terrain/AI) | IN PROGRESS
3) Physics accuracy wiring (flight limiter, atmosphere/drag, weapon/warhead params) | NEXT
4) Performance pass (profile hotspots, allocation control, render/AI loop tightening) | NEXT
5) Data pipeline alignment (raw -> normalized -> DataStore; loadouts/schema) | NEXT
6) AI + mission integration (sensor-limited observations, mission director) | NEXT
7) Data pipeline consolidation (normalized vs packaged tables; loadouts schema) | NEXT

-------------------------------------------------------------------------------
DATA PIPELINE REVIEW (SUMMARY)
-------------------------------------------------------------------------------
- Two ingestion paths exist:
  - `warbits/data/normalized/ingest_warbits_excels_v1.py` -> JSONL tables in `warbits/data/normalized` (vehicle_id keys, richer merges).
  - `tools/data_pipeline/build_tables.py` -> JSON arrays in `warbits/data` (id keys, packaged DataStore inputs).
- Runtime uses `warbits/data` via `DataStore`; normalized JSONL is not consumed today.
- Count mismatch: normalized vehicles/weapons/warheads > packaged tables; loadouts empty in packaged tables.
- Schema mismatch: normalized uses `vehicle_id` / `weapon_id` / `warhead_id`, packaged uses `id`.
- Decision needed: pick a canonical pipeline and map normalized outputs into the packaged schema.

-------------------------------------------------------------------------------
CODE-REVIEW FIXES (OPEN)
-------------------------------------------------------------------------------
High
C2  Ground update stride can skip fast hits
    - Files: warbits/scene/animation.py
    - Validation: test_enemy_ground.py + SIM fast projectile hits

Medium
C5  ProjectileBuffer max_samples hard-cap can raise on small dt/large max_time | DONE
    - Files: warbits/logic/state.py
    - Validation: buffer limit tests + SIM with small dt

Low
C6  argmax t=0 hit bug in fast paths | DONE
    - Files: warbits/physics/ballistics.py, warbits/physics/rockets.py
    - Validation: solver tests for starting below ground

C7  Solvers swallow exceptions silently | DONE
    - Files: warbits/physics/bombs.py, warbits/physics/rockets.py, warbits/physics/ballistics.py
    - Validation: error logging or explicit failure tests

C8  Profiling lists grow without bounds
    - Files: warbits/scene/animation.py
    - Validation: long-run profiling memory check

C9  Parachute sway freezes after stage 2
    - Files: warbits/physics/parachute.py
    - Validation: SIM parachute sway continues

C11 Fullscreen guard does not call callable device_pixel_ratio
    - Files: warbits/scene/animation.py
    - Validation: backend test + SIM fullscreen stability

C12 Placeholder module masking + unclosed CPU pool
    - Files: warbits/utils/__init__.py, warbits/utils/concurrency.py
    - Validation: import error surfaces; no orphan processes

C13 CLI backend guard only checks agg/svg
    - Files: warbits/cli/warbits_cli.py
    - Validation: CLI rejects non-interactive backends

-------------------------------------------------------------------------------
BEHAVIOR POLISH (ACTIVE)
-------------------------------------------------------------------------------
B1  Smarter flight plan (less hardcoded, more target-centric) | IN PROGRESS
B2  Smarter ground movement (patrol/engage/evade) | IN PROGRESS
B3  Impact visuals polish (splash/debris/more cinematic blasts) | PENDING
B4  Loop reset stability (avoid frame-0 resets inside hold loops) | IN PROGRESS
B5  Bomb-drop alignment + phase padding (avoid early drops) | IN PROGRESS

-------------------------------------------------------------------------------
KNOWN BEHAVIOR DECISIONS
-------------------------------------------------------------------------------
- AIM_ASSIST defaults ON: bullets/rockets aim at nearest target; bombs use plane velocity.
- Aircraft hits do NOT destroy aircraft; show small explosion only.
- Bogie scripted hit is OFF by default.
- Bombs drop only when target is ahead/within drop window (not random).
- Default camera mode is follow-center; POV is not in use.

-------------------------------------------------------------------------------
RECENT IMPLEMENTED CHANGES (CONTEXT)
-------------------------------------------------------------------------------
- Impact detection and logging added (enemy_ground, enemy_bogies, aircraft_hits).
- Aim assist for bullets/rockets (animation.py, enemy_ground.py).
- Explosion visuals improved (explosions.py, bombs.py, rockets.py).
- Terrain sampling cache + stable color range (terrain.py).
- Perf mode + canvas pixel cap (settings.py).
- Flight plan spread + target anchoring (flight_paths.py).
- Ground movement improved (enemy_ground.py).
- Camera follow view restored and centered on aircraft.
- Camera update stride configurable; perf mode defaults to stride=2.
- Weapons spawn from aircraft nose instead of center.
- Player aircraft color set to bright green + pulse effect.
- Terrain footprint increased.
- Victory fly-off gated until all enemies destroyed + short hold.
- Dogfight/ground hold loops now run forward-only and keep sim frame pinned to prevent camera jumps.
- Guarded loop resets to only trigger on true loop starts; bomb-drop alignment uses ballistic estimate + phase padding.
- SmartLib flight pack staged into `warbits/simlib/flight` with tests added.
- SmartLib v6 ai/mission merged into `warbits/simlib` and v6 tests copied into `tests/`.
- pytest discovery locked to `tests/` and `warbits/lib/**` ignored; architecture docs updated.
- Packaging now excludes `warbits/lib/**`; archive guard added (`warbits/lib/__init__.py`) + package layout test.
- SimServices added; core Simulation now owns deterministic RNG and passes it to engagement bullets.
- MissionRuntime wired into headless Simulation with time-limit objective + smoke test.
- Bullet/rocket trajectories clamp below-ground starts to z=0 (physics tests).
- Scenario bogie appear/hit frames constrained to Escape/Dogfight bounds (tests).
- Aircraft bomb-hit test now enables env flag; ground test seeds + resets placements.

-------------------------------------------------------------------------------
RUNTIME TOGGLES (ENV VARS)
-------------------------------------------------------------------------------
Behavior and debug:
- WARBITS_IMPACT_DEBUG=1   (logs impacts to console)
- WARBITS_AIM_ASSIST=0/1   (aim bullets/rockets at nearest target; default ON)
- WARBITS_BOGIE_SCRIPTED_HIT=0/1 (force bogie hit timing; default OFF)
- WARBITS_AIRCRAFT_BOMB_HITS=0/1 (allow bombs to hit aircraft; default OFF)
- WARBITS_SCENARIO_SEED=1234 (deterministic loops)
- WARBITS_TERRAIN_PROFILE=rolling|desert|mountain|forest|urban|auto
- WARBITS_CELEBRATION_SECONDS=3.0 (hold after victory before looping)
- WARBITS_STRICT_PHYSICS=1 (raise on physics solver errors)
- WARBITS_PROJECTILE_AUTO_RESIZE=0/1 (auto-grow projectile buffers; default ON)

Performance:
- WARBITS_PERF_MODE=1
- WARBITS_PERF_CANVAS_MAX_PIXELS=2200000 (lower for more FPS)
- WARBITS_PROFILE=1
- WARBITS_FPS_HUD=1
- WARBITS_CAMERA_UPDATE_STRIDE=2 (update camera every N frames)

-------------------------------------------------------------------------------
VALIDATION COMMANDS (QUICK)
-------------------------------------------------------------------------------
Impact recognition tests:
- python -m unittest discover -s tests -p "test_enemy_ground.py"
- python -m unittest discover -s tests -p "test_enemy_bogies.py"
- python -m unittest discover -s tests -p "test_aircraft_hits.py"
- python -m unittest discover -s tests -p "test_bombs_release.py"
- python -m unittest discover -s tests -p "test_settings_env.py"
- python -m unittest discover -s tests -p "test_flight_paths_validation.py"
- python -m warbits.tools.validate_data

Perf profiling (PowerShell):
- $env:WARBITS_LOOP="0"
- $env:WARBITS_PROFILE="1"
- $env:WARBITS_FPS_HUD="1"
- $env:WARBITS_PROFILE_SAMPLE_EVERY="2"
- warbits

Perf summary JSONL (PowerShell):
- Get-ChildItem profiling\\run-*.jsonl | Sort-Object LastWriteTime | Select-Object -Last 1 | Get-Content -Tail 1

Config dump (PowerShell):
- warbits config

Manual sim checks (visual):
- Run `warbits` and watch 2-3 loops:
  - Flight path spans larger footprint and varies per loop.
  - Ground units patrol/engage/evade (not back-and-forth).
  - Bombs drop only when targets are in front/within range.

-------------------------------------------------------------------------------
MATPLOTLIB REFERENCE EXAMPLES (LOCAL)
-------------------------------------------------------------------------------
Reference folders:
- C:\\Users\\MrDra\\OneDrive\\Desktop\\warbits\\0 TEST\\Layer Files\\OVERFLOW MATPLOTLIB_DOCS
- C:\\Users\\MrDra\\OneDrive\\Desktop\\warbits\\0 TEST\\Layer Files
- C:\\Users\\MrDra\\OneDrive\\Desktop\\warbits\\0 TEST\\Misc Versions

Notes for Warbits:
- Prefer in-place artist updates over remove+replot.
- Lock axis limits to avoid autoscale cost.
- blit=True helps 2D overlays; 3D artists rarely benefit.
- LightSource + facecolors is a viable terrain-shading path.
- text2D is best for HUD/labels anchored to screen space.

-------------------------------------------------------------------------------
REPO ADDITIONS (PLANNED)
-------------------------------------------------------------------------------
- pyproject.toml with locked dependencies.
- warbits/__main__.py for python -m warbits.
- README.md install/run instructions.
- docs/ARCHITECTURE.md engine <-> renderer <-> data flow.
- docs/DATA_CONTRACT.md schemas + units + cross-links.
- docs/RUNBOOK.md clean machine verification.
- .github/workflows/ci.yml for tests + data validation + headless sim + perf gates.

-------------------------------------------------------------------------------
FILE-BY-FILE PLAN (FROM MOVE TO PANDA3D)
-------------------------------------------------------------------------------
TRACKER.md
Plan:
- Turn each major item into a gate; "Done" means tests + visual check + no perf regression.
- Add Determinism contract section (seed inputs -> expected outputs).
- Add Performance budget section (frame time breakdown + allowed regressions).
- Add Fresh machine checklist section.
Done means:
- Someone can read TRACKER.md and run validations without tribal knowledge.

warbits_cli.py
Plan:
- Add CLI modes: run, headless, ingest, validate-data, benchmark.
- Friendly dependency checks (Matplotlib backend/display).
- Explicit config sources (env + config file + CLI flags -> merged config).
Done means:
- New machine can run `warbits run` and get predictable failure message if missing.

settings.py
Plan:
- Split config into SimConfig, RenderConfig, PerfConfig.
- Make computed settings explicit (e.g., max_samples per projectile).
- Add JSON-serializable config dump object.
Done means:
- Run is reproducible from saved config dump.

style.py
Plan:
- Keep pure: no simulation imports or runtime state.
- Add quality tiers (low/medium/high).
- Make fullscreen behavior robust across backends; document what works.
Done means:
- Renderer look is consistent and adjustable without sim code changes.

mpl_setup.py
Plan:
- Add deprecation note in docstring; keep until imports stabilize.
Done means:
- Old imports do not break during refactor.

concurrency.py
Plan:
- Make use_all_cores opt-in and safe (avoid oversubscribing BLAS/OpenMP).
- Set sane thread limits, not blindly max.
- Policy: interactive sim favors smooth frame time; headless allows full CPU.
Done means:
- Performance toggles do not cause stutter or random slowdown.

hardware.py
Plan:
- Keep wrapper; document deprecation path.

profile_report.py
Plan:
- Standardize profiling output schema.
- Add compare-two-runs mode with regression thresholds.
- Ensure headless CI compatibility.
Done means:
- FPS regressions detected automatically.

objects.py
Plan:
- Audit usage; remove if unused or move to utils if needed.
Done means:
- No dead files.

math_tools.py
Plan:
- Centralize segment-to-point distance.
- Add vectorized versions for batch checks.
- Add numerical edge case tests.
Done means:
- Hit detection logic is shared, correct, and tested.

state.py
Plan:
- Define event schemas: ImpactEvent, ExplosionEvent, ParachuteEvent.
- Formalize ProjectileBuffer contract (sample_index semantics, dt relation, remove/swap).
- Add full reset API.
- Add headless stepping contract (no renderer needed).
Done means:
- Headless sim runs with deterministic outputs.

aircraft.py
Plan:
- Separate model space mesh from render instance.
- Replace global artists with AircraftRenderer object.
- Orientation accepts quaternion/rotation matrix; fallback for zero velocity.
- Add visual LOD for distance.
Done means:
- Aircraft renders in Matplotlib, sim not tied to Matplotlib decisions.

models.py
Plan:
- Keep until refactor finishes; add warnings later.

aircraft_hits.py
Plan:
- Route hits to DamageModel (future).
- Create ImpactEvent with weapon_id/warhead_id once data-driven.
- Use shared segment-distance kernel.
- Make min-sample rules configurable (no magic numbers).
- Add tests for tunneling prevention and self-hit prevention.
Done means:
- Hits feed the unified damage system and behave consistently.

enemy_bogies.py
Plan:
- Convert globals to EnemyBogieSystem object.
- Stage 1: keep timelines but enforce speed/turn constraints from vehicle data.
- Stage 2: simple pursuit guidance using acceleration limits.
- Shared collision kernel; unify projectile families.
- Deterministic ejection/parachute events; separate physics vs renderer.
Done means:
- Bogie behavior is seed-stable and not tied to module globals.

enemy_ground.py
Plan:
- Convert to GroundEmplacementSystem object.
- Split movement AI from rendering.
- Data-drive parameters (speed, engage radius, evade rules, hit radius, armor).
- Terrain interaction (friction/roughness affects acceleration/turn).
- Targeting realism (turret rotation limits; sensor detection before firing).
Done means:
- N ground units remain stable and fast.

engagement.py
Plan:
- Decide canonical weapon spawn path (keep or retire).
- Data-drive spawns (dispersion/rate/muzzle velocity; mass/drag/thrust).
- Add ammo/reload/heat constraints (here or WeaponController).
Done means:
- One data-driven weapon spawning path.

scenario.py
Plan:
- Scenario DSL concept (JSON/YAML): entities, spawn rules, triggers, objectives, weather.
- ActionSchedule as compiled output (scenario -> compiler -> ActionSchedule).
- DecisionDirector becomes pluggable AI policy.
- Validation: scenario must be self-contained and deterministic under a seed.
Done means:
- User-defined scenarios replay reliably.

flight_paths.py
Plan:
- Deterministic generator under seed.
- Enforce vehicle constraints (max speed, climb rate, turn rate).
- Autopilot target path concept (waypoints -> physics integrator).
Done means:
- Paths look good and respect data-defined envelope.

phases.py
Plan:
- Keep legacy wrapper; document deprecation path.

weather.py
Plan:
- Layered wind (altitude bands).
- Spatially coherent turbulence.
- ISA-style air density for drag/lift.
- Visibility affects sensors and AI detection.
Done means:
- Weather affects physics and sensors, not just numbers.

terrain.py
Plan:
- Terrain query API: height(x,y), normal(x,y), LOS(a,b).
- Keep cached arrays; add lower-res collision grid.
- Terrain material presets affect movement/traction.
Done means:
- Terrain is ground truth for collisions and sensors.

ballistics.py
Plan:
- Fix argmax t=0 hit bug.
- Remove silent exceptions in dev/test; log + raise.
- Add atmosphere density-based drag.
- Use weapon-driven parameters (muzzle velocity, mass, drag coeff).
- Deterministic tracer/dispersion.
Done means:
- Ballistics matches known drop/TOF test cases.

ballistics_fast.py
Plan:
- Keep temporarily; document legacy.

rockets.py
Plan:
- Fix argmax t=0 hit bug.
- Data-driven modeling (thrust, burn time, drag, mass, guidance type).
- Guidance modes: dumb rocket now, simple PN later.
- Fuse logic from warheads.json (proximity radius, impact delay/sensitivity).
Done means:
- Rockets behave correctly and fusing matches warhead specs.

bombs.py
Plan:
- Data-drive parameters (mass, drag, guidance, fuse delay).
- Add air density drag scaling.
- Add arming time / safe separation rules.
- Tie impact to damage model (blast radius + falloff).
Done means:
- Bombing feels real and matches warhead data.

explosions.py
Plan:
- Event-driven: ExplosionEvent -> renderer spawns/updates.
- Add LOD for distant explosions.
- Size from warhead explosive mass.
Done means:
- Explosions are cheap, scalable, and consistent.

parachute.py
Plan:
- Split ParachutePhysicsState and ParachuteRenderer.
- Wind coupling consistent with weather model.
- Deterministic stage timing.
Done means:
- Parachutes are realistic, deterministic, and render-only.

effects.py
Plan:
- Keep until imports stop moving.

ai.py
Plan:
- Define AI policy contract (observations -> actions).
- Centralize helpers (behavior trees, utility scoring).
- Deterministic RNG handling.
Done means:
- AI is a plug-in system instead of scattered logic.

vehicle_specs.py
Plan:
- Replace empty dict with loader contract (vehicles.json).
- Enforce schema/units; provide lookup functions.
- Keep backward-compatible dict view if needed.
Done means:
- Vehicles are accessible via stable API, not raw JSON poking.

weapon_specs.py
Plan:
- Load weapons.json + warheads.json; resolve links.
- Typed accessors + derived fields (blast radius, detection ranges).
- Treat as build outputs with schema version + source hashes + counts.
- Enforce per-weapon-type schema; normalize attributes and fuse fields.
- Derived performance curves (max speed vs altitude, climb rate interpolation).
- Validation: required fields by type, mass sanity, cross-links.
- Loadouts pipeline: compile loadouts.json with station definitions + compatibility.
- Alias resolution: curated map + auto-suggestions; normalize names; fuzzy match.
- Use data to parameterize ground physics and sensors; keep schema stable.
Done means:
- Data artifacts are authoritative and traceable (vehicles, weapons, warheads, sensors, terrain, loadouts).
- Provenance files (jsonl + checksums) support reproducible builds.

ingest_warbits_excels_v1.py
Plan:
- Convert to deterministic package tool with explicit schema version output.
- Validation phase; fail on unresolved cross-links.
- Diff mode against previous ingestion.
- Document per-sheet parsing rules + known quirks.
- Raw-data manifest (file hashes + timestamps).
- Use extracted CSVs as validation oracles (sea level speed, climb profiles).
Done means:
- Ingestion is a repeatable compiler; anyone can reproduce outputs.

warbits/tools/validate_data.py
Plan:
- Validate schema + cross-links; exit non-zero on error with clear report.
Done:
- Validator tool implemented with JSON/text output and strict mode.

warbits/tools/run_panda3d.py
Plan:
- Run Simulation with Panda3DRenderer; flags for frames/seed/headless-sim.

warbits/tools/benchmark_renderers.py
Plan:
- Benchmark Matplotlib vs Panda3D with fixed scenario; print avg frame time.
