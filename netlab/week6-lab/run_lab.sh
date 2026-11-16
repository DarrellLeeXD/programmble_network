#!/usr/bin/env bash
# Reproduce Week 6 lab Parts 1-6 inside the course's privileged Linux container.
set -euo pipefail
mkdir -p week6-lab/evidence
mn -c >/dev/null 2>&1 || true

mn --topo single,2 --mac --switch lxbr --controller none --ipbase 10.40.0.0/24 <<'MININET' > week6-lab/evidence/namespaces.txt 2>&1
dump
sh lsns -t net -o NS,PID,COMMAND
h1 ip -br link
sh ip -br link
exit
MININET

ip netns del red 2>/dev/null || true
ip netns del blue 2>/dev/null || true
ip link del br0 2>/dev/null || true
{
  set -x
  ip netns add red
  ip netns add blue
  ip link add veth-red type veth peer name red-br
  ip link add veth-blue type veth peer name blue-br
  ip link set veth-red netns red
  ip link set veth-blue netns blue
  ip link add br0 type bridge
  ip link set red-br master br0
  ip link set blue-br master br0
  ip link set br0 up
  ip link set red-br up
  ip link set blue-br up
  ip netns exec red ip addr add 10.40.9.1/24 dev veth-red
  ip netns exec red ip link set veth-red up
  ip netns exec blue ip addr add 10.40.9.2/24 dev veth-blue
  ip netns exec blue ip link set veth-blue up
  ip netns exec red ping -c 2 -W 2 10.40.9.2
  bridge fdb show br br0
  set +x
} > week6-lab/evidence/manual_bridge.txt 2>&1
ip netns del red
ip netns del blue
ip link del br0

mn -c >/dev/null 2>&1 || true
mn --topo single,2 --mac --switch lxbr --controller none --ipbase 10.40.0.0/24 <<'MININET' > week6-lab/evidence/vxlan.txt 2>&1
sh echo '== Part 3: VXLAN over IPv4 =='
h1 ip link add vxlan100 type vxlan id 100 local 10.40.0.1 remote 10.40.0.2 dstport 4789 dev h1-eth0
h1 ip addr add 10.40.100.1/24 dev vxlan100
h1 ip link set vxlan100 up
h2 ip link add vxlan100 type vxlan id 100 local 10.40.0.2 remote 10.40.0.1 dstport 4789 dev h2-eth0
h2 ip addr add 10.40.100.2/24 dev vxlan100
h2 ip link set vxlan100 up
h1 ping -c 2 -W 2 10.40.100.2
h2 timeout 4 tcpdump -ni h2-eth0 udp port 4789 > /tmp/week6-ipv4.txt 2>&1 &
h1 ping -c 1 -W 2 10.40.100.2
sh sleep 5
sh cat /tmp/week6-ipv4.txt
sh echo '== Part 4: IPv4 overhead and throughput =='
h1 ip link show h1-eth0
h1 ip link show vxlan100
h1 ping -M do -c 1 -W 2 -s 1422 10.40.100.2
h1 ping -M do -c 1 -W 2 -s 1423 10.40.100.2
h2 iperf3 -s -D
h1 iperf3 -c 10.40.0.2 -t 5
h1 iperf3 -c 10.40.100.2 -t 5
sh echo '== Part 5: VXLAN over IPv6 =='
h1 ip -6 addr add fd00:4940::1/64 dev h1-eth0
h2 ip -6 addr add fd00:4940::2/64 dev h2-eth0
h1 ping -6 -c 2 -W 2 fd00:4940::2
h1 ip link add vxlan106 type vxlan id 106 local fd00:4940::1 remote fd00:4940::2 dstport 4789 dev h1-eth0
h1 ip addr add 10.40.106.1/24 dev vxlan106
h1 ip link set vxlan106 up
h2 ip link add vxlan106 type vxlan id 106 local fd00:4940::2 remote fd00:4940::1 dstport 4789 dev h2-eth0
h2 ip addr add 10.40.106.2/24 dev vxlan106
h2 ip link set vxlan106 up
h1 ping -c 2 -W 2 10.40.106.2
h1 ip link show vxlan106
h1 ping -M do -c 1 -W 2 -s 1402 10.40.106.2
h1 ping -M do -c 1 -W 2 -s 1403 10.40.106.2
h2 timeout 4 tcpdump -ni h2-eth0 udp port 4789 > /tmp/week6-ipv6.txt 2>&1 &
h1 ping -c 1 -W 2 10.40.106.2
sh sleep 5
sh cat /tmp/week6-ipv6.txt
sh echo '== Part 6: underlay MTU mismatch =='
h2 ip link set h2-eth0 mtu 1400
h1 ping -c 2 -W 2 10.40.100.2
sh cat /sys/class/net/s1-eth2/statistics/tx_dropped
h2 cat /sys/class/net/h2-eth0/statistics/rx_dropped
h1 ping -c 2 -W 1 -s 1400 10.40.100.2
h1 timeout 20 iperf3 -c 10.40.100.2 -t 5
h1 ping -M do -c 1 -W 1 -s 1322 10.40.100.2
h1 ping -M do -c 1 -W 1 -s 1326 10.40.100.2
h1 ping -M do -c 1 -W 1 -s 1327 10.40.100.2
sh cat /sys/class/net/s1-eth2/statistics/tx_dropped
h2 cat /sys/class/net/h2-eth0/statistics/rx_dropped
h2 ip link set h2-eth0 mtu 1500
h1 ping -c 2 -W 2 -s 1400 10.40.100.2
h1 iperf3 -c 10.40.100.2 -t 5
exit
MININET

python3 week6-lab/check_lab.py
