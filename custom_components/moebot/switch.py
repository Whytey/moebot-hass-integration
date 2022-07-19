import logging
from typing import Any

from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from ..switch import SwitchEntity

_log = logging.getLogger()


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([ParkWhenRainingSwitch(moebot)])


class ParkWhenRainingSwitch(SwitchEntity):
    should_poll = False

    def __init__(self, moebot):
        """Initialize the sensor."""
        self.__moebot = moebot

        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"moebot.{self.__moebot.id}_park_when_raining"

        # The name of the entity
        self._attr_name = f"MoeBot (%s) Park When Raining" % self.__moebot.id

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

    def is_on(self) -> bool | None:
        return self.__moebot.mow_in_rain

    def turn_on(self, **kwargs: Any) -> None:
        self.__moebot.mow_in_rain = True

    def turn_off(self, **kwargs: Any) -> None:
        self.__moebot.mow_in_rain = False
