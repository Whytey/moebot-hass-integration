from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    StateVacuumEntityDescription,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_STATUS_TO_HA = {
    "STANDBY": VacuumActivity.DOCKED,
    "MOWING": VacuumActivity.CLEANING,
    "CHARGING": VacuumActivity.DOCKED,
    "EMERGENCY": VacuumActivity.ERROR,
    "LOCKED": VacuumActivity.ERROR,
    "PAUSED": VacuumActivity.IDLE,
    "PARK": VacuumActivity.RETURNING,
    "CHARGING_WITH_TASK_SUSPEND": VacuumActivity.DOCKED,
    "FIXED_MOWING": VacuumActivity.CLEANING,
    "ERROR": VacuumActivity.ERROR,
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

        self.__attr_icon = "mdi:robot-mower"

        self._attr_supported_features = 0
        self._attr_supported_features |= VacuumEntityFeature.PAUSE
        self._attr_supported_features |= VacuumEntityFeature.STOP
        self._attr_supported_features |= VacuumEntityFeature.RETURN_HOME
        self._attr_supported_features |= VacuumEntityFeature.STATE
        self._attr_supported_features |= VacuumEntityFeature.START

    @property
    def activity(self) -> VacuumActivity | None:
        mb_state = self._moebot.state
        return _STATUS_TO_HA[mb_state]

    def start(self) -> None:
        """Start or resume the cleaning task."""
        self._moebot.start()

    def pause(self) -> None:
        """Pause the cleaning task."""
        self._moebot.pause()

    def stop(self, **kwargs: Any) -> None:
        self._moebot.cancel()

    def return_to_base(self, **kwargs: Any) -> None:
        self._moebot.dock()

    def clean_spot(self, **kwargs: Any) -> None:
        self._moebot.start(spiral=True)
