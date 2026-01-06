# Visual Blueprint System Tracker (Master)

This tracker is for the **visual/blueprint** system only (not physics realism). It’s meant to stay brutally practical: every box corresponds to code, tests, and an integration surface.

## Status

- v0  Research + DB design: ✅ done
- v1  Ingest (OBJ → blueprint JSONL): ✅ done
- v2  Runtime registry + caching: ✅ done
- v3  Matplotlib renderer adapter: ✅ done
- v4  Procedural fallback blueprints: ✅ done
- v5  Panda3D renderer adapter: ✅ done
- v6  Panda3D terrain + HUD base: ✅ done
- v7  Tooling (preview, compile, validate): ✅ done
- v8  Mapping (data IDs → blueprint IDs): ✅ done
- v9  Anchors + scaling rules: ✅ done
- v10 Effects/VFX primitives (cheap): ✅ done
- v11 HUD + targeting symbology: ✅ done
- v12 Perf harness + LOD policy: ✅ **done (this pack)**

### Remaining (planned)

- v13 **Integration + coverage**
  - “Coverage report”: which vehicles/weapons have real mesh blueprints vs procedural placeholders.
  - “Visual manifest”: record blueprint DB version + hashes per run.
  - Reference integration patches:
    - MatplotlibRenderer uses blueprint registry and LOD
    - Panda3DRenderer uses blueprint registry, LOD, batching
  - One-click smoke test scenes:
    - vehicle lineup scene (air)
    - vehicle lineup scene (ground)
    - ordnance lineup scene

## Definition of Done (visual system)

You’re “done enough” when:

- Picking a `vehicle_id` and a `weapon_id` yields a **stable** blueprint render (no missing keys).
- Far objects do not tank FPS because LOD reduces line counts.
- Projectiles and effects are batched (no per-bullet objects).
- There is a coverage report that tells you what’s still placeholder.

