# Warbits Tracker (Unified)

Purpose: single source of truth for current state, priorities, and validation.

Overall completion for the Matplotlib performance + distribution research stream: **100%** (profiling hooks mapped, bottleneck hypotheses logged, benchmarking harness + baseline capture plan drafted, packaging/PyInstaller scope defined, measurement stabilization plan authored, line-level renderer map captured, resize/adaptive staging risks identified, fullscreen/warm-up/rewind telemetry targets documented, color-churn risks cataloged, profiling/config wiring gaps mapped, fullscreen/adapt provenance requirements captured, fullscreen guard/DPI scaling behaviors mapped, projectile buffer growth + camera stride provenance gaps logged, terrain regeneration/LOD resolution gaps documented, camera/fullscreen/terrain math hotspots logged, chase-camera smoothing and preflight allocation costs mapped, terrain color normalization cache behavior recorded, loop rewind/decision churn telemetry targets captured; outstanding: timed baselines, blitting experiments, GC probes, backend matrix tests, wizard prototype, packaging smoke matrix, resize/adaptive telemetry capture, fullscreen guard logging, color-cadence instrumentation, PROFILE_* plumbing, DPI/base-size telemetry, projectile-resize + stride telemetry, terrain generation counters, resolved LOD reporting, camera view_init counters, terrain RNG/mesh reuse telemetry, chase-camera skip/execute telemetry, preflight prep timing, color-range provenance logging, loop-mode transition + celebration telemetry, pingpong wrap/rearm counters).

Execution state: research is finished; proceed directly to wiring profiling toggles and running the baseline harness before any renderer changes.

-------------------------------------------------------------------------------
NEXT ACTIONS (POST-RESEARCH EXECUTION ORDER)
-------------------------------------------------------------------------------
1) Wire `PROFILE_*`/adaptive/fullscreen provenance into `_update` and enable the existing per-stage timers.
2) Capture the baseline harness runs (warm-up + timed frames) with provenance fields: backend, fullscreen state, adaptive flags, camera stride, terrain context, DPI/base size, projectile buffer growth.
3) Layer instrumentation in this order to keep baselines clean: fullscreen guard counters, adaptive scaler provenance, terrain regen/LOD + RNG/geometry timing, camera view_init + chase-camera skip/execute, projectile buffer growth + color cadence + stride provenance, loop/rewind/celebration counters.
4) Run renderer experiments in the harness: terrain surface reuse A/B, blitting/background caching, adaptive staging (DPI then LOD), rcParam perf bundles, projectile color throttling.
5) Execute backend matrix and packaging smoke: QtAgg/WXAgg/TkAgg harness runs with provenance logging, then PyInstaller draft spec + wheel/venv smoke tests capturing startup-to-first-frame timing and backend selection.

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
MATPLOTLIB FPS TRACKER (LIVE)
-------------------------------------------------------------------------------
Legend: [S] studying, [P] planned, [D] doing, [C] complete. Aim: raise Matplotlib FPS without sacrificing quality while avoiding diminishing-return passes.

Instrumentation / insight loop
- [S] Built-in timings exist for rockets, bullets, bombs, bogies, ground, explosions, and parachutes when profiling is enabled; `profile_enabled` is hardcoded `False`, so timing HUD/logs are dark. Task: gate via env/CLI and capture baselines. 【F:warbits/scene/animation.py†L1434-L1517】【F:warbits/scene/animation.py†L1520-L1569】
- [P] Run baseline captures (profile on) and log per-stage medians; repeat after each renderer tweak to visualize gains.
- [P] Immediate stabilization plan: 5x 300-frame captures per backend with current defaults, HUD tick marker every N frames, and CSV export stored under `docs/perf_runs/` to make regressions obvious.
- [P] Wire `settings.PROFILE_*` (GC, artists, HUD, sample cadence) through `_update` and emit resolved flags into harness CSV/HUD metadata so runs are reproducible and toggles are visible. 【F:warbits/config/settings.py†L438-L520】【F:warbits/scene/animation.py†L1434-L1569】
- [P] Count artist allocations per frame (ground/terrain/HUD) to locate churn before enabling blitting.
- [P] Build a mini benchmarking harness: N warm-up frames, N measured frames, export CSV/JSON (`frame_idx, render_ms, sim_ms, gc_pause_ms, backend, dpi, blit, adaptive_flags, rc_bundle`). Capture back-to-back runs so rcParam changes and backend swaps are measurable, not anecdotal. Pair with a baseline capture plan (3x 300-frame runs per backend with blit/adaptive toggles) to avoid anecdotal guesses.
- [P] Backend matrix timing sweep (QtAgg/WXAgg/TkAgg) with and without blitting + background caching; record best default per platform.
- [P] GC cost probe: record collection frequency and duration; test `gc.disable()` during hot loops with safe re-enable on rewinds/pauses.
- [P] Fullscreen guard audit: log `_guard_fullscreen` resize events + durations to see if window-manager thrash is eating render budget; wire into harness output.
- [P] Startup warm-up metric: time first 30 frames post-`FuncAnimation` creation per backend to isolate shader/font/setup cost from steady-state FPS.
- [P] Warm-up + rewind tagging: mark `_loop_mode` rewinds, celebration holds, and the `_adapt_warmup_remaining` window in CSV/HUD output so baseline medians exclude warm-up noise and show loop stability explicitly.
- [P] Loop-mode telemetry: log mode transitions (dogfight/ground/celebration), `_reset_interpolation` invocations, `_pingpong_loop_frame` wraps, `_decision_director.rearm` counts, celebration tick countdowns, and forced-end triggers so rewind/celebration churn is visible in harness output. 【F:warbits/scene/animation.py†L1580-L1740】
- [P] Color-change cadence probe: count projectile `set_color` executions versus position updates so color cycling can be throttled without losing visibility when blitting/background caching is turned on. 【F:warbits/rendering/matplotlib_renderer.py†L73-L160】
- [P] DPI/size provenance: log `_AdaptiveScaler` base size/DPI, each applied scale, and whether the resize-window or DPI path fired; count `_guard_fullscreen` ratio failures and redraws so resize-induced spikes show up in baselines. 【F:warbits/scene/animation.py†L1941-L2017】【F:warbits/scene/animation.py†L2049-L2117】
- [P] Projectile buffer growth telemetry: record when `_resize_samples` expands `max_samples` and include the new size in harness output to attribute mid-run allocations. 【F:warbits/logic/state.py†L66-L207】
- [P] Camera stride provenance: emit resolved `CAMERA_UPDATE_STRIDE` (including perf-mode bumps) into harness metadata so backend/FPS comparisons are not skewed by hidden stride changes. 【F:warbits/config/settings.py†L483-L520】
- [P] Terrain generation counters: log when `_ensure_animation` or renderer `draw_terrain` regenerates the surface and emit the terrain context (profile/seed/step/rcount/ccount) so frame spikes can be tied to terrain churn. 【F:warbits/scene/animation.py†L1844-L1876】【F:warbits/rendering/matplotlib_renderer.py†L61-L105】
- [P] Resolved LOD telemetry: include the post-clamp `(step, rcount, ccount)` from `_effective_grid` in harness outputs to avoid misreading adaptive LOD adjustments. 【F:warbits/physics/terrain.py†L338-L347】
- [P] Camera view_init counters: log every `ax.view_init` invocation (first-frame + smoothed updates) and tag whether it followed adaptive resize, rewind, or fullscreen guard to see if camera resets align with render spikes. 【F:warbits/scene/animation.py†L330-L373】【F:warbits/scene/animation.py†L1941-L2012】
- [P] Fullscreen invocation telemetry: count `make_fullscreen` calls (initial + guard) and include ratios used in `_guard_fullscreen` to attribute resize thrash by backend/platform. 【F:warbits/config/settings.py†L493-L520】【F:warbits/scene/animation.py†L1941-L2012】
- [P] Terrain RNG/mesh reuse probes: emit RNG seed used per terrain regen (default 42 vs scenario seed), record clamp decisions from `_clamp_grid`/`_effective_grid`, and track whether meshgrid/height fields were reused or rebuilt to pinpoint allocation churn. 【F:warbits/scene/animation.py†L334-L358】【F:warbits/physics/terrain.py†L300-L367】
- [P] Terrain math timing: split terrain regen timing into geometry (meshgrid + trig/noise) vs. artist creation so caching experiments can isolate wins. 【F:warbits/physics/terrain.py†L316-L336】
- [P] Chase-camera smoothing telemetry: capture skip vs. execution counts for `_update_camera_view`, record heading deltas that triggered `view_init`, and tag whether the update followed adaptive/fullscreen resizes to correlate camera resets with render spikes. 【F:warbits/scene/animation.py†L330-L373】
- [P] Preflight prep timing: log allocations + elapsed time for `_compute_flight_velocities` and `_apply_flight_clearance` so scenario reloads/rewinds expose any hidden prep spikes before animation starts. 【F:warbits/scene/animation.py†L340-L404】
- [P] Terrain color-range provenance: emit profile/seed keys and cached vs recomputed min/max decisions during terrain regeneration to surface color-normalization rescans when LOD/adaptive toggles oscillate. 【F:warbits/physics/terrain.py†L259-L287】

