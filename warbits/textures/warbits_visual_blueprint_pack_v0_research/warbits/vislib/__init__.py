"""WarBits visual utilities.

This package is intentionally engine-agnostic:
- Blueprints describe geometry (wireframes).
- Render adapters (Matplotlib/Panda3D) consume blueprints + styles.

The simulation core must NEVER depend on this package.
"""
