"""The ebusd add-ons the Supervisor lists: only ebusd ones, by name; nothing without the Supervisor or its list."""
from __future__ import annotations

from homeassistant.components import hassio

from custom_components.weishaupt import supervisor
from custom_components.weishaupt.supervisor import Addon


async def test_ebusd_addons_from_the_supervisor(hass, monkeypatch):
    monkeypatch.setattr(supervisor, "is_hassio", lambda _hass: True)
    monkeypatch.setattr(hassio, "get_addons_list", lambda _hass: [
        {"slug": "a0d7b954_ebusd", "name": "ebusd", "state": "started"},
        {"slug": "local_ebusd_test", "state": "stopped"},  # no name: its slug
        {"slug": "core_mosquitto", "name": "Mosquitto broker", "state": "started"},  # not ebusd
        {"name": "no slug"}])
    assert supervisor.ebusd_addons(hass) == [Addon("a0d7b954_ebusd", "ebusd", "started"),
                                             Addon("local_ebusd_test", "local_ebusd_test", "stopped")]
    assert supervisor.addon_states(hass) == {"a0d7b954_ebusd": "started", "local_ebusd_test": "stopped"}


async def test_no_list_no_addons(hass, monkeypatch):
    assert supervisor.ebusd_addons(hass) == []  # no Supervisor
    monkeypatch.setattr(supervisor, "is_hassio", lambda _hass: True)

    def not_ready(_hass):
        raise KeyError("addons")

    monkeypatch.setattr(hassio, "get_addons_list", not_ready)
    assert supervisor.ebusd_addons(hass) == []
    monkeypatch.setattr(hassio, "get_addons_list", lambda _hass: None)
    assert supervisor.ebusd_addons(hass) == []