Renderer + loop efficiency
- [P] Terrain LOD/cache: keep surface artist stable and mutate data instead of recreating on every draw. 【F:warbits/rendering/matplotlib_renderer.py†L35-L218】
- [P] Blitting experiment: return explicit artist list from `_update`, compare blit on/off with cached background to avoid full-scene redraws. 【F:warbits/scene/animation.py†L1520-L1569】
- [P] Camera + entity stride: extend existing ground/bogie stride concept to HUD/effects when perf mode is active. 【F:warbits/scene/animation.py†L1434-L1517】
- [P] Projectile buffers: maintain in-place NumPy arrays for HUD and ground markers, mirroring projectile scatter reuse. 【F:warbits/rendering/matplotlib_renderer.py†L35-L218】
- [P] Stress scripts: dense projectile bursts + high camera motion + rapid loop rewinds to watch for adaptive LOD thrash or artist leaks.
- [P] Micro-rcParam bundles to test in the harness: marker simplification off, lowered DPI vs adaptive DPI, `agg.path.chunksize` high, `axes3d.grid` off, safe defaults for text antialiasing.
 - [P] Terrain dirty-flag A/B test: reuse the existing surface artist for multiple frames and log render_ms deltas before investing in blitting changes.
- [P] Adaptive staging: sequence DPI scaler and LOD scaler so only one adjusts per window; measure oscillation reduction vs. simultaneous tuning. 【F:warbits/scene/animation.py†L1844-L1923】
- [P] Terrain cache reuse at startup: ensure `_terrain_surface` drawn in `_ensure_animation` is reused by updates instead of discarded. 【F:warbits/scene/animation.py†L1844-L1923】
- [P] Color throttling experiment: gate projectile color cycling behind visibility/position changes or lower-frequency ticks to prevent setter-heavy frames when blitting is on. 【F:warbits/rendering/matplotlib_renderer.py†L73-L160】

