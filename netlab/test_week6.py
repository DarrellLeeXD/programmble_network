"""Check the Week 6 design and generated VTEP commands without Mininet."""

import ast
from copy import deepcopy
import ipaddress
from pathlib import Path
import re
import unittest

import yaml


HERE = Path(__file__).resolve().parent
tree = ast.parse((HERE / "build_overlay.py").read_text())
functions = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name in {"plan", "vm_ports", "check_spec", "check_mtu", "tenant_commands", "all_commands"}
]
scope = {"ipaddress": ipaddress, "NAME": re.compile(r"^[a-z][a-z0-9]{0,7}$"), "VXLAN_OVERHEAD": 50}
exec(compile(ast.Module(body=functions, type_ignores=[]), "build_overlay.py", "exec"), scope)


def fixture():
    return {
        "student_id_last4": "4940",
        "underlay": {"network": "10.40.0.0/24", "mtu": 1500},
        "hypervisors": ["hv1", "hv2", "hv3", "hv4"],
        "tenants": [
            {"name": "amber", "vni": 494001, "network": "10.40.60.0/24", "mtu": 1450,
             "vms": [["am1", "hv1"], ["am2", "hv2"], ["am3", "hv3"]]},
            {"name": "violet", "vni": 494002, "network": "10.40.60.0/24", "mtu": 1450,
             "vms": [["vi1", "hv1"], ["vi2", "hv3"], ["vi3", "hv4"]]},
        ],
    }


class Week6DesignTests(unittest.TestCase):
    def test_boundary_and_jumbo_fix(self):
        spec = fixture()
        self.assertEqual([], scope["check_spec"](spec))
        self.assertEqual([], scope["check_mtu"](spec))
        spec["tenants"][0]["mtu"] = 1451
        self.assertIn("amber", " ".join(scope["check_mtu"](spec)))
        self.assertIn("1", " ".join(scope["check_mtu"](spec)))
        spec["underlay"]["mtu"] = 9000
        spec["tenants"][0]["mtu"] = 1500
        spec["tenants"][1]["mtu"] = 1500
        self.assertEqual([], scope["check_mtu"](spec))

    def test_each_vtep_has_local_ports_and_exact_flood_peers(self):
        spec = fixture()
        commands = scope["all_commands"](spec)
        addresses = scope["plan"](spec)["hypervisors"]
        for hv in spec["hypervisors"]:
            hosted = [t for t in spec["tenants"] if any(where == hv for _, where in t["vms"])]
            self.assertEqual(len(hosted), sum(c.startswith("ip link add br") for c in commands[hv]))
            self.assertFalse(any(" remote " in c for c in commands[hv]))
            for tenant in hosted:
                vni = tenant["vni"]
                joined = [where for _, where in tenant["vms"]]
                self.assertIn(
                    f"ip link add vxlan{vni} type vxlan id {vni} local {addresses[hv]} dstport 4789 dev {hv}-eth0",
                    commands[hv],
                )
                floods = [c for c in commands[hv] if c.startswith("bridge fdb append") and f"dev vxlan{vni} " in c]
                self.assertEqual(
                    {f"bridge fdb append 00:00:00:00:00:00 dev vxlan{vni} dst {addresses[peer]}"
                     for peer in set(joined) - {hv}},
                    set(floods),
                )
                for vm, where in tenant["vms"]:
                    if where == hv:
                        port = scope["vm_ports"](spec, hv)[vm]
                        self.assertIn(f"ip link set {port} master br{vni}", commands[hv])

    def test_checked_yaml_variants_and_overlapping_addresses(self):
        expected = [("blackhole.yaml", 2), ("mtu_a.yaml", 0), ("mtu_b.yaml", 0), ("overlay.yaml", 0)]
        for filename, count in expected:
            with self.subTest(filename=filename):
                spec = yaml.safe_load((HERE / filename).read_text())
                self.assertEqual([], scope["check_spec"](spec))
                self.assertEqual(count, len(scope["check_mtu"](spec)))
                p = scope["plan"](spec)["vms"]
                self.assertEqual(p["am1"]["ip"], p["vi1"]["ip"])
                self.assertNotEqual(p["am1"]["mac"], p["vi1"]["mac"])


if __name__ == "__main__":
    unittest.main()
