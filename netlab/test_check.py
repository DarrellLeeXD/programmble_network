"""Local tests for the lab's data checks, without requiring Mininet."""

import ast
import ipaddress
from pathlib import Path
import unittest


def load_check():
    source = ast.parse(Path(__file__).with_name("build_topo.py").read_text())
    function = next(
        node for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == "check"
    )
    namespace = {"ipaddress": ipaddress}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "build_topo.py", "exec"), namespace)
    return namespace["check"]


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.check = load_check()

    def test_reports_duplicate_ipv4(self):
        spec = {"hosts": [
            {"name": "h2", "ip": "10.7.0.2/24"},
            {"name": "h4", "ip": "10.7.0.2/16"},
        ]}
        self.assertIn("h4 and h2 both use 10.7.0.2", self.check(spec))

    def test_reports_duplicate_ipv6(self):
        spec = {"hosts": [
            {"name": "h2", "ipv6": "fd00:4207::2/64"},
            {"name": "h4", "ipv6": "fd00:4207:0:0::2/32"},
        ]}
        self.assertIn("h4 and h2 both use fd00:4207::2", self.check(spec))

    def test_accepts_distinct_addresses(self):
        spec = {"hosts": [
            {"name": "h2", "ip": "10.7.0.2/24", "ipv6": "fd00:4207::2/64"},
            {"name": "h4", "ip": "10.7.0.4/24", "ipv6": "fd00:4207::4/64"},
        ]}
        self.assertEqual([], self.check(spec))

    def test_invalid_address_does_not_hide_duplicate(self):
        spec = {"hosts": [
            {"name": "h1", "ip": "10.NN.0.1/24"},
            {"name": "h2", "ip": "10.7.0.2/24"},
            {"name": "h4", "ip": "10.7.0.2/24"},
        ]}
        self.assertIn("h4 and h2 both use 10.7.0.2", self.check(spec))

    def test_reports_link_to_missing_node(self):
        spec = {
            "switches": ["s1"],
            "hosts": [{"name": "h1", "ip": "10.7.0.1/24"}],
            "links": [["h1", "s1"], ["h1", "s9"]],
        }
        self.assertIn("link h1 - s9 names missing node s9", self.check(spec))


if __name__ == "__main__":
    unittest.main()