Distribution / usability for perf toggles
- [S] Env toggles for adaptivity (`WARBITS_ADAPT_*`, `WARBITS_CAMERA_UPDATE_STRIDE`, `WARBITS_PROFILE_*`) exist but default off; need presets for `warbits run --max-perf` and first-launch guides. 【F:warbits/config/settings.py†L438-L520】【F:warbits/cli/warbits_cli.py†L87-L143】
- [P] Add console script + `make run` helper to standardize launch commands; integrate profiling presets for reproducible FPS testing. 【F:pyproject.toml†L1-L69】【F:warbits/cli/warbits_cli.py†L13-L143】
- [P] Capture fullscreen/adaptive/stride provenance in the harness output (FULLSCREEN on/off, ADAPT_RENDER/LOD, CAMERA_UPDATE_STRIDE) so backend comparisons do not conflate screen state with backend performance. 【F:warbits/config/settings.py†L438-L520】【F:warbits/scene/animation.py†L1844-L1959】
- [P] PyInstaller/Briefcase smoke: verify Matplotlib fonts/backends, ship assets via manifest, and measure startup on Windows/macOS/Linux. Draft spec should include QtAgg + TkAgg backends, font cache data, and runtime assets; record COLLECT size and cold-start time. 【F:MANIFEST.in†L1-L14】
- [P] Packaging smoke checklist: clean-venv CLI run (`--max-perf`), PyInstaller onefile (QtAgg + TkAgg) with fonts collected, double-click smoke on Win/macOS/Linux VMs, capture startup + first-frame timings via harness.
- [P] First-launch wizard design: detect backend/GPU, surface FPS overlay hotkey, set recommended `WARBITS_ADAPT_*`, and cache choices in a user config dir; emit remediation steps per OS/backend in both CLI and GUI paths.
- [P] Draft PyInstaller `.spec` with hiddenimports for matplotlib backends/fonts + asset graft list; include smoke-test checklist for each OS.
- [P] Add backend readiness table/output (QtAgg > WXAgg > TkAgg fallback) with install tips per OS so users understand why a backend was chosen or skipped; wire to CLI `--backend` override for deterministic benchmarks. 【F:warbits/cli/warbits_cli.py†L71-L143】
 - [P] Installer/wizard UX: CLI `warbits wizard` and GUI wizard both run a 60-frame harness, compute recommended toggles, and store them in `~/.warbits/config.toml` while emitting remediation commands for missing backends.
 - [P] Distribution smoke matrix: wheel install (Linux/macOS), PyInstaller onefile (Win/macOS/Linux), clean-venv CLI run, and double-click launch; each must log backend chosen, startup-to-first-frame time, and whether font cache warm-up was required.
- [P] Backend warm-up & resize telemetry in packaging runs: capture first 30-frame cost and resize counts during PyInstaller and wheel smoke tests so frozen builds can be compared to venv runs.

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

# Matplotlib Performance & Distribution Findings

## Where everything lives right now
- **This FINDINGS.md**: detailed renderer/performance observations (line-by-line) plus distribution/package guidance.
- **TRACKER.md**: live progress tracker with completion percentage (currently 100%) and the remaining instrumentation/benchmarking tasks to execute.
- **Next step to act**: flip the dormant profiling flags in `animation._update`, wire the env/CLI toggles, and run the harness/baseline plan captured in TRACKER.md before changing any renderer logic.

## Immediate execution checklist (post-research)
1) **Enable profiling paths** so `_update` honors `WARBITS_PROFILE_*`/CLI toggles and emits per-stage timings + GC stats.
2) **Capture baseline runs** with profiling on: N warm-up frames + N timed frames, recording backend, fullscreen, adaptive flags, camera stride, terrain context, DPI/base size, and projectile-buffer size changes.
3) **Stage instrumentation** in this order to avoid noisy baselines:
   - Fullscreen guard counters (invocations, ratio failures, redraw requests).
   - Adaptive scaler provenance (base size/DPI, applied scales, resize_window vs DPI path).
   - Terrain regeneration telemetry (regen counts, resolved LOD/clamp values, RNG seed provenance, geometry-vs-artist timing).
   - Camera/view_init telemetry (trigger counts, heading deltas, correlation with resizes/rewinds) and chase-camera skip/execute rates.
   - Projectile buffer growth + color cadence (resize events, gated color updates) and ground/bogie/HUD stride provenance.
   - Loop/rewind/celebration provenance (wrap counts, decision rearm counts, `_reset_interpolation` hits, forced-end triggers).
4) **Run renderer experiments** in the harness: terrain-surface reuse vs recreation, blitting/background caching on/off, adaptive staging (sequential DPI then LOD), rcParam perf bundles, and projectile color-throttling.
5) **Backend matrix + packaging smoke**: QtAgg/WXAgg/TkAgg runs with provenance logging, followed by PyInstaller draft spec (hiddenimports/fonts/assets) and wheel/venv smoke tests capturing startup + first-frame timing.

## Execution-ready snapshot (what is already locked in)
- Research coverage is complete (see TRACKER.md: 100%). No further discovery passes are pending before implementation.
- All profiling targets, adaptive/terrain/cache risks, and packaging smoke expectations are documented in this file and mirrored in TRACKER.md.
- The next action is purely operational: wire the profiling toggles and start the baseline harness as listed above; no additional scoping is required.

## Observations from the current codebase
- The Matplotlib renderer reuses scatter artists for bullets, rockets, and bombs but removes and recreates the terrain surface each draw; every scatter update uses the private `_offsets3d` path and toggles visibility when no points are active. This reuse pattern already avoids reallocation for projectiles but leaves terrain recreation as a hot spot. 【F:warbits/rendering/matplotlib_renderer.py†L35-L218】
- The animation driver builds the figure once, wires profiling callbacks, and deliberately disables `cache_frame_data` while also keeping `blit` off. It layers two adaptive controllers: one scales canvas DPI/size based on render time and another rebuilds the terrain grid with lower/higher resolution as needed. Both controllers target a configurable render time and are gated by environment variables (`WARBITS_ADAPT_*`). 【F:warbits/scene/animation.py†L1844-L1900】【F:warbits/config/settings.py†L453-L520】
- Styling uses Matplotlib's `fast` preset and sets a low default figure DPI (40) along with disabling the toolbar and grids, which favors speed over pixel density unless overridden. 【F:warbits/config/style.py†L24-L90】
- The CLI exposes `warbits run` and `warbits config` commands; when `--max-perf` or `AUTO_MAX_PERF` is enabled it pins BLAS/OpenMP threads to all cores to warm up CPU throughput. The CLI also blocks non-interactive Matplotlib backends to prevent headless slowdowns. 【F:warbits/cli/warbits_cli.py†L13-L143】【F:warbits/utils/concurrency.py†L29-L109】
- The frame loop clamps variable real-time ticks into fixed simulation steps, interpolates camera state, and immediately returns an empty artist tuple—so blitting is effectively disabled and every frame renders the whole scene. Looping/hold logic also rewinds sections of the scripted flight path without resetting artists, which can accumulate work if terrain or ground actors are recreated per cycle. 【F:warbits/scene/animation.py†L1520-L1837】
- Profiling and detail toggles are already threaded through environment variables (`WARBITS_PROFILE_*`, `WARBITS_ADAPT_*`, `WARBITS_CAMERA_UPDATE_STRIDE`, `WARBITS_PROJECTILE_AUTO_RESIZE`), but they currently default to off; enabling them selectively would expose where per-frame time is spent (physics, camera, explosions, GC). 【F:warbits/config/settings.py†L438-L520】
- Projectile, bogie, ground, explosion, and parachute updates are individually timed when profiling is enabled, but `profile_enabled` is hardcoded to `False` inside the `_update` loop, meaning the instrumentation is never triggered in normal runs; flipping this flag (or wiring it to `WARBITS_PROFILE`) would immediately provide granular timing for each subsystem. 【F:warbits/scene/animation.py†L1434-L1517】【F:warbits/scene/animation.py†L1520-L1569】

