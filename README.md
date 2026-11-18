# Weishaupt WCM (ebusd)

An **unofficial** Home Assistant integration that reads and sets Weishaupt WCM regulators (system manager KA,
room units FS, heating modules EM) through ebusd, with the commands `5022` (read) and `5023` (write), both
protected by the Weishaupt CRC. Numeric settings are written through the message definitions of ebusd
(`write -c <circuit> <Message>`), everything else as `hex` telegrams. The readings and boiler states that ebusd
publishes over MQTT are left as they are; this integration adds the settings.

Not affiliated with Weishaupt. It writes to a heating system: read the section on writes before enabling them.

## Requirements

- ebusd started with `--enablehex`, reachable over TCP (port 8888 by default): reads, dates, choices, time
  programs and the clock go through `hex`.
- For the numeric settings: an ebusd that computes the Weishaupt CRC at run time (john30/ebusd#1825) and a
  Weishaupt configuration whose `5023` writes are marked `[WCRC]` (for example `RoomNormalTemp` on `fs1`).
- The telegram log of the ebusd add-on (`sqlite_db`) readable by Home Assistant, for example
  `/share/ebusd/telegrams.db`: it tells whether the WCM-Diagnose service tool is connected.

## Languages

The repository is in English. The user interface is translated: entity and device names, the options of the
choices, the service descriptions and the error messages come from `strings.json` and `translations/`
(English and French today). Home Assistant picks the language of each user; device names follow the language
of the server. A new language is one more file in `translations/`; the tests check that every file has the
same keys and that every key used by the code is translated.

Identifiers are language-neutral and in English: option values (`off`, `monday`, `frost`…), the day of the
`set_time_program` action and the attributes of the program sensors (`monday`…`sunday`).

## Entities

Per regulator: the settings as `number` entities, the choices (modes) as `select`, the holiday dates of the FS as
`date` entities and their temperature level (frost protection or setback) as a `select`, the time programs
(heating 1 to 3, hot water, circulation) as sensors (state = today's slots, one attribute per day, read again
every hour). Some fine-regulation registers whose write is not validated yet are exposed as read-only `sensor`
entities. The action `weishaupt.set_time_program` rewrites the slots of one day (e.g. `06:30-18:00, 19:00-21:00`,
quarters of an hour, three at most), slot by slot, without rewriting those that do not change.

Regulators covered (`registers.py`): **KA** (cascade: flow and modulation, hot water, legionella protection, PI
controller, boiler start order A/B, change-over time, blocking time, hydraulic separator `DeCoupleMin` and buffer
differential), **FS1-3** (setpoints, gradient, summer/winter, flow maximum and minimum, anticipation
`SwitchOnRuntime`, room influence factor, mixed-circuit boost, frost protection, adaption, holidays, programs) and
**EM1-3** (extension circuits driven by an external boiler demand on the H1 input: setpoints, gradient,
summer/winter, flow limits; boiler demand `H1Status` read-only; the EM have no time program, they follow the
relay). Only registers whose write was tried and retained on the bus of the test installation (30/10 to
15/11/2026) are open for writing; the source address rule (`ff` or `31`) is carried per register.

A global **write switch** (platform `switch`) cuts every write: it is the run-time kill switch (it toggles
`guard.enabled`).

## Writes

Disabled by default (fail-safe). Two levels: the integration option `writes_enabled` (if `true`, writes start
**enabled** after a restart of Home Assistant; this is how the test installation runs, with the regulation of the
circuits in service since 15/11/2026) and the **run-time write switch** (off = everything is refused, whatever
`writes_enabled` says). Every write goes through `guard.py`:

- bounds per register, taken from the manuals WCM-FS 2.0 (83277701) and WCM-KA 3.0 (83258401), narrowed by the
  linked settings (setback ≤ normal, flow minimum ≤ maximum, modulation minimum ≤ maximum);
- at most one write per register every 10 s and 30 writes per hour;
- one register per `5023` telegram, read back after the write; a value that was not retained is reported as an
  error;
- numeric settings (`number`) are written through their ebusd definition (`message` in `registers.py`): ebusd
  computes the CRC and refuses a value outside the bounds of the definition before sending it; dates, choices,
  programs and the clock go as `hex`, with the CRC computed by `protocol.py`. The read-back is in `hex` in both
  cases;
- most settings are accepted only from the address of the service tool, `ff` (other addresses are acknowledged,
  then ignored). A write from `ff` is refused if a telegram from `ff` is in the log of the last 10 minutes
  (WCM-Diagnose connected: two masters on the same address would disturb each other) or if the log cannot be
  read or is not being fed.

Every write is logged (`WRITE …` in the Home Assistant log) and fires the event `weishaupt_write` (value before,
value read back, source address).

## History

- 0.1.0 (30/10/2026): KA and FS settings with `5022`/`5023` as `hex` telegrams, write guard, holidays, time
  programs, action `set_clock`.
- `main` since 07/11/2026: numeric settings written through the ebusd definitions.
- 15/11/2026: the whole regulation of the circuits is opened: anticipation and fine regulation of the FS,
  extension circuits EM1-3 (external boiler demand), cascade and hydraulic separator settings; global write
  switch and persistent option `writes_enabled`.
- After 0.1.0, not released yet: repository in English, interface translated (English, French). Option values,
  the `day` of `set_time_program` and the program sensor attributes changed from French words to English keys:
  automations that use them must be adapted. Entity ids and unique ids are unchanged.

## Tests

```bash
python3 -m pytest tests
```

The tests cover the protocol (frames compared with those of a live bus), the write guard and the translation
files, without Home Assistant.

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
