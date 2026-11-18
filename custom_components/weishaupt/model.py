"""The metadata file of a definitions release as devices, messages and entity descriptions.

No Home Assistant dependency: the platforms, the translation generator (`scripts/vendor_metadata.py`) and the tests
all build on this module, so that names, keys and translations cannot drift apart.

The metadata file is `weishaupt-metadata-<version>.json` of a release of the definitions
(https://github.com/aghulas/ebusd-configuration, format in `docs/companion-contract.md` of
https://github.com/aghulas/weishaupt-ebus). A message is identified by `<circuit>/<name>`; these are ebusd's names.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = 1
METADATA_FILE = Path(__file__).parent / "metadata.json"
# Definitions releases this version of the integration accepts. The second number of a definitions version changes
# when a message or a field is renamed, removed or retyped; the third only adds. 0.5.0 renamed a message of the
# system manager, so 0.4.x and 0.5.x do not expose the same names. 0.5.1 and 0.5.2 added messages: an ebusd that
# runs 0.5.0 or 0.5.1 lacks some of the messages of this metadata and the comparison would name them, so the range
# starts at the release the metadata comes from. A later 0.5.x only adds messages.
ACCEPTED_DEFINITIONS = ">=0.5.2, <0.6"

ON_OFF = {"0": "off", "1": "on"}
NAME_SEPARATOR = " – "
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def slug(text: str) -> str:
    """`BurnerInOperation` -> `burner_in_operation`: a translation key for a value-list entry."""
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return re.sub(r"[^a-z0-9]+", "_", words.lower()).strip("_")


@dataclass(frozen=True)
class Field:
    name: str
    type: str
    index: int  # position in the answer of `read`
    kind: str
    label: dict[str, str] | None = None
    unit: str | None = None
    divisor: int | None = None
    values: dict[str, str] | None = None
    value_labels: dict[str, dict[str, str]] | None = None  # raw value -> label per language
    skip: bool = False
    guard: bool = False
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None

    @property
    def shown(self) -> bool:
        return not self.skip and not self.guard


@dataclass(frozen=True)
class WriteConditions:
    """`write` of a message in the metadata: present only when a lot proves the write."""

    source: str  # "ff" or "31"
    runtime_checksum: bool
    risk: str  # "comfort" or "regulation"
    proof: str
    open: tuple[str, ...] = ()


@dataclass(frozen=True)
class Message:
    key: str
    circuit: str
    name: str
    address: str
    device: str
    menu: str
    kind: str
    label: dict[str, str]
    passive: bool
    poll: str | None
    fields: tuple[Field, ...]
    compose: bool = False
    family: str | None = None
    group: str | None = None
    position: dict[str, int] | None = None
    same_as: str | None = None
    write: WriteConditions | None = None
    renamed_from: str | None = None  # key of the message in the releases before the rename

    @property
    def writable(self) -> bool:
        return self.write is not None

    @property
    def guard(self) -> Field | None:
        return next((f for f in self.fields if f.guard), None)

    def field(self, name: str) -> Field | None:
        return next((f for f in self.fields if f.name == name), None)


@dataclass(frozen=True)
class Circuit:
    circuit: str
    address: str
    file: str


@dataclass(frozen=True)
class Device:
    id: str
    type: str
    label: dict[str, str]
    circuits: tuple[Circuit, ...]


@dataclass(frozen=True)
class Group:
    """Messages shown as one object: a weekly program, the fault history of a boiler."""

    key: str  # <circuit>/<id>
    family: str
    circuit: str
    device: str
    id: str
    label: dict[str, str]
    members: tuple[str, ...]


@dataclass(frozen=True)
class ValueEntity:
    """One value of one message, shown as a sensor or a binary sensor."""

    message: Message
    field: Field
    translation_key: str
    name: dict[str, str]

    @property
    def key(self) -> str:
        """Identity of the entity: circuit, message and field, never a label."""
        return f"{self.message.key}/{self.field.name}"

    @property
    def platform(self) -> str:
        return "binary_sensor" if self.field.values == ON_OFF else "sensor"

    @property
    def kind(self) -> str:
        return self.field.kind

    @property
    def options(self) -> dict[str, str] | None:
        """ebusd name of each value-list entry -> state key, for an enumeration sensor."""
        if self.field.values is None or self.platform != "sensor":
            return None
        return {name: slug(name) for name in self.field.values.values()}

    def option_labels(self, language: str) -> dict[str, str]:
        """State key -> label of the value-list entry, for the translations."""
        values, labels = self.field.values or {}, self.field.value_labels or {}
        return {slug(name): labels[raw][language] for raw, name in values.items()}

    @property
    def former_key(self) -> str | None:
        """Key the entity had before its message was renamed, None when it was not."""
        former = self.message.renamed_from
        return f"{former}/{self.field.name}" if former else None

    @property
    def diagnostic(self) -> bool:
        """Shown in the diagnostic section of the device: everything that is not a live value or a state.
        Settings are there too in a read-only version (a sensor cannot be in the configuration section)."""
        return self.kind not in ("live", "state")

    @property
    def enabled_default(self) -> bool:
        """Enabled when created: live values, states and the operating counters. Settings, diagnostics and the
        per-fault counters are created disabled; a disabled entity is never requested from the bus."""
        if self.message.family == "fault_counter":
            return False
        return self.kind in ("live", "state", "counter")


@dataclass(frozen=True)
class GroupEntity:
    """One sensor for a group of messages."""

    group: Group
    translation_key: str
    name: dict[str, str]

    @property
    def key(self) -> str:
        return f"{self.group.circuit}/group/{self.group.id}"

    @property
    def enabled_default(self) -> bool:
        """The fault history of a boiler is enabled when created; the weekly programs are not."""
        return self.group.family == "fault_history"


@dataclass(frozen=True)
class Mismatch:
    """A message of the metadata that ebusd did not load, or loaded with another definition."""

    key: str
    reason: str  # "missing" or "differs"
    detail: str = ""


@dataclass
class Model:
    version: str
    commit: str
    languages: tuple[str, ...]
    devices: dict[str, Device]
    messages: dict[str, Message]
    groups: dict[str, Group]
    value_entities: tuple[ValueEntity, ...] = ()
    group_entities: tuple[GroupEntity, ...] = ()
    _by_circuit: dict[str, Device] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = METADATA_FILE) -> Model:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Model:
        if data.get("schema") != SCHEMA:
            raise ValueError(f"metadata schema {data.get('schema')!r}, this version reads schema {SCHEMA}")
        devices = {
            key: Device(key, d["type"], d["label"], tuple(Circuit(**c) for c in d["circuits"]))
            for key, d in data["devices"].items()}
        messages = {key: _message(key, m) for key, m in data["messages"].items()}
        groups = {
            f"{g['circuit']}/{g['id']}": Group(f"{g['circuit']}/{g['id']}", g["family"], g["circuit"], g["device"],
                                               g["id"], g["label"], tuple(g["members"]))
            for g in data["groups"]}
        model = cls(data["definitions"]["version"], data["definitions"].get("commit", ""),
                    tuple(data["languages"]), devices, messages, groups)
        model._by_circuit = {c.circuit: d for d in devices.values() for c in d.circuits}
        model.value_entities = _value_entities(model)
        model.group_entities = _group_entities(model)
        return model

    def device_of(self, message: Message) -> Device:
        return self.devices[message.device]

    def present_devices(self, slave_addresses: set[str]) -> dict[str, Device]:
        """Devices with at least one circuit whose address answers on the bus. The device of the broadcast
        messages has no address of its own: it is present as soon as another device is."""
        present = {key: device for key, device in self.devices.items()
                   if any(c.address in slave_addresses for c in device.circuits)}
        if present:
            present.update({key: device for key, device in self.devices.items()
                            if all(c.address == "fe" for c in device.circuits)})
        return present

    def compare(self, circuits: set[str], loaded: dict[str, list]) -> list[Mismatch]:
        """Compare the messages of `circuits` with the definitions ebusd loaded (`loaded`: circuit -> list of
        ebusd.Definition). ebusd cannot tell which release it runs, so this is done message by message."""
        mismatches = []
        for message in self.messages.values():
            if message.circuit not in circuits:
                continue
            candidates = [d for d in loaded.get(message.circuit, [])
                          if d.name == message.name and (d.is_passive if message.passive else d.is_read)]
            if not candidates:
                mismatches.append(Mismatch(message.key, "missing"))
                continue
            detail = _difference(message, candidates[0])
            if detail:
                mismatches.append(Mismatch(message.key, "differs", detail))
        return mismatches


def _message(key: str, data: dict[str, Any]) -> Message:
    fields = tuple(
        Field(f["name"], f["type"], index, f.get("kind", data["kind"]), f.get("label"), f.get("unit"),
              f.get("divisor"), f.get("values"), f.get("value_labels"), bool(f.get("skip")), bool(f.get("guard")),
              f.get("min"), f.get("max"), f.get("step"))
        for index, f in enumerate(data["fields"]))
    write = data.get("write")
    conditions = None if write is None else WriteConditions(
        write["source"], bool(write.get("runtime_checksum")), write["risk"], write.get("proof", ""),
        tuple(write.get("open", ())))
    return Message(key, data["circuit"], data["name"], data["address"], data["device"], data["menu"], data["kind"],
                   data["label"], bool(data["passive"]), data.get("poll"), fields, bool(data.get("compose")),
                   data.get("family"), data.get("group"), data.get("position"), data.get("same_as"),
                   conditions, data.get("renamed_from"))


def _base_type(name: str) -> str:
    """`BI0:1` of ebusd is the `BI0` of the metadata; other lengths (`BI0:7`, `HEX:2`) are written in both."""
    return name[:-2] if name.startswith("BI") and name.endswith(":1") else name


def _difference(message: Message, definition) -> str:
    """Empty when the definition ebusd loaded is the one the metadata describes."""
    loaded = [f for f in definition.fields if not f.type.startswith("IGN")]
    if [f.name for f in loaded] != [f.name for f in message.fields]:
        return f"fields {','.join(f.name for f in loaded)}"
    for ours, theirs in zip(message.fields, loaded):
        if _base_type(theirs.type) != _base_type(ours.type):
            return f"{ours.name}: type {theirs.type}, expected {ours.type}"
        if ours.values is not None:
            expected = ";".join(f"{raw}={name}" for raw, name in sorted(ours.values.items(), key=lambda i: int(i[0])))
        else:
            expected = "" if ours.divisor is None else str(ours.divisor)
        if theirs.divisor_or_values != expected:
            return f"{ours.name}: divisor or values {theirs.divisor_or_values!r}, expected {expected!r}"
        if theirs.unit != (ours.unit or ""):
            return f"{ours.name}: unit {theirs.unit!r}, expected {ours.unit!r}"
    return ""


def _value_entities(model: Model) -> tuple[ValueEntity, ...]:
    """One entity per value that is not part of a group, with a name that is unique on its device.

    The translation key is `<device type>_<message>` (one value) or `<device type>_<message>_<field>`: devices of
    one type share their names. A message that reads the same register as another of its device is left out."""
    drafts = []
    for message in model.messages.values():
        if message.same_as or message.family in ("program", "fault_history"):
            continue
        shown = [f for f in message.fields if f.shown]
        for fld in shown:
            if fld.type.startswith(("TTQ",)):
                continue
            single = len(shown) == 1
            label = message.label if single or fld.label is None else fld.label
            composed = {lang: f"{message.label[lang]}{NAME_SEPARATOR}{text}" for lang, text in label.items()}
            name = label if single or not message.compose else composed
            drafts.append([message, fld, single, name, composed])
    device_type = {m.key: model.device_of(m).type for m in model.messages.values()}
    # a field whose name is already used on its device is prefixed with the label of its message
    for _ in range(2):
        used = Counter((message.device, name["en"]) for message, _, _, name, _ in drafts)
        for draft in drafts:
            message, _, single, name, composed = draft
            if used[(message.device, name["en"])] > 1 and not single:
                draft[3] = composed
    entities = []
    for message, fld, single, name, _ in drafts:
        key = f"{device_type[message.key]}_{message.name.lower()}" + ("" if single else f"_{fld.name.lower()}")
        entities.append(ValueEntity(message, fld, key, name))
    _check_unique(entities)
    return tuple(entities)


def _group_entities(model: Model) -> tuple[GroupEntity, ...]:
    entities = []
    for group in model.groups.values():
        if group.family == "fault_counter":  # its counters are value entities
            continue
        prefix = "program" if group.family == "program" else model.devices[group.device].type
        entities.append(GroupEntity(group, f"{prefix}_{group.id}", group.label))
    _check_unique(entities)
    return tuple(entities)


def _check_unique(entities) -> None:
    names: dict[str, dict[str, str]] = {}
    for entity in entities:
        known = names.setdefault(entity.translation_key, entity.name)
        if known != entity.name:
            raise ValueError(f"translation key {entity.translation_key}: {known} and {entity.name}")
    per_device = Counter(
        ((e.message.device if isinstance(e, ValueEntity) else e.group.device), e.name["en"]) for e in entities)
    twice = [key for key, count in per_device.items() if count > 1]
    if twice:
        raise ValueError(f"names used twice on a device: {twice}")
