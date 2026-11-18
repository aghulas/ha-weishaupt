# Weishaupt WTC / WCM for Home Assistant (through ebusd)

An **unofficial** Home Assistant integration for Weishaupt WTC condensing boilers and their WCM
controllers (system manager, heating modules, room units). It reads them through
[ebusd](https://github.com/john30/ebusd) and shows, per device, the live values, states, counters,
fault memory, settings and weekly programs.

Not affiliated with Weishaupt or with the ebusd project.

**Read-only unless you enable writes.** Out of the box it sends nothing to the heating system but
read requests. With writes enabled in its options, it can change **the settings a release of the
definitions proves writable** — 66 with definitions 0.5.5 — and nothing else, through a write
guard, with a confirmation for the settings that change the regulation
([Writing settings](#writing-settings)). Its ebusd client refuses every command other than `info`,
`find`, `read` and one form of register write.

Version 0.3 is a pre-release. Reading was tested against a simulated ebusd, a real ebusd without a
bus, and once on a heating system for twelve minutes. **Writing was tested against a simulated
ebusd and a real ebusd without a bus only: no write of this version has been sent to a bus yet**
(see [Tests](#tests)).

## What it needs

- **ebusd** connected to the eBUS of the heating system, reachable from Home Assistant on its TCP
  command port (8888 by default). A stock ebusd is enough: reading needs no special build.
- **A release of the Weishaupt definitions** loaded by that ebusd, started with `--scanconfig`:
  <https://github.com/aghulas/ebusd-configuration/releases> (tags `weishaupt-…`, with their own
  instructions). These definitions are not yet part of the official ebusd configuration.
- Home Assistant 2026.10 or later.

No MQTT broker, no `--enablehex`, no HTTP port.

To **write** settings, in addition:

- an ebusd build that computes the **run-time checksum** of the Weishaupt register writes
  (john30/ebusd#1825, not merged yet): the build of `aghulas/ebusd`. The integration checks it
  itself, without sending anything to the bus, and refuses every write on another build;
- for the settings written from the address of the vendor service tool (`ff`, 62 of the 66), the
  **telegram log** the ebusd add-on keeps (an SQLite file), readable by Home Assistant: a write
  from `ff` is refused while the service tool may be connected, and whenever the log cannot be read
  or is not fed.

### Compatibility

| Integration | Built for definitions | Accepts definitions | ebusd | Home Assistant |
|---|---|---|---|---|
| 0.3 | 0.5.5 | 0.5.3 and later 0.5.x | 26.1; writes need the build of `aghulas/ebusd` | 2026.10 and later |
| 0.2 | 0.5.2 | 0.5.2 and later 0.5.x | 26.1 (official, or the build of `aghulas/ebusd`) | 2026.10 and later |
| 0.1 | none: its own register table, raw telegrams | — | with `--enablehex` | 2026.1 and later |

The integration ships the metadata file of the definitions release it was built for
(`weishaupt-metadata-0.5.5.json`) and builds everything from it. ebusd cannot tell which release
it loaded, so at start-up the integration compares, message by message, what ebusd loaded with
that file:

- a device of the definitions that does not answer on the bus gets no device in Home Assistant;
- a message that ebusd did not load, or loaded with other fields, types or units, gets **no
  entity**, and one repair issue names the messages and the release expected. Load a release of
  the accepted range in ebusd, then reload the integration.

Why 0.5.3 and later 0.5.x: the second number of a definitions version changes when a message is
renamed, removed or retyped, the third when messages are only added. 0.5.0 renamed one message of
the system manager (`DHWOperationMode` became `DHWLoadingPriority`) and made a message of the
heating modules decodable, so definitions 0.4.x are not accepted. 0.5.1 and 0.5.2 added messages
(settings of the system manager and of a room unit), 0.5.3 five more reads; with an older 0.5.x in
ebusd those messages are missing and the comparison names them in a repair issue, the other
entities work. 0.5.4 differs from 0.5.3 only by the write definitions of the two flow limits of the
system manager's own circuit: with 0.5.3 in ebusd everything is read, and those two settings stay
read-only (64 writable instead of 66). 0.5.5 changes only the metadata (write ranges, risk
classes), which the integration ships itself: an ebusd with 0.5.3 or 0.5.4 behaves the same. An entity
created under a former message name keeps its entity id and history when the name changes: the
metadata says which name it had.

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
| Settings (setpoints, heating curve, limits, cascade and hot-water settings) | diagnostic sensors, read-only; with writes enabled, also a number entity for each proven setting | no (the numbers: yes) |
| Weekly programs | one diagnostic sensor per program: the state is today's switch times (`06:30-18:00, 19:00-21:00`), one attribute per day | no |
| Fault memory of a boiler | one diagnostic sensor: the state is the most recent entry (`W12`, `F11`), the attribute `entries` lists all of them with the values the boiler stored | yes |
| One counter per fault number, software versions, clock, system fault log, raw status bytes | diagnostic sensors | no |

Settings and weekly programs are created disabled to keep the list short: enable those you want
on the device page (*entities not shown*), they are then read like the others. Home Assistant
reloads the integration about 30 s after an entity is enabled; the integration then reads the
newly enabled entity first, before the other values.

Things to know:

- A value the device does not have (ebusd answers `-`) is shown as unknown. A temperature whose
  sensor is not fitted may read a fixed value instead (for example −40 °C on the boilers).
- Every memory read of the boilers starts with a byte that is 0 in a valid answer. A reading whose
  first byte is not 0 is dropped whole and the previous value is kept.
- A register that two messages of one device read is shown once.
- The same holds on a heating module or the system manager, where an outside sensor that is not
  fitted reads −100 °C. Nothing in the telegram marks these values, so they are shown as they are.
- States of value lists (operating phases, hot-water loading priority) are translated; in
  automations their values are keys in English (`burner_in_operation`, `priority`).

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

## Writing settings

Off by default. To turn it on: *Devices & services → Weishaupt → Configure*, tick **Enable writes
of the proven settings**, check the path of the telegram log, save. The integration reloads and
adds:

- a **number entity** (configuration section of its device) for each setting the definitions
  prove writable, with the range, step and unit of the definitions, enabled, named like the sensor
  of the same register with "(setting)" after it (*Normal room temperature (setting)*);
- a **write switch** on the ebusd device, **off**. Writes are refused while it is off; turning it
  off also withdraws every change waiting for a confirmation.

What is writable is decided by the definitions, not by the integration: a setting gets a number
entity only when the metadata of the release gives it **write conditions** (a lot of the
definitions proves the write on a bus and an evidence record names it) and ebusd loaded its write
definition as the release has it. Structural settings (circuit type, control variant, boiler
sequence…) never have write conditions. With definitions 0.5.5, 66 settings, 16 of them comfort:

| Device | Comfort | Regulation | Source |
|---|---|---|---|
| System manager (`ka`, 12) | hot-water setpoint | blocking time, boiler changeover time, power controller 1/P and I, de-couple minimum, calorifier and hot-water switching differentials, maximum hot-water loading time, legionella setpoint and circulation time, maximum flow temperature | `ff` |
| System manager, own circuit (`em1`, 7) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover, minimum and maximum flow temperature | `ff` |
| Heating modules 2 and 3 (`em2`, `em3`, 7 each) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover | `ff` |
| Heating modules 2 and 3 | | maximum and minimum flow temperature | `31` |
| Room units 1, 2, 3 (`fs1`–`fs3`, 11 each) | normal and setback room temperature, hot-water setpoint | frost protection room temperature, heating curve gradient, summer / winter changeover, maximum and minimum flow temperature, optimised switch-on lead time, frost protection limit, boiler boost offset | `ff` |

The source is the one the metadata gives each setting: the address the device takes the value from
(`ff`, the address of the vendor service tool; `31`, ebusd's own address). Written from another
source, a device acknowledges and keeps its value — the flow limits of the system manager's own
circuit are taken from `ff` only, those of the heating modules from `31`.

The system manager's own circuit reads three registers of the system manager: the integration
shows each register once. The maximum flow temperature, writable on both, has one number (through
`ka`); the normal and setback room temperatures, proven written through `em1` only, have a number
that writes through `em1`. So 65 number entities for 66 settings.

Ranges and steps are those of the definitions. Twelve settings cannot carry one in the CSV
(setback room temperature and heating curve of every heating circuit and room unit: fractional
bounds); the metadata gives theirs in the write conditions, with its source (10.0–21.5 °C and
2.5–40.0, step 0.5, from the room unit's manual): attributes `bounds_from: metadata` and
`range_source`. A setting with no range anywhere is not writable. The linked bounds (setback at or
below normal, minimum at or below maximum flow) are not in the metadata yet: the integration holds
them until the definitions carry them.

**Risk classes** (from the metadata):

- **comfort**: written as soon as you set the number;
- **regulation**: setting the number writes nothing, and is not an error. A notification says that
  the change waits for a confirmation, with a link to *Settings → Repairs*; the number's attribute
  `pending` shows the value waiting. The repair ("Confirm: … to …") opens a dialog with the device,
  the setting, the current and new values with the decimals of the step, the range and step, the
  bus address, the register and the source address; **Write to the controller** writes it, reads it
  back, and the last dialog says what happened (written and read back, with the telegram;
  unchanged; not taken over; refused, and why). It expires after 15 minutes. Repairs are shown to
  administrators only and cannot be confirmed by an automation: a regulation setting is never
  written without a person;
- **structural**: never writable.

Clicks: a comfort setting is one change of the number. A regulation setting is the change, then
the notification's link (or *Settings → Repairs*), the repair, *Write to the controller*, and
*Close* on the result. Home Assistant gives an entity no way to open a dialog by itself, has no
link to one repair's dialog, and always ends a repair with a result dialog: these steps cannot be
merged without giving up the confirmation.

**Each write**, in this order, stops at the first refusal and tells you why:

1. write switch on; the setting writable; ebusd known to compute the run-time checksum; ebusd
   reachable; for the settings proven written from ebusd's own address `31` (the flow limits of the
   heating modules), ebusd's address is `31`; the value in the range and on a step;
2. the setting read from the device, and the setting it is linked to: setback room temperature at
   or below the normal one, minimum flow temperature at or below the maximum;
3. for a write from `ff`, the telegram log: no telegram from `ff` that is not ours in the last 10
   minutes, a telegram of any source in the last 2 minutes; then at most one write per register
   every 10 s and 30 writes an hour (option *Maximum writes per hour*, 1 to 200: keep 30 in
   service, a higher value is for a supervised test campaign);
4. the telegram is built by the integration and handed to ebusd with
   `write [-s ff] -c <circuit> -h <bytes>`: ebusd sends it only if it matches the write definition
   it loaded for that circuit, checksum included;
5. the setting is read back from the device. A value not taken over is an error.

A value equal to the current one is not written. Every write sent gives a log line (`WRITE …`), an
event `weishaupt_write` (setting, register, source, value before, requested, read back, result,
telegram, user) and an entry in the diagnostics download (the last 50).

**How the run-time checksum is checked.** Today's builds do not announce it, and the version
string of the fork's build is the same as a stock one's. At start-up (only when writes are
enabled) the integration hands ebusd one write telegram twice under a circuit name no message has,
once with the correct checksum and once with the checksum byte of the definition: the fork's build
matches the first and refuses it for its circuit; a stock ebusd matches only the second. Both are
refused by ebusd before sending: nothing reaches the bus. The result is the attribute
`run_time_checksum` of the write switch (`present`, `absent`, `unknown`); anything but `present`
refuses every write.

## Diagnostics

*Devices & services → Weishaupt → ⋮ → Download diagnostics* gives the ebusd version, the scan
results (address, identification, software and hardware version; the bus carries no serial
number), the result of the comparison with the definitions, the counters of the reader (requests,
failed and dropped readings), the last readings and, with writes enabled, the writable settings, the
result of the checksum probe and the last writes. The address of ebusd is redacted. It is the
file to attach to a report about another boiler model or software version.

## Coming from 0.1

0.1 read and wrote registers with raw telegrams from its own table. 0.2 and 0.3 are a different
integration under the same name:

- **Only the proven settings can be written**: with definitions 0.5.5, the 66 numeric settings of
  0.1 that 0.1 can write (its other five, modulation limits and room factor, fail in 0.1 too). The
  choices (legionella day, circulation with legionella, boiler sequence, holiday level, adaption,
  control variation, circuit type), the holiday dates, the weekly programs and the clock are not
  proven yet: the `select` and `date` entities and the actions `weishaupt.set_time_program` and
  `weishaupt.set_clock` are gone, and automations that call them stop working. If you rely on
  them, stay on 0.1 until the definitions prove them.
- Regulation settings need a confirmation in *Repairs* for every change: an automation that sets
  one of them in 0.1 cannot do so any more. The hourly write limit is an option again, 30 by default
  (1 to 200), as in 0.1.2; it is not carried over from 0.1 by the update.
- Writes are off after the update, even if they were on in 0.1: enable them again in the options.
- **ebusd must load a definitions release.** 0.1 worked with any configuration and `--enablehex`;
  0.3 needs the release and no longer needs `--enablehex`; writes still need the fork's ebusd and
  the telegram log.
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
- `ebusd.py` (client), `model.py` (metadata), `writes.py` (what is writable, the bytes of a write)
  and `guard.py` (the write guard of 0.1, proven in service) have no Home Assistant dependency;
  `writer.py` runs a write, `number.py`, `switch.py` and `repairs.py` are its interface.
- `brand/` holds the images Home Assistant and HACS show; they are drawn by `scripts/make_brand.py`
  (an own mark, no vendor logo).

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
  without a bus, with one telegram of every message injected as already seen. The telegrams are
  those of the fixtures file of the definitions release (`tests/data/fixtures.json`): captured on
  a bus, 579 of them for all 531 messages. It is recorded with `scripts/capture_ebusd.py`, which
  fails if ebusd answers anything else than the fixtures say.
- The integration runs inside a Home Assistant test instance against a **simulated ebusd**
  (`tests/fake_ebusd.py`), a TCP server that replays those answers. It makes up no value.
- **Writes.** The telegram built for each of the 66 settings equals, byte for byte, the 112 write
  telegrams captured on the bus (changes and restores, fixtures of the release), from the source
  the capture and the metadata give (`tests/test_writes.py`). The recording also holds the answers
  of a real ebusd, the fork's build and a stock 26.1, to 448 write commands (the checksum probes, each captured
  write, the same with a wrong checksum), recorded without a bus; the simulated ebusd matches
  writes as ebusd does and gives each of these answers. Inside Home Assistant
  (`tests/test_ha_writes.py`): entities, the comfort path, the confirmation of a regulation
  setting, the sources `ff` and `31`, every refusal (switch, range, step, linked bound, rate,
  service tool, telegram log, run-time checksum absent or unknown, not writable), a value not taken
  over, a write ebusd does not send.
- `tests/test_packaging.py` applies the rules of HACS to `hacs.json`, the manifest and the brand
  images.
- hassfest, the validation of Home Assistant:
  `docker run --rm -v "$PWD":/github/workspace ghcr.io/home-assistant/hassfest`.
- Two workflows run on GitHub: `tests.yml` (the suite, with coverage) and `validate.yml` (hassfest
  and the HACS action, which looks at the pushed repository and cannot be run on local files).
- `custom_components/weishaupt/quality_scale.yaml` is the quality-scale checklist of Home
  Assistant, rule by rule.

**On a real bus.** The integration ran for twelve minutes, read-only, from a throwaway Home
Assistant test instance against the ebusd of the installation the definitions were established on
(definitions 0.5.2 at the time, ebusd 26.1 also serving its own polling and MQTT): the nine devices found by
the scan, no definitions mismatch, the first fill in about two minutes (61 messages), then about
eight requests a minute, never two closer than 2 s, of which a third were answered from the cache
of ebusd. No bus error, no lost signal, no reconnection of ebusd; the values equal those ebusd
published to its other clients at the same time.

What this does not prove: behaviour over days, while a boiler fires (the passive load messages of
the boilers are only sent then), and the values of an installation other than that one.

## History

- 0.3.0rc1: the confirmation of a regulation setting is no error any more, says what it writes
  (device, register, source, values with their decimals) and what it did; numbers enabled and named
  "(setting)"; a newly enabled entity is read first.
- 0.3 (pre-release): writes of the settings the definitions prove, behind the guard of 0.1, risk
  classes and a check of the run-time checksum of ebusd. 0.3.0b1 on definitions 0.5.2 (22
  settings, not published), 0.3.0b2 on definitions 0.5.5 (66 settings, 16 comfort).
- 0.2 (pre-release): read-only integration built from the metadata of the definitions.
- 0.1.0 (2026-10-30) and `main` until 2026-11-18: settings of the WCM controllers read and written
  as raw telegrams from a register table, write guard, time programs, clock.

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
