# Free / Open Sources for Visual Blueprints

This file is intentionally practical: sources you can actually use,
plus the licensing reality check.

## 1) FlightGear (huge aircraft coverage)

FlightGear is an open-source flight simulator with a giant ecosystem of aircraft add-ons.
Many aircraft include detailed 3D models (often AC3D `.ac`, sometimes OBJ).

Strategy:
- Use FlightGear aircraft models as the **raw mesh source**
- Compile them into our **wireframe cache**
- Track the license per-aircraft (varies by model/package)

Where to get them:
- FGAddon mirror notes:
  - SourceForge repo exists
  - Direct-download HTTP mirror exists (useful for automated downloads)

NOTE: Each aircraft may have its own license/attribution requirements.
Record it in `licenses.json` for safety.

## 2) BlendSwap (some CC0 models, but coverage is hit/miss)

BlendSwap has community models with explicit licenses. Some are CC0,
which is ideal for redistribution.

Reality check:
- downloads can require a login
- military models may be incomplete or inconsistent
- still useful as a seed set

## 3) Sketchfab (mixed licenses, many non-commercial)

Sketchfab has a big selection, but a lot of “free” models are non-commercial.
If you plan to ship, **avoid NC** assets unless you know the licensing implications.

## 4) Wikimedia Commons (blueprints / silhouettes)

Wikimedia can be a goldmine for public domain or CC-licensed 3-view drawings.
These can feed a *silhouette hull* reconstruction pipeline (visual hull / voxel carving).

(We will build the importer once we lock the schema.)

## 5) When there is no good source

We fall back to **parametric archetypes** driven by:
- length / wingspan / height
- wing/tail config tags
- weapon class tags

This is how we get “everything works” even before every real model is imported.
