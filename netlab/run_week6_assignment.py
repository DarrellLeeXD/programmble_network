#!/usr/bin/env python3
"""Collect Week 6 assignment evidence on a fresh Mininet network for each case."""

from pathlib import Path
import subprocess
import time

from build_overlay import build, load, plan, problems_for


OUT = Path("evidence6")
OUT.mkdir(exist_ok=True)
TARGET = "10.40.60.11"


def command(node, shell_command, lines):
    lines.append(f"$ {node.name} {shell_command}\n")
    result = node.cmd(shell_command)
    lines.append(result.rstrip() + "\n")
    return result


def require_ping(result, label):
    if "1 received" not in result and "2 received" not in result and "3 received" not in result:
        raise RuntimeError(f"{label} did not receive a reply:\n{result}")


def fresh_network(filename):
    subprocess.run(["mn", "-c"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    spec = load(filename)
    problems = problems_for(spec, force=filename == "blackhole.yaml")
    if problems:
        raise RuntimeError("Invalid design: " + "; ".join(problems))
    print(f"== Fresh build: {filename} ==", flush=True)
    net, _ = build(spec)
    return spec, net


def save(name, lines):
    (OUT / name).write_text("\n".join(lines).rstrip() + "\n")


def check_rejection():
    result = subprocess.run(
        ["python3", "build_overlay.py", "blackhole.yaml"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    (OUT / "check.txt").write_text("$ python3 build_overlay.py blackhole.yaml\n" + result.stdout)
    if result.returncode == 0 or result.stdout.count("PROBLEM:") != 2 or "nothing was built" not in result.stdout:
        raise RuntimeError("The black-hole design was not rejected before building")


def flood_and_isolation():
    spec, net = fresh_network("overlay.yaml")
    try:
        lines = ["== hv1: amber VXLAN before any traffic =="]
        command(net["hv1"], "bridge fdb show dev vxlan494001", lines)
        net["hv3"].cmd("timeout 8 tcpdump -ni hv3-eth0 udp port 4789 > /tmp/week6-hv3.txt 2>&1 &")
        time.sleep(1)
        result = command(net["am1"], f"ping -c 2 -W 2 {TARGET}", lines)
        require_ping(result, "amber cross-hypervisor ping")
        time.sleep(8)
        lines.append("== captured on hv3's underlay ==")
        command(net["hv3"], "cat /tmp/week6-hv3.txt", lines)
        lines.append("== hv1: amber VXLAN after traffic ==")
        command(net["hv1"], "bridge fdb show dev vxlan494001", lines)
        lines.append("== hv3: amber VXLAN after traffic ==")
        command(net["hv3"], "bridge fdb show dev vxlan494001", lines)
        save("flood.txt", lines)

        lines = ["== amber and violet share 10.40.60.11 but are isolated =="]
        net["vi2"].cmd("timeout 8 tcpdump -ni vi2-eth0 > /tmp/week6-vi2.txt 2>&1 &")
        time.sleep(1)
        result = command(net["am1"], f"ping -c 3 -W 2 {TARGET}", lines)
        require_ping(result, "amber same-VNI ping")
        command(net["am1"], f"ip neigh show {TARGET}", lines)
        time.sleep(8)
        lines.append("== captured on violet VM vi2 during amber traffic ==")
        command(net["vi2"], "cat /tmp/week6-vi2.txt", lines)
        result = command(net["vi1"], f"ping -c 2 -W 2 {TARGET}", lines)
        require_ping(result, "violet same-VNI ping")
        command(net["vi1"], f"ip neigh show {TARGET}", lines)
        save("isolation.txt", lines)

        lines = ["== Every ordered pair within each tenant =="]
        addresses = plan(spec)["vms"]
        for tenant in spec["tenants"]:
            for src, _ in tenant["vms"]:
                for dst, _ in tenant["vms"]:
                    if src != dst:
                        result = command(net[src], f"ping -c 1 -W 2 {addresses[dst]['ip']}", lines)
                        require_ping(result, f"{src} to {dst}")
        save("connectivity.txt", lines)
    finally:
        net.stop()


def measure_blackhole():
    _, net = fresh_network("blackhole.yaml")
    try:
        lines = ["== Forced build: tenant MTU 1500 over underlay MTU 1500 =="]
        result = command(net["am1"], f"ping -c 2 -W 2 {TARGET}", lines)
        require_ping(result, "small ping through black-hole design")
        command(net["am1"], f"ping -c 2 -W 1 -s 1472 {TARGET}", lines)
        command(net["am2"], "iperf3 -s -D", lines)
        command(net["am1"], f"timeout 20 iperf3 -c {TARGET} -t 5", lines)
        for size in (1400, 1422, 1423, 1450, 1472):
            command(net["am1"], f"ping -M do -c 1 -W 1 -s {size} {TARGET}", lines)
        save("blackhole.txt", lines)
    finally:
        net.stop()


def measure_fix(filename, label, sizes):
    _, net = fresh_network(filename)
    try:
        lines = [f"== {label} =="]
        for size in sizes:
            result = command(net["am1"], f"ping -M do -c 1 -W 2 -s {size} {TARGET}", lines)
            if size == sizes[0]:
                require_ping(result, f"{label} boundary")
        command(net["am2"], "iperf3 -s -D", lines)
        result = command(net["am1"], f"timeout 20 iperf3 -c {TARGET} -t 5", lines)
        if "receiver" not in result:
            raise RuntimeError(f"iperf3 did not finish for {label}:\n{result}")
        return lines
    finally:
        net.stop()


def main():
    check_rejection()
    flood_and_isolation()
    measure_blackhole()
    a = measure_fix("mtu_a.yaml", "fix A: tenant MTU 1450, underlay 1500", (1422, 1423))
    b = measure_fix("mtu_b.yaml", "fix B: tenant MTU 1500, underlay 9000", (1472, 1473))
    save("fixes.txt", a + [""] + b)
    print("Week 6 assignment evidence saved in evidence6/", flush=True)


if __name__ == "__main__":
    main()
