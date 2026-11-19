#!/usr/bin/env python3
"""Record what a real ebusd answers for a definitions release, as test data for the simulated ebusd.

Development tool, not part of the integration. It runs an ebusd binary in a container WITHOUT any bus device,
loads the CSV of a definitions release, injects scan answers and telegrams as "already seen" messages
(`--inject`), and stores the text ebusd answers on its TCP command port:

- `info` (version, scanned devices, loaded files),
- `find -f -c <circuit>` for every circuit of the metadata (the definitions as ebusd loaded them),
- `read -m <age> -c <circuit> <name>` for one telegram of every message, taken from the fixtures file of the
  release (bus captures); the answer must be the text the fixtures give for that telegram;
- `find -f -w -c <circuit>` (the write definitions) and, for every captured write telegram of the fixtures, the
  answers to the forms of `write -h` the integration uses or must never see accepted: the probe of the run-time
  checksum (a circuit that is not the message's: matched, then refused before sending), the same with the
  placeholder checksum of the definition, a wrong checksum. Without a bus, a telegram ebusd accepts ends in
  `ERR: no signal`: nothing can be sent. With `--stock-image`, the same answers of a stock ebusd (no run-time
  checksum) are recorded too.

Nothing is sent to a bus: there is none. Usage:

    scripts/capture_ebusd.py --ebusd /path/to/ebusd-linux-binary --config /path/to/weishaupt-ebusd-config-X.Y.Z \
        --fixtures tests/data/fixtures.json --out tests/data/ebusd-golden.json [--stock-image john30/ebusd:v26.1]
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


def run(ebusd: Path | None, config: Path, inject: list[str], scanconfig: bool = True, image: str = "") -> None:
    """Start ebusd without a bus device: the binary `ebusd` in a plain image, or the ebusd of `image`."""
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)
    start = (["-v", f"{ebusd}:/ebusd:ro", "-v", f"{config}:/cfg:ro", "debian:trixie-slim", "/ebusd"] if not image
             else ["-v", f"{config}:/cfg:ro", "--entrypoint", "ebusd", image])
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER, "-p", f"127.0.0.1:{PORT}:8888", *start,
         "-f", *(["--scanconfig"] if scanconfig else []), "--configpath=/cfg", "-d", "/dev/null",
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


def crc(data: bytes) -> int:
    """Checksum of a Weishaupt register telegram over the bytes after it (CRC-8, polynomial 0x5C)."""
    value = data[0]
    for byte in data[1:]:
        for _ in range(8):
            value = ((value << 1) ^ 0x5C) & 0xFF if value & 0x80 else (value << 1) & 0xFF
        value ^= byte
    return value


def probe_commands(fixtures: list[dict], write_definitions: dict[str, str]) -> list[str]:
    """The `write -h` commands asked of ebusd for every captured write telegram."""
    placeholders = {}
    for circuit, text in write_definitions.items():
        for row in csv.reader(io.StringIO(text)):
            if len(row) > 8:
                placeholders[f"{circuit}/{row[2]}"] = row[7][:2]
    commands = []
    for reading in fixtures:
        key = f"{reading['circuit']}/{reading['message']}"
        if reading["type"] != "write" or key not in placeholders:
            continue
        data = bytes.fromhex(reading["master"])
        telegram = f"{reading['zz']}5023{len(data):02x}{data.hex()}"
        placeholder = f"{reading['zz']}5023{len(data):02x}{placeholders[key]}{data[1:].hex()}"
        wrong = f"{reading['zz']}5023{len(data):02x}{(data[0] ^ 1):02x}{data[1:].hex()}"
        source = "" if reading["qq"] == "31" else f"-s {reading['qq']} "
        commands += [f"write -c weishaupt-probe -h {telegram}", f"write -c weishaupt-probe -h {placeholder}",
                     f"write {source}-c {reading['circuit']} -h {telegram}",
                     f"write {source}-c {reading['circuit']} -h {wrong}"]
    return list(dict.fromkeys(commands))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ebusd", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "tests" / "data" / "fixtures.json")
    parser.add_argument("--out", type=Path, default=ROOT / "tests" / "data" / "ebusd-golden.json")
    parser.add_argument("--stock-image", default="", help="image of a stock ebusd, to record its write answers")
    args = parser.parse_args()

    metadata = json.loads(METADATA.read_text())
    circuits = {c["circuit"]: c["address"] for d in metadata["devices"].values() for c in d["circuits"]}
    scans = [f"ff{address}070400/{SCAN_ANSWER}" for address in circuits.values() if address != "fe"]

    run(args.ebusd.resolve(), args.config.resolve(), scans)
    info = command("info")
    definitions = {circuit: command(f"find -f -c {circuit}") for circuit in circuits}
    write_definitions = {circuit: text for circuit in circuits
                         if (text := command(f"find -f -w -c {circuit}")) and not text.startswith("ERR")}
    fixtures = json.loads(args.fixtures.read_text())["readings"]
    write_commands = probe_commands(fixtures, write_definitions)
    writes = {"fork": {c: command(c) for c in write_commands}}
    if args.stock_image:
        run(None, args.config.resolve(), scans, image=args.stock_image)
        writes["stock"] = {c: command(c) for c in write_commands}
        writes["stock_version"] = command("info").splitlines()[0].removeprefix("version: ")

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
        "info": info, "definitions": definitions, "write_definitions": write_definitions, "writes": writes,
        "reads": reads,
        "reads_not_decoded_here": sorted(written_only)}, indent=1, ensure_ascii=False) + "\n")
    print(f"{version}: {len(definitions)} circuits, {len(reads)} of {len(metadata['messages'])} messages read "
          f"({len(written_only)} taken from the fixtures as they are), "
          f"{len(differ)} answers that differ from the fixtures")
    for key, got, expected in differ[:10]:
        print(" ", key, repr(got), "fixtures:", repr(expected))
    readable = [k for k, m in metadata["messages"].items() if m.get("read") or m.get("passive")]
    if differ or set(reads) != set(readable):  # a write-only message (the date and time broadcast) has no read
        raise SystemExit(1)


if __name__ == "__main__":
    main()
