#!/usr/bin/env python3
"""Publish a readable Week 4 report from a validated Mininet transcript."""

from html import escape
from pathlib import Path

from check_week4 import extract, validate


ROOT = Path(__file__).resolve().parent.parent
SESSION = ROOT / "netlab/evidence4/session.txt"
OUTPUT = ROOT / "docs/week4/index.html"
REPOSITORY = "https://github.com/DarrellLeeXD/programmble_network"

STEPS = [
    ("0 · Empty switch", "With no controller and no rules, h1 could not reach h2.", [
        ("Empty flow table", "EMPTY_FLOW"), ("h1 → h2: 100% loss", "EMPTY_PING")]),
    ("1 · Hub", "A flood rule restored all six ordered host paths, but h3 overheard h1 and h2.", [
        ("All-host ping", "HUB_PINGALL"), ("Flood rule and counter", "HUB_FLOW"),
        ("h3 packet capture", "HUB_CAPTURE")]),
    ("2 · MAC forwarding", "ARP flooded; destination MAC rules sent unicast frames to the correct ports. h3 captured no h1–h2 ICMP.", [
        ("All-host ping", "LEARNING_PINGALL"), ("h3 packet capture", "LEARNING_CAPTURE"),
        ("Flow table", "LEARNING_FLOW")]),
    ("3 · Firewall priority", "The equal-priority drop saw no packets in this run. At priority 40000 it blocked h1 → h3 and the reply to h3 → h1 while h1 → h2 remained reachable.", [
        ("First drop rule: ping", "LOW_FIREWALL_PING"), ("First drop rule: counter", "LOW_FIREWALL_FLOW"),
        ("High priority: h1 → h3", "HIGH_FIREWALL_H1H3"), ("High priority: h1 → h2", "HIGH_FIREWALL_H1H2"),
        ("High priority: h3 → h1", "HIGH_FIREWALL_H3H1"), ("High-priority flow table", "HIGH_FIREWALL_FLOW")]),
    ("4 · Controller", "The connected controller installed a table-miss rule and conversation flows with 60-second idle timeouts.", [
        ("Controller connected", "CONTROLLER_STATUS"), ("Two conversations", "CONTROLLER_PINGS"),
        ("Reactive flows", "CONTROLLER_FLOW")]),
    ("5 · Lost control channel", "Cached h1–h2 traffic survived at first. New h1–h3 traffic failed, and h1–h2 failed after its flows expired.", [
        ("Controller disconnected", "DISCONNECTED_STATUS"), ("Cached h1 → h2", "CACHED_PING"),
        ("New h1 → h3", "NEW_PING"), ("h1 → h2 after idle timeout", "EXPIRED_PING")]),
    ("6 · Standalone fallback", "After switching to standalone mode, h1 could reach h3 again through ordinary MAC learning.", [
        ("Fail-mode", "STANDALONE_MODE"), ("h1 → h3", "STANDALONE_PING")]),
]

ANSWERS = [
    ("Why did the first firewall rule have no effect, and why does h3 → h1 fail too?",
     "The first drop overlapped the destination-MAC forwarding rule at the same default priority, 32768. OpenFlow does not specify which equal-priority rule wins. In this run, the drop counted zero packets while h1 reached h3. At priority 40000, the drop won. When h3 pings h1, h1’s echo reply has source 10.40.0.1 and destination 10.40.0.3, so it is dropped too."),
    ("Why did one conversation survive controller failure?",
     "The controller had already installed h1–h2 flows in the switch, so those packets kept forwarding. A new h1–h3 packet matched the table-miss rule, which sent it to the disconnected controller; no forwarding flow arrived. After 60 seconds of idleness, the h1–h2 flows expired and that conversation failed too."),
    ("Secure or standalone for a campus network?",
     "I would choose secure for switches that enforce campus firewall policy. New traffic may stop when the controller fails, but the switch will not silently bypass the policy. Standalone keeps basic connectivity by falling back to MAC learning, at the cost of losing controller-installed security and traffic rules. Controller redundancy can reduce secure mode’s availability cost."),
]


