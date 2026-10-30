#!/usr/bin/env python3
"""Validate the observations captured from the Week 4 Mininet session."""

import re
import sys
from pathlib import Path


MARKER = re.compile(r"(?m)^(?:mininet> )*@W4:([A-Z0-9_]+)@$\n?")


def extract(session, name):
    markers = list(MARKER.finditer(session))
    for index, marker in enumerate(markers):
        if marker.group(1) == name:
            end = markers[index + 1].start() if index + 1 < len(markers) else len(session)
            return session[marker.end():end].strip()
    return ""


def packet_loss(output):
    matches = re.findall(r"(\d+)% packet loss", output)
    return int(matches[-1]) if matches else None


def packets_received(output):
    matches = re.findall(r"\d+ packets transmitted,\s*(\d+) received", output)
    return int(matches[-1]) if matches else None


def validate(session):
    errors = []

    def expect(name, description, predicate):
        section = extract(session, name)
        if not section or not predicate(section):
            errors.append(f"{name}: expected {description}")

    def ping(name, loss):
        expect(name, f"{loss}% packet loss", lambda s: packet_loss(s) == loss)

    def contains(name, description, pattern):
        expect(name, description, lambda s: re.search(pattern, s, re.I | re.S) is not None)

    expect("EMPTY_FLOW", "empty flow table", lambda s: "NXST_FLOW reply" in s and "actions=" not in s)
    ping("EMPTY_PING", 100)
    contains("HUB_FLOW", "flood rule with packet count", r"n_packets=[1-9]\d*.*actions=FLOOD")
    contains("HUB_PINGALL", "all hosts reachable", r"0% dropped")
    contains("HUB_CAPTURE", "h3 overheard h1 to h2", r"10\.40\.0\.1\s*>\s*10\.40\.0\.2")
    contains("LEARNING_PINGALL", "all hosts reachable", r"0% dropped")
    expect("LEARNING_CAPTURE", "zero packets captured at h3", lambda s: "0 packets captured" in s and "10.40.0.1 > 10.40.0.2" not in s)
    # Equal-priority overlap is unspecified, so record this trial without asserting its result.
    expect("LOW_FIREWALL_PING", "an observed ping result", lambda s: packet_loss(s) is not None)
    ping("HIGH_FIREWALL_H1H3", 100)
    ping("HIGH_FIREWALL_H1H2", 0)
    ping("HIGH_FIREWALL_H3H1", 100)
    contains("HIGH_FIREWALL_FLOW", "high-priority ICMP drop", r"priority=40000,icmp.*nw_src=10\.40\.0\.1.*nw_dst=10\.40\.0\.3.*actions=drop")
    contains("CONTROLLER_STATUS", "connected controller", r"is_connected:\s*true")
    contains("CONTROLLER_PINGS", "two successful conversations", r"0% packet loss.*0% packet loss")
    contains("CONTROLLER_FLOW", "reactive OpenFlow entries", r"idle_timeout=60")
    contains("CONTROLLER_FLOW", "table-miss to controller", r"priority=0.*actions=CONTROLLER")
    contains("DISCONNECTED_STATUS", "disconnected controller", r"is_connected\s*:\s*false")
    expect("CACHED_PING", "at least one cached-flow reply", lambda s: (packets_received(s) or 0) > 0)
    ping("NEW_PING", 100)
    ping("EXPIRED_PING", 100)
    contains("STANDALONE_MODE", "standalone fail-mode", r"standalone")
    ping("STANDALONE_PING", 0)
    return errors


if __name__ == "__main__":
    session = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence4/session.txt").read_text()
    errors = validate(session)
    if errors:
        for error in errors:
            print("FAIL:", error)
        sys.exit(1)
    print("Week 4 evidence checks passed")
