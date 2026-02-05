"""Visual blueprint subsystem (renderer-agnostic).

This package is intentionally modular. Some submodules (e.g. Panda3D, Matplotlib)
may not be installed in every environment.
"""

from __future__ import annotations

# Optional exports (keep imports resilient for partial installs / tooling runs)
try:  # pragma: no cover
    from .lod import LODPolicy  # type: ignore
except Exception:  # pragma: no cover
    LODPolicy = None  # type: ignore

try:  # pragma: no cover
    from .registry import VisualRegistry  # type: ignore
except Exception:  # pragma: no cover
    VisualRegistry = None  # type: ignore

# Always-available core helpers
from .anchors import AnchorDB, AnchorRecord, compute_default_anchors
from .attach import AttachmentSpec, Pose, attach_child_pose
from .scale_fit import TargetDims
from .scale_fit import compute_nonuniform_scale
from .scale_fit import compute_nonuniform_scale as compute_scale_xyz
from .scale_fit import compute_uniform_scale

__all__ = [
    "LODPolicy",
    "VisualRegistry",
    "AnchorDB",
    "AnchorRecord",
    "compute_default_anchors",
    "TargetDims",
    "compute_uniform_scale",
    "compute_nonuniform_scale",
    "compute_scale_xyz",
    "Pose",
    "AttachmentSpec",
    "attach_child_pose",
]
