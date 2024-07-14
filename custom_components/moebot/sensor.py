import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE, )
from homeassistant.helpers.entity import EntityCategory

from . import BaseMoeBotEntity
from .const import DOMAIN

_log = logging.getLogger()


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [MowingStateSensor(moebot), BatterySensor(moebot), EmergencyStateSensor(moebot), WorkModeSensor(moebot),
         PyMoebotVersionSensor(moebot), TuyaVersionSensor(moebot)])


class SensorBase(BaseMoeBotEntity, SensorEntity):
    def __init__(self, moebot):
        """Initialize the sensor."""
        super().__init__(moebot)


class MowingStateSensor(SensorBase):
    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_state"

        # The name of the entity
        self._attr_name = f"Mowing State"

        self._state = "UNKNOWN"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._moebot.state


class EmergencyStateSensor(SensorBase):
    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_emergency_state"

        # The name of the entity
        self._attr_name = f"Emergency State"

        self._state = "UNKNOWN"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._moebot.emergency_state


class WorkModeSensor(SensorBase):
    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_work_mode"

        # The name of the entity
        self._attr_name = f"Work Mode"

        self._state = "UNKNOWN"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._moebot.work_mode


class BatterySensor(SensorBase):
    def __init__(self, moebot):
        """Initialize the sensor."""
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_battery"

        # The name of the entity
        self._attr_name = f"Battery Level"

        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    # The value of this sensor. As this is a SensorDeviceClass.BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return int(self._moebot.battery)


class PyMoebotVersionSensor(SensorBase):
    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_pymoebot_version"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # The name of the entity
        self._attr_name = f"pymoebot Version"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._moebot.pymoebot_version


class TuyaVersionSensor(SensorBase):
    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_tuya_version"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # The name of the entity
        self._attr_name = f"Tuya Protocol Version"

    # The value of this sensor.
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._moebot.tuya_version
