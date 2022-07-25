import logging

from homeassistant.components.number import NumberEntity, NumberMode

from . import BaseMoeBotEntity
from .const import DOMAIN

_log = logging.getLogger(__package__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([WorkingTimeNumber(moebot)])


class WorkingTimeNumber(BaseMoeBotEntity, NumberEntity):

    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_mow_time_hrs"

        self._attr_name = f"Mowing Time"

        self._attr_native_min_value = 1
        self._attr_native_max_value = 12
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._number_option_unit_of_measurement = "hrs"

    @property
    def native_value(self) -> float:
        return self._moebot.mow_time

    def set_native_value(self, value: float) -> None:
        self._moebot.mow_time = int(value)
