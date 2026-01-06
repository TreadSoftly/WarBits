# Visual Blueprint System Plan (v0)

## What we're building (in plain language)

WarBits needs **accurate-looking** vehicles/weapons in a **see-through wireframe / hologram** style
(think "sim replay overlay"), without letting visuals infect the simulation logic.

This system is a **Visual Blueprint DB** + **render adapters**:

- The DB stores (or points to) the shape description for an entity: aircraft, ground unit, missile, bomb, etc.
- The renderer (Matplotlib today, Panda3D later) consumes that blueprint and draws it in your style:
  neon outlines, sparse structural ribs, readable at distance, optional pixel mode.

## Reality check from the FactChecker spreadsheets

The WarThunder FactChecker spreadsheets you uploaded are **excellent for physics/data tuning**
(turn rate vs speed tables, missile thrust/burn guidance-ish parameters, vehicle lists),
but they **do not contain 3D geometry**.

That means: visuals require a separate source of truth, which can be:

- imported open 3D models (preferred for accuracy),
- reconstructed from 3‑view blueprint silhouettes (visual hull technique),
- or a parametric “archetype” model (fallback when we have only dimensions).

## Non-negotiable design rules for the visuals stack

1) **Simulation does not depend on rendering.**
   The sim state is authoritative. Visuals are a view.

2) **All blueprint geometry is stored in SI units (meters)**
   and uses the same local coordinate convention everywhere:
   - +X forward
   - +Y left
   - +Z up

3) **Licensing is tracked per-asset.**
   Every imported model/blueprint must have a recorded license + source URL.

4) **Performance is engineered at build-time.**
   We compile raw assets into:
   - wireframe edges
   - LOD tiers (near/medium/far)
   - cached numpy arrays (fast runtime)

## Visual Blueprint DB: schema overview

A *blueprint* answers: “how do I draw this entity?”

Each blueprint record has:

- `entity_id`: canonical ID (vehicle_id / weapon_id / etc).
- `entity_kind`: `"aircraft" | "ground" | "weapon" | "effect"`.
- `source`: `"procedural" | "mesh" | "silhouette_hull"`.
- `units`: always meters internally.
- `mesh_ref`: path(s) to a compiled wireframe cache (e.g., .npz) OR procedural params.
- `metadata`: extra tags (nation, era, role, etc).
- `provenance`: source URL(s), license, author, attribution requirements.

## Disk layout (recommended)

(You can adjust, but keep the separation between *raw* and *compiled*.)

- `assets/visual/raw/`
  - downloaded source models, blueprint images, etc.
  - never imported directly at runtime

- `assets/visual/compiled/`
  - compiled wireframes (.npz), LOD variants
  - this is what runtime loads

- `assets/visual/blueprints/blueprints.json`
  - index mapping entity_id -> blueprint record

- `assets/visual/blueprints/licenses.json`
  - machine-readable manifest of licenses + sources

## Build pipeline

1) Acquire source geometry (manual download, or curated repos)
   - save to `assets/visual/raw/...`

2) Import + normalize
   - parse mesh / silhouettes
   - orient to (+X forward, +Y left, +Z up)
   - scale to meters (using known dimensions when available)

3) Compile wireframe
   - extract edges (feature edges + boundary edges)
   - optionally add sparse “rib” lines
   - generate LOD tiers
   - save compiled `.npz`

4) Register blueprint
   - add entry to `blueprints.json`
   - update `licenses.json`

5) Runtime use
   - DataStore selects entity_id
   - VisualRegistry resolves blueprint
   - Renderer draws wireframe using selected style profile

## Style system (War Thunder-ish “holo wireframe”)

We separate *geometry* from *style*.

Style decides:
- palette (neon green by default)
- line widths (silhouette thicker than ribs)
- dash patterns (internal structure hints)
- glow (multi-pass lines in Matplotlib; shader/bloom in Panda3D)
- pixel mode (nearest filtering + quantized line sampling)

## “Definition of Done” for v1 visuals

- You can request any entity_id and get *some* depiction:
  - imported mesh if available,
  - otherwise a parametric archetype scaled by dimensions,
  - otherwise a safe generic placeholder (but logged).

- Matplotlib renderer can draw:
  - terrain style + wireframe units + weapon traces
  - consistent look across machines (within tolerance)

- Panda3D renderer can draw:
  - same blueprint wireframes with similar style

- Licenses are tracked for all non-procedural assets.

- There are tests that:
  - ensure the blueprint DB loads
  - ensure compiled wireframes are valid
  - ensure determinism of procedural blueprint generation
