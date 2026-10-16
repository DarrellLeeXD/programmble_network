# Week 2 netlab

This topology uses student ID suffix `4940`: IPv4 addresses are in
`10.40.0.0/16`, and IPv6 addresses are in `fd00:4940::/32`.

## Run in the course container

From this directory on a machine with Docker:

```sh
docker run -it --rm --privileged -v "${PWD}:/lab" -w /lab firdaussahran/netlab-mininet:1.0
```

Inside the container, run either version of the same network:

```sh
python3 build_topo.py topology.yaml
# at the mininet> prompt:
net
pingall
h1 ping -6 -c 1 fd00:4940::2
h1 ip neigh
exit

python3 build_topo.py topology.json
# at the mininet> prompt:
pingall
exit
```

The four-host topology has 12 directed host-to-host ping attempts. To see
the duplicate-address failure, temporarily give h4 the same `ip` and `ipv6`
values as h2, then run `python3 build_topo.py topology.yaml`. The script
reports both conflicting addresses before starting Mininet. Restore h4's
addresses to `.4` and `::4` afterward.

## Lab wrap-up

1. The data model is the switches, hosts, addresses, and links. YAML and JSON
   are two ways to write that same model. Conversion to JSON loses the YAML
   comments and the original formatting.
2. `check()` identifies both duplicate addresses before the network starts;
   `pingall` can show only a small failure count. IPv6 Duplicate Address
   Detection marks a duplicate address as `dadfailed`; IPv4 ARP does not
   perform that check.
3. `git diff` shows exactly which lines changed, while folders named
   `topology-v2-final` do not provide a reliable change history.
