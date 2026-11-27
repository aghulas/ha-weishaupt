"""Tests for the MQTT transport (`MqttHub`, `MqttWriter`, and MQTT config/options flow)."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weishaupt.const import (
    CONF_BASE_TOPIC,
    CONF_TRANSPORT,
    CONF_WRITES_ENABLED,
    DOMAIN,
    TRANSPORT_MQTT,
)
from custom_components.weishaupt.diagnostics import async_get_config_entry_diagnostics
from custom_components.weishaupt.mqtt_bridge import MqttHub, MqttWriter
from custom_components.weishaupt.writer import ConfirmationPending


@dataclass
class _FakeMsg:
    topic: str
    payload: str


class _FakeMqttBus:
    """In-memory MQTT broker stub for `homeassistant.components.mqtt`."""

    def __init__(self) -> None:
        self.subs: list[tuple[str, Any]] = []
        self.published: list[tuple[str, str, int, bool]] = []
        self.retained: dict[str, str] = {}

    @staticmethod
    def _matches(pattern: str, topic: str) -> bool:
        p_parts = pattern.split("/")
        t_parts = topic.split("/")
        for i, p in enumerate(p_parts):
            if p == "#":
                return True
            if i >= len(t_parts):
                return False
            if p != "+" and p != t_parts[i]:
                return False
        return len(p_parts) == len(t_parts)

    async def subscribe(self, hass: HomeAssistant, topic: str, callback_fn: Any, qos: int = 0) -> Any:
        entry = (topic, callback_fn)
        self.subs.append(entry)
        # Deliver any matching retained messages immediately
        for r_topic, r_payload in list(self.retained.items()):
            if self._matches(topic, r_topic):
                callback_fn(_FakeMsg(r_topic, r_payload))

        def unsub() -> None:
            if entry in self.subs:
                self.subs.remove(entry)

        return unsub

    async def publish(self, hass: HomeAssistant, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        self.published.append((topic, payload, qos, retain))
        if retain:
            self.retained[topic] = payload

    def emit(self, topic: str, payload: Any) -> None:
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        for pattern, cb in list(self.subs):
            if self._matches(pattern, topic):
                cb(_FakeMsg(topic, raw))


def _bridge_info(circuits: list[str] | None = None, checksum: str = "present") -> dict[str, Any]:
    return {
        "bridge_version": "0.1.2",
        "definitions_version": "1.3.1",
        "ebusd_version": "26.1.p20261120",
        "run_time_checksum": checksum,
        "bus_signal": True,
        "circuits": circuits or ["bc1", "ka", "em2", "fs1", "broadcast"],
        "writes": {"enabled": False, "installer_enabled": False, "used_last_hour": 0, "max_per_hour": 30},
    }


async def _setup_mqtt_entry(
    hass: HomeAssistant, bus: _FakeMqttBus, *, writes_enabled: bool = False
) -> MockConfigEntry:
    bus.retained["weishaupt/bridge/state"] = "online"
    bus.retained["weishaupt/bridge/info"] = json.dumps(_bridge_info())
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Weishaupt",
        unique_id="mqtt:weishaupt",
        data={CONF_TRANSPORT: TRANSPORT_MQTT, CONF_BASE_TOPIC: "weishaupt"},
        options={CONF_WRITES_ENABLED: writes_enabled},
        version=2,
        minor_version=3,
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_wait_for_mqtt_client", AsyncMock(return_value=True)),
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_subscribe", side_effect=bus.subscribe),
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_publish", side_effect=bus.publish),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_mqtt_setup_state_and_program_push(hass: HomeAssistant) -> None:
    """MQTT bridge info creates devices/entities; state and program pushes update entities immediately."""
    bus = _FakeMqttBus()
    entry = await _setup_mqtt_entry(hass, bus, writes_enabled=False)
    assert entry.state is ConfigEntryState.LOADED
    hub = entry.runtime_data
    assert isinstance(hub, MqttHub)
    assert hub.available is True
    assert hub.capability == "present"
    assert {"boiler1", "manager", "module2", "room1", "system"} <= set(hub.devices)

    # Push scalar + multi-field state on ka
    bus.emit(
        "weishaupt/ka/state",
        {
            "OutsideTemp": 7.5,
            "DeCoupleTemp": 59.1,
            "Boiler1Status": {
                "status1": 1,
                "operatingphase": "BurnerOff",
                "flame": "off",
                "supplytemp": 72.0,
                "outsidetemp": 7.5,
            },
            "_updated": "2026-11-24T18:10:00+01:00",
        },
    )
    await hass.async_block_till_done()
    assert hub.reading("ka/OutsideTemp") == ("7.5",)
    assert hub.reading("ka/DeCoupleTemp") == ("59.1",)

    # Push weekly program on fs1
    bus.emit(
        "weishaupt/fs1/program/heating1",
        {
            "circuit": "fs1",
            "program": "heating1",
            "days": {"1": ["06:30-18:00", "19:00-21:00"], "2": ["06:30-18:00"], "3": [], "4": [], "5": [], "6": [], "7": []},
        },
    )
    await hass.async_block_till_done()
    assert hub.reading("fs1/HCProgram1Mon1") == ("18:00", "Enabled", "06:30", "Enabled")
    assert hub.reading("fs1/HCProgram1Mon2") == ("21:00", "Enabled", "19:00", "Enabled")
    assert hub.reading("fs1/HCProgram1Mon3") == ("00:00", "Disabled", "00:00", "Disabled")

    # Bridge offline flips availability
    bus.emit("weishaupt/bridge/state", "offline")
    assert hub.available is False
    bus.emit("weishaupt/bridge/state", "online")
    assert hub.available is True

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_mqtt_level1_and_level2_writes_and_program(hass: HomeAssistant) -> None:
    """Level 1 comfort writes go to <circuit>/set, Level 2 installer writes need confirmation and go to installer/set."""
    bus = _FakeMqttBus()
    with (
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_wait_for_mqtt_client", AsyncMock(return_value=True)),
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_subscribe", side_effect=bus.subscribe),
        patch("custom_components.weishaupt.mqtt_bridge.mqtt.async_publish", side_effect=bus.publish),
    ):
        entry = await _setup_mqtt_entry(hass, bus, writes_enabled=True)
        hub = entry.runtime_data
        assert isinstance(hub.writer, MqttWriter)
        writer = hub.writer

        # Enable write switch -> publishes bridge/config/set
        writer.set_switch(True)
        await hass.async_block_till_done()
        assert any(t == "weishaupt/bridge/config/set" and json.loads(p) == {"writes_enabled": True} for t, p, _, _ in bus.published)

        # Level 1 comfort write: fs1/RoomNormalTemp
        async def _reply_next(circuit: str, status: str = "ok", read_back: Any = 21.5) -> None:
            for _ in range(50):
                await asyncio.sleep(0.01)
                for topic, payload, _, _ in reversed(bus.published):
                    if topic.startswith(f"weishaupt/{circuit}/"):
                        data = json.loads(payload)
                        if "correlation_id" in data:
                            bus.emit(f"weishaupt/{circuit}/result", {
                                "status": status,
                                "correlation_id": data["correlation_id"],
                                "read_back": read_back,
                            })
                            return

        bus.published.clear()
        reply_task = asyncio.create_task(_reply_next("fs1", "ok", 21.5))
        res = await writer.async_request("fs1/RoomNormalTemp", 21.5, "user-1")
        await reply_task
        assert res["result"] == "ok"
        assert bus.published[0][0] == "weishaupt/fs1/set"
        assert json.loads(bus.published[0][1])["RoomNormalTemp"] == 21.5

        # Level 2 regulation/installer write: em2/SupplyMaxTemp -> must require confirmation first
        bus.published.clear()
        with pytest.raises(ConfirmationPending) as exc_info:
            await writer.async_request("em2/SupplyMaxTemp", 74.0, "user-1", inline=True)
        assert bus.published == []  # nothing sent before confirmation

        reply_task = asyncio.create_task(_reply_next("em2", "ok", 74.0))
        res2 = await writer.async_confirm(exc_info.value.pending_id, "user-1")
        await reply_task
        assert res2["result"] == "ok"
        assert bus.published[0][0] == "weishaupt/em2/installer/set"
        sent2 = json.loads(bus.published[0][1])
        assert sent2["SupplyMaxTemp"] == 74.0
        assert sent2["confirm"] is True

        # Weekly program write on fs1/heating1
        bus.published.clear()
        reply_task = asyncio.create_task(_reply_next("fs1", "ok"))
        prog_res = await writer.async_write_day("fs1/heating1", 1, "06:30-18:00, 19:00-21:00", "user-1")
        await reply_task
        assert prog_res["status"] == "ok"
        assert bus.published[0][0] == "weishaupt/fs1/program/heating1/set"
        assert json.loads(bus.published[0][1])["days"] == {"1": ["06:30-18:00", "19:00-21:00"]}

        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_reconfigure_switch_to_mqtt(hass: HomeAssistant) -> None:
    """Reconfigure menu offers Weishaupt2MQTT and switches an ebusd entry to MQTT cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Weishaupt",
        unique_id="10.0.0.1:8888",
        data={"host": "10.0.0.1", "port": 8888},
        version=2,
        minor_version=3,
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )
    assert result["type"] is FlowResultType.MENU and result["step_id"] == "reconfigure"
    assert "mqtt" in result["menu_options"]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "mqtt"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "mqtt"

    with patch.object(hass.config_entries, "async_reload", AsyncMock()):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_BASE_TOPIC: "weishaupt"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TRANSPORT] == TRANSPORT_MQTT
    assert entry.data[CONF_BASE_TOPIC] == "weishaupt"
    assert entry.unique_id == "mqtt:weishaupt"


