"""Check Week 3 route validation and page output without launching Mininet."""

import ast
from copy import deepcopy
import html
import ipaddress
from pathlib import Path
import re
import unittest

import yaml


HERE = Path(__file__).parent


def load_functions(filename, names, namespace):
    tree = ast.parse((HERE / filename).read_text())
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    exec(compile(ast.Module(body=functions, type_ignores=[]), filename, "exec"), namespace)
    return namespace


BUILDER = load_functions(
    "build_routed.py",
    {"plan", "hosts", "owner", "lookup", "check_spec", "check_paths"},
    {"ipaddress": ipaddress},
)
PAGE = load_functions(
    "make_page3.py", {"esc", "routing_tables_section"},
    {"html": html, "ipaddress": ipaddress, "plan": BUILDER["plan"]},
)


def example_spec():
    """A four-router ring with r1's summary toward r4."""
    return {
        "student_id_last4": "4940",
        "routers": ["r1", "r2", "r3", "r4"],
        "lans": [
            {"name": "lan-h1", "network": "10.40.1.0/24", "router": "r1", "host": "h1"},
            {"name": "lan-h2", "network": "10.40.16.0/24", "router": "r2", "host": "h2"},
            {"name": "lan-h3", "network": "10.40.32.0/24", "router": "r3", "host": "h3"},
            {"name": "lan-h4", "network": "10.40.33.0/24", "router": "r4", "host": "h4"},
        ],
        "links": [
            ["r1", "r2", "10.40.12.0/30"],
            ["r2", "r3", "10.40.23.0/30"],
            ["r3", "r4", "10.40.34.0/30"],
            ["r4", "r1", "10.40.41.0/30"],
        ],
        "routes": {
            "r1": [
                {"to": "10.40.16.0/24", "via": "10.40.12.2"},
                {"to": "10.40.32.0/23", "via": "10.40.41.1"},
            ],
            "r2": [
                {"to": "10.40.1.0/24", "via": "10.40.12.1"},
                {"to": "10.40.32.0/24", "via": "10.40.23.2"},
                {"to": "10.40.33.0/24", "via": "10.40.23.2"},
            ],
            "r3": [
                {"to": "10.40.1.0/24", "via": "10.40.23.1"},
                {"to": "10.40.16.0/24", "via": "10.40.23.1"},
                {"to": "10.40.33.0/24", "via": "10.40.34.2"},
            ],
            "r4": [
                {"to": "10.40.1.0/24", "via": "10.40.41.2"},
                {"to": "10.40.16.0/24", "via": "10.40.41.2"},
                {"to": "10.40.32.0/24", "via": "10.40.34.1"},
            ],
        },
    }


class RouteTests(unittest.TestCase):
    def test_valid_ring_has_all_host_paths(self):
        spec = example_spec()
        self.assertEqual([], BUILDER["check_spec"](spec))
        self.assertEqual([], BUILDER["check_paths"](spec))

    def test_two_routers_sending_h3_traffic_to_each_other_is_a_loop(self):
        spec = example_spec()
        spec["routes"]["r4"][-1]["via"] = "10.40.41.2"
        problems = BUILDER["check_paths"](spec)
        self.assertTrue(any("h1" in p and "h3" in p and "loop" in p for p in problems), problems)

    def test_missing_route_reports_affected_host_pair(self):
        spec = example_spec()
        spec["routes"]["r2"].pop()
        problems = BUILDER["check_paths"](spec)
        self.assertTrue(any("h2" in p and "h4" in p and "no route" in p for p in problems), problems)

    def test_network_file_meets_design_requirements(self):
        spec = yaml.safe_load((HERE / "network.yaml").read_text())
        self.assertEqual(example_spec(), spec)
        self.assertEqual([], BUILDER["check_spec"](spec) + BUILDER["check_paths"](spec))


class PageTests(unittest.TestCase):
    def test_each_router_table_shows_connected_and_static_routes_longest_first(self):
        output = PAGE["routing_tables_section"](example_spec())
        self.assertNotIn("TODO", output)
        self.assertEqual(4, output.count("<table>"))
        r1 = re.search(r"<h3>r1</h3>(.*?)</table>", output, re.S)
        self.assertIsNotNone(r1)
        table = r1.group(1)
        self.assertIn("directly connected", table)
        self.assertIn("10.40.41.1", table)
        self.assertLess(table.index("10.40.12.0/30"), table.index("10.40.1.0/24"))
        self.assertLess(table.index("10.40.1.0/24"), table.index("10.40.32.0/23"))


if __name__ == "__main__":
    unittest.main()