### File-by-file renderer notes (line-level)
- `warbits/scene/animation.py` `_update` loop clamps simulation ticks to fixed `SIM_DT_MS` while letting render cadence float; forced steps set `sim_alpha = 1.0`, which prevents interpolation from hiding timing drift during slow frames. This means FPS drops produce visible jumps unless rendering is sped up, so render-side optimizations directly reduce visual stutter. 【F:warbits/scene/animation.py†L1531-L1576】
- The frame driver initializes terrain LOD and adaptive DPI controllers together, seeds terrain from either config or a random 32-bit seed, and always recreates the terrain surface once per animation startup. Backends are hardcoded to `blit=False` and `cache_frame_data=False`, meaning the render loop redraws the entire scene every frame regardless of scene stability. 【F:warbits/scene/animation.py†L1844-L1923】
- `_on_draw` subtracts the last update duration from render time before feeding the adaptive controllers, so timing accuracy depends on `_last_update_ms` being kept in sync. It also always calls `_guard_fullscreen(fig)` which may trigger expensive canvas resizes if OS window managers report stale sizes; capturing those resize counts would show whether fullscreen handling is a hidden perf sink. 【F:warbits/scene/animation.py†L1941-L1959】
- `warbits/rendering/matplotlib_renderer.py` creates separate scatter artists per projectile type and toggles visibility instead of re-instantiating, but terrain drawing always re-calls `_draw_terrain` from `_ensure_animation`. The terrain surface is stored as `_terrain_surface` yet never re-used between frames, leaving a ready-made cache handle unused. 【F:warbits/rendering/matplotlib_renderer.py†L35-L218】【F:warbits/scene/animation.py†L1844-L1923】
- `warbits/config/style.py` pins `plt.style.use("fast")`, disables toolbar/grid, and sets `DEFAULT_FIGURE_DPI = 40`. Combined with adaptive DPI scaling this yields acceptable defaults for profiling but also means any DPI increase from adaptivity or user override can balloon per-frame raster cost. Documenting "fast" overrides per backend will be necessary when shipping presets. 【F:warbits/config/style.py†L24-L90】
- Projectile scatter artists keep colors cycling via per-frame `set_color` calls keyed on frame index and altitude. This adds an extra setter per frame even when no positions change and will magnify allocation churn once blitting/background caching is enabled unless color changes are gated on visible data. 【F:warbits/rendering/matplotlib_renderer.py†L73-L160】

### Deeper observations from recent review
- Adaptive DPI and terrain quality tuning reuse the same render time target; if both oscillate simultaneously (e.g., slow terrain rebuild + canvas resize in the same frame), the feedback loop can thrash. We need to stage these adaptors or clamp their stepsizes so terrain LOD is recalculated only after DPI has stabilized. 【F:warbits/scene/animation.py†L1844-L1900】
- Terrain rebuilds currently allocate new grids and artists on each call to `update_terrain`; when `_loop_mode` rewinds, this happens repeatedly. Marking the terrain as dirty only when the adaptive LOD toggles or when the flight path revisits a new tile would cut redundant allocation. 【F:warbits/scene/animation.py†L1520-L1837】
- Background timing (`_on_draw`) reports only aggregate render duration; a HUD overlay or CSV export that pairs `_on_draw` render_ms with per-system timers would expose whether blitting or terrain caching actually helps. Right now the data is fragmented and unused.
- The CLI already rejects non-interactive backends but does not select a preferred accelerated backend; users on macOS/Linux with both Qt and Tk installed may land on TkAgg. An explicit `--backend` flag with a priority list (QtAgg > WXAgg > TkAgg) would reduce confusion and give deterministic benchmark comparisons. 【F:warbits/cli/warbits_cli.py†L71-L143】

### Profiling + config wiring gaps (new findings)
- `settings.PROFILE_*` exposes fine-grained env toggles for GC timing, artist counting, deep profiling, and sampling frequency, but `_update` hardcodes `profile_enabled = False` and ignores these toggles. None of the GC/artist switches flow into the animation loop, leaving the profiling HUD dark even when users export `WARBITS_PROFILE=1`. Wiring these flags through the renderer driver is a prerequisite for the planned CSV baselines. 【F:warbits/config/settings.py†L438-L520】【F:warbits/scene/animation.py†L1434-L1517】
- `AUTO_MAX_PERF` defaults adaptive render scaling on only when **not** fullscreen; fullscreen runs ship with adaptivity off and no guardrails for high-DPI displays. This means the "easy button" (`warbits run --max-perf`) leaves fullscreen users without DPI/LOD protection unless they also set `WARBITS_ADAPT_RENDER=1`. The harness needs to track fullscreen/adapt flags per run so we do not misread backend comparisons. 【F:warbits/config/settings.py†L438-L520】【F:warbits/config/settings.py†L504-L520】【F:warbits/scene/animation.py†L1844-L1923】
- `create_scene_canvas` calls `make_fullscreen` twice when `FULLSCREEN` is set (once via `make_fullscreen` wrapper, then via `fig.subplots_adjust`), and `_guard_fullscreen` can force additional resize events. Without logging these invocations the render loop cannot explain sudden DPI/size jumps. Harness telemetry should capture both fullscreen calls and guard-triggered resizes to spot backend-specific jitter. 【F:warbits/config/settings.py†L493-L520】【F:warbits/scene/animation.py†L1941-L2012】

