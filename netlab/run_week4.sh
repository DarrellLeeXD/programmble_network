#!/usr/bin/env bash
# Run the Week 4 OpenFlow lab in the course Mininet container.
set -euo pipefail
mkdir -p evidence4
mn -c >/dev/null 2>&1 || true

mn --topo single,3 --mac --switch ovs,datapath=user --controller none --ipbase 10.40.0.0/24 <<'MININET' 2>&1 | tee evidence4/session.txt
sh echo '@W4:PORTS@'
sh ovs-ofctl show s1
sh echo '@W4:EMPTY_FLOW@'
sh ovs-ofctl dump-flows s1
sh echo '@W4:EMPTY_PING@'
h1 ping -c 2 -W 1 h2

sh ovs-ofctl add-flow s1 actions=flood
sh echo '@W4:HUB_PINGALL@'
pingall
sh echo '@W4:HUB_FLOW@'
sh ovs-ofctl dump-flows s1
h3 timeout 4 tcpdump -ni h3-eth0 icmp > /tmp/h3-hub.txt 2>&1 &
h1 ping -c 3 -W 1 h2
sh sleep 4
sh echo '@W4:HUB_CAPTURE@'
sh cat /tmp/h3-hub.txt

sh ovs-ofctl del-flows s1
sh ovs-ofctl add-flow s1 arp,actions=flood
sh ovs-ofctl add-flow s1 dl_dst=00:00:00:00:00:01,actions=output:1
sh ovs-ofctl add-flow s1 dl_dst=00:00:00:00:00:02,actions=output:2
sh ovs-ofctl add-flow s1 dl_dst=00:00:00:00:00:03,actions=output:3
sh echo '@W4:LEARNING_PINGALL@'
pingall
h3 timeout 4 tcpdump -ni h3-eth0 icmp > /tmp/h3-learning.txt 2>&1 &
h1 ping -c 3 -W 1 h2
sh sleep 4
sh echo '@W4:LEARNING_CAPTURE@'
sh cat /tmp/h3-learning.txt
sh echo '@W4:LEARNING_FLOW@'
sh ovs-ofctl dump-flows s1

sh ovs-ofctl add-flow s1 icmp,nw_src=10.40.0.1,nw_dst=10.40.0.3,actions=drop
sh echo '@W4:LOW_FIREWALL_PING@'
h1 ping -c 3 -W 1 h3
sh echo '@W4:LOW_FIREWALL_FLOW@'
sh ovs-ofctl dump-flows s1
sh ovs-ofctl --strict del-flows s1 icmp,nw_src=10.40.0.1,nw_dst=10.40.0.3
sh ovs-ofctl add-flow s1 priority=40000,icmp,nw_src=10.40.0.1,nw_dst=10.40.0.3,actions=drop
sh sleep 2
sh echo '@W4:HIGH_FIREWALL_H1H3@'
h1 ping -c 3 -W 1 h3
sh echo '@W4:HIGH_FIREWALL_H1H2@'
h1 ping -c 3 -W 1 h2
sh echo '@W4:HIGH_FIREWALL_H3H1@'
h3 ping -c 3 -W 1 h1
sh echo '@W4:HIGH_FIREWALL_FLOW@'
sh ovs-ofctl dump-flows s1

sh ovs-testcontroller ptcp:6653 > /tmp/ovs-controller.log 2>&1 &
sh ovs-ofctl del-flows s1
sh ovs-vsctl set-controller s1 tcp:127.0.0.1:6653
sh sleep 4
sh echo '@W4:CONTROLLER_STATUS@'
sh ovs-vsctl show
sh echo '@W4:CONTROLLER_PINGS@'
h1 ping -c 2 -W 1 h2
h2 ping -c 2 -W 1 h3
sh echo '@W4:CONTROLLER_FLOW@'
sh ovs-ofctl dump-flows s1

sh pkill -f '[o]vs-testcontroller'
sh sleep 5
sh echo '@W4:DISCONNECTED_STATUS@'
sh ovs-vsctl list controller
sh echo '@W4:CACHED_PING@'
h1 ping -c 2 -W 1 h2
sh echo '@W4:NEW_PING@'
h1 ping -c 2 -W 1 h3
sh sleep 65
sh echo '@W4:EXPIRED_PING@'
h1 ping -c 2 -W 1 h2
sh ovs-vsctl set-fail-mode s1 standalone
sh sleep 20
sh echo '@W4:STANDALONE_MODE@'
sh ovs-vsctl get-fail-mode s1
sh echo '@W4:STANDALONE_PING@'
h1 ping -c 2 -W 1 h3
sh echo '@W4:END@'
exit
MININET

python3 check_week4.py evidence4/session.txt
