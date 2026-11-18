# Weishaupt WTC / WCM for Home Assistant (through ebusd)

An **unofficial** Home Assistant integration for Weishaupt WTC condensing boilers and their WCM
controllers (system manager, heating modules, room units). It reads them through
[ebusd](https://github.com/john30/ebusd) and shows, per device, the live values, states, counters,
fault memory, settings and weekly programs.

Not affiliated with Weishaupt or with the ebusd project.

**This version is read-only.** It sends nothing to the heating system but read requests: no
setting can be changed from Home Assistant, there is no action, and its ebusd client refuses every
command other than `info`, `find` and `read`. Changing settings is planned for a later version, for
the settings whose write is proven on a bus.

Version 0.2 is a pre-release: it has been tested against a simulated ebusd and against a real
ebusd without a bus, not yet on a heating system (see [Tests](#tests)).

## What it needs

- **ebusd** connected to the eBUS of the heating system, reachable from Home Assistant on its TCP
  command port (8888 by default). A stock ebusd is enough: reading needs no special build.
- **A release of the Weishaupt definitions** loaded by that ebusd, started with `--scanconfig`:
  <https://github.com/aghulas/ebusd-configuration/releases> (tags `weishaupt-…`, with their own
  instructions). These definitions are not yet part of the official ebusd configuration.
- Home Assistant 2026.10 or later.

No MQTT broker, no `--enablehex`, no HTTP port.

### Compatibility

| Integration | Built for definitions | Accepts definitions | ebusd | Home Assistant |
|---|---|---|---|---|
| 0.2 | 0.4.3 | 0.4.2 and later 0.4.x | 26.1 (official, or the build of `aghulas/ebusd`) | 2026.10 and later |
| 0.1 | none: its own register table, raw telegrams | — | with `--enablehex` | 2026.1 and later |

The integration ships the metadata file of the definitions release it was built for
(`weishaupt-metadata-0.4.3.json`) and builds everything from it. ebusd cannot tell which release
it loaded, so at start-up the integration compares, message by message, what ebusd loaded with
that file:

- a device of the definitions that does not answer on the bus gets no device in Home Assistant;
- a message that ebusd did not load, or loaded with other fields, types or units, gets **no
  entity**, and one repair issue names the messages and the release expected. Load a release of
  the accepted range in ebusd, then reload the integration.

Checked on one installation only (see the definitions): two WTC boilers in cascade, a system
manager, three heating circuits. Other models and software versions may differ.

## Installation

Through HACS, as a custom repository:

1. HACS → menu → *Custom repositories* → add `https://github.com/aghulas/ha-weishaupt`, type
   *Integration*.
2. Install "Weishaupt WTC / WCM (ebusd, unofficial)". For a pre-release, enable *Show beta
   versions* for the repository. Restart Home Assistant.
3. *Settings → Devices & services → Add integration → Weishaupt*: enter host and port of ebusd.
   The connection is tested (`info` only) before the entry is created.

Without HACS: copy `custom_components/weishaupt` into the `custom_components` folder of the Home
Assistant configuration and restart.

To remove it: delete the integration entry in *Devices & services*, then uninstall it in HACS.

## What you get

A device for ebusd and one device per controller found on the bus: *Boiler 1*, *Boiler 2*,
*System manager*, *Heating module 2/3*, *Room unit 1/2/3*, and *Installation* for what the boilers
broadcast. On each of them, only entities:

| Kind | Shown as | Enabled when created |
|---|---|---|
| Live values (temperatures, burner load, ionisation, pump speed…) | sensors | yes |
| States (operating phase, flame, pumps, valves, fault…) | sensors with a list of states, binary sensors | yes |
| Operating counters (hours, burner starts, hours since service) | diagnostic sensors | yes |
| Settings (setpoints, heating curve, limits, cascade and hot-water settings) | diagnostic sensors, **read-only** | no |
| Weekly programs | one diagnostic sensor per program: the state is today's switch times (`06:30-18:00, 19:00-21:00`), one attribute per day | no |
| Fault memory of a boiler | one diagnostic sensor: the state is the most recent entry (`W12`, `F11`), the attribute `entries` lists all of them with the values the boiler stored | yes |
| One counter per fault number, software versions, clock, system fault log, raw status bytes | diagnostic sensors | no |

Settings and weekly programs are created disabled to keep the list short: enable those you want
on the device page (*entities not shown*), they are then read like the others.

Things to know:

- A value the device does not have (ebusd answers `-`) is shown as unknown. A temperature whose
  sensor is not fitted may read a fixed value instead (for example −40 °C on the boilers).
- Every memory read of the boilers starts with a byte that is 0 in a valid answer. A reading whose
  first byte is not 0 is dropped whole and the previous value is kept.
- A register that two messages of one device read is shown once.
- Entries of value lists (operating phases, hot-water mode) are shown with the name the
  definitions give them, in English in every language for now.

### Names, languages and entity ids

The interface is in English and French; names of devices and entities come from the metadata of
the definitions (`translations/*.json` are generated, see [Development](#development)).

This is the normal behaviour of Home Assistant, not a choice of this integration: it builds an
entity id from the name **in the language of the server** when the entity
is first created: the same sensor is `sensor.boiler_1_flow_temperature_i35` on an English server
and `sensor.chaudiere_1_temperature_de_depart_i35` on a French one. The unique id does not depend
on the language (it is built from the ebusd circuit, message and field), so renaming or changing
language later loses nothing — but do not copy entity ids from someone else's configuration.

## Load on the bus

No measurement says how often these devices may be asked, so the integration is cautious and says
what it does:

- one request at a time, and **never two requests closer than 2 s** (option, 1 to 30 s);
- live values every 5 minutes (option, 1 minute to 1 hour);
- counters and fault memory at start and then every hour, settings every 6 hours, weekly programs
  once a day;
- states the devices send by themselves (boiler status, room unit exchanges) are read from the
  cache of ebusd every 30 s and cost the bus nothing;
- a message is requested only while an **enabled** entity shows it: disabling entities lowers the
  load, enabling diagnostics raises it;
- ebusd answers from its cache when it already holds a recent enough value, for example after a
  restart of Home Assistant;
- no request while ebusd reports that it has no signal.

With the entities enabled when created on a two-boiler, three-circuit installation, 156 of 338
entities are enabled and 61 messages are requested: about 45 requests every 5 minutes in steady
state, and two minutes of one request every 2 s after a first start. Enabling the settings and the
weekly programs adds about 300 messages, read once (some ten minutes at that pace) and then every
6 hours for the settings and once a day for the programs. For comparison, the vendor's service tool was seen to send about two requests per second
while logging.

If ebusd itself is configured to poll (`--pollinterval`, poll priorities in the CSV), both loads
add up; the definitions release sets no poll priority.

## Diagnostics

*Devices & services → Weishaupt → ⋮ → Download diagnostics* gives the ebusd version, the scan
results (address, identification, software and hardware version; the bus carries no serial
number), the result of the comparison with the definitions, the counters of the reader (requests,
failed and dropped readings) and the last readings. The address of ebusd is redacted. It is the
file to attach to a report about another boiler model or software version.

## Coming from 0.1

0.1 read and wrote registers with raw telegrams from its own table. 0.2 is a different
integration under the same name:

- **Nothing can be written any more**: the `number`, `select`, `date` and `switch` entities and
  the actions `weishaupt.set_time_program` and `weishaupt.set_clock` are gone. Automations that
  call them stop working. If you rely on them, stay on 0.1 until a version with settings exists.
- **ebusd must load a definitions release.** 0.1 worked with any configuration and `--enablehex`;
  0.2 needs the release (and no longer needs `--enablehex` or the telegram log).
- **Every entity is new.** Unique ids are built differently, so the entities and devices of 0.1
  stay in the registry as unavailable; delete the old devices by hand once you no longer need
  their history. New entities get new entity ids.
- The config entry is kept (same host and port); its former options are dropped.
- Program sensors still exist, one per program, with the same state format and the attributes
  `monday` … `sunday`.

## Development

- `custom_components/weishaupt/metadata.json` is a verbatim copy of the metadata file of a
  definitions release; `translations/*.json` are generated from it and from
  `scripts/translations/` (the texts of the integration itself). For a new definitions release:
  `scripts/vendor_metadata.py --release-dir <folder with the release files> --version <x.y.z>`,
  which verifies the checksums. Never edit `translations/*.json` by hand; a test fails if they
  differ from what the script generates.
- `ebusd.py` (client) and `model.py` (metadata) have no Home Assistant dependency.
- `brand/` holds the images Home Assistant and HACS show; they are drawn by `scripts/make_brand.py`
  (an own mark, no vendor logo).
- `guard.py` is the write guard of 0.1, kept with its tests for the version that will write
  settings. Nothing imports it.

### Tests

```bash
scripts/test.sh
```

creates the test environment in `.venv` (once) and runs everything; arguments go to pytest
(`scripts/test.sh -k reader`). It needs **Python 3.14**: `requirements_test.txt` pins
`pytest-homeassistant-custom-component`, which pins Home Assistant (2026.10.4 today) and the pytest
plugins. With a bare `pytest` and no such environment, only the tests that need neither Home
Assistant nor asyncio run, and the others are skipped with a message. By hand:

```bash
python3.14 -m venv .venv && .venv/bin/pip install -r requirements_test.txt && .venv/bin/pytest
```

- The client, the model and the comparison are tested against **recorded answers of a real
  ebusd** (`tests/data/ebusd-golden.json`): the release loaded in ebusd 26.1 in a container,
  without a bus, with telegrams injected as already seen. The bytes of those telegrams are those
  quoted in the evidence records of the definitions (`tests/data/telegrams.json`). It is recorded
  with `scripts/capture_ebusd.py`.
- The integration runs inside a Home Assistant test instance against a **simulated ebusd**
  (`tests/fake_ebusd.py`), a TCP server that replays those answers and makes up values for the
  messages without a recording.
- `tests/test_packaging.py` applies the rules of HACS to `hacs.json`, the manifest and the brand
  images.
- hassfest, the validation of Home Assistant:
  `docker run --rm -v "$PWD":/github/workspace ghcr.io/home-assistant/hassfest`.
- Two workflows run on GitHub: `tests.yml` (the suite, with coverage) and `validate.yml` (hassfest
  and the HACS action, which looks at the pushed repository and cannot be run on local files).
- `custom_components/weishaupt/quality_scale.yaml` is the quality-scale checklist of Home
  Assistant, rule by rule.

What this does not prove: timing and load on a real bus, the behaviour of the devices, and the
values of an installation other than the one the definitions were established on.

## History

- 0.2 (pre-release): read-only integration built from the metadata of the definitions.
- 0.1.0 (2026-10-30) and `main` until 2026-11-18: settings of the WCM controllers read and written
  as raw telegrams from a register table, write guard, time programs, clock.

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
