# Week 2 network lab

This network has three switches in a chain, with two hosts on each switch.
The student ID suffix `4940` gives the IPv4 block `10.40.0.0/16` and IPv6
block `fd00:4940::/32`; only the suffix is stored in this repository.

## Run the lab

From this `netlab` directory on a machine with Docker:

```sh
docker run -it --rm --privileged -v "${PWD}:/lab" -w /lab firdaussahran/netlab-mininet:1.0
```

Inside the container:

```sh
python3 build_topo.py topology.yaml
# At mininet>:
pingall
h1 ping -6 -c 1 fd00:4940::2
h1 ip neigh
exit

python3 build_topo.py topology.json
# At mininet>:
pingall
exit
```

Both files describe the same three switches, six hosts and eight links.
The captured run achieved 30/30 IPv4 replies and a successful h1-to-h2 IPv6
probe. See `evidence/pingall.txt` and `evidence/ipv6.txt`.

## Check bad data and collect evidence

`bad.yaml` contains duplicate IPv4 and IPv6 addresses for h2 and h6, plus
a link to nonexistent s9. Run `python3 build_topo.py bad.yaml` to see the
three `PROBLEM` lines before Mininet starts. The checked output is saved in
`evidence/check.txt`.

The GitHub Actions workflow at `.github/workflows/netlab-evidence.yml` runs
the course container and uploads its captured files as an artifact. The files
in `evidence/` are from its successful run, including `pingall.txt`,
`ipv6.txt`, `neigh.txt`, `macs.txt`, `dad.txt`, and the full `session.txt`.

## Generate the page

From this directory in the course container, run:

```sh
python3 make_page.py topology.yaml
```

The generator checks the topology and writes `netlab/docs/index.html`. For
GitHub Pages in this repository, copy that generated file to the repository
root's `docs/index.html`, commit it, and select branch `main` and folder
`/docs` in Settings → Pages. This keeps the original `netlab/` layout while
publishing the generated page.

## Lab wrap-up

1. The data model is the switches, hosts, addresses and links. YAML and JSON
   serialise the same model; JSON conversion loses YAML comments and layout.
2. `check()` rejects duplicate addresses and missing nodes before building.
   A small `pingall` loss would be much less specific. IPv6 DAD can mark a
   duplicate `dadfailed`, while IPv4 accepts the duplicate.
3. `git diff` shows exactly which lines changed, and commits preserve an
   inspectable sequence of work. Versioned folder names cannot do that.
