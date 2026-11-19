# Weishaupt WTC / WCM for Home Assistant (through ebusd)

An **unofficial** Home Assistant integration for Weishaupt WTC condensing boilers and their WCM
controllers (system manager, heating modules, room units). It reads them through
[ebusd](https://github.com/john30/ebusd) and shows, per device, the live values, states, counters,
fault memory, settings and weekly programs.

Not affiliated with Weishaupt or with the ebusd project.

**Read-only unless you enable writes.** Out of the box it sends nothing to the heating system but
read requests. With writes enabled in its options, it can change **the settings a release of the
definitions proves writable** — 71 settings, 12 weekly programs and the clock with
definitions 0.5.8 — and nothing else, through a write
guard, with a confirmation for the settings that change the regulation
([Writing settings](#writing-settings)). Its ebusd client refuses every command other than `info`,
`find`, `read` and one form of register write.

Version 0.8 is tested against a simulated ebusd in the test suite and on one heating system (see
[Supported devices and limits](#supported-devices-and-limits)): reads, writes of settings, choices,
program days and the clock, each read back, since 0.3.

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
| 0.4 – 0.8 | 0.5.8 shipped; a newer 0.5.x metadata file can be placed beside the configuration | 0.5.3 and later 0.5.x | 26.1; writes need the build of `aghulas/ebusd` | 2026.10 and later |
| 0.3 | 0.5.8 | 0.5.3 and later 0.5.x | 26.1; writes need the build of `aghulas/ebusd` | 2026.10 and later |
| 0.2 | 0.5.2 | 0.5.2 and later 0.5.x | 26.1 (official, or the build of `aghulas/ebusd`) | 2026.10 and later |
| 0.1 | none: its own register table, raw telegrams | — | with `--enablehex` | 2026.1 and later |

The integration ships the metadata file of the definitions release it was built for
(`weishaupt-metadata-0.5.8.json`) and builds everything from it. ebusd cannot tell which release
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
classes), which the integration ships itself: an ebusd with 0.5.3 or 0.5.4 behaves the same. 0.5.6
adds five choices, the program writes of room unit 1 and the clock, 0.5.7 and 0.5.8 the
programs of room unit 3 and of the system manager: with an older release in ebusd these stay read-only, the rest is the same. An entity
created under a former message name keeps its entity id and history when the name changes: the
metadata says which name it had.

Checked on one installation only (see the definitions): two WTC boilers in cascade, a system
manager, three heating circuits. Other models and software versions may differ.

## Supported devices and limits

Weishaupt heating systems whose controllers speak eBUS, as the definitions describe them:

| Device | Bus address(es) | Read | Written (with the run-time checksum build) |
|---|---|---|---|
| WTC gas condensing boiler (automat W-FM, one per boiler) | 08, 18 | live values, statistics and counters, fault memory and fault counters | — |
| WCM-SG system manager (cascade manager), and its own heating circuit | 15, 50 | live values, cascade and hot-water settings, its fault-log entry, weekly programs | settings, choices, programs proven writable, the clock |
| WCM-EM heating module (up to two) | 51, 52 | live values, settings | settings |
| WCM-FS room unit (up to three) | 35, 75, f5 | room values, settings, weekly programs | settings, programs proven writable |

What is read or written is decided by the definitions release, message by message, with evidence; a device or a
register they do not describe is not shown. Limits a second installation should know:

- **Tested on one installation**: two WTC boilers in cascade, one system manager, two heating modules, three room
  units, one software version each. Another model or version may answer differently: the comparison at start-up
  names what ebusd did not load as described, and a diagnostics download shows what was read.
- **Writes need the ebusd build** that computes the run-time checksum (until john30/ebusd#1825 is merged), and the
  telegram log for the settings written from the service tool's address. Without them everything is read only.
- **Programs**: only those proven writable on their device can be changed (heating program 1 of room units 1 and 3,
  and the others the metadata marks comfort); the others are shown, read only.
- **Absent sensors** read −40.0 °C (boiler) or −100.0 °C (system manager, heating module); the panel shows "no
  sensor", the entities show the value.
- **No time** is stored with a boiler's fault entry; the system manager's fault log shows the entry its operating
  unit has selected.
- **One request at a time** on the bus, at the gap set in the options (2 s by default): after a start, all settings
  are read within about 5 minutes and the program days within about 6.
- **Not a climate entity**: settings are numbers, selects and texts; no `climate` or `water_heater` entity yet.

**Reporting a problem**: open an issue with the diagnostics download (Settings → Devices & services → Weishaupt →
⋮ → Download diagnostics). The integration's own data (`data`) holds no address of ebusd, no file path, no entry
id and no user id; it does hold the values read. Home Assistant
itself adds to every download a `setup_times` object keyed by the entry id and, when the integration has repairs
open, an `issues` list whose ids contain it: an opaque local id, no address, which an integration cannot remove.

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

## The Weishaupt panel

An entry **Weishaupt** in the sidebar, for administrators only, shows the installation the way the
vendor's controllers and service tool organise it, and changes what the definitions prove
writable, through the same write path and guard as the entities (writes switch, hourly limit,
ranges and steps, source addresses of the metadata, read-back). *Open* still shows the entity.

- **Changing a setting**: *Change* on a writable row shows the value as a number (range and step) or
  as a choice (its labels), with the write path in words (bus address, register, source address)
  and its class. A comfort setting is written at once and read back. A regulation setting opens a
  confirmation in the panel with the facts of the repair (current and new value, allowed values,
  address, register, source): nothing is written until it is confirmed, and cancelling withdraws
  it. The result shows before → after, the frame sent and the read-back, as the logbook entry. A
  change made from an entity or an automation is still confirmed in *Repairs*.
- **Editing a program**: the programs proven writable on their device have *Edit* on their week
  grid. A day is changed by typing `06:30-18:00, 19:00-21:00` (or `-`), or by dragging on its bar
  to add a range in quarters of an hour; a click on a range removes it; a day can be copied to
  every day, Monday to Friday, the weekend or one day. Before writing, the panel shows the days
  changed, the writes they may cost (at most three a day: only changed slots are written) and the
  writes left this hour. Each day is written as by its program-day entity: three slots, read back.
  Programs not proven writable are read only.
- **Setting the clock**: the header's *Set the clock* asks for the same confirmation as the
  button entity and sends at second 00.
- **Faults** (read only), per device that has them: the boilers' fault memory, most recent first
  when its pointer is read, each entry with its code, the text of the manual's fault list as the
  definitions give it, and the values the automat stored with it (the automat stores no time);
  the boilers' fault counters with their texts; the fault-log entry the system manager's operating
  unit has selected, with its time (selecting another entry is a write, which the panel does not
  do). Messages no enabled entity reads have *Read now*: read once, at the pace of the bus, after
  what the entities wait for, with the number of requests shown.
- **Report and CSV**: *Printable report* opens every setting of the installation (device, menu,
  setting, value as read or why it is not, unit, range and step or the entries of a choice,
  writable and its class) in a page the browser prints, with page margins and the table header
  repeated on each page; *Export CSV* saves the same rows, comma-separated in English and semicolon-separated in
  French. The definitions carry no factory values yet; a value not read when the report is made
  is empty.

- **Devices and menus**: one node per device on the bus, with its bus address and software and
  hardware versions, and the menus of the definitions under it (*Info → Sensors*, *Process
  values*, *Statistics*, *Settings*, *Weekly programs*…).
- **The table of a menu**: name and description, value with its unit (a value-list entry by its
  label), when it was read, range and step, whether it is writable and its class (comfort,
  regulation), and a button to the entity. A value kept across a reload of the integration is
  shown with its age and marked as kept until it is read again. A register read by two messages
  (the system manager's direct circuit `em1` and its circuit 1) is shown once, with the value of
  whichever is read and where it is changed ("through em1"). A temperature the device sends as
  -40.0 °C (boiler) or -100.0 °C (system manager, heating module) is shown as *no sensor*: these
  are the values of a sensor that is not fitted (release notice of the definitions); a marker in
  the metadata replaces this rule when the definitions carry it. A value that is not read says
  why: not loaded by ebusd, or no enabled entity reads it.
- **Weekly programs**: every program the definitions know, as a week grid (bars over 24 h and
  the ranges in text); the programs proven writable are edited in the grid (above) or through
  their program-day entities, the others are read only. A program no enabled entity reads has a button *Read now*: its 21 slots
  are read once, at the pace of the bus and after what the entities wait for (about 45 s); it is
  not kept up to date unless its sensor is enabled. Opening the panel reads nothing.
- **Definitions**: the definitions in use (shipped or a file beside the configuration), how many
  readable messages ebusd loaded and each one it did not (write-only messages and the devices
  not on the bus by circuit), files not used and why, differences with ebusd, the entities named
  from the definitions by their entity ids, the ebusd version,
  and the state of writes (switch, run-time checksum, writes this hour).
- The offset of the clock master in the header.

The panel follows the language (English, French) and the theme of Home Assistant, and becomes one
choice list on a phone. Its file is served by the integration; nothing is added to the dashboards
and nothing has to be installed apart from the integration.

## Load on the bus

**After a restart of ebusd, the integration waits for its scan.** ebusd answers before it has scanned the
bus and loaded the definitions of every device. When a device seen before is not on the bus yet, or a device
on the bus has no definitions loaded yet, the integration does not compare with that partial view: it waits
and tries again (Home Assistant's retry, 5 s growing to 80 s), for up to 5 minutes, its entities kept and
unavailable meanwhile. After 5 minutes it goes on with what ebusd has and names what is missing; stale
entities are never looked for on such a partial view.

No measurement says how often these devices may be asked, so the integration is cautious and says
what it does:

- one request at a time, and **never two requests closer than 2 s** (option, 1 to 30 s);
- live values every 5 minutes (option, 1 minute to 1 hour);
- after a start, a **first pass** asks every enabled message once **from the device** (`read -m 0`):
  ebusd, which may have stayed up, would otherwise answer from its own cache, with a value up to a
  day old. Order: passive messages, live values, then what the entities that set a value show
  (numbers and selects, then the slots of enabled program days), then the rest. During the pass a
  message already read is asked again only when its value is older than 15 minutes, so that live
  values do not hold the pass up. With everything enabled (540 messages) and the default gap, the
  settings come from the device after about 5 minutes, the enabled program days after about 7, and
  the pass ends after about 21 to 25 minutes; then each class keeps its own interval;
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
  off also withdraws every change waiting for a confirmation. It is **off again after every
  restart of Home Assistant and every reload of the integration**, whatever it was before: writing
  is switched on for a session of changes, never left on by a restart.

What is writable is decided by the definitions, not by the integration: a setting gets a number
entity (a select for a choice) only when the metadata of the release gives it **write conditions** (a lot of the
definitions proves the write on a bus and an evidence record names it) and ebusd loaded its write
definition as the release has it. Structural settings (circuit type, control variant, boiler
sequence…) never have write conditions. With definitions 0.5.8, 71 settings of one value, 16 of them
comfort:

| Device | Comfort | Regulation | Source |
|---|---|---|---|
| System manager (`ka`, 12) | hot-water setpoint | blocking time, boiler changeover time, power controller 1/P and I, de-couple minimum, calorifier and hot-water switching differentials, maximum hot-water loading time, legionella setpoint and circulation time, maximum flow temperature | `ff` |
| System manager, own circuit (`em1`, 7) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover, minimum and maximum flow temperature | `ff` |
| Heating modules 2 and 3 (`em2`, `em3`, 7 each) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover | `ff` |
| Heating modules 2 and 3 | | maximum and minimum flow temperature | `31` |
| Room units 1, 2, 3 (`fs1`–`fs3`, 11 each) | normal and setback room temperature, hot-water setpoint | frost protection room temperature, heating curve gradient, summer / winter changeover, maximum and minimum flow temperature, optimised switch-on lead time, frost protection limit, boiler boost offset | `ff` |
| System manager, choices (2) | | legionella protection day (off, Monday … Sunday), circulation during legionella protection (off, on): **selects** | `ff` |
| Room units 1, 2, 3, choice (1 each) | | holiday temperature level (antifreeze, setback): **select** | `ff` |

### Weekly programs

Where the definitions prove the slots writable — with definitions 0.5.8 the five programs of room
units 1 and 3, and the hot-water and circulation programs of the system manager (its own circuit,
`50`; the hot-water program the installation applies); never room unit 2, which acknowledges slot
writes and keeps none — each program has **one text entity per day** (*Heating program 1 – Monday
(setting)*), in the configuration section of its device: 84 in all. Only a program whose slots the
metadata classes *comfort* is offered (all twelve are): a day is written without a confirmation, so
a program of another class would stay read-only. Its value is the day as the program sensors show it:
`06:30-18:00, 19:00-21:00`, up to three ranges in quarters of an hour, `-` for none. Heating program
1 is enabled when created (room units 1 and 3: 14 texts), the others not. A text is unknown until
its three slots are read; after a start they are read right after the live values and the
settings (numbers and selects), not after the whole first pass.

Setting a day writes its three slots and reads them back: comfort class, no confirmation, from
ebusd's own address as the definitions prove. Only the slots that change are written. It takes a few
seconds: the three slots are read first, then each changed slot is written and read back, every
request at the pace of the bus (one every 2 s by default), so about 8 s for one changed slot. Each
day written is kept in the attribute `last_write` of its text entity (time, before, after, the frames
sent, the result of the read-back; numbers and selects have the same attribute) and gives an entry
in the **logbook** of the entity (*Activity*, or the logbook panel): `<before> → <after> (<frames>):
read back ok`, one entry per day, per setting and per clock broadcast, visible without any setting.
The same facts go to the log at info level (`PROGRAM <device> <program> <day>: …`, `WRITE …`),
which Home Assistant shows only with `logger:` / `logs:` / `custom_components.weishaupt: info` in
`configuration.yaml`; a write that fails or stops halfway gives a short notification. A text that is
not a valid day (`2h-3h`, `25:00-26:00`, start after end, overlap, more than three ranges) is
refused with a translated message that says why and shows the format: the text entity has no
pattern, since Home Assistant would refuse a text that does not match it with the raw regular
expression as its message. A slot with
only one of its two times enabled is shown as unused and is rewritten unused.

The action **`weishaupt.set_program`** (device, program, and the days to change) writes several
days at once, for an automation or to copy a week. A whole week costs 21 writes at most (3 a day),
fewer when slots do not change. Every day is checked, then the slots are read from the device; if
more slots would change than writes are left within the hour (option *Maximum writes per hour*, 30
by default), **nothing is written** and the action fails with the count. A failure midway stops the
rest and says how many slots were written. It returns `written` and `unchanged` when asked for a
response.

### The clock

A diagnostic sensor on the *Installation* device, **Clock offset of the installation**, gives the
seconds the clock master is ahead of the clock of ebusd's host (negative: behind), from its last date
and time broadcast, which ebusd keeps: no request to the bus, read every minute. It is unknown when
the last broadcast came from ebusd itself, and when ebusd's host does not agree with Home Assistant
on the time within two minutes (another time zone or clock): the figure would then mean nothing.

With writes enabled, a button **Set the clock from Home Assistant** (same device). Regulation
class: pressing it opens a confirmation in *Repairs* with the current offset. Confirmed, the
integration keeps the bus quiet before second 00 of the next minute and broadcasts Home Assistant's
time **at second 00 exactly**, from ebusd's own address; every controller takes it over, seconds
included. If the connection to ebusd is not free within 2 s of second 00, **nothing is sent**: a
time sent late would set the whole installation late. There is no action: no automation sets the
clock. If an automation of yours broadcasts the time (for example at Home Assistant's start), make it
send at second 00 of the minute it carries, or use the button: a broadcast sent 12 s late sets every
controller 12 s late until the next correct one.

The source is the one the metadata gives each setting: the address the device takes the value from
(`ff`, the address of the vendor service tool; `31`, ebusd's own address). Written from another
source, a device acknowledges and keeps its value — the flow limits of the system manager's own
circuit are taken from `ff` only, those of the heating modules from `31`.

The system manager's own circuit reads three registers of the system manager: the integration
shows each register once. The maximum flow temperature, writable on both, has one number (through
`ka`); the normal and setback room temperatures, proven written through `em1` only, have a number
that writes through `em1`. So 65 numbers and 5 selects for 71 settings.

Ranges and steps are those of the definitions. Twelve settings cannot carry one in the CSV
(setback room temperature and heating curve of every heating circuit and room unit: fractional
bounds); the metadata gives theirs in the write conditions, with its source (10.0–21.5 °C and
2.5–40.0, step 0.5, from the room unit's manual): attributes `bounds_from: metadata` and
`range_source`. A setting with no range anywhere is not writable: it is listed in the diagnostics and
on the panel's definitions page, and logged at debug level only. The linked bounds (setback at or
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

Coming from 0.3.0b2, which created the numbers of the regulation settings disabled: the first start
of 0.3.0rc2 enables, once, the numbers the integration itself disabled (never one you disabled) and
reads them first. A reload of the integration keeps the values already read on screen, so entities
do not show *unknown*, and reads every enabled entity again in the first pass, in the usual order:
a value changed at the device itself does not wait for the end of its interval (a day for the
programs).

**Each write**, in this order, stops at the first refusal and tells you why:

1. write switch on; the setting writable; ebusd known to compute the run-time checksum; ebusd
   reachable; for the settings proven written from ebusd's own address `31` (the flow limits of the
   heating modules), ebusd's address is `31`; the value in the range and on a step;
2. the setting read from the device, and the setting it is linked to: setback room temperature at
   or below the normal one, minimum flow temperature at or below the maximum;
3. for a write from `ff`, the telegram log: no telegram from `ff` that is not ours in the last 10
   minutes, a telegram of any source in the last 2 minutes; then at most one write per register
   every 10 s and 30 writes an hour (option *Maximum writes per hour*, 1 to 200: keep 30 in
   service, a higher value is for a supervised test campaign). These counters are kept on disk
   (`.storage/weishaupt.<entry>.writes`), saved before each write is sent: a restart or a reload
   does not reset them;
4. the telegram is built by the integration and handed to ebusd with
   `write [-s ff] -c <circuit> -h <bytes>`: ebusd sends it only if it matches the write definition
   it loaded for that circuit, checksum included;
5. the setting is read back from the device. A value not taken over is an error.

A value equal to the current one is not written. Every write sent gives a log line (`WRITE …`), an
event `weishaupt_write` (setting, register, source, value before, requested, read back, result,
telegram, user) and an entry in the diagnostics download (the last 50). Each change asked by a user
(a setting, a program day, the clock) also gives an event `weishaupt_change`, which the logbook
shows on the entity.

**How the run-time checksum is checked.** Today's builds do not announce it, and the version
string of the fork's build is the same as a stock one's. At start-up (only when writes are
enabled) the integration hands ebusd one write telegram twice under a circuit name no message has,
once with the correct checksum and once with the checksum byte of the definition: the fork's build
matches the first and refuses it for its circuit; a stock ebusd matches only the second. Both are
refused by ebusd before sending: nothing reaches the bus. The result is the attribute
`run_time_checksum` of the write switch (`present`, `absent`, `unknown`); anything but `present`
refuses every write.

## Newer definitions without a new release of the integration

A release of the definitions that changes nothing the code has to know (settings that become
writable, write conditions, ranges, risk classes, labels, messages added) can be used with a reload of
the integration, without waiting for a release of the integration:

1. From the release page of the definitions, take `weishaupt-metadata-<version>.json` and
   `sha256sums-<version>.txt`.
2. Put both in the folder `weishaupt` of Home Assistant's configuration (beside `configuration.yaml`;
   create it). Updates of the integration do not touch it; backups keep it.
3. Reload the integration (*Devices & services → Weishaupt → ⋮ → Reload*).

The file is used only if its sha256 matches the `sha256sums` file beside it, its schema is the one
this version of the integration reads, and its version is newer than the definitions the integration
ships and within the range it accepts. Otherwise the shipped definitions are used and a repair issue
says why; a file that is used raises none. The definitions in use go to an info line of the log
(`definitions in use: …`) and to the diagnostics download.

Names: the translations shipped with the integration name an entity first. A message added in a
newer release, which they do not name yet, gets the label of the definitions (English and French,
in the language of Home Assistant, English otherwise), so that it has an entity with no new release
of the integration; a setting gets the suffix " (setting)" as the others. Unnamed fields of the
definitions (`ukn…`, marked skip) have no entity, as with the shipped definitions. The states of a
new value list are shown by their keys until a release of the integration translates them. The
diagnostics list the entities named from the definitions. Changes to existing entities (writable or
not, write conditions, ranges, classes) take effect at the reload. An entity the definitions in use
no longer yield (a field now marked skip, a message dropped) is removed from the registry at the
reload, as integrations do with stale entities, if its identifier follows the scheme of 0.2 and
later; one you changed (name, icon, area, labels, aliases, hidden or disabled, display precision
or unit) is kept, and a repair issue names it. Entities left by version 0.1 (other identifiers)
are never removed at a load: one repair lists them, and removes them only when you confirm it in
its dialog.

## Diagnostics

*Devices & services → Weishaupt → ⋮ → Download diagnostics* gives the ebusd version, the scan
results (address, identification, software and hardware version; the bus carries no serial
number), the result of the comparison with the definitions, the counters of the reader (requests,
failed and dropped readings), the last readings and, with writes enabled, the writable settings, the
result of the checksum probe and the last writes. In the integration's data the address of ebusd, the
telegram-log path, the entry id and the user ids are redacted, even inside texts. Home Assistant
itself adds to every download a `setup_times` object keyed by the entry id and, when the integration has repairs
open, an `issues` list whose ids contain it: an opaque local id, no address, which an integration cannot remove. It is the file to
attach to a report about another boiler model or software version.

## Coming from 0.1

0.1 read and wrote registers with raw telegrams from its own table. 0.2 and 0.3 are a different
integration under the same name:

- **Only the proven settings can be written**: with definitions 0.5.8, the 66 numeric settings of
  0.1 that 0.1 can write (its other five, modulation limits and room factor, fail in 0.1 too), and
  five of its choices (legionella day, circulation with legionella, holiday level of the three room
  units). The weekly programs come back for room units 1 and 3 (all five) and the system
  manager (hot water, circulation), as text entities per day and the action `weishaupt.set_program`, and the clock as a
  confirmed button. Not offered: the other choices (boiler sequence, adaption, control variation,
  circuit type), the holiday dates, the programs of room unit 2; the `date` entities and the actions
  `weishaupt.set_time_program` and `weishaupt.set_clock` are gone, and automations that call them
  stop working. If you rely on
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
- `panel.py` registers the panel and its WebSocket commands (administrators only): reads, and
  writes that call the Writer of `writer.py` exactly as the entities do; it builds no telegram.
  The panel's sources are in `frontend/` (TypeScript and Lit); `npm ci && npm test && npm run
  build` in that folder writes `custom_components/weishaupt/frontend/dist/weishaupt-panel.js`,
  the same bytes for the same sources and lock file. The built file is committed (HACS runs no
  build); the workflow *Frontend* rebuilds it and fails when it differs. It needs Node 24 or later.
- `brand/` holds the images Home Assistant and HACS show; they are drawn by `scripts/make_brand.py`
  (an own mark, no vendor logo).

### Tests

A new definitions release can be checked before it is shipped or placed beside a configuration:

```bash
WEISHAUPT_NEXT_METADATA=/path/to/weishaupt-metadata-0.5.14.json scripts/test.sh tests/test_next_metadata.py -s
```

(its `sha256sums-<version>.txt` beside it): accepted as a file beside the configuration, every message named,
what it adds or removes.

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
- **Writes.** The telegram built for each of the 71 settings equals, byte for byte, the 122 write
  telegrams captured on the bus for them (changes and restores, fixtures of the release), from the
  source the capture and the metadata give (`tests/test_writes.py`). The recording also holds the
  answers of a real ebusd, the fork's build and a stock 26.1, to 536 write commands (the checksum probes, each captured
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

- 0.8.0: the code of 0.8.0b2, checked on a heating system: ready for a second installation
  (devices that appear later reload the entry, a device absent for 7 days gets a repair offering
  its removal; diagnostics without address, path, user id or entry id in the integration's data;
  icons; issue templates; supported devices and limits).
- 0.7.0: the code of 0.7.0b2, checked on a heating system: fault tables in the panel (history
  and counters, read on demand with an honest cost), a printable report and a CSV export of the
  settings; after an ebusd restart the integration waits for the scan and never removes an
  entity on a partial view.
- 0.6.0: the code of 0.6.0b2, checked on a heating system: the panel writes settings, choices,
  program days and the clock through the guard of the entities; the writes switch is off after
  every restart or reload; the hourly counter survives restarts; no value is prefilled.
- 0.8.0b2: the diagnostics download redacts the config entry id too, wherever it appears.
- 0.8.0b1: ready for a second installation: devices that appear later reload the entry, a device
  absent for 7 days gets a repair offering its removal (confirmed by the user); diagnostics
  without user ids or addresses; icons; issue templates; a section on supported devices and
  limits; a test hook for the next definitions release.
- 0.7.0b2: the printed report has page margins, its header on each page and no row split across
  pages; choices list their entries instead of a numeric range; ranges read `−10 … −1 (0,5)` in the
  language of Home Assistant; a value not read says why; *Read now* counts only the requests it
  really sends and says what it waits behind.
- 0.7.0b1: fault tables in the panel (fault memory with texts, counters, the system manager's
  fault-log entry), read on demand; a printable report and a CSV export of the settings; the write
  switch's `writes_last_hour` follows each write; after a restart of ebusd, the entry waits for its
  scan instead of comparing with a partial view.
- 0.6.0b2: the write switch is off after every restart or reload; the hourly and per-register
  counters survive restarts; the panel never prefills a value it has not read, follows the switch
  live, shows "writing…", says when a call was interrupted, names the switch when it is the cause,
  and lets a proven program be edited before it is fully read.
- 0.6.0b1: the panel writes: settings and choices (regulation confirmed in the panel), days of
  the proven programs (typed or dragged, copied), the clock; same writer and guard as the
  entities.
- 0.5.0: the code of 0.5.0b3, checked on a heating system: the Weishaupt panel (read only) with the
  devices, their menus, tables, week grids, the definitions in use and the clock; absent sensors
  shown as such; stale entities of the current scheme removed, others only from a confirmed repair.
- 0.5.0b3: automatic removal limited to stale entities of the current identifier scheme; the
  entities of 0.1 are removed only from a repair the user confirms; options Home Assistant writes
  itself no longer count as a change by the user; long entity ids wrap on the panel.
- 0.5.0b2 (replaced by 0.5.0b3: it removed the entities left by 0.1 without asking): the panel shows values kept across a reload and follows a reload of the entry, a
  register read by two messages once, absent sensors as such, programs read once on demand,
  real entity ids, the messages not read and the settings left read-only; entities the
  definitions no longer yield are removed (customised ones kept, with a repair); a setting left
  read-only for want of a range is logged at debug, not as a warning.
- 0.5.0b1: the Weishaupt panel, read only: devices and menus, the table of each menu, weekly
  programs as a week grid, the definitions in use, the clock offset.
- 0.4.0: the code of 0.4.0b2. On a heating system: definitions 0.5.9 beside the configuration
  used at a reload without a restart, a corrupted copy refused with the bundled definitions kept.
- 0.4.0b2: no repair issue for a file in use, only for a refused one; entities of messages the
  shipped translations do not name yet are named from the labels of the definitions.
- 0.4.0b1: definitions from a verified file beside the configuration, used at a reload.
- 0.3.1: each change written gives a logbook entry on its entity, visible without a `logger:`
  setting; a malformed program day gets the translated message, not Home Assistant's raw pattern.
- 0.3.0: the code of 0.3.0rc6, proven on a heating system: after a restart the settings were read
  from the devices within 5 minutes and the enabled program days within 6; writes of numbers,
  choices, program days and the clock, each read back. Known limits (fixed in 0.3.1): the log lines
  are at info level; a malformed program day is refused by Home Assistant with its raw pattern.
- 0.3.0rc6: a first pass that asks every enabled message from the device and ends, settings and
  program days first; `last_write` attributes; the pattern of the program days back.
- 0.3.0rc5: a log line per program day written, a notification when a program write fails, clear
  messages for a day that is not in the expected format; after a reload, values kept on screen and
  read again in the first pass.
- 0.3.0rc4: after a start, the settings and the slots of enabled program days are read before the
  rest of the first pass.
- 0.3.0rc3: definitions 0.5.8; 12 weekly programs of room units 1 and 3 and of the system manager (text per day, action
  `set_program`); clock offset sensor and a set-clock button that sends at second 00 or not at all.
- 0.3.0rc2: definitions 0.5.6, five choices as selects; numbers that 0.3.0b2 created disabled
  enabled once; a successful confirmation ends in a "Success" dialog with the whole frame; values
  kept across a reload of the entry.
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