# ---- first set-up over MQTT: an entry made for the bridge alone, which never had an ebusd -------------------------

def _mqtt(bus: _FakeMqttBus, available: bool = True):
    """Home Assistant's MQTT integration replaced by the in-memory broker; `available`: whether it is set up."""
    from contextlib import ExitStack
    stack = ExitStack()
    base = "custom_components.weishaupt.mqtt_bridge.mqtt"
    stack.enter_context(patch(f"{base}.async_wait_for_mqtt_client", AsyncMock(return_value=available)))
    stack.enter_context(patch(f"{base}.async_subscribe", side_effect=bus.subscribe))
    stack.enter_context(patch(f"{base}.async_publish", side_effect=bus.publish))
    stack.enter_context(patch("custom_components.weishaupt.mqtt_bridge.BRIDGE_PROBE_TIMEOUT", 0.05))
    return stack


def _online(bus: _FakeMqttBus, topic: str = "weishaupt") -> None:
    bus.retained[f"{topic}/bridge/state"] = "online"
    bus.retained[f"{topic}/bridge/info"] = json.dumps(_bridge_info())


async def _bridge_step(hass: HomeAssistant) -> dict[str, Any]:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.MENU and result["menu_options"] == ["bridge", "ebusd"]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "bridge"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "bridge"
    assert result["data_schema"]({}) == {CONF_BASE_TOPIC: "weishaupt"}  # the default base topic
    return result


