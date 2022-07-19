import logging
from typing import Any

from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN
from ..number import NumberEntity, ATTR_MIN, ATTR_MAX, ATTR_STEP, NumberMode
from ...const import ATTR_MODE

_log = logging.getLogger()


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([WorkingTimeNumber(moebot)])


class WorkingTimeNumber(NumberEntity):
    should_poll = False

    def __init__(self, moebot):
        """Initialize the sensor."""
        self.__moebot = moebot

        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"moebot.{self.__moebot.id}_mow_time_hrs"

        # The name of the entity
        self._attr_name = f"MoeBot (%s) Mowing Time" % self.__moebot.id

    # To link this entity to the moebot device, this property must return an
    # identifiers value matching that used in the vacuum, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, f"moebot.{self.__moebot.id}")},
        }

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        # The call back registration is done once this entity is registered with HA
        # (rather than in the __init__)
        def listener(raw_msg):
            _log.info("Got an update: %r" % raw_msg)
            self.async_write_ha_state()

        self.__moebot.add_listener(listener)

    @property
    def capability_attributes(self) -> dict[str, Any]:
        """Return capability attributes."""
        return {
            ATTR_MIN: 1,
            ATTR_MAX: 12,
            ATTR_STEP: 1,
            ATTR_MODE: NumberMode.SLIDER,
        }

    @property
    def value(self) -> int :
        return self.__moebot.mow_time

    def set_value(self, value: float) -> None:
        self.__moebot.mow_time = int(value)