### Fresh code-path notes from deeper file-by-file review
- Fullscreen guarding is throttled to once per second and probes Qt/Tk/WX window objects before falling back to canvas dimensions; if the OS window size lags behind the figure size, `_guard_fullscreen` silently repositions/resizes the window with no telemetry. Capturing guard invocations and resize ratios would reveal hidden spikes from fullscreen enforcement. 【F:warbits/scene/animation.py†L1941-L2012】
- The adaptive warm-up window (`_adapt_warmup_remaining`) defers both DPI and LOD feedback until several frames have rendered; coupling this counter to the benchmarking harness will prevent early-frame outliers from contaminating medians. 【F:warbits/scene/animation.py†L1930-L1960】
- Terrain initialization caches `_terrain_surface` and LOD tuple on startup but never reuses the surface after `_draw_terrain` returns; rerouting subsequent updates through this cached artist is the lowest-risk cache win before attempting blitting. 【F:warbits/scene/animation.py†L1844-L1923】【F:warbits/rendering/matplotlib_renderer.py†L35-L218】
- Simulation rewinds (`_loop_mode`) can repeatedly call `_reset_interpolation` and rearm decision directors without resetting adaptive state, risking mixed-quality frames after a rewind. Logging adaptive scale/LOD values across a rewind will show whether adaptors jump or stay stable. 【F:warbits/scene/animation.py†L1520-L1837】【F:warbits/scene/animation.py†L1844-L1900】
- Projectile updates are already timed in isolation, but ground checks and VFX only measure when the feature is active; merging these timers into a single per-frame record (even when zero) will simplify CSV analysis and keep column counts stable. 【F:warbits/scene/animation.py†L1434-L1517】【F:warbits/scene/animation.py†L1520-L1569】

### Newly surfaced renderer behaviors (line-by-line)
- `_AdaptiveScaler` caches the initial figure size/DPI and scales either window size or DPI depending on fullscreen state; if `resize_window` is false (fullscreen), DPI is mutated in place and `_fig.canvas.draw_idle()` is requested after each adjustment. The harness should log base size/DPI and each scale change to correlate resize work with render spikes. 【F:warbits/scene/animation.py†L2049-L2117】
- `_guard_fullscreen` considers a frame fullscreen if either the backend reports it or the canvas size matches `SCREEN_*` within a 0.9 ratio (adjusted for device pixel ratio). When this heuristic fails, it re-applies fullscreen and triggers `subplots_adjust` + `draw_idle`, potentially forcing extra redraws with no logging. Adding counters for `ratio_ok` failures and guard-triggered redraws will expose hidden cost. 【F:warbits/scene/animation.py†L1941-L2012】
- Fullscreen enforcement uses `make_fullscreen` then immediately calls `subplots_adjust` and `draw_idle`; repeated guard triggers could therefore schedule multiple canvas draws per second if the window manager reports stale dimensions. Telemetry for guard frequency and redraw requests will tell us whether this path is dominating certain backends. 【F:warbits/scene/animation.py†L1941-L2012】
- Projectile buffers auto-resize their sample dimension when new trajectories exceed `max_samples`, allocating a fresh zeroed array and copying previous data before accepting the batch. There is no logging for these growth events, so sudden allocations can land mid-run with no provenance; harness telemetry should record `max_samples` growth and whether auto-resize was triggered. 【F:warbits/logic/state.py†L66-L207】
- `CAMERA_UPDATE_STRIDE` silently bumps to at least 2 when `PERF_MODE` is active and the stride env var is unset; this alters camera interpolation cadence relative to render cadence without being emitted anywhere. Baselines need to log the resolved stride so FPS comparisons are not skewed by hidden perf-mode defaults. 【F:warbits/config/settings.py†L483-L520】
- Terrain generation is unconditional: `_ensure_animation` always regenerates terrain at startup and the Matplotlib renderer removes and re-runs `draw_terrain` every time `draw_terrain` is called, even when the context has not changed. Without a dirty flag or reuse counter, identical seeds still trigger full terrain noise generation and surface recreation. Harness telemetry should log the resolved terrain context and generation count so we can attribute frame spikes to terrain churn. 【F:warbits/scene/animation.py†L1844-L1876】【F:warbits/rendering/matplotlib_renderer.py†L61-L105】
- `_effective_grid` clamps `rcount`/`ccount` to be no larger than `step` and may shrink `step` to `max(rcount, ccount)`, so adaptive LOD targets can collapse to the highest of the row/column counts rather than the requested step. Baseline outputs should record the resolved `(step, rcount, ccount)` to avoid misreading adaptive LOD movement or terrain timing changes. 【F:warbits/physics/terrain.py†L338-L347】
## Recommended in-repo optimizations (no code applied yet)
- **Terrain caching and LOD:** Keep the existing adaptive LOD hook but avoid removing/re-creating the terrain surface every frame; instead, update the underlying data arrays (`set_verts` / `set_data`) or gate redraws behind a dirty flag tied to LOD changes. This reduces artist churn and GC pressure, a common FPS killer in Matplotlib animations.
- **Blitting and artist lists:** Consider enabling `blit=True` in `FuncAnimation` with an explicit list of artists (scatter handles, HUD text) returned from `_update`. Blitting dramatically reduces redraw cost on most interactive backends, especially if the background can be cached between frames.
- **Batch updates:** Projectile scatters already update offsets in place; apply the same pattern for HUD text, bogies/ground markers, and terrain overlays to avoid per-frame artist creation. Preallocate NumPy arrays for positions to trim Python overhead.
- **Backend selection:** Stick to interactive, hardware-accelerated backends (QtAgg/WXAgg) where available; fall back to TkAgg only when needed. Ensure `MPLCONFIGDIR` is writable on target systems so the `fast` style and font cache do not stall startup.
- **Profiling hooks:** The existing `_on_draw` timing data can drive per-system presets. Capture a short profile trace on first run, persist recommended `WARBITS_ADAPT_*` values, and reuse them to avoid runtime oscillation.
- **Camera and update stride:** The camera update stride already increases in perf mode (`CAMERA_UPDATE_STRIDE`); extend the concept to enemy/ground updates and explosion/parachute effects to reduce work on low-end GPUs while keeping trajectories accurate.
- **Control the hold/loop rewinds:** When `_loop_mode` rewinds a fight segment, ensure terrain/ground artists are not rebuilt unnecessarily and that projectile caches are reset only when needed; otherwise, repeating sections can accumulate stale artists and slow future frames. 【F:warbits/scene/animation.py†L1520-L1837】
- **Expose FPS/GC profiling presets:** Ship a `WARBITS_PROFILE=1` preset that enables `PROFILE_GC`, `PROFILE_ARTISTS`, and HUD display for users to quickly locate bottlenecks without editing code, then keep a lean default for players. 【F:warbits/config/settings.py†L438-L520】
- **Turn on timing data in practice:** Un-hardcode `_update`'s `profile_enabled` flag and gate it with environment or CLI settings so the built-in subsystem timers populate the HUD/profile logs without code edits. 【F:warbits/scene/animation.py†L1434-L1517】【F:warbits/scene/animation.py†L1520-L1569】
- **Gate color churn:** Only change projectile scatter colors when visible data exists or at lower cadence (e.g., on trajectory milestones) so future blitting/background caching runs are not dominated by repeated `set_color` calls. 【F:warbits/rendering/matplotlib_renderer.py†L73-L160】

