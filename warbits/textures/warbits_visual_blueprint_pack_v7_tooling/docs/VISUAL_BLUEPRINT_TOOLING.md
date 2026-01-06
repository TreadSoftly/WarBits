# Visual Blueprint Tooling (Atlas + Metrics + Budgets)

This pack adds *offline* tools that help you build and evaluate the **wireframe / hologram** visual system
without needing to run the full WarBits sim.

These tools answer three practical questions:

1. **Coverage:** do we have blueprints for everything we care about?
2. **Aesthetics:** do shapes read in the intended style (silhouette + ribs)?
3. **Performance:** will the system stay fast at high entity counts (budgets + LOD)?

Everything here is renderer-agnostic:
- it works for Matplotlib preview workflows today
- and it feeds Panda3D (or any future renderer) later

---

## Files introduced in this pack

- `warbits/visual/metrics.py`  
  Computes per-blueprint metrics: vertex count, edge count, bounds, LOD counts.

- `warbits/visual/budgets.py`  
  Complexity budgets (per blueprint kind and LOD) + budget check helpers.

- `warbits/visual/tools/atlas.py`  
  Generates a PNG atlas (grid) of blueprint previews using a fast **2D projection**.

- `warbits/visual/tools/report.py`  
  Generates a JSON report of metrics + budget checks across a blueprint DB.

- `warbits/visual/tools/pipeline.py`  
  One CLI entrypoint with subcommands: `atlas`, `report`, `validate`.

---

## Blueprint DB format

These tools assume a **JSONL** blueprint DB (one blueprint per line).

Example path:
- `data/visual/blueprints.jsonl`

Each blueprint contains:
- `blueprint_id`
- `kind` (vehicle / weapon / sensor / effect)
- `vertices_m` + `edges`
- optional `lod_edges` (e.g., `lod0`, `lod1`, `lod2`)

---

## LOD naming

The visual system uses `lod0`, `lod1`, `lod2`, `lod3` (where `lod0` is closest/highest detail).

For convenience, the CLI accepts aliases:
- `near` → `lod0`
- `mid`  → `lod1`
- `far`  → `lod2`

---

## Typical workflow

### 1) Generate an atlas (fast visual QA)

From repo root:

```bash
python -m warbits.visual.tools.pipeline atlas \
  --db data/visual/blueprints.jsonl \
  --out artifacts/blueprint_atlas_iso.png \
  --view iso \
  --lod lod0 \
  --max 200
```

You can also build 3-view atlases:

```bash
python -m warbits.visual.tools.pipeline atlas --db data/visual/blueprints.jsonl --out artifacts/atlas_top.png  --view top  --lod lod1
python -m warbits.visual.tools.pipeline atlas --db data/visual/blueprints.jsonl --out artifacts/atlas_side.png --view side --lod lod1
python -m warbits.visual.tools.pipeline atlas --db data/visual/blueprints.jsonl --out artifacts/atlas_iso.png  --view iso  --lod lod0
```

---

### 2) Generate a metrics report (perf + coverage QA)

```bash
python -m warbits.visual.tools.pipeline report \
  --db data/visual/blueprints.jsonl \
  --out artifacts/blueprint_metrics.json \
  --lod lod0
```

Report includes:
- counts by kind/tag
- per-blueprint edge/vertex counts + bounds
- budget pass/fail flags

---

### 3) Validate against budgets (FPS-first guardrail)

```bash
python -m warbits.visual.tools.pipeline validate \
  --db data/visual/blueprints.jsonl \
  --lod lod2
```

The validator prints the worst offenders and exits non-zero if budgets are violated.

Budgets are intentionally conservative for **uncapped FPS** goals.
Tune them in `warbits/visual/budgets.py` once you profile real hardware.

---

## Why 2D atlas rendering (instead of Matplotlib 3D)

Matplotlib 3D rendering is slow and view-dependent.

For blueprint QA, we want:
- stable camera
- predictable results
- fast generation (hundreds of blueprints in seconds)
- consistent line weights

So the atlas uses deterministic 2D projections (top/side/front/iso).

The in-game renderer can still be true 3D.
