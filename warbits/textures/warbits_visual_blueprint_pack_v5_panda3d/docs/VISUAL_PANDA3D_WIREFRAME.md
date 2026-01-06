# Panda3D Wireframe Layer (v5)

This pack adds a **Panda3D-backed wireframe renderer** for the Visual Blueprint DB.

Why Panda3D:
- It can render **lots of line segments** at high FPS.
- It is Python-friendly.
- It lets you keep the sim core in Python while upgrading the viewport.

## Design goals

- **Optional dependency**
  - If Panda3D is not installed, imports stay safe and tooling still works.
- **Batch-first**
  - Avoid per-entity NodePath spam.
  - Push “all wireframe edges for the world” through **one dynamic line batch**.
- **Coordinate sanity**
  - Sim coordinates and Panda coordinates may differ; we provide one canonical mapping.

## Install (when you’re ready)

Panda3D is intentionally optional.
When you want it:

- `pip install panda3d`

(If your project defines extras, use the extras entry later.)

## Quick usage (viewer)

A small preview tool is included:

- `python -m warbits.visual.tools.preview_panda3d --help`

This lets you:
- load a blueprint JSONL
- display one blueprint by id
- rotate/inspect in real-time

## Performance notes (important)

- Lines are drawn using a single dynamic `Geom`.
- Vertex updates stream into the GPU each frame.
- LOD matters:
  - keep per-vehicle edge budgets sane (hundreds → a few thousand)
  - avoid “millions of segments” because you *can*.

## Known limitations

- “Thick neon lines” are GPU/driver-dependent.
  - Some systems clamp line width.
- True glow and dashed lines are best done as a post-process
  - We keep v5 minimal; fancier pipeline lands in later packs.

