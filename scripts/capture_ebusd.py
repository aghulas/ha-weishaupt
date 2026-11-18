#!/usr/bin/env python3
"""Record what a real ebusd answers for a definitions release, as test data for the simulated ebusd.

Development tool, not part of the integration. It runs an ebusd binary in a container WITHOUT any bus device,
loads the CSV of a definitions release, injects scan answers and telegrams as "already seen" messages
(`--inject`), and stores the text ebusd answers on its TCP command port:

- `info` (version, scanned devices, loaded files),
- `find -f -c <circuit>` for every circuit of the metadata (the definitions as ebusd loaded them),
- `read -m <age> -c <circuit> <name>` for one telegram of every message, taken from the fixtures file of the
  release (bus captures); the answer must be the text the fixtures give for that telegram.

Nothing is sent to a bus: there is none. Usage:

    scripts/capture_ebusd.py --ebusd /path/to/ebusd-linux-binary --config /path/to/weishaupt-ebusd-config-X.Y.Z \
        --fixtures tests/data/fixtures.json --out tests/data/ebusd-golden.json
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA = ROOT / "custom_components" / "weishaupt" / "metadata.json"
CONTAINER = "weishaupt-capture"
PORT = 18888
# Scan answer of every device: manufacturer 0x50, identification "W", software 11.04 as the scan of the test
# installation reports; the hardware version is made up (the scan answer is all the simulated ebusd needs).
SCAN_ANSWER = "0a50570000000011040102"


def command(text: str) -> str:
    with socket.create_connection(("127.0.0.1", PORT), timeout=10) as sock:
        sock.sendall(text.encode() + b"\n")
        buf = b""
        while b"\n\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
    return buf.split(b"\n\n", 1)[0].decode()


def run(ebusd: Path, config: Path, inject: list[str], scanconfig: bool = True) -> None:
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER, "-p", f"127.0.0.1:{PORT}:8888",
         "-v", f"{ebusd}:/ebusd:ro", "-v", f"{config}:/cfg:ro", "debian:trixie-slim",
         "/ebusd", "-f", *(["--scanconfig"] if scanconfig else []), "--configpath=/cfg", "-d", "/dev/null",
         "--inject", *inject],
        capture_output=True, check=True)
    for _ in range(40):
        time.sleep(0.5)
        try:
            info = command("info")
            if "messages: " in info and ("loaded" in info or not scanconfig):
                time.sleep(1.0)
                return
        except OSError:
            continue
    raise SystemExit("ebusd did not come up")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ebusd", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "tests" / "data" / "fixtures.json")
    parser.add_argument("--out", type=Path, default=ROOT / "tests" / "data" / "ebusd-golden.json")
    args = parser.parse_args()

    metadata = json.loads(METADATA.read_text())
    circuits = {c["circuit"]: c["address"] for d in metadata["devices"].values() for c in d["circuits"]}
    scans = [f"ff{address}070400/{SCAN_ANSWER}" for address in circuits.values() if address != "fe"]

    run(args.ebusd.resolve(), args.config.resolve(), scans)
    info = command("info")
    definitions = {circuit: command(f"find -f -c {circuit}") for circuit in circuits}

    # ID and addresses of every message, from what ebusd loaded
    lines: dict[str, list[str]] = {}
    for circuit, text in definitions.items():
        for row in csv.reader(io.StringIO(text)):
            if len(row) > 8:
                lines.setdefault(f"{circuit}/{row[2]}", row)
    # One telegram per message, from the fixtures of the release: bus captures, each with the text ebusd is
    # known to answer for it. A reading that is an example of an invalid answer is not the one replayed.
    chosen: dict[str, dict] = {}
    for reading in json.loads(args.fixtures.read_text())["readings"]:
        key = f"{reading['circuit']}/{reading['message']}"
        if reading["type"] == "write" or reading.get("case") == "first-byte-not-zero" or key not in lines:
            continue
        chosen.setdefault(key, reading)
    inject = scans + [reading["telegram"] for reading in chosen.values()]

    # Second run without --scanconfig: every file is loaded at start-up, before the telegrams are injected
    # (with --scanconfig the files are loaded after the scan answers, too late for the injected telegrams).
    run(args.ebusd.resolve(), args.config.resolve(), inject, scanconfig=False)
    reads, differ = {}, []
    for key, reading in chosen.items():
        circuit, name = key.split("/")
        reads[key] = command(f"read -m 9999 -c {circuit} {name}")
        if reads[key] != reading["text"]:
            differ.append((key, reads[key], reading["text"]))
    # A setting of which only the write telegram was captured: ebusd cannot be made to hold a read of it. Its
    # read answers the value of that write, as the fixtures give it (the evidence record has the read-back).
    written_only = {}
    for reading in json.loads(args.fixtures.read_text())["readings"]:
        key = f"{reading['circuit']}/{reading['message']}"
        if reading["type"] == "write" and key not in reads and key in lines:
            written_only[key] = reading["text"]
    reads.update(written_only)
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)

    version = info.splitlines()[0].removeprefix("version: ")
    args.out.write_text(json.dumps({
        "note": "Answers of a real ebusd without a bus device; see scripts/capture_ebusd.py",
        "ebusd": version, "definitions_version": metadata["definitions"]["version"],
        "info": info, "definitions": definitions, "reads": reads,
        "reads_not_decoded_here": sorted(written_only)}, indent=1, ensure_ascii=False) + "\n")
    print(f"{version}: {len(definitions)} circuits, {len(reads)} of {len(metadata['messages'])} messages read "
          f"({len(written_only)} taken from the fixtures as they are), "
          f"{len(differ)} answers that differ from the fixtures")
    for key, got, expected in differ[:10]:
        print(" ", key, repr(got), "fixtures:", repr(expected))
    if differ or len(reads) != len(metadata["messages"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
