import numpy as np

from warbits.visual.attach import Pose, AttachmentSpec, attach_child_pose


def test_attach_child_pose_inherits_rotation_and_moves_to_anchor():
    parent_pose = Pose(pos_m=np.array([100.0, 0.0, 0.0]), rot=np.eye(3))
    parent_scale = 2.0

    anchors = {"mount": np.array([1.0, 0.0, 0.0])}

    spec = AttachmentSpec(child_blueprint_id="weapon:test", parent_anchor="mount", offset_local_m=np.array([0.5, 0.0, 0.0]))
    child_pose = attach_child_pose(parent_pose=parent_pose, parent_scale=parent_scale, anchors=anchors, spec=spec)

    # local point = anchor*scale + offset = [1*2 + 0.5,0,0] = [2.5,0,0]
    assert np.allclose(child_pose.pos_m, [102.5, 0.0, 0.0])
    assert np.allclose(child_pose.rot, np.eye(3))
