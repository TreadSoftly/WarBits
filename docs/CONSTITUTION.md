# Warbits Project Constitution

Purpose: establish non-negotiable rules that keep the sim deterministic, testable,
and portable while allowing the renderer to evolve.

## Non-negotiables
- Single unit system: SI internally (m, s, kg, N, rad).
- Determinism must exist and be testable.
- No silent physics failures in dev/test (surface errors explicitly).
- Sim core runs headless (no renderer required).
- Renderer does not own simulation truth.
- Data lineage preserved (sources + hashes + schema version).
- FPS is a feature: perf budgets and regression checks required.

## Determinism contract
- Discrete decisions and event ordering must match exactly for a given seed.
- Continuous physics must match within tolerance (documented per test).
- Single RNG source for sim logic (passed explicitly; no hidden globals).

## Error handling
- Debug/CI: raise on physics errors or log structured DebugEvent + fail test.
- Release/demo: may log and continue, but must not silently discard failures.

## Headless requirement
- The sim step loop must run without Matplotlib or any renderer.
- Renderer reads state; it does not mutate outcomes.

## Data lineage
- Every generated data artifact must include source metadata:
  - source name/path
  - source hash
  - ingestion time
  - schema version
- Derived artifacts must be reproducible from raw sources.

## Performance rule
- Each major change must include a perf note and a regression check.
- Frame budget targets must be documented (sim_ms vs render_ms).