async def test_first_setup_with_the_bridge_alone(hass: HomeAssistant) -> None:
    """The first step offers the bridge; its base topic is checked and the entry is created and set up without any
    ebusd address. Nothing is published to find the bridge."""
    bus = _FakeMqttBus()
    _online(bus, "heating/weishaupt")
    with _mqtt(bus):
        result = await _bridge_step(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_TOPIC: "/heating/weishaupt/"})
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY and result["title"] == "Weishaupt"
        assert result["data"] == {CONF_TRANSPORT: TRANSPORT_MQTT, CONF_BASE_TOPIC: "heating/weishaupt"}
        entry = result["result"]
        assert entry.unique_id == "mqtt:heating/weishaupt"
        assert (entry.version, entry.minor_version) == (2, 3)
        assert entry.state is ConfigEntryState.LOADED
        assert isinstance(entry.runtime_data, MqttHub) and entry.runtime_data.base_topic == "heating/weishaupt"
        assert bus.published == []
        assert await hass.config_entries.async_unload(entry.entry_id)
    assert bus.subs == []  # the subscriptions of the check and of the hub are gone


async def test_first_setup_errors_then_recovers(hass: HomeAssistant) -> None:
    """MQTT integration missing, no bridge on the topic, bridge offline, a topic with a wildcard: each its error, and
    the same form creates the entry once the bridge is online."""
    bus = _FakeMqttBus()
    with _mqtt(bus, available=False):
        result = await _bridge_step(hass)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_BASE_TOPIC: "weishaupt"})
        assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "mqtt_not_available"}
    assert bus.subs == []
    with _mqtt(bus):
        flow_id = result["flow_id"]
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt/#"})
        assert result["errors"] == {CONF_BASE_TOPIC: "invalid_topic"}
        # nothing retained on the topic
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        assert result["step_id"] == "bridge" and result["errors"] == {"base": "no_bridge"}
        # a bridge on another base topic is not this one
        _online(bus, "other")
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        assert result["errors"] == {"base": "no_bridge"}
        # `online` without `bridge/info`, and `bridge/info` that is not an object
        bus.retained["weishaupt/bridge/state"] = "online"
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        assert result["errors"] == {"base": "no_bridge"}
        bus.retained["weishaupt/bridge/info"] = "not json"
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        assert result["errors"] == {"base": "no_bridge"}
        # the last will of a bridge that stopped: its info is still retained
        _online(bus)
        bus.retained["weishaupt/bridge/state"] = "offline"
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        assert result["errors"] == {"base": "bridge_offline"}
        assert result["data_schema"]({}) == {CONF_BASE_TOPIC: "weishaupt"}
        assert bus.subs == [] and bus.published == []
        _online(bus)
        result = await hass.config_entries.flow.async_configure(flow_id, {CONF_BASE_TOPIC: "weishaupt"})
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert await hass.config_entries.async_unload(result["result"].entry_id)