### Immediate measurement and stabilization actions

- **Warm-up aware baselines:** Treat the `_adapt_warmup_remaining` window as a structured warm-up for every run and drop those frames from medians; log both warm-up duration and first stable render_ms so startup jitter and steady-state can be separated in reports. 【F:warbits/scene/animation.py†L1930-L1960】
- **Rewind-aware logging:** Tag frames that occur during `_loop_mode` rewinds or celebration holds so cache behavior and adaptive scaling during scripted loops can be measured separately from forward progression. 【F:warbits/scene/animation.py†L1520-L1837】
- **Profile toggle plumbing:** Thread `settings.PROFILE_*` (GC, artists, HUD, sample cadence) through `_update` so HUD/CSV captures can be toggled without code edits; emit the resolved flags into harness output to keep baselines reproducible. 【F:warbits/config/settings.py†L438-L520】【F:warbits/scene/animation.py†L1434-L1569】
- **Flip profiling on for real runs:** Wire `profile_enabled` to `WARBITS_PROFILE` and record 5x 300-frame captures per backend with current defaults. Preserve raw CSVs to avoid guessing whether later tweaks helped or hurt.
- **Start with terrain cache experiment:** Prototype a dirt-simple terrain dirty flag and switch `_update` to reuse the existing surface artist for three A/B runs (dirty flag only vs. current rebuild) to quantify terrain churn cost before tackling blitting.
- **Backends under load:** Run the same harness with TkAgg, QtAgg, and WXAgg on one machine using the same camera path to see how backend selection impacts frame time variance; keep DPI/adaptive settings constant to isolate backend differences.
- **Foreground vs. background GC:** With `PROFILE_GC` on, capture collection pauses during intense projectile segments and during loop rewinds; compare with a run that disables GC during the hot loop but re-enables during rewinds to see if pauses drop without leaking.
- **HUD/overlay timing:** Add a HUD tick marker that prints render_ms and per-system medians every N frames to the console/log so regressions are visible without attaching a profiler.
- **Fullscreen guard audit:** Count how often `_guard_fullscreen` resizes the canvas during runs; if frequent, feed those events into the harness output so resize thrash is visible alongside render_ms.
- **Adaptive controller staging:** Stage DPI and LOD adaptors so only one adjusts per window of frames; measure whether staging reduces oscillation in terrain LOD or canvas size.
- **Color-change cadence probe:** Log how often projectile color updates occur relative to position updates so we can cap color-change frequency without losing visual cues, preventing setter-heavy frames when blitting/background caching is enabled. 【F:warbits/rendering/matplotlib_renderer.py†L73-L160】

## Baseline capture plan (to avoid guesswork)

- **Adaptive cross-check:** Capture adaptive scale and LOD values per frame alongside render_ms to see whether oscillations align with terrain redraws or fullscreen guard activity; store as extra CSV columns to keep future regressions measurable. 【F:warbits/scene/animation.py†L1844-L1959】
- **Backend readiness probe:** During baselines, emit the detected backend, device pixel ratio, and whether fullscreen guard was invoked so platform differences (HiDPI vs. standard DPI) show up in the dataset without guesswork. 【F:warbits/scene/animation.py†L1941-L2012】
- **Flag provenance:** Record the resolved `PROFILE_*`, `ADAPT_*`, `FULLSCREEN`, and `CAMERA_UPDATE_STRIDE` values at run start and per harness output so CSVs capture what toggles were active; this closes the loop between env settings and observed FPS. 【F:warbits/config/settings.py†L438-L520】【F:warbits/scene/animation.py†L1434-L1576】
- **Canvas/base-size provenance:** Log `_AdaptiveScaler` base figure size/DPI plus each applied scale and whether the window resize vs. DPI path was taken; pair with `_guard_fullscreen` ratio/resize counts to correlate redraws with render_ms spikes. 【F:warbits/scene/animation.py†L1941-L2017】【F:warbits/scene/animation.py†L2049-L2117】
- **Terrain regeneration + resolved LOD:** Emit the terrain context and generation count whenever `_ensure_animation` or renderer `draw_terrain` regenerates the surface, and log the post-clamp `(step, rcount, ccount)` from `_effective_grid` so adaptive LOD adjustments match observed timing changes. 【F:warbits/scene/animation.py†L1844-L1876】【F:warbits/rendering/matplotlib_renderer.py†L61-L105】【F:warbits/physics/terrain.py†L338-L347】
- **Frame-time CSVs:** Capture 3x 300-frame runs for each backend (QtAgg/TkAgg/WXAgg if available) with blitting on/off, adaptive DPI on/off, and terrain caching on/off. Store `frame_idx, render_ms, sim_ms, gc_pause_ms, backend, dpi, blit, adapt_flags, terrain_dirty`.
- **GC pressure:** Run with `PROFILE_GC=1` and log collection frequency + pause duration. If GC pauses exceed 5% of frame time, test `gc.disable()` during animation and re-enable during rewinds/pauses.
- **Artist churn audit:** Instrument artist creation counts per frame (terrain, HUD text, ground markers, explosions). Any artist created >1 per frame becomes a caching target.
- **Loop rewind stress:** Force multiple loop rewinds with dense projectiles to see if terrain/ground caches leak. Compare frame times before/after the first rewind to detect accumulation.
- **Start/first-frame timings:** Measure cold start to first frame for (a) venv + `warbits run --max-perf`, (b) PyInstaller onefile, (c) wheel install; record backend chosen and whether font cache creation stalls startup.
- **Font cache heating:** Record whether `MPLCONFIGDIR` is writable and whether the first run triggers font cache rebuilds. If so, bake the cache into frozen builds and add a warm-up step (`python -m matplotlib.font_manager`) to installer scripts to avoid 1st-launch stalls.
- **Resize/guard telemetry:** Record any DPI or window resize events triggered by `_guard_fullscreen` or adaptive scaling; correlate with render_ms spikes to see if window manager interactions dominate certain platforms.
- **Backend warm-up:** Time the first 30 frames after `FuncAnimation` creation for each backend to see whether startup shader/font compilation costs bleed into steady-state FPS; include in harness output.

