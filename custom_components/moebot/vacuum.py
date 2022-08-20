from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import StateVacuumEntity, STATE_DOCKED, StateVacuumEntityDescription, \
    STATE_CLEANING, STATE_RETURNING, STATE_ERROR, VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level
from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_STATUS_TO_HA = {
    "STANDBY": STATE_DOCKED,
    "MOWING": STATE_CLEANING,
    "CHARGING": STATE_DOCKED,
    "EMERGENCY": STATE_ERROR,
    "LOCKED": STATE_ERROR,
    "PAUSED": STATE_IDLE,
    "PARK": STATE_RETURNING,
    "CHARGING_WITH_TASK_SUSPEND": STATE_DOCKED,
    "FIXED_MOWING": STATE_CLEANING,
    "ERROR": STATE_ERROR,
}

_log = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up MoeBot from a config entry."""
    moebot = hass.data[DOMAIN][entry.entry_id]

    moebot_entity = MoeBotVacuumEntity(moebot)
    async_add_entities([moebot_entity])


class MoeBotVacuumEntity(BaseMoeBotEntity, StateVacuumEntity):
    entity_description: StateVacuumEntityDescription

    def __init__(self, moebot: MoeBot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_vacuum"

        self._attr_name = f"MoeBot"

        # The vacuum Entity is actually the Device for the MoeBot integration. Therefore, we can provide the
        # other supporting metadata about the Device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._moebot.id)},
            manufacturer="MoeBot",
            name=f"{self.name} ({self._moebot.id})"
        )

        self._attr_supported_features = 0
        self._attr_supported_features |= VacuumEntityFeature.PAUSE
        self._attr_supported_features |= VacuumEntityFeature.STOP
        self._attr_supported_features |= VacuumEntityFeature.RETURN_HOME
        self._attr_supported_features |= VacuumEntityFeature.BATTERY
        self._attr_supported_features |= VacuumEntityFeature.STATUS
        self._attr_supported_features |= VacuumEntityFeature.CLEAN_SPOT
        self._attr_supported_features |= VacuumEntityFeature.STATE
        self._attr_supported_features |= VacuumEntityFeature.START

    @property
    def state(self) -> str | None:
        mb_state = self._moebot.state
        return _STATUS_TO_HA[mb_state]

    @property
    def battery_icon(self) -> str:
        """Return the battery icon for the vacuum cleaner."""
        charging = bool(self._moebot.state == "CHARGING" or self._moebot.state == "CHARGING_WITH_TASK_SUSPEND")

        return icon_for_battery_level(
            battery_level=self.battery_level, charging=charging
        )

    @property
    def battery_level(self) -> int | None:
        return round(self._moebot.battery)

    def start(self) -> None:
        """Start or resume the cleaning task."""
        raise NotImplementedError()

    def pause(self) -> None:
        """Pause the cleaning task."""
        raise NotImplementedError()

    def stop(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    def return_to_base(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    def clean_spot(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    def locate(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        raise NotImplementedError()

    def send_command(self, command: str, params: dict | list | None = None, **kwargs: Any) -> None:
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Not supported."""
        raise NotImplementedError()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Not supported."""
        raise NotImplementedError()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Not supported."""
        raise NotImplementedError()
