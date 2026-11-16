"""Require key real observations in the Week 6 lab transcripts."""

from pathlib import Path
import re

root = Path("week6-lab/evidence")
ns = (root / "namespaces.txt").read_text()
manual = (root / "manual_bridge.txt").read_text()
vx = (root / "vxlan.txt").read_text()


def ping_received(size, count):
    # Mininet does not echo commands from a here-document. ping prints the
    # requested data size as "1422(1450) bytes" before its own statistics.
    match = re.search(rf"PING [^\n]* {size}\(\d+\).*?(?=mininet>|\Z)", vx, re.S)
    return bool(match and f"1 packets transmitted, {count} received" in match.group())


checks = {
    "Mininet namespace dump": "<Host h1:" in ns and "h1-eth0" in ns and "s1-eth1" in ns,
    "manual bridge ping": "10.40.9.2" in manual and "2 received" in manual,
    "IPv4 VXLAN VNI 100 capture": bool(re.search(r"vni 100", vx, re.I)),
    "IPv6 VXLAN VNI 106 capture": bool(re.search(r"vni 106", vx, re.I)),
    "IPv4 overlay MTU 1450": "mtu 1450" in vx,
    "IPv6 overlay MTU 1430": "mtu 1430" in vx,
    "IPv4 size boundary": ping_received(1422, 1) and ping_received(1423, 0),
    "IPv6 size boundary": ping_received(1402, 1) and ping_received(1403, 0),
    "MTU mismatch size boundary": ping_received(1326, 1) and ping_received(1327, 0),
    "throughput receivers": vx.count("receiver") >= 3,
}
for label, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {label}")
if not all(checks.values()):
    raise SystemExit(1)
