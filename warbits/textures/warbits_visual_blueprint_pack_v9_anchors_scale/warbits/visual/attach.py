from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from .anchors import AnchorMap


@dataclass(frozen=True)
class Pose:
    """
    Minimal pose: position (meters) + rotation matrix (3x3).

    Rotation matrix is assumed orthonormal.
    """

    pos_m: NDArray[np.float_]  # (3,)
    rot: NDArray[np.float_]  # (3,3)

    @staticmethod
    def identity() -> "Pose":
        return Pose(pos_m=np.zeros(3, dtype=float), rot=np.eye(3, dtype=float))


@dataclass(frozen=True)
class AttachmentSpec:
    """
    Attach a child blueprint at a named anchor on the parent.

    - offset_local_m is applied in PARENT local space (after parent scale).
    """

    child_blueprint_id: str
    parent_anchor: str = "mount"
    offset_local_m: NDArray[np.float_] = field(default_factory=lambda: np.zeros(3, dtype=float))

    # Future: rotational offsets, hinge constraints, turret yaw/pitch, etc.


def world_point_from_anchor(
    *,
    parent_pose: Pose,
    parent_scale: float | NDArray[np.float_],
    anchor_local_m: NDArray[np.float_],
    offset_local_m: Optional[NDArray[np.float_]] = None,
) -> NDArray[np.float_]:
    """
    Convert a local-space anchor point into world coordinates.

    parent_scale can be:
      - float (uniform)
      - np.ndarray shape (3,) (non-uniform)
    """
    a = np.asarray(anchor_local_m, dtype=float).reshape(
        3,
    )
    if offset_local_m is None:
        off = np.zeros(3, dtype=float)
    else:
        off = np.asarray(offset_local_m, dtype=float).reshape(
            3,
        )

    if isinstance(parent_scale, np.ndarray):
        s = np.asarray(parent_scale, dtype=float).reshape(
            3,
        )
        local = (a * s) + off
    else:
        local = (a * float(parent_scale)) + off

    return parent_pose.pos_m + parent_pose.rot @ local


def attach_child_pose(
    *,
    parent_pose: Pose,
    parent_scale: float | NDArray[np.float_],
    anchors: AnchorMap,
    spec: AttachmentSpec,
) -> Pose:
    """
    Child inherits parent's rotation by default.
    """
    if spec.parent_anchor not in anchors:
        raise KeyError(f"Anchor '{spec.parent_anchor}' not found")

    child_pos = world_point_from_anchor(
        parent_pose=parent_pose,
        parent_scale=parent_scale,
        anchor_local_m=anchors[spec.parent_anchor],
        offset_local_m=spec.offset_local_m,
    )
    return Pose(pos_m=child_pos, rot=parent_pose.rot.copy())
