"""The MoeBot integration."""
from __future__ import annotations

import logging
from pymoebot import MoeBot

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.VACUUM, Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]
_log = logging.getLogger()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MoeBot from a config entry."""
    moebot = MoeBot(entry.data["device_id"], entry.data["ip_address"], entry.data["local_key"])
    _log.info("Created a moebot: %r" % moebot)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = moebot

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
