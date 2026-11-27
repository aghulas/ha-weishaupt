"""The ebusd endpoints of an entry, and which one it uses.

One adapter can be used by one ebusd at a time, so on Home Assistant OS the ebusd add-ons of an installation (the
stock one, the Weishaupt one, a test build) run one at a time, each under its own host name. The entry holds the
list of these endpoints (`endpoints`, in its data) and how it picks one (`mode`):

- `follow`: the one that answers `info` with a signal on the bus. At a set-up every endpoint is asked `info`;
  while the entry runs, the others are asked only after the one in use failed SWITCH_AFTER_FAILURES connections in
  a row. A lost signal alone never moves the entry: that is the adapter or the bus, not ebusd;
- `pinned`: only the one in use, never another.

The endpoint in use is `host` and `port` of the data, as before 0.12.0. A switch updates them, and the entry
reloads: same entities and history, writes off, the build probed again. Nothing is sent to the bus to choose: `info`
only.

Each endpoint carries its telegram log (`telegram_db`): each ebusd add-on has its own `sqlite_db` option.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import CONF_HOST, CONF_PORT

from .const import CONF_TELEGRAM_DB, DEFAULT_TELEGRAM_DB
from .ebusd import EbusdClient, EbusdError, EbusdInfo

CONF_ENDPOINTS = "endpoints"
CONF_MODE = "mode"
CONF_LABEL = "label"
CONF_ADDON = "addon"  # slug of the add-on the endpoint came from (Home Assistant OS), or None
MODE_FOLLOW = "follow"
MODE_PINNED = "pinned"
MODES = (MODE_FOLLOW, MODE_PINNED)
SWITCH_AFTER_FAILURES = 3  # failed connections in a row to the endpoint in use before the others are asked
PROBE_TIMEOUT = 5.0  # seconds to wait for `info` from an endpoint that is not the one in use


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int
    label: str
    addon: str | None = None
    telegram_db: str = DEFAULT_TELEGRAM_DB

    @property
    def key(self) -> str:
        return f"{self.host}:{self.port}"

    def as_dict(self) -> dict[str, Any]:
        return {CONF_HOST: self.host, CONF_PORT: self.port, CONF_LABEL: self.label, CONF_ADDON: self.addon,
                CONF_TELEGRAM_DB: self.telegram_db}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Endpoint:
        return cls(str(data[CONF_HOST]), int(data[CONF_PORT]), str(data.get(CONF_LABEL) or data[CONF_HOST]),
                   data.get(CONF_ADDON) or None, str(data.get(CONF_TELEGRAM_DB) or DEFAULT_TELEGRAM_DB))


def endpoints_of(data: dict[str, Any]) -> list[Endpoint]:
    """The endpoints of an entry's data, the one in use always among them. An entry made for the MQTT bridge has
    no ebusd in use (no `host`): none, unless a list was stored."""
    found = [Endpoint.from_dict(item) for item in data.get(CONF_ENDPOINTS) or []]
    if CONF_HOST not in data:
        return found
    if not any(e.host == data[CONF_HOST] and e.port == data[CONF_PORT] for e in found):
        found.insert(0, Endpoint(data[CONF_HOST], int(data[CONF_PORT]), "ebusd"))
    return found


def current(data: dict[str, Any]) -> Endpoint:
    return next(e for e in endpoints_of(data) if e.host == data[CONF_HOST] and e.port == data[CONF_PORT])


def mode_of(data: dict[str, Any]) -> str:
    mode = data.get(CONF_MODE)
    return mode if mode in MODES else MODE_PINNED


def manual_label(endpoints: list[Endpoint]) -> str:
    """Label of an endpoint typed by hand: "ebusd", "ebusd 2"…. Not its address: labels appear in repair issues,
    which the diagnostics download of Home Assistant carries."""
    used = {e.label for e in endpoints}
    if "ebusd" not in used:
        return "ebusd"
    return next(f"ebusd {n}" for n in range(2, 100) if f"ebusd {n}" not in used)


def use(data: dict[str, Any], endpoint: Endpoint | None, mode: str | None = None) -> dict[str, Any]:
    """The data with `endpoint` in use (None: the one in use stays) and `mode` (None: unchanged)."""
    chosen = endpoint or current(data)
    return {**data, CONF_HOST: chosen.host, CONF_PORT: chosen.port,
            CONF_MODE: mode or mode_of(data), CONF_ENDPOINTS: [e.as_dict() for e in endpoints_of(data)]}


@dataclass(frozen=True)
class Survey:
    """What one endpoint answered to `info`: its info, or the error."""

    endpoint: Endpoint
    info: EbusdInfo | None
    error: str | None = None

    @property
    def answers(self) -> bool:
        return self.info is not None

    @property
    def signal(self) -> bool:
        return self.info is not None and self.info.signal


async def survey(endpoints: list[Endpoint], timeout: float = PROBE_TIMEOUT) -> list[Survey]:
    """`info` to each endpoint, one after the other. Nothing reaches the bus."""
    found = []
    for endpoint in endpoints:
        try:
            info = await EbusdClient(endpoint.host, endpoint.port, timeout=timeout).info()
        except EbusdError as err:
            found.append(Survey(endpoint, None, str(err)))
        else:
            found.append(Survey(endpoint, info))
    return found


def choose(in_use: Endpoint, surveys: list[Survey]) -> tuple[Endpoint | None, list[Endpoint]]:
    """The endpoint to use in `follow` mode, and those answering with a signal.

    The one in use when it has a signal; else the first other one with a signal; else the one in use when it
    answers (unavailable with "no signal" as before); else the first that answers; else None."""
    with_signal = [s.endpoint for s in surveys if s.signal]
    answering = [s.endpoint for s in surveys if s.answers]
    for candidates in (with_signal, answering):
        if in_use in candidates:
            return in_use, with_signal
        if candidates:
            return candidates[0], with_signal
    return None, with_signal


# ---- in Home Assistant ----------------------------------------------------------------------------------------

def issue_not_running(entry_id: str) -> str:
    return f"ebusd_not_running_{entry_id}"


def issue_several(entry_id: str) -> str:
    return f"ebusd_several_{entry_id}"


def describe(surveys: list[Survey], states: dict[str, str]) -> str:
    """One line per endpoint, by its label (never its address): what it answered, and its add-on's state."""
    lines = []
    for item in surveys:
        state = states.get(item.endpoint.addon or "")
        what = ("answers, signal" if item.signal else "answers, no signal") if item.answers else "no answer"
        lines.append(f"- {item.endpoint.label}: {what}" + (f" (add-on {state})" if state else ""))
    return "\n".join(lines)


