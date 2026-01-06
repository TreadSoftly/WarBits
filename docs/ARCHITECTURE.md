# Warbits Architecture

## Current (as-is)
Pipeline:
CLI -> animation -> scenario/decision -> physics -> state -> renderer

Entry:
- warbits.cli.warbits_cli:main (console script and python -m warbits)

Render loop:
- warbits.scene.animation._update() drives frames via FuncAnimation.
- _step_sim() updates world state, spawns projectiles, checks hits, etc.
- Matplotlib updates are done per frame in the same module.

State:
- warbits.logic.state.RUNTIME is the canonical runtime state container.

Modules:
- warbits.logic: scenario, AI decisions, entity logic.
- warbits.physics: ballistics, rockets, bombs, terrain, explosions, parachute.
- warbits.scene: Matplotlib rendering utilities.
- warbits.config: settings + style.
- warbits.utils: math, concurrency, profiling.

## Target (to-be)
CoreSim + RendererAdapter + DataStore + Tools

CoreSim:
- Owns config, RNG, runtime state, and step() loop.
- Produces typed events (impacts/explosions/parachutes).
- No renderer imports.

RendererAdapter:
- MatplotlibRenderer (debug/analysis).
- Panda3DRenderer (realtime).
- Renders current state; never mutates sim outcomes.

DataStore:
- Loads and validates canonical data (vehicles, weapons, warheads, sensors, loadouts).
- Provides typed accessors with unit enforcement.

Tools:
- headless_run, validate_data, benchmark_renderers, ingestion pipeline.

## Responsibilities (by area)
- logic/state: runtime state and game logic decisions (deterministic).
- physics: numerical solvers and collision checks.
- rendering: view-only representation of state.
- data: schema, validation, ingestion outputs.

## Hot loops and perf rules
Hot loops:
- animation._update() and _step_sim()
- projectile stepping (bullets, rockets, bombs)
- collision checks (segment-distance)
- terrain sampling and LOS checks

Perf rules:
- Avoid per-frame allocations in hot loops.
- Prefer pre-allocated numpy arrays and in-place updates.
- Do not use global random in loops; pass RNG explicitly.
- Keep renderer updates separate from sim math.

## SmartLib canonical location
- Runtime SmartLib lives only in `warbits/simlib`.
- `warbits/lib/warbits_smartlib_pack_*` are archives only (no runtime imports, packaging, or tests).
