import unittest

from warbits.cli import warbits_cli


class TestCLI(unittest.TestCase):
    def test_build_parser(self) -> None:
        parser = warbits_cli.build_parser()
        ns = parser.parse_args([])
        self.assertTrue(hasattr(ns, "command"))

    def test_help_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            warbits_cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
