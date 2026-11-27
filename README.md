# Weishaupt WTC / WCM for Home Assistant (through ebusd)

An **unofficial** Home Assistant integration for Weishaupt WTC condensing boilers and their WCM
controllers (system manager, heating modules, room units). It reads them through
[ebusd](https://github.com/john30/ebusd) and shows, per device, the live values, states, counters,
fault memory, settings and weekly programs.

Not affiliated with Weishaupt or with the ebusd project. It is provided as is, without warranty (Apache License
2.0): the heating system remains the responsibility of its owner and installer, and the vendor's own controls
remain the reference.

**Read only unless you enable writes.** Out of the box it sends nothing to the heating system but read requests.
With writes enabled, it can change what a release of the definitions proves writable (with definitions 0.6.0, 83
of its 92 settings, the nine without a range kept read only, 12 weekly programs and the clock; see
[Writing settings](#writing-settings)) and nothing else, through
a write guard, with a confirmation by a person for every setting that changes the regulation. Its ebusd client
refuses every command other than `info`, `find`, `read`, one form of register write and the clock broadcast.

Words such as *circuit*, *source address*, *comfort* or *beside the configuration* are explained in
[Words used here](#words-used-here).

## First installation: reading

Do the steps in this order. Nothing here writes to the heating system.

### 1. ebusd, with the Weishaupt definitions loaded

- An eBUS adapter and **ebusd 26.1** connected to the bus. On Home Assistant OS this is an ebusd add-on. A stock
  ebusd (the add-on of [LukasGrebe/ha-addons](https://github.com/LukasGrebe/ha-addons)) is enough for reading.
  **If you mean to write settings later, install the add-on *eBUSd (Weishaupt CRC)* from the start** (see
  [What writing needs](#what-writing-needs)): it reads the same way, and changing add-on later means copying the
  definitions again, setting its options again and adding it to the entry ([Which ebusd](#which-ebusd)).
- **Definitions 0.6.0 or a later 0.6.x** loaded by that ebusd, started with `--scanconfig`: take a release tagged
  `weishaupt-…` from <https://github.com/aghulas/ebusd-configuration/releases>, the latest 0.6.x, and follow its
  notice. 0.6.0 is flagged *pre-release* on GitHub; from 0.6.1 the releases are normal ones. The figures of this
  README are those of the metadata 0.6.0 the integration ships; 0.6.1 has the same messages and the same counts. These definitions are not
  part of the official ebusd configuration yet: with a local `--configpath`, ebusd no longer uses the official
  online files.
- With the add-on: each option of ebusd is one entry of *Additional ebusd options*, and a folder in the add-on's
  configuration folder (`/addon_configs/<prefix>_ebusd/` on the host) is `/config/…` for ebusd (the add-on's
  documentation, *App config folder*).

**Check that ebusd loaded them**, before installing the integration, with `ebusctl` where ebusd runs. With the
add-on, the way used on the test installation: the add-on *Advanced SSH & Web Terminal*, its protection mode off
(on its own Info page); in its terminal, `sudo docker ps` shows the ebusd add-on's container
(`app_<prefix>_ebusd`), and each command below becomes `sudo docker exec app_<prefix>_ebusd ebusctl …`. The ebusd
add-on's documentation also offers a shell under its **Open Web UI**; that was not tried on the test installation. `ebusctl info` gives one line per device found, with the file it loaded:

```text
address 08: slave #11, scanned "MF=Kromschroeder;ID=W;SW=…;HW=…", loaded "kromschroeder/08.w.bc1.csv"
address 15: slave #2, scanned "MF=Kromschroeder;ID=W;SW=…;HW=…", loaded "kromschroeder/15.w.ka.csv"
```

| Device | Address | File ebusd should load |
|---|---|---|
| Boiler 1, boiler 2 | 08, 18 | `08.w.bc1`, `18.w.bc2` |
| System manager, and its own heating circuit | 15, 50 | `15.w.ka`, `50.w.em1` |
| Heating module 2, heating module 3 | 51, 52 | `51.w.em2`, `52.w.em3` |
| Room units 1, 2, 3 | 35, 75, f5 | `35.w.fs1`, `75.w.fs2`, `f5.w.fs3` |

The first line of `ebusctl info` names the ebusd build: `version: ebusd 26.1.p20261029` for the build with the
run-time checksum (`v26.1-weishaupt.1`), another string for a stock 26.1 (`ebusd 26.1.26.1` in the official image).
Only the devices of your installation appear. Then read one value, for example `ebusctl read -c bc1 SupplyTemp`
(the flow temperature of boiler 1). A device that loaded another file, or none, does not answer as these
definitions expect: do not go on with it, the integration will name its messages as missing.

### 2. Let Home Assistant reach ebusd

The integration talks to ebusd's TCP command port, **8888** unless ebusd was started with another `--port`.

- **ebusd as an add-on of the same Home Assistant**: nothing to type. On Home Assistant OS the integration lists the
  ebusd add-ons installed (from the Supervisor) with their state; tick those it may use (see
  [Which ebusd](#which-ebusd)). Each add-on's host name is `<prefix>-ebusd` (the prefix of the add-on's folder
  `<prefix>_ebusd` with a hyphen, shown on its Info page) and its port 8888. The integration connects through Home
  Assistant's internal network: it was checked on the test installation with port 8888 not published, reading as
  usual. Publishing the port on the host is only for clients outside Home Assistant.
- **ebusd on another machine**: its address and port.

Anyone who can open this port can send ebusd any command, writes to the boilers and controllers included. Publish
port 8888 of the add-on on the host (its *Network* settings) only if another machine needs it, and keep ebusd on a
network you trust.

### 3. Install the integration through HACS

[HACS](https://hacs.xyz) must be installed first.

1. HACS → ⋮ → *Custom repositories* → add `https://github.com/aghulas/ha-weishaupt`, type *Integration*.
2. Install *Weishaupt WTC / WCM (ebusd, unofficial)*, then restart Home Assistant.

Without HACS: copy `custom_components/weishaupt` into the `custom_components` folder of the Home Assistant
configuration and restart.

### 4. Add the entry

*Settings → Devices & services → Add integration → Weishaupt*, then *ebusd (add-on or address)* (the other
choice, the MQTT bridge, is [With Weishaupt2MQTT](#with-weishaupt2mqtt-mqtt)). On Home Assistant OS: tick the ebusd add-ons (the
running ones are ticked), and, if ebusd also runs elsewhere, its host and port. Otherwise: host and port from
step 2. The connection is tested (`info` only) before the entry is created; *No ebusd answers at this address*
means none of them could be reached. A stopped add-on is kept without being tested.

### 5. What you then see

- A device **ebusd** and one device per controller found on the bus: *Boiler 1*, *Boiler 2*, *System manager*,
  *Heating module 2*, *Heating module 3*, *Room unit 1/2/3*, and *Installation* for what is broadcast.
- On an installation with all nine devices, 496 entities, 185 of them enabled: live values, states, operating
  counters, fault memories. Settings and weekly programs exist as disabled diagnostic sensors: enable those you
  want ([What you get](#what-you-get)).
- The first values within a few minutes: after a start every enabled message is asked from the device, one request
  every 2 s (85 messages with the entities enabled by default, 13 of them from ebusd's cache).
- Under *Settings → Repairs*, if something is wrong: *No Weishaupt device found on the bus*, or *The definitions
  loaded by ebusd are not those this integration expects*, which names the messages and the release expected
  (those messages get no entity; the others work).
- An entry **Weishaupt** in the sidebar for administrators ([the panel](#the-weishaupt-panel)).

**If ebusd moves** (another add-on, so another host name, or another machine): see [Which ebusd](#which-ebusd).
An add-on already in the entry's list is followed with no step; a new one is added with *Settings → Devices &
services → Weishaupt → ⋮ → Reconfigure*. The entry, its devices, entities, history and options are kept.

To remove it: delete the integration entry in *Devices & services*, then uninstall it in HACS.

## With Weishaupt2MQTT (MQTT)

From 1.4.0 the integration can use the bridge [weishaupt2mqtt](https://github.com/aghulas/weishaupt2mqtt)
instead of talking to ebusd itself. The bridge (a Home Assistant add-on, or a container) holds ebusd, the
definitions and the write guards, and publishes the heating system on MQTT; the integration then reads and
writes through Home Assistant's MQTT integration only. This is the setup of the test installation since
2026-11-25. The rest of this README describes the ebusd mode; what differs is below.

### A new installation, with the bridge alone

From 1.5.0 the entry is created against the bridge: no ebusd add-on and no ebusd address are needed, and
steps 1 and 2 of [First installation](#first-installation-reading) do not apply (the bridge ships the
definitions and keeps its ebusd to itself).

1. Have an MQTT broker and Home Assistant's MQTT integration set up on it (*Settings → Devices & services →
   Add integration → MQTT*; on Home Assistant OS the Mosquitto add-on is found by itself).
2. Install and start the bridge as its README says, on the same broker, with no other ebusd running on the
   adapter (one adapter, one ebusd). `weishaupt/bridge/state` then reads `online`.
3. Install this integration ([step 3](#3-install-the-integration-through-hacs) above) and restart Home
   Assistant.
4. *Settings → Devices & services → Add integration → Weishaupt → Weishaupt2MQTT (MQTT bridge)*, and give the
   base topic of the bridge (`weishaupt` unless you changed it). The integration looks for the bridge on that
   topic before it creates the entry: it subscribes to `bridge/state` and `bridge/info` (both retained),
   waits up to 5 seconds and publishes nothing. What it may answer:
   - *Home Assistant's MQTT integration is not set up*: step 1.
   - *No Weishaupt2MQTT bridge was found on this base topic*: the bridge is not started, has another base
     topic, or publishes to another broker than the one Home Assistant uses.
   - *The Weishaupt2MQTT bridge on this base topic is offline*: it ran and stopped (its last will reads
     `offline`). Start it and submit again.
   - *The bridge on this base topic is already configured*: an entry exists for it.

What you then see is as in [step 5](#5-what-you-then-see), with a device **Weishaupt2MQTT** in place of
**ebusd**. Such an entry knows no ebusd: its *Reconfigure* menu has no *Telegram log of each ebusd*, and its
diagnostics download holds what the bridge announced (`bridge`) with an empty list of ebusd.

### An existing entry in the ebusd mode

1. Install and start the bridge as its README says, the ebusd add-on stopped (one adapter, one ebusd), and
   check that `weishaupt/bridge/state` reads `online`. Home Assistant's MQTT integration must be set up on
   the same broker.
2. On the entry: *⋮ → Reconfigure → Weishaupt2MQTT (MQTT bridge)*, give the base topic of the bridge
   (`weishaupt` unless you changed it) and submit. The entry reloads; devices, entities, history and
   options are kept. This step does not look for the bridge: with a wrong topic the entry waits (*No
   weishaupt2mqtt bridge info received*) until the topic is corrected the same way.

### In this mode

- The switch **Writes** switches the bridge's user-level writes on and off. Switching it off also switches
  the bridge's installer level off.
- The option *Enable writes of the proven settings* (*Reconfigure → Bus load and writes*) is still needed
  before the switch **Writes** acts.
- Regulation settings still wait for a confirmation, and are then sent to the bridge's installer level,
  which the integration never switches on: publish `{"installer_writes_enabled": true}` on
  `weishaupt/bridge/config/set` (*Developer tools → Actions → `mqtt.publish`*), and again after each time
  **Writes** was switched off, or they are refused (`installer_writes_disabled`). The add-on option of the
  same name only counts until the bridge's switches are first changed at run time.
- Of [What writing needs](#what-writing-needs), the ebusd build and the telegram log do not apply: the
  bridge runs its own ebusd, with the checksum, and the integration reads no telegram log in this mode.
- Write the room unit's copy of a circuit setting: on the test installation the regulation follows it, not
  the heating module's (notice of the definitions 1.3.1, *Known limits*; the item *Two copies of a setting*
  further down predates that test).
- The clock is not offered.
- The limits of the bridge apply, in particular: `online` does not prove that values are fresh (its README,
  *Known limits*).

To go back, or to move an entry made for the bridge to an ebusd: stop the bridge, start the ebusd add-on,
then *⋮ → Reconfigure → ebusd (the list, and which one to use)*.

## Which ebusd

There is one eBUS adapter, so one ebusd uses it at a time. On Home Assistant OS an installation may have several
ebusd add-ons, started one at a time: the stock *eBUSd*, *eBUSd (Weishaupt CRC)* with the run-time checksum, a test
build. Each has its own host name, its own definitions folder and its own telegram log. The entry keeps a list of
the ebusd it may use and picks one:

- **Follow the running ebusd** (the default for a new entry): the one that answers with a signal on the bus. You
  switch by starting the other add-on and stopping the one in use, in *Settings → Add-ons*; after about three
  failed connections (about a minute) the integration asks the others and moves to the one that answers. A lost
  signal alone (adapter, bus) never moves it while the ebusd in use still answers.
- **Pinned**: one ebusd only, never another. An entry created before 0.12.0 is pinned to its address, so it behaves
  as before until you change it.

Where: *Settings → Devices & services → Weishaupt → ⋮ → Reconfigure → ebusd*. One step edits the list (which
add-ons, another ebusd by address) and the follow/pin choice. The *Configure* button opens the
[panel](#the-weishaupt-panel), not these settings, so Reconfigure is their way in. The integration never starts,
stops or configures an add-on: stopping an ebusd add-on cuts it for every other client too (MQTT included), so that
stays your decision.

**What a switch does.** Choosing the ebusd sends `info` to each one and nothing else; the bus is not involved. The
integration then reloads on the new ebusd, as after a restart:

- the same devices and entities, with their entity ids and history (a gap of *unavailable* while the add-ons are
  swapped);
- the values shown are the last ones read, then every enabled message is read once from the devices (a few
  minutes); if the new ebusd is still scanning the bus, the integration waits for it, up to 5 minutes;
- the definitions are compared again: **each add-on has its own definitions folder**, so load the same release in
  each, or the repair about the definitions names what differs;
- **writes**: the switch *Writes* is off and every change waiting for a confirmation is dropped; the build of the
  new ebusd is checked again before anything can be written; the hourly write limit carries over;
- the panel and the diagnostics show the ebusd in use, by its name, and its build.

**What each ebusd allows.** Reads are the same with every build. The build is found without sending anything to the
bus (*Run-time checksum* on the panel's definitions page). The build that computes the run-time checksum writes
every controller; a stock ebusd writes the non-boiler controllers once *Allow writes on a stock ebusd* is enabled
(off by default):

| ebusd | Run-time checksum | Writes |
|---|---|---|
| eBUSd (Weishaupt CRC), build `v26.1-weishaupt.1` | `present` | allowed, through the guard |
| eBUSd (Weishaupt next, test), pre-release `v26.1-weishaupt.2-rc1` | `present` expected | allowed when `present`; a test build |
| stock eBUSd 26.1 | `absent` | non-boiler controllers allowed with *Allow writes on a stock ebusd*; boiler automats refused |
| any other answer | `unknown` | refused |

On a stock ebusd the write carries the checksum byte of the write definition (its placeholder), not a computed one.
On-site validation on 2026-11-23 showed a stock ebusd 26.1 writes every published setting of the non-boiler
controllers — the system manager (`ka`, `15`), the heating modules (`em1`–`em3`) and the room units (`fs1`–`fs3`) —
end to end, from sources `ff` and `31`; those controllers accept the placeholder checksum byte on the bus and take
the value. This is opt-in (*Allow writes on a stock ebusd*, off by default) because it bypasses the integration's
build check. The boiler automats (`08`/`18`) are never written on a stock ebusd: that was never tested, and today
no boiler setting is proven writable anyway. `unknown` is always refused. The test build's other features (composite
reads, longer message IDs) need nothing from the integration: with definitions that use them, its messages simply
load.

**When the ebusd in use does not answer**, its entities are unavailable and a repair says which ebusd answer and,
for an add-on, whether it is started. When another ebusd answers, the repair offers to use it (pinned) or to follow
the running one; that changes the entry only. Two ebusd answering with a signal at once (two add-ons started, one
adapter) raise a repair as well; the integration keeps the one it uses and does not switch between them.

Each ebusd has its own **telegram log** for the writes from `ff`: *⋮ → Reconfigure → Telegram log of each ebusd*.

## Words used here

| Word | Meaning |
|---|---|
| definitions, definitions release | The files that tell ebusd how to decode each message of these devices (one CSV per device), published as releases `weishaupt-<version>` with a **metadata** file the integration reads |
| circuit | In ebusd: the name of a device's file, used in commands (`-c ka`). Where this README means the heating circuit of a boiler installation, it says *heating circuit* |
| register | one value a controller keeps at a numbered place, read and written by these messages; a setting is one register |
| scan | at start-up (`--scanconfig`), ebusd asks every device on the bus for its identification and loads the file the definitions give for it |
| `bc1`, `bc2` | the two boilers, addresses `08`, `18` |
| `ka` | the system manager (cascade manager), address `15` |
| `em1` | the system manager's own heating circuit, address `50`: the same device as `ka`, not a module |
| `em2`, `em3` | heating modules 2 and 3, addresses `51`, `52` |
| `fs1`–`fs3` | room units 1 to 3, addresses `35`, `75`, `f5` |
| address | the hexadecimal address of a device on the eBUS; `fe` is a broadcast to all |
| source address | the address a write is sent from: `31` is ebusd's own (its default), `ff` the vendor's service tool's. A device keeps some settings only when written from the source the definitions give |
| service tool | the vendor's diagnostic software, connected to the bus by an installer; it sends from `ff` |
| stock ebusd / ebusd with the run-time checksum | the official ebusd, which does not compute the run-time checksum (it writes the non-boiler controllers only with *Allow writes on a stock ebusd*, and never a boiler automat); the build of `aghulas/ebusd` (also called the fork's build), which computes it and writes every controller |
| run-time checksum | a checksum over the register and the value that these devices require in a write; ebusd must compute it when it sends (`[WCRC]` in the definitions' comments) |
| telegram | one exchange on the bus; the **telegram log** is the SQLite file the ebusd add-on keeps of all of them |
| slot | one of the three time ranges of a day of a weekly program |
| comfort, regulation, structural | the risk classes of the definitions: written at once, written after a person confirms, never written |
| proven writable | a write seen changing the value on a bus and recorded as evidence in the definitions |
| beside the configuration | the folder `weishaupt` next to `configuration.yaml`, where a newer metadata file can be placed |
| repair | an entry under *Settings → Repairs*: the integration's problems, and the confirmation of a regulation setting |
| store | where a device keeps a value; room unit 2 on the test installation reads some of its values from room unit 1's |

## What you get

A device for ebusd and one device per controller found on the bus: *Boiler 1*, *Boiler 2*,
*System manager*, *Heating module 2/3*, *Room unit 1/2/3*, and *Installation* for what is
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

- A value the device does not have (ebusd answers `-`) is shown as unknown, and so is a temperature whose sensor
  is not fitted (−40 °C on the boilers, −100 °C elsewhere), with the attribute `no_sensor`.
- Every memory read of the boilers starts with a byte that is 0 in a valid answer. A reading whose
  first byte is not 0 is dropped whole and the previous value is kept.
- A register that two messages of one device read is shown once.
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
- **Reading what no entity follows**: a row that no enabled entity reads says *not read: no enabled entity*.
  *Read this menu once* (above each table), *Read this device once* and *Read everything once* (under the header)
  first show what it would cost: the requests, their time at the reader's pace and what they wait behind; nothing is
  asked until *Start*. Then a progress bar, and *Stop*, which withdraws what is not asked yet (the request under way
  finishes). The reads go into the reader's queue after what the entities wait for, one request at a time, at the
  gap of the options, as *Read now* of a program; reads only. A value read this way shows its time and *read once*:
  it is not kept up to date. A reload of the integration drops what was not asked yet, and the panel says so. With
  definitions 0.6.0, all nine devices and the entities enabled when created, *Read everything once* is 223
  requests, about 7½ minutes at 2 s (the system manager 58, each room unit 41, each heating module 12, each boiler
  9); program slots and fault tables keep their own *Read now*. Counted from the metadata on the test bench.
- **Following**: each row and each program has *Follow*, the sensor that keeps it up to date (enabled), and each
  table *Follow all* and *Follow none*. Choices are collected and applied together with *Apply*, which enables or
  disables those sensors in Home Assistant's entity registry, as their own settings would. Home Assistant reloads
  the integration about 30 s after an entity is enabled (once, however many were enabled); the panel says so and
  reloads with it. A disabled sensor stops at once, with no reload. Disabling a sensor that is followed by default
  (live values, states, counters) is allowed and says what it stops: no more readings, no more history, and
  dashboards or automations that use it no longer find it. An entity disabled by its device or its config entry is
  left as it is. Administrators only, checked by Home Assistant for each command.
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
  (the system manager's direct circuit `em1` and its heating circuit 1) is shown once, with the value of
  whichever is read and where it is changed ("through em1"). A temperature equal to the value the definitions
  mark as "sensor not fitted" (−40.0 °C on a boiler, −100.0 °C elsewhere) is shown as *no sensor*; a °C field
  they do not mark gets the same rule by device (−40.0 on a boiler, −100.0 on the system manager or a module). A value that is not read says
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

## Dashboard card: one weekly program

The integration adds a card to the dashboards (nothing to install): *Add card → Weishaupt weekly program*, or

```yaml
type: custom:weishaupt-program-card
entity: sensor.room_unit_1_heating_program_1   # the program's sensor
title: Heating, room unit 1                     # optional
today: true                                     # mark today's row (default)
```

It shows the week grid of the program from its sensor, for every user who sees the dashboard. The program sensors
are created disabled: enable the one you put on a dashboard (Settings → Entities). An **administrator** can also
edit a program proven writable on its device: type a day, copy it to other days, see the writes it may cost and the
writes left this hour, then write. The card writes through the program-day entities (`text.set_value`), so the
write switch, the hourly limit and the read-back apply as everywhere else; a refusal shows the same message.


## Writing settings

### What writing needs

Reading works without any of this. Writing needs all of it; the integration checks each point itself and refuses
every write while one is missing.

1. **An ebusd that computes the run-time checksum** of the Weishaupt register writes, **or** the option *Allow
   writes on a stock ebusd* for the non-boiler controllers (see *What each ebusd allows* above).
   A stock ebusd loads the write
   lines of the definitions but cannot give them a valid checksum; it then writes the non-boiler controllers with
   the placeholder checksum of the definition (opt-in, validated on site), never a boiler automat. The build of
   [aghulas/ebusd](https://github.com/aghulas/ebusd/releases) computes the checksum and writes every controller,
   until john30/ebusd#1825 is merged. How to run it
   is in the notice of the definitions release. For Home Assistant OS, the add-on *eBUSd (Weishaupt CRC)* is the
   ebusd add-on with this build: in the add-on store (⋮ → *Repositories*) add
   `https://github.com/aghulas/ha-addons#weishaupt`. That form, with `#weishaupt`, is for the store only; in a
   browser it opens another page. To read about the add-on, open
   <https://github.com/aghulas/ha-addons/tree/weishaupt>. Home Assistant builds the add-on on the device when it
   is installed: the first install takes a few minutes. If a stock ebusd add-on runs already, stop it first (an
   adapter can be used by one add-on at a time), copy the definitions into the new add-on's own folder and set its
   options again: they do not carry over. The new add-on has another prefix, so another host name: tick it in
   *Reconfigure* ([Which ebusd](#which-ebusd)); following the running ebusd, the integration then moves to it once
   it is started.
   Check the build with the first line of `ebusctl info` (step 1). The integration checks it too, without
   sending anything to the bus, at every start: *Run-time checksum* on the panel's definitions page and, once writes
   are enabled (item 3), the attribute `run_time_checksum` of the switch
   **Writes** reads `present`, `absent` or `unknown`. `present` allows every write; `absent` allows the non-boiler
   controllers only with *Allow writes on a stock ebusd*; `unknown` allows none.
2. **The telegram log**, for the settings written from the address of the vendor service tool (`ff`, 79 of the
   83): every telegram ebusd sees, kept in an SQLite file Home Assistant can read. A write from `ff` is refused
   while the service tool may be connected (a telegram from `ff` that is not ours in the last 10 minutes), and
   whenever the log cannot be read or has received nothing for 2 minutes. With the ebusd add-on: set its option
   **SQLite telegram log (database file)** (`sqlite_db`) to `/share/ebusd/telegrams.db`, keep
   **SQLite telegram log retention (days)** (10 by default), and restart the add-on; the integration's option
   *Telegram log of each ebusd* (*⋮ → Reconfigure*) has that path by default, for each ebusd of the entry. The add-on's documentation puts the log at about 50 to
   170 MB a day depending on bus traffic, so up to some 1.7 GB with 10 days kept, and `/share` is part of Home
   Assistant's backups: check the room on the device and in the backups. A shorter retention works for the
   integration, which looks at the last 10 minutes only.
3. **Writes enabled**: *Devices & services → Weishaupt → ⋮ → Reconfigure → Bus load and writes* → *Enable writes of the proven
   settings*. The integration reloads and adds a number (or a select) per writable setting, enabled, in the
   configuration section of its device and named like the sensor of the same register with "(setting)" after it
   (*Normal room temperature (setting)*); one text per day of the writable programs; a button to set the clock;
   and the switch **Writes** on the ebusd device, off.
4. **The switch Writes on**, for a session of changes. While it is on, a comfort setting or a program day is
   written as soon as anyone sets it, from a dashboard, a phone or an automation. **Switch it off when you are
   done**; turning it off also withdraws every change waiting for a confirmation. It is off again after every
   restart of Home Assistant and every reload of the integration, whatever it was before, so it is never left on by
   a restart.

In its ebusd mode this integration does not use MQTT. If the ebusd add-on's MQTT discovery is on (its default), ebusd publishes
entities of its own; with the file the add-on seeds (`mqtt-hassio.cfg`, `filter-direction = r|u`) they are read
only, and writable messages become entities only if that filter is changed (definitions notice). Such entities do
not pass through this guard: do not change the filter with a stock ebusd.

Each setting has a **risk class** from the definitions: **comfort** settings (room and hot-water setpoints, the
program days) are written as soon as you set them; **regulation** settings (heating curve, limits, cascade and
hot-water parameters, the clock) wait for a person to confirm under *Settings → Repairs*; **structural** settings
(circuit type, boiler sequence…) are never written. Details: [Writing settings](#writing-settings).

### Before you change a setting

- **Note the value first.** The integration reads the setting from the device before writing and reads it back
  after; the logbook of the entity keeps *before → after*. To undo, set the former value the same way.
- **One installation.** Every write was proven on one installation (two WTC boilers in cascade, a system manager,
  two heating modules, room units at three addresses); another model or software version may answer differently.
- **Two copies of a setting.** A room unit and its heating module answer the same setting registers with different
  values, and which copy the regulation uses is not established (definitions notice): a change may show no effect
  on the heating, or the other copy may win.
- **A write acknowledged is not always a value taken.** A device can acknowledge a write and keep its value, for
  example when it comes from another source address than the one the definitions give: the read-back shows it, and
  the integration reports *not taken over*.
- **Not offered, on purpose**: the control variation and the third holiday registers of the room units (meaning not
  established; on the test installation, while a control variation of 0 was set, the heating modules raised their
  flow setpoint, definitions notice), and
  anything a device keeps in another device's store (room unit 2's setback and frost protection temperatures and its
  heating program 1, on the test installation: changed on room unit 1).
- **30 writes an hour** by default. It is a precaution, not a measured limit: whether the controllers wear out
  by writes is not known.
- If the heating behaves unexpectedly after a change, set the former value again, or change it on the controller
  itself.

### What is writable

What is writable is decided by the definitions, not by the integration: a setting gets a number
entity (a select for a choice) only when the metadata of the release gives it **write conditions** (the
definitions prove the write on a bus and an evidence record names it) and ebusd loaded its write
definition as the release has it. Structural settings (circuit type, boiler sequence…) never have
write conditions. The definitions notice counts 92 settings written on the test installation, and the metadata of
0.6.0 gives all 92 write conditions; nine of them, the control variation and the two third holiday registers
(start, end) of the three room units, have no range, their meaning not established: the integration keeps them read
only. That leaves 83, 15 of them comfort, each with a change and its restore captured
on the bus of the test installation (fixtures of the release):

| Device | Comfort | Regulation | Source |
|---|---|---|---|
| System manager (`ka`, 14) | hot-water setpoint | blocking time, boiler changeover time, power controller 1/P and I, de-couple minimum, calorifier and hot-water switching differentials, maximum hot-water loading time, legionella setpoint and circulation time, maximum flow temperature, maximum and minimum modulation (optimal range) | `ff` |
| System manager, own circuit (`em1`, 7) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover, minimum and maximum flow temperature | `ff` |
| Heating modules 2 and 3 (`em2`, `em3`, 7 each) | normal and setback room temperature | frost protection room temperature, heating curve gradient, summer / winter changeover | `ff` |
| Heating modules 2 and 3 | | maximum and minimum flow temperature | `31` |
| Room units 1 and 3 (`fs1`, `fs3`, 15 each) | normal and setback room temperature, hot-water setpoint | frost protection room temperature, heating curve gradient, summer / winter changeover, maximum and minimum flow temperature, optimised switch-on lead time, frost protection limit, boiler boost offset, holiday start and end (day, month) | `ff` |
| Room unit 2 (`fs2`, 13) | normal room temperature, hot-water setpoint | as room units 1 and 3, without the frost protection room temperature; its setback and frost protection room temperatures are kept by room unit 1 and changed there (definitions 0.6.0) | `ff` |
| System manager, choices (2) | | legionella protection day (off, Monday … Sunday), circulation during legionella protection (off, on): **selects** | `ff` |
| Room units 1, 2, 3, choice (1 each) | | holiday temperature level (antifreeze, setback): **select** | `ff` |

### Weekly programs

Where the definitions prove the slots writable — with definitions 0.6.0 the five programs of room
units 1 and 3, and the hot-water and circulation programs of the system manager (its own circuit,
`50`; the hot-water program the installation applies); none of room unit 2 (its heating program 1
acknowledged slot writes and kept none; its other programs have no write conditions) — each program has **one text entity per day** (*Heating program 1 – Monday
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
source, a device may acknowledge and keep its value: the flow limits of the system manager's own
circuit are taken from `ff` only; those of the heating modules are written from `31`, as the metadata gives (the
definitions notice reports them taken from `ff` as well).

The system manager's own circuit reads three registers of the system manager: the integration
shows each register once. The maximum flow temperature, writable on both, has one number (through
`ka`); the normal and setback room temperatures, proven written through `em1` only, have a number
that writes through `em1`. So 77 numbers and 5 selects for 83 settings.

Ranges and steps are those of the definitions. Eleven settings cannot carry one in the CSV
(setback room temperature of `em1`–`em3`, `fs1`, `fs3` and heating curve of `em1`–`em3`, `fs1`–`fs3`: fractional
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

A reload of the integration keeps the values already read on screen, so entities
do not show *unknown*, and reads every enabled entity again in the first pass, in the usual order:
a value changed at the device itself does not wait for the end of its interval (a day for the
programs).

**Each write**, in this order, stops at the first refusal and tells you why:

1. write switch on; the setting writable; ebusd able to send the write — it computes the run-time
   checksum, or the target is a non-boiler controller and *Allow writes on a stock ebusd* is on (a
   boiler automat and an `unknown` build are always refused); ebusd
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

**How the run-time checksum is checked.** The version string tells today's builds apart (`26.1.p20261029` for
the build with the run-time checksum), but it is a label, not a capability: ebusd does not announce the run-time
checksum, and another build could carry any string. So the integration tests the capability itself. At every start-up (writes
enabled or not) the integration hands ebusd one write telegram twice under a circuit name no message has,
once with the correct checksum and once with the checksum byte of the definition: the fork's build
matches the first and refuses it for its circuit; a stock ebusd matches only the second. Both are
refused by ebusd before sending: nothing reaches the bus. The result (`present`, `absent`, `unknown`) is on the
panel's definitions page, in the diagnostics and, with writes enabled, the attribute `run_time_checksum` of the
write switch. `present` allows every write; `absent` with *Allow writes on a stock ebusd* allows the non-boiler
controllers (the write then carries the placeholder checksum of the definition); `unknown` refuses every write. It
is checked again whenever the integration moves to
another ebusd, and when the ebusd in use reports another version after a lost connection (an add-on updated in
place).

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
  values do not hold the pass up;
- counters and fault memory at start and then every hour, settings every 6 hours, weekly programs
  once a day;
- states the devices send by themselves (boiler status, room unit exchanges) are read from the
  cache of ebusd every 30 s and cost the bus nothing;
- a message is requested only while an **enabled** entity shows it: disabling entities lowers the
  load, enabling diagnostics raises it;
- ebusd answers from its cache when it already holds a recent enough value, for example after a
  restart of Home Assistant;
- no request while ebusd reports that it has no signal.

With definitions 0.6.0 and the entities enabled when created (all nine devices present): 85 messages, 13 of them
passive, so 72 requests in the first pass (about two and a half minutes at 2 s), then about 50 requests every
5 minutes for the live values, 20 an hour for counters and fault memories and 2 every 6 hours. With everything enabled
(668 readable messages, 655 of them asked from the devices), the first pass takes about 22 minutes at 2 s, then
the settings are asked every 6 hours and the programs once a day. These figures are counted from the metadata and
the reader's intervals, not measured on a bus; the vendor's service tool was seen sending about two requests per
second while logging.

If ebusd itself is configured to poll (`--pollinterval`, poll priorities in the CSV), both loads
add up; the definitions release sets no poll priority.

## Supported devices and limits

Weishaupt heating systems whose controllers speak eBUS, as the definitions describe them:

| Device | Bus address(es) | Read | Written (run-time checksum build, or stock ebusd with *Allow writes on a stock ebusd* for the non-boiler controllers) |
|---|---|---|---|
| WTC gas condensing boiler (automat W-FM, one per boiler) | 08, 18 | live values, statistics and counters, fault memory and fault counters | — |
| WCM system manager (cascade manager), and its own heating circuit | 15, 50 | live values, cascade and hot-water settings, its fault-log entry, weekly programs | settings, choices, programs proven writable, the clock |
| WCM-EM heating module (up to two) | 51, 52 | live values, settings | settings |
| WCM-FS room unit (up to three addresses) | 35, 75, f5 | room values, settings, weekly programs, its fault-log entry | settings, programs proven writable |

What is read or written is decided by the definitions release, message by message, with evidence; a device or a
register they do not describe is not shown. Limits a second installation should know:

- **Tested on one installation**: two WTC boilers in cascade, one system manager, two heating modules, room units
  answering at three addresses (on that installation one unit serves heating circuits 1 and 2 and answers at `35` and `75`,
  definitions notice), one software version each. Another model or version may answer differently: the comparison at start-up
  names what ebusd did not load as described, and a diagnostics download shows what was read.
- **Writes need the ebusd build** that computes the run-time checksum (until john30/ebusd#1825 is merged), or, for
  the non-boiler controllers only, a stock ebusd with *Allow writes on a stock ebusd* enabled (validated on site on
  2026-11-23; the boiler automats always need the build). Writes from the service tool's address also need the
  telegram log. Without a usable build or the option, everything is read only.
- **Room unit 2 reads some values from room unit 1's store** (as on the tested installation): its heating
  program 1 and its setback and frost protection room temperatures. A write sent to room unit 2 is acknowledged and
  not kept: they are read only there, and the panel, the program sensor and the card say they are changed on room
  unit 1 (metadata `shared_with`). Its other programs have no write conditions; whether they are shared the same
  way is not established (definitions notice), so they are read only too, with no pointer. A room unit at `75` addressed for heating circuit 2 alone may keep its own: the definitions
  would have to say so.
- **Programs**: only those proven writable on their device can be changed (heating program 1 of room units 1 and 3,
  and the others the metadata marks comfort); the others are shown, read only.
- **Absent sensors** read −40.0 °C (boiler) or −100.0 °C (system manager, heating module, room unit). The
  definitions mark these values on each field concerned: the entity reads *unknown* with the attribute
  `no_sensor: true` while the device sends exactly that value; any other value, even close, is shown. The panel
  shows "no sensor".
- **No time** is stored with a boiler's fault entry; the system manager's fault log shows the entry its operating
  unit has selected.
- **One request at a time** on the bus, at the gap set in the options (2 s by default): see
  [Load on the bus](#load-on-the-bus).
- **Not a climate entity**: settings are numbers, selects and texts; no `climate` or `water_heater` entity yet.

**Reporting a problem**: open an issue with the diagnostics download (Settings → Devices & services → Weishaupt →
⋮ → Download diagnostics). The integration's own data (`data`) holds no address of ebusd, no file path, no entry
id and no user id; it does hold the values read. Home Assistant
itself adds to every download a `setup_times` object keyed by the entry id and, when the integration has repairs
open, an `issues` list whose ids contain it: an opaque local id, no address, which an integration cannot remove.

## Compatibility

| Integration | Definitions shipped | Accepts definitions | ebusd | Home Assistant |
|---|---|---|---|---|
| 1.2 | 1.3.0 | 0.6.0 to 1.x | 26.1; writes need the build with the run-time checksum | 2026.10 and later |
| 1.0 – 1.1 | 1.0.0 | 0.6.0 to 1.x | 26.1; writes need the build with the run-time checksum | 2026.10 and later |
| 0.13 | 0.8.0 | 0.6.0 to 0.8.x | 26.1; writes need the build with the run-time checksum | 2026.10 and later |
| 0.10 – 0.12 | 0.6.0 | 0.6.0 and later 0.6.x | 26.1; writes need the build with the run-time checksum | 2026.10 and later |
| 0.4 – 0.9 | 0.5.8 (a newer 0.5.x beside the configuration) | 0.5.3 and later 0.5.x | 26.1; writes as above | 2026.10 and later |

The integration ships the metadata file of definitions 1.3.0 (`weishaupt-metadata-1.3.0.json`: 687 messages, of
which 686 can be read) and builds everything from it. ebusd cannot tell which release it loaded, so at start-up the
integration compares, message by message, what ebusd loaded with that file:

- a device of the definitions that does not answer on the bus gets no device in Home Assistant;
- a message that ebusd did not load, or loaded with other fields, types or units, gets **no entity**, and one repair
  names the messages and the release expected. Load a release of the accepted range in ebusd, then reload the
  integration.

The counts of messages differ by what is counted: ebusd counts 1073 messages in release 0.6.0 (`--checkconfig`, every
device's file, write definitions included); the metadata describes 669 (one per message
name and device); the fixtures of the release hold 949 telegrams captured on a bus for 617 of them.

**Why 0.6.x.** The definitions notice says that from 0.6.0 on, message and field names change only with a new first
number. This version accepts 0.6.x and a later release of the integration accepts a newer one once it has been
checked against it. 0.6.0 itself renamed or retyped four messages against 0.5.x: with 0.5.x still in ebusd, the
two mixer pumps of the heating modules, the legionella start time and the hot-water excess temperature have no
entity and one repair names them; everything else works. A metadata file 0.5.x beside the configuration is not
used (outside the accepted range) and a repair says so: remove it.

When a message or a field is renamed, its entity keeps its entity id and history: the metadata says which name it
had. The mixer pump became a binary sensor in 0.10.0; Home Assistant cannot move an entity from one domain to
another, so the former `sensor.…_mixer_circuit_pump` is removed at the first load (kept, with a repair, if you
changed it) and `binary_sensor.…_mixer_circuit_pump` replaces it; automations or cards using the former id must be
changed.

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
failed and dropped readings), the last readings, the ebusd of the entry by name (which one is in use, follow or pinned), the result
of the checksum probe and, with writes enabled, the writable settings and the last writes. In the integration's
data the address of every ebusd, the telegram-log paths, the entry id and the user ids are redacted, even inside
texts; the repairs name each ebusd by its name, never by its address. Home Assistant
itself adds to every download a `setup_times` object keyed by the entry id and, when the integration has repairs
open, an `issues` list whose ids contain it: an opaque local id, no address, which an integration cannot remove. It is the file to
attach to a report about another boiler model or software version.

## Coming from 0.1

0.1 read and wrote registers with raw telegrams from its own table; later versions are a different integration
under the same name. After the update:

- ebusd must load a definitions release (see [First installation](#first-installation-reading)); `--enablehex` is
  no longer needed.
- Every entity is new (other unique ids). The entities of 0.1 stay as unavailable until you remove them: one repair
  lists them and removes them only when you confirm it.
- Writes are off, even if they were on in 0.1; regulation settings need a confirmation by a person for every change,
  so an automation can no longer set them. The actions `weishaupt.set_time_program` and `weishaupt.set_clock` and the
  `date` entities are gone: programs are written per day (text entities, `weishaupt.set_program`), the clock by a
  confirmed button. Only what the definitions prove is offered.
- The config entry is kept (same host and port); its former options are dropped.

## History

The release notes on GitHub give each version in full; here only what changed what you install or see.

- 1.5.0: a first installation with the bridge Weishaupt2MQTT alone. *Add integration* now starts with a choice,
  *Weishaupt2MQTT (MQTT bridge)* or *ebusd (add-on or address)*; the first asks for the base topic and creates the
  entry once the bridge is found online on it, without any ebusd address (before, an entry had to be made against
  an ebusd and switched afterwards). The diagnostics download and the menus no longer assume an ebusd.
- 1.2.0: definitions 1.3.0 shipped (687 messages, of which 686 can be read): boiler heating-specialist parameters
  (`InstallerParameters1`–`5`, new *Heating specialist parameters* menu), boiler fan speeds while firing
  (`FanOperation`), module H1 digital input (`H1Status`), 16-bit `FloorDryingTemp` / `RoomThermostatTemp`, and all
  five `fs2` programs marked `shared_with` `fs1`.
- 1.1.0: panel and card usability (global search, quick filters, program editing; no definitions change).
- 1.0.0: definitions 1.0.0 shipped and accepted (`>=0.6.0, <2.0`, 668/668 readable messages covered by fixtures);
  `stored_only` badge and note on room-unit DHW/circulation programs in the panel; `DeviceEntry.config_entry_id`
  in `services.py` (removes HA 2027.10 deprecation warning).
- 0.13.0: definitions 0.8.0 shipped and accepted (`>=0.6.0, <0.9`). Linked bounds (`write.below` / `write.above`,
  including `ka/ModulationMax` and `ka/ModulationMin`), `stored_only` on room-unit DHW/circulation programs,
  `pointer` metadata for boiler fault history, and `fs2` shared-store markers extended to `HCProgram2`, `DHWProgram`
  and `CircProgram`.
- 0.12.1: *Reconfigure* is a menu giving a UI path to bus load, writes and the telegram log per ebusd.
- 0.12.0: several ebusd per entry (the ebusd add-ons listed from the Supervisor), following the running one or
  pinned to one, with a repair when it does not answer; the build checked at every start, writes enabled or not;
  the telegram log set per ebusd. Existing entries are pinned to their address.
- 0.11.0: the panel reads on demand what no entity follows, per menu, per device or everything, with its cost
  first, a progress bar and a stop; and follows or stops following rows and programs, applied in one go.
- 0.10.2: documentation only: install the add-on with the run-time checksum from the start if you mean to write,
  *Reconfigure* when ebusd moves, one way to a shell, switch Writes off after use, the size of the telegram log;
  writing in one section, developer sections at the end.
- 0.10.1: documentation only: a first-installation path, what writing needs, a glossary, figures for
  definitions 0.6.0.
- 0.10.0: definitions 0.6.0 shipped and accepted (0.6.x; 0.5.x no longer). Renamed fields keep their entity; the
  legionella start time is a time, the hot-water excess temperature a difference in K, the mixer pumps binary
  sensors.
- 0.9: a dashboard card for one weekly program; nothing is written to a device that reads the value from another
  device's store.
- 0.8: devices that appear later are added, a device absent for 7 days can be removed from a repair; diagnostics
  without addresses or ids.
- 0.7: fault tables, a printable report and a CSV export in the panel; the entry waits for ebusd's scan.
- 0.6: the panel writes, through the same guard as the entities; the write switch is off after every restart.
- 0.5: the Weishaupt panel, read only.
- 0.4: a newer metadata file beside the configuration.
- 0.3: writes of the proven settings, programs and clock, with risk classes and the run-time checksum check.
- 0.2: read only, built from the metadata of the definitions.
- 0.1: raw telegrams from the integration's own register table.

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
- `frontend/src/weishaupt-card.ts` is the dashboard card of one weekly program; the week grid is shared with the
  panel (`src/week-grid.ts`). Both bundles are built by `npm run build`.
- `brand/` holds the images Home Assistant and HACS show; they are drawn by `scripts/make_brand.py`
  (an own mark, no vendor logo).

### Tests

A new definitions release can be checked before it is shipped or placed beside a configuration:

```bash
WEISHAUPT_NEXT_METADATA=/path/to/weishaupt-metadata-0.6.1.json scripts/test.sh tests/test_next_metadata.py -s
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
  a bus, 949 of them for 617 of the 668 readable messages of definitions 0.6.0. It is recorded with
  `scripts/capture_ebusd.py`, which fails if ebusd answers anything else than the fixtures say. The 51 messages
  without a fixture (room units 2 and 3, the heating modules) are answered by the simulated ebusd from the same
  message of another device when the fields match, otherwise with neutral values.
- The integration runs inside a Home Assistant test instance against a **simulated ebusd**
  (`tests/fake_ebusd.py`), a TCP server that replays those answers. It makes up no value.
- **Writes.** The telegram built for each of the 83 settings equals, byte for byte, the 146 write
  telegrams captured on the bus for them (changes and restores, fixtures of the release), from the
  source the capture and the metadata give (`tests/test_writes.py`). The recording also holds the
  answers of a real ebusd, the fork's build and a stock 26.1, to 762 write commands (the checksum probes, each captured
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

**On a real bus.** Every write path (settings, choices, program days, the clock, from the entities, the panel and
the card) was used on the installation the definitions were established on, each write read back and restored,
with integration 0.3 to 0.9 and definitions 0.5.x. A first read-only run (integration 0.2, definitions 0.5.2, twelve
minutes, from a throwaway Home Assistant test instance, ebusd 26.1 also serving its own polling and MQTT) found the nine devices of
the scan, no definitions mismatch, the first fill in about two minutes (61 messages), then about
eight requests a minute, never two closer than 2 s, of which a third were answered from the cache
of ebusd. No bus error, no lost signal, no reconnection of ebusd; the values equal those ebusd
published to its other clients at the same time.

What this does not prove: behaviour over days, while a boiler fires (the passive load messages of
the boilers are only sent then), and the values of an installation other than that one.

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