## External Matplotlib performance resources
- Matplotlib Animation FAQ (blitting/background caching): https://matplotlib.org/stable/users/explain/animations/blitting.html
- Official performance tips (marker simplification, path simplification, rcParams for speed): https://matplotlib.org/stable/users/explain/backends.html#performance-considerations
- High-FPS scatter/line updates using `set_offsets` and `set_data`: https://matplotlib.org/stable/gallery/animation/animation_demo.html
- Efficient 3D surface updates via `plot_surface` data mutation: example discussion at https://matplotlib.org/stable/gallery/mplot3d/surface3d.html#updating-the-surface

## Packaging and distribution notes
- Current entry points live under `warbits` (Python module) and `warbits run` via the CLI; adding a `console_scripts` entry in `pyproject.toml` would give users a `warbits` executable after `pip install .`, aligning with your desired `warbits/run/start` invocation patterns. 【F:warbits/cli/warbits_cli.py†L87-L143】
- For click-to-run distributions, bundle the app with PyInstaller or Briefcase. Capture non-Python assets (textures, data, docs) via a MANIFEST or PyInstaller dataspec to keep the package portable.
- Provide a `make run`/`make build` wrapper that shells out to `python -m warbits` for terminal users, plus an installer script that sets `WARBITS_*` defaults (e.g., `ADAPT_RENDER`, `TARGET_FPS`, `TERRAIN_*`) based on detected hardware.
- Ship a first-launch check that warns when Matplotlib falls back to non-interactive backends; the CLI already errors out for Agg/SVG, so surface remediation steps (install Qt bindings, ensure `$DISPLAY`) to keep newcomers unblocked. 【F:warbits/cli/warbits_cli.py†L71-L82】
- Tighten the source distribution manifest to include textures/blueprints and exclude heavy caches: the current `MANIFEST.in` prunes build/test artifacts but would need explicit `graft` rules for runtime assets before freezing with PyInstaller or publishing wheels. 【F:MANIFEST.in†L1-L14】
- Draft a PyInstaller spec now so we can prove bundling works: include `matplotlib.backends.backend_qt`, `matplotlib.backends.backend_tkagg`, font cache data, and runtime assets from `warbits/assets`/`docs`. Capture the `Analysis`/`COLLECT` size and startup time to see if font caching is still happening on first launch.
- Draft installer UX: (a) CLI `warbits wizard` that detects available backends/GPU, runs a 60-frame harness, and writes recommendations to `~/.warbits/config.toml`; (b) GUI wizard (Tk/Qt) that runs the same harness with a progress bar and shows remediation commands for missing backends so users can self-fix without docs hunting.
- Add a distribution smoke matrix that must be green before shipping: clean-venv CLI run with `--max-perf`, PyInstaller onefile on Windows/macOS/Linux, wheel install on Linux/macOS, double-click launch on Windows/macOS, each capturing startup-to-first-frame timing and chosen backend.

## Next research directions
- Benchmark frame times with and without blitting and with different adaptive settings to identify the best default for mid-tier GPUs.
- Map every artist creation site (ground units, explosions, HUD text) and rank them by allocation count using the existing profiling toggles (`WARBITS_PROFILE_*`).
- Add a thin benchmarking harness that runs N warm-up frames, then collects N timed frames with profiling enabled and exports CSV/JSON rows (frame_idx, render_ms, sim_ms, gc_pause_ms, backend, dpi, blit, adaptive_flags). This lets us correlate rcParam tweaks with real FPS movement and reduces anecdotal guessing.
- Pre-bake rcParam perf bundles (fast-path rendering defaults): disable `path.simplify_threshold`, `agg.path.chunksize` tuning, capped marker sizes, and `axes3d.grid` off; toggle them in the harness to quantify each knob rather than stack them blindly.
- Prototype a small PyInstaller spec to verify all Matplotlib fonts/backends are bundled and to measure startup time on Windows/macOS/Linux.
- Draft a packaging smoke checklist: (1) `python -m warbits run --max-perf` under a clean venv with only runtime deps, (2) PyInstaller onefile build (QtAgg + TkAgg) with fonts collected, (3) double-clickable build launch on Windows/macOS/Linux VMs, (4) capture startup + first-frame timings in the harness for each.
- Write down backend readiness heuristics for the wizard: prefer QtAgg if Qt5/6 present, else WXAgg, else TkAgg with warning when blitting disabled; emit a remediation snippet (pip install + OS package) in the wizard output and in CLI errors.
- Audit per-stage timing by enabling `_update` profiling, record baselines (rockets, bullets, bogies, ground, explosions, parachutes), and feed the data into the tracker below to avoid diminishing-return loops. 【F:warbits/scene/animation.py†L1434-L1517】【F:warbits/config/settings.py†L438-L520】
- Add renderer stress cases: dense projectile storms, high camera motion, rapid loop rewinds; record whether adaptive LOD thrashes or stabilizes.
- Capture back-to-back runs across backends (QtAgg, WXAgg, TkAgg) to see whether blitting wins uniformly or needs backend-specific defaults.
- Measure GC activity during animation to decide whether to pin `gc.disable()` during frame bursts and re-enable during rewinds/pauses.
- Inventory third-party wheels needed for frozen builds (PyInstaller hooks for matplotlib, pillow, font caches) and assemble a draft `.spec` listing asset grafts and hidden imports.
- Draft a first-launch wizard plan: detect GPU/backends, set recommended `WARBITS_ADAPT_*`, surface FPS overlay hotkey, and cache chosen backend in a user config directory.
- Sketch a launcher UX: (CLI) `warbits run --wizard` writes a `~/.warbits/config.toml` with detected backend, `MAX_PERF` preset, and optional `BLIT=1`; (GUI) a minimal Tk/Qt dialog that runs the harness for 30 frames, reports FPS and recommended toggles, then stores them. Do not change simulation defaults until wizard completes.
- Add a mini “backend readiness” table to the wizard output so users can see why a backend was chosen or skipped (missing Qt libs, no DISPLAY, TkAgg fallback). Pair this with suggested install commands per OS to keep the flow self-serve.
- Define a regression gate: any change to rcParam bundles or backend defaults should be accompanied by harness CSVs showing ± FPS deltas to stop speculative tweaks.

