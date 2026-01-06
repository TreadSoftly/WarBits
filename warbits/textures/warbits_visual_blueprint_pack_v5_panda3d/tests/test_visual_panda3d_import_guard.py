from __future__ import annotations

import pytest

from warbits.visual.panda3d import Panda3DNotInstalled, is_panda3d_available, require_panda3d


def test_panda3d_optional_import_guard():
    # This import should succeed regardless of Panda3D being installed.
    assert callable(is_panda3d_available)
    assert callable(require_panda3d)


def test_require_panda3d_raises_when_missing():
    if is_panda3d_available():
        pytest.skip("Panda3D is installed in this environment")
    with pytest.raises(Panda3DNotInstalled):
        require_panda3d()