async def test_first_setup_same_bridge_twice(hass: HomeAssistant) -> None:
    bus = _FakeMqttBus()
    entry = await _setup_mqtt_entry(hass, bus)
    with _mqtt(bus):
        result = await _bridge_step(hass)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_BASE_TOPIC: "weishaupt/"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "bridge_already_configured"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_bridge_entry_diagnostics_panel_and_menus(hass: HomeAssistant, hass_ws_client) -> None:
    """What an entry reaches that used to assume an ebusd address: the diagnostics download, the tree of the panel,
    the reconfigure and options menus."""
    bus = _FakeMqttBus()
    entry = await _setup_mqtt_entry(hass, bus, writes_enabled=True)
    bus.emit("weishaupt/ka/state", {"OutsideTemp": 7.5})
    await hass.async_block_till_done()

    data = await async_get_config_entry_diagnostics(hass, entry)
    assert data["transport"] == "mqtt" and data["bridge"]["bridge_version"] == "0.1.2"
    assert data["ebusd"]["commands_sent"] == {} and data["ebusd"]["endpoints"] == []
    assert data["ebusd"]["endpoint_in_use"] is None and data["ebusd"]["run_time_checksum"] == "present"
    assert data["readings"]["ka/OutsideTemp"] == "7.5"
    assert data["entry"]["data"] == {CONF_TRANSPORT: TRANSPORT_MQTT, CONF_BASE_TOPIC: "weishaupt"}
    assert entry.entry_id not in json.dumps(data)

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "weishaupt/panel/tree", "entry_id": entry.entry_id})
    tree = (await client.receive_json())["result"]
    assert tree["ebusd"]["endpoints"] == [] and tree["ebusd"]["endpoint"] is None
    assert tree["ebusd"]["available"] is True and tree["ebusd"]["capability"] == "present"
    assert {"boiler1", "manager", "module2", "room1"} <= {d["id"] for d in tree["devices"]}

    # no ebusd to choose and no telegram log to set; the bridge's topic and an ebusd can still be given
    result = await entry.start_reconfigure_flow(hass)
    assert result["menu_options"] == ["mqtt", "endpoints", "settings"]
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU and result["menu_options"] == ["settings", "mqtt"]
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "settings"
    hass.config_entries.options.async_abort(result["flow_id"])
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_bridge_entry_reconfigured_to_an_ebusd(hass: HomeAssistant, fake) -> None:
    """An entry made for the bridge can be given an ebusd from the reconfigure menu: it has no endpoint in use to
    start from."""
    bus = _FakeMqttBus()
    entry = await _setup_mqtt_entry(hass, bus)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "endpoints"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "endpoints"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "127.0.0.1", "port": fake.port})
    assert result["step_id"] == "reconfigure_use" and result["data_schema"]({}) == {"use": "follow"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"use": "follow"})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.unique_id == f"127.0.0.1:{fake.port}"
    assert entry.data[CONF_TRANSPORT] == "ebusd" and entry.data["host"] == "127.0.0.1"
    assert [e["label"] for e in entry.data["endpoints"]] == ["ebusd"] and entry.data["mode"] == "follow"
    assert entry.state is ConfigEntryState.LOADED and not isinstance(entry.runtime_data, MqttHub)
    assert await hass.config_entries.async_unload(entry.entry_id)