def main():
    session = SESSION.read_text()
    errors = validate(session)
    if errors:
        raise SystemExit("Cannot publish invalid evidence:\n" + "\n".join(errors))

    step_html = []
    for title, explanation, observations in STEPS:
        details = "\n".join(
            f'<details><summary>{escape(label)}</summary><pre>{escape(extract(session, marker))}</pre></details>'
            for label, marker in observations
        )
        step_html.append(f'<section class="step"><h2>{escape(title)}</h2><p>{escape(explanation)}</p>{details}</section>')
    answers = "\n".join(
        f'<section><h3>{escape(question)}</h3><p>{escape(answer)}</p></section>'
        for question, answer in ANSWERS
    )
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Week 4 · OpenFlow lab · 4940</title>
<style>
:root {{ color-scheme: light; }}
body {{ font: 16px/1.6 system-ui,sans-serif; color:#152238; background:#f6f8fc; margin:0; }}
main {{ max-width:900px; margin:auto; padding:24px 20px 80px; }}
a {{ color:#075ca4; }} h1 {{ font-size:2.3rem; line-height:1.15; margin:14px 0; }} h2 {{ font-size:1.35rem; margin:0; }}
.eyebrow {{ color:#53657d; text-transform:uppercase; letter-spacing:.12em; font-size:.75rem; font-weight:700; }}
.intro,.step,.answers {{ background:white; border:1px solid #dbe4f0; border-radius:14px; padding:20px 24px; margin:18px 0; box-shadow:0 3px 12px #182c4610; }}
.step p {{ margin:8px 0 16px; }} .topology {{ display:grid; justify-items:center; gap:10px; margin:22px 0; }}
.hosts {{ display:flex; justify-content:center; gap:14px; flex-wrap:wrap; width:100%; border-top:2px solid #bdd2eb; padding-top:14px; }}
.node {{ min-width:105px; padding:12px; text-align:center; border-radius:12px; background:#e9f1fb; border:1px solid #bdd2eb; }}
.switch {{ background:#173b66; color:white; }} .node small {{ display:block; }}
details {{ border-top:1px solid #e2e8f0; padding:10px 0; }} summary {{ cursor:pointer; font-weight:600; }}
pre {{ background:#111b2c; color:#e8f1ff; padding:14px; border-radius:8px; overflow-x:auto; font-size:.78rem; line-height:1.45; }}
.answers h3 {{ font-size:1.08rem; margin-bottom:4px; }} .answers p {{ margin-top:0; }}
@media(max-width:520px) {{ h1 {{font-size:1.8rem}} .intro,.step,.answers {{padding:17px}} }}
</style></head><body><main>
<p><a href="../week3/">← Week 3</a></p><p class="eyebrow">WIC2005 · Week 4 · Student ID ending 4940</p>
<h1>OpenFlow, one rule at a time</h1>
<div class="intro"><p>Three Mininet hosts on <code>10.40.0.0/24</code> connect through Open vSwitch. I changed its flow table from empty to hub, MAC forwarding, firewall and controller-driven forwarding, then tested control-channel failure and standalone fallback.</p>
<div class="topology"><div class="node switch">s1<small>Open vSwitch</small></div><div class="hosts"><div class="node">h1<small>10.40.0.1 · port 1</small></div><div class="node">h2<small>10.40.0.2 · port 2</small></div><div class="node">h3<small>10.40.0.3 · port 3</small></div></div></div>
<p>These observations came from the <a href="{REPOSITORY}/actions/workflows/week4-evidence.yml">course Mininet container in GitHub Actions</a>. <a href="{REPOSITORY}/blob/main/netlab/evidence4/session.txt">Read the full transcript</a> or <a href="{REPOSITORY}/blob/main/netlab/README.md#week-4-openflow-lab">the lab README</a>.</p></div>
{''.join(step_html)}
<div class="answers"><h2>Wrap-up answers</h2>{answers}</div>
</main></body></html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
