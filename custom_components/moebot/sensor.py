import logging

from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    PERCENTAGE,
)
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

_log = logging.getLogger()


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([StateSensor(moebot), BatterySensor(moebot)])


class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, moebot):
        """Initialize the sensor."""
        self.__moebot = moebot

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


class StateSensor(SensorBase):
    def __init__(self, moebot):
        """Initialize the sensor."""
        super().__init__(moebot)

        self.__moebot = moebot

        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"moebot.{self.__moebot.id}_state"

        # The name of the entity
        self._attr_name = f"MoeBot (%s) State" % self.__moebot.id

        self._state = "UNKNOWN"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.__moebot.state


class BatterySensor(SensorBase):
    device_class = DEVICE_CLASS_BATTERY

    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, moebot):
        """Initialize the sensor."""
        super().__init__(moebot)

        self.__moebot = moebot

        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"moebot.{self.__moebot.id}_battery"

        # The name of the entity
        self._attr_name = f"MoeBot (%s) Battery" % self.__moebot.id

        self._state = 0

    # The value of this sensor. As this is a DEVICE_CLASS_BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.__moebot.battery
