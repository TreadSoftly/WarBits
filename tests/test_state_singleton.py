import unittest

from warbits.logic import RUNTIME as LOGIC_RUNTIME
from warbits.logic import state as state_module


class TestStateSingleton(unittest.TestCase):
    def test_singleton_runtime(self) -> None:
        self.assertIs(LOGIC_RUNTIME, state_module.RUNTIME)
