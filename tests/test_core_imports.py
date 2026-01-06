import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestCoreImports(unittest.TestCase):
    def test_core_sim_does_not_import_matplotlib(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH")
        if pythonpath:
            env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{pythonpath}"
        else:
            env["PYTHONPATH"] = str(repo_root)
        output = subprocess.check_output(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "import warbits.core.sim; "
                    "print('matplotlib' in sys.modules or 'mpl_toolkits' in sys.modules)"
                ),
            ],
            cwd=repo_root,
            env=env,
            text=True,
        ).strip()
        self.assertEqual(output, "False")
