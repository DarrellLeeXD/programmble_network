# Week 6 lab: namespaces, VXLAN and containers

This folder keeps the hands-on lab separate from the Week 6 overlay assignment
in the parent `netlab/` folder. The transcripts in `evidence/` came from the
course Mininet image on a privileged GitHub Actions Linux runner. To reproduce
Parts 1–6 from `netlab/`, run:

```sh
docker run --rm -i --privileged -v "$PWD:/lab" -w /lab \
  firdaussahran/netlab-mininet:1.0 bash week6-lab/run_lab.sh
```

Part 7 runs Alpine Docker on the Linux host in `.github/workflows/week6-evidence.yml`.
The course container is already a container and has no nested Docker daemon.

## Observations

1. `namespaces.txt` shows Mininet `h1` and `h2` as bash processes whose PIDs
   match `lsns -t net`. `h1` sees `h1-eth0`, while the outer namespace sees
   `s1-eth1` and `s1-eth2`.
2. `manual_bridge.txt` shows the hand-built `red` and `blue` namespaces,
   their two veth pairs and `br0`. `red` received both replies from
   `10.40.9.2`, and the bridge FDB learned a MAC on each port.
3. `vxlan.txt` captures IPv4 VXLAN on UDP port 4789 with VNI 100 between
   `10.40.0.1` and `10.40.0.2`. The overlay addresses are
   `10.40.100.1/24` and `10.40.100.2/24`.
4. In this five-second runner measurement, the underlay receiver rate was
   **46.8 Gbit/s** and the VXLAN overlay rate was **29.0 Gbit/s**. These
   virtual links share one host, so the absolute numbers are not physical
   link speeds. `h1-eth0` had MTU 1500, `vxlan100` MTU 1450, and DF ping
   payload 1422 worked while 1423 failed locally with `mtu=1450`.
5. The IPv6 underlay used `fd00:4940::1` and `fd00:4940::2`. The capture
   shows VNI 106 inside IPv6. `vxlan106` had MTU 1430; DF payload 1402
   worked and 1403 failed with `mtu=1430`.
6. Lowering only `h2-eth0` to MTU 1400 left small overlay pings working,
   but the 1400-byte payload received no replies. The largest successful DF
   payload was 1326 and 1327 failed. The bridge transmit and h2 receive
   drop counters rose together. TCP's receiver rate fell to **1.89 Mbit/s**;
   after restoring MTU 1500, the large ping replied and the receiver reached
   **29.2 Gbit/s** in this run.
7. `containers.txt` records Alpine's `eth0@if…` interface, its
   `/etc/os-release` and its container-local process list.

## Wrap-up answers

1. A Mininet host is a process in its own network namespace, with its own
   interfaces, IP addresses and routes. A Mininet cable is a veth pair:
   one end is moved into the host namespace and the other attaches to the
   bridge. A Linux bridge forwards between those outer ends and learns MACs.
2. IPv4 VXLAN added 50 bytes for every inner IP packet: inner Ethernet 14,
   VXLAN 8, UDP 8 and outer IPv4 20. That lowered the usable overlay MTU
   from 1500 to 1450. The measured receiver rates were 46.8 Gbit/s without
   VXLAN and 29.0 Gbit/s through it. The 50 bytes reduce payload efficiency,
   while encapsulation, decapsulation and virtual host CPU work also affect
   throughput. With IPv6 outside, the outer IP header is 40 rather than 20
   bytes: 70 bytes total overhead and an MTU of 1430.
3. During the mismatch, small encapsulated packets still fit the 1400-byte
   receiver link. Full-size packets did not; the receiving link dropped them
   without a useful path-MTU error reaching the sender. TCP repeatedly sent
   large segments, backed off and almost stopped. The 1326-byte DF ping
   payload plus 28 inner and 50 tunnel bytes is 1404: Linux's receiving
   interface tolerated four bytes above its nominal 1400 MTU, but not 1405.
4. A Docker container also has an isolated filesystem from its image and a
   separate process namespace. Mininet gives its hosts network namespaces
   and veth links, but they use the lab container's filesystem and are not
   packaged as independent Alpine-like images.
5. Week 5's P4 tunnel added a four-byte custom header ahead of IPv4; every
   switch on that path had to understand it, and our hop-limit field stopped
   indefinite forwarding loops. VXLAN over IPv4 adds 50 bytes but hides the
   tenant frame inside ordinary UDP/IP, so the underlay only needs to route
   IP. Routers decrement the outer IP TTL on a routed underlay. A bridged
   overlay still needs loop prevention such as correct VTEP forwarding rules;
   each new encapsulation can create a fresh outer TTL.
