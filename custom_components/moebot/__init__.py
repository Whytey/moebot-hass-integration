"""The MoeBot integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, DeviceInfo
from pymoebot import MoeBot

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.VACUUM, Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]
_log = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MoeBot from a config entry."""
    moebot = await hass.async_add_executor_job(MoeBot, entry.data["device_id"], entry.data["ip_address"], entry.data["local_key"])
    _log.info("Created a moebot: %r" % moebot)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = moebot
    await hass.async_add_executor_job(moebot.listen)

    def shutdown_moebot(event):
        _log.debug("In the shutdown callback")
        moebot.unlisten()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shutdown_moebot)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        moebot = hass.data[DOMAIN][entry.entry_id]
        moebot.unlisten()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class BaseMoeBotEntity(Entity):
    """The abstract base device for all MoeBot entities."""

    def __init__(self, moebot: MoeBot):
        self._moebot = moebot

        # MoeBot class is LOCAL PUSH, so we tell HA that it should not be polled
        self._attr_should_poll = False

        # Link this Entity under the MoeBot (vacuum) device by ensuring this property returns an
        # identifiers value matching that used in the vacuum Entity, but no other information.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._moebot.id)}
        )

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        # The call back registration is done once this entity is registered with HA
        # (rather than in the __init__)
        def listener(raw_msg):
            _log.debug("%r got an update: %r" % (self.__class__.__name__, raw_msg))
            self.async_write_ha_state()

        self._moebot.add_listener(listener)

    @property
    def available(self) -> bool:
        return self._moebot.state is not None