### Latest deep-dive (camera + terrain generation hot paths)
- `create_scene_canvas` executes `make_fullscreen` twice when fullscreen is enabled and immediately calls `configure_3d_axes`, which triggers a fresh `ax.view_init` before any adaptive scaling has started. If `_guard_fullscreen` later resizes or if adaptive DPI fires, the camera ends up doing repeated `view_init` calls with no telemetry. Add counters for fullscreen invocations and first-frame `view_init` to correlate resize churn with camera resets. 【F:warbits/config/settings.py†L493-L520】【F:warbits/scene/animation.py†L1941-L2012】
- `_update_camera_view` applies smoothing but still performs `ax.view_init` whenever azimuth/elevation deltas exceed ~0.1°, with no log of how often the expensive view change is issued. Tracking `view_init` frequency and whether it coincides with adaptive resize or rewinds will help isolate camera-driven render spikes. 【F:warbits/scene/animation.py†L330-L373】
- Terrain generation rebuilds two identical grid clamps: `_clamp_grid` in the animation loop and `_effective_grid` in the terrain module. Both clamp `(step, rcount, ccount)` separately before allocating meshes. Because the renderer discards the cached surface each call, every regen re-allocates the meshgrid, trigonometric fields, and a fresh RNG with default seed 42 when no scenario seed is provided. Logging clamp decisions and seed provenance—and reusing the cached RNG/meshgrid when context matches—would expose and mitigate repeated allocations. 【F:warbits/scene/animation.py†L334-L358】【F:warbits/physics/terrain.py†L300-L367】
- `_draw_terrain` constructs `np.meshgrid` plus multiple `sin/cos` grids and a noise field for every regeneration, regardless of whether only color/style changes are needed. With adaptive LOD oscillations, this math cost repeats. Add harness counters for terrain math time and a flag showing whether geometry or only style changed so we can test geometry caching separate from surface removal. 【F:warbits/physics/terrain.py†L316-L336】

### New deep-dive (camera smoothing, flight prep, color normalization)
- `_update_camera_view` only executes in chase mode but still calls `ax.view_init` whenever azimuth/elevation drift exceeds 0.1°; the smoothing threshold keeps the camera hot path active even on small heading jitters, and there is no stride gate separate from the global `CAMERA_UPDATE_STRIDE`. Telemetry should capture skip vs. execution counts, resolved heading deltas, and whether the view change followed adaptive/fullscreen resizes to attribute FPS drops to camera resets. 【F:warbits/scene/animation.py†L330-L373】
- Flight prep recomputes velocity arrays every time `_compute_flight_velocities` runs and applies clearance against sampled terrain in `_apply_flight_clearance`; both paths allocate fresh arrays and sample the current terrain grid. Capturing timing and allocation counts for these preflight steps will reveal whether scenario reloads or rewinds pay repeated costs before animation begins. 【F:warbits/scene/animation.py†L340-L404】
- Ground engagement windows (`_ground_attack_bounds`, `_ground_search_bounds`, `_dogfight_bounds`) recompute slice spans and oscillation periods from `slice_map` each time; tagging the resolved periods and hit/miss cases in telemetry would clarify whether ground AI scheduling aligns with render spikes or rewinds. 【F:warbits/scene/animation.py†L360-L451】
- Terrain color normalization caches min/max ranges keyed by profile + seed, but any regeneration that shifts the cache key forces a new `nanmin`/`nanmax` over the whole height grid. Logging color-range provenance per regen will show when normalization is recomputed versus reused, helping decide if cached ranges or seeded reuse should be enforced to cut repeated scans. 【F:warbits/physics/terrain.py†L259-L287】

### New deep-dive (loop rewinds, interpolation resets, and decision churn)
- The loop controller re-enters celebration/dogfight/ground modes based on `_bogies.is_alive`, `_ground.has_live_targets`, and pending bogies, and each mode switch resets interpolation and loop ticks. Mode toggles can happen mid-frame when enemies respawn or victory ends, forcing repeated `_reset_interpolation` calls and tick re-initialization that may spike allocations or camera resets; logging loop-mode transitions, `_reset_interpolation` invocations, and tick rearm counts will surface this churn. 【F:warbits/scene/animation.py†L1580-L1668】
- During loop holds, `_pingpong_loop_frame` is invoked for both dogfight and ground bounds. Whenever a loop wraps, `_decision_director.rearm` is called again, potentially reallocating decision state and re-triggering VFX in quick succession if bounds are narrow. Instrument wrap frequency, rearm counts, and active loop spans so FPS drops from rapid rewind/decision churn can be attributed instead of misdiagnosed as render-only. 【F:warbits/scene/animation.py†L1669-L1740】
- Celebration holds reuse the final victory slice with a countdown and can force an early animation end (`force_end`) while leaving the simulation tick at the victory frame. Tracking celebration tick counts, forced-end triggers, and remaining celebration frames will clarify whether celebration gating or early stops are stealing frame budget or causing mismatched terrain/camera state. 【F:warbits/scene/animation.py†L1715-L1739】


