from __future__ import annotations

import asyncio
import logging
from typing import Any

from pymoebot import MoeBot

from homeassistant.components.vacuum import StateVacuumEntity, STATE_DOCKED, StateVacuumEntityDescription, \
    STATE_CLEANING, STATE_RETURNING, STATE_ERROR, VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level
from .const import DOMAIN
from ...const import STATE_PAUSED, STATE_IDLE
from ...helpers.entity import DeviceInfo

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
}

_log = logging.getLogger()

async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up MoeBot from a config entry."""
    moebot = hass.data[DOMAIN][entry.entry_id]

    moebot_entity = MoeBotVacuumEntity(moebot)
    # hass.async_add_executor_job(moebot_entity.initialise())
    async_add_entities([moebot_entity])


class MoeBotVacuumEntity(StateVacuumEntity):
    entity_description: StateVacuumEntityDescription

    # MoeBot class is PUSH, so we tell HA that it should not be polled
    should_poll = False

    def __init__(self, moebot):
        self.__moebot = moebot
        # self.__moebot.add_listener(self.moebot_listener)
        # # self.__moebot.listen()

        self._attr_unique_id = f"moebot.{self.__moebot.id}"
        self._attr_supported_features = 0
        self._attr_supported_features |= VacuumEntityFeature.PAUSE
        self._attr_supported_features |= VacuumEntityFeature.STOP
        self._attr_supported_features |= VacuumEntityFeature.RETURN_HOME
        self._attr_supported_features |= VacuumEntityFeature.BATTERY
        self._attr_supported_features |= VacuumEntityFeature.STATUS
        self._attr_supported_features |= VacuumEntityFeature.CLEAN_SPOT
        self._attr_supported_features |= VacuumEntityFeature.STATE
        self._attr_supported_features |= VacuumEntityFeature.START

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # The call back registration is done once this entity is registered with HA
        # (rather than in the __init__)
        def listener(raw_msg):
            _log.info("Got an update: %r" % raw_msg)
            self.async_write_ha_state()

        self.__moebot.add_listener(listener)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "manufacturer": "MoeBot",
            "name": self.name,
        }

    @property
    def state(self) -> str | None:
        mb_state = self.__moebot.state
        return _STATUS_TO_HA[mb_state]

    # @property
    # def should_poll(self) -> bool:
    #     return False

    @property
    def name(self) -> str | None:
        return "MoeBot (%s)" % self.__moebot.id



    @property
    def battery_icon(self) -> str:
        """Return the battery icon for the vacuum cleaner."""
        charging = bool(self.__moebot.state == "CHARGING" or self.__moebot.state == "CHARGING_WITH_TASK_SUSPEND")

        return icon_for_battery_level(
            battery_level=self.battery_level, charging=charging
        )

    @property
    def battery_level(self) -> int | None:
        return round(self.__moebot.battery)

    def moebot_listener(self, data):
        _log.warning("UPDATE: ", data)
        self.async_write_ha_state()

    def start(self) -> None:
        """Start or resume the cleaning task."""
        raise NotImplementedError()

    async def async_start(self) -> None:
        """Start or resume the cleaning task.

        This method must be run in the event loop.
        """
        await self.hass.async_add_executor_job(self.start)

    def pause(self) -> None:
        """Pause the cleaning task."""
        raise NotImplementedError()

    async def async_pause(self) -> None:
        """Pause the cleaning task.

        This method must be run in the event loop.
        """
        await self.hass.async_add_executor_job(self.pause)

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
