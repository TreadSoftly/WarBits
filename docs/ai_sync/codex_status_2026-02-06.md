# Codex Handoff Status (2026-02-06)

This note is for the parallel ChatGPT 5.2 Pro session working on the **pure Matplotlib** WarBits repo.
It summarizes research completed in the STL branch and the shared docs/packs the other session should consider.
No STL code changes are pushed here.

**Scope Completed**
- Reviewed all research handoff passes P1–P16 plus related packs and images.
- Completed full read of `warbits/visual/*` (renderer-agnostic core, Matplotlib renderer, Panda3D renderer, FX, HUD, tools, QA).
- Studied determinism and event log specs and tooling packs.

**Key Findings To Carry Forward**
- **STL fragments**: Vehicles appearing as “puzzle pieces” are caused by selecting STL files under `/Parts/` without assembly transforms. Default to assembled (non-Parts) models until a real part-assembly pipeline exists.
- **Camera stability**: Start with Mode A (fixed top-down), then Mode B (angled top-down tracking), only then Mode C (chase). Keep `up = +Z`, avoid roll, smooth the **center**, clamp dt for camera math.
- **Target cycling**: Deterministic Next/Prev ordering is required; stable sorts + event logging for selection/lock.
- **Determinism**: Use `<= frame` scheduling for weapons/explosions to avoid skipped events when frames are dropped.
- **Performance reality**: Matplotlib 3D is CPU-bound; short-term gains come from batching + LOD + fewer artists + lighter terrain; long-term fix is Panda3D.

**Issue Index Highlights (from log-derived index)**
- ammo counters increment on denied fire
- terrain sampling clamp can be disabled (OOB risk)
- track manager misses/dup edge cases
- weapon/bomb schedule uses `== frame` (skips on dropped frames)
- event log uses `json.dumps` on non-JSON objects

**Recommended Next Actions (Pure Matplotlib Repo)**
1. Implement **Mode A** fixed top-down camera in the frame loop.
2. Add **stage timers** and **artist budget logging** to get real perf numbers.
3. Fix weapon scheduling to `<= frame` and add typed JSONL event log hooks.
4. Implement deterministic target cycling + HUD highlight (Next/Prev).

**Coordination Notes**
- The STL work is happening in a **separate local workspace** and is not being pushed here.
- This repo is used for documentation and baseline Matplotlib behavior only.
- Keep changes to this repo limited to docs/notes until explicit instruction to sync code changes.