def raise_not_running(hass, entry, surveys: list[Survey], states: dict[str, str]) -> None:
    """The repair while the ebusd in use does not answer. Fixable when another endpoint answers: its flow lets the
    user choose it (or follow), which changes the entry only — it starts no add-on and sends nothing to the bus."""
    from homeassistant.helpers import issue_registry as ir

    from .const import DOCUMENTATION_URL, DOMAIN
    in_use = current(dict(entry.data))
    others = [s for s in surveys if s.answers and s.endpoint.key != in_use.key]
    ir.async_create_issue(
        hass, DOMAIN, issue_not_running(entry.entry_id), is_fixable=bool(others), severity=ir.IssueSeverity.ERROR,
        translation_key="ebusd_not_running_fixable" if others else "ebusd_not_running",
        learn_more_url=DOCUMENTATION_URL, data={"entry_id": entry.entry_id, "kind": "ebusd_choice"},
        translation_placeholders={"label": in_use.label, "mode": mode_of(dict(entry.data)),
                                  "endpoints": describe(surveys, states)})


def clear_not_running(hass, entry_id: str) -> None:
    from homeassistant.helpers import issue_registry as ir

    from .const import DOMAIN
    ir.async_delete_issue(hass, DOMAIN, issue_not_running(entry_id))


def update_several(hass, entry, with_signal: list[Endpoint]) -> None:
    """A repair while two endpoints or more answer with a signal: the entry keeps the one it uses, never switches
    between them, and asks the user to pin one."""
    from homeassistant.helpers import issue_registry as ir

    from .const import DOCUMENTATION_URL, DOMAIN
    issue = issue_several(entry.entry_id)
    if len(with_signal) < 2:
        ir.async_delete_issue(hass, DOMAIN, issue)
        return
    ir.async_create_issue(
        hass, DOMAIN, issue, is_fixable=False, severity=ir.IssueSeverity.WARNING, translation_key="ebusd_several",
        learn_more_url=DOCUMENTATION_URL,
        translation_placeholders={"labels": ", ".join(e.label for e in with_signal),
                                  "label": current(dict(entry.data)).label})


def apply_choice(hass, entry, choice: str) -> None:
    """Use `choice`: MODE_FOLLOW, or the key of an endpoint to pin. Changes the entry, which reloads (through its
    update listener when loaded, by a scheduled reload otherwise)."""
    from homeassistant.config_entries import ConfigEntryState
    data = dict(entry.data)
    if choice == MODE_FOLLOW:
        new = use(data, None, MODE_FOLLOW)
    else:
        endpoint = next(e for e in endpoints_of(data) if e.key == choice)
        new = use(data, endpoint, MODE_PINNED)
    loaded = entry.state is ConfigEntryState.LOADED
    hass.config_entries.async_update_entry(entry, data=new)
    if not loaded:  # not set up (no ebusd answered): no update listener, so reload now rather than at the next retry
        hass.config_entries.async_schedule_reload(entry.entry_id)
