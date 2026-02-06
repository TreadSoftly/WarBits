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

## 2026-02-06 Coordination Note
- See `docs/AI_LIVE_TRACKER.md` and `docs/ai_live_tracker.yaml` for cross-AI status.
- STL branch research handoff: `docs/ai_sync/codex_status_2026-02-06.md`.
