import logging
from enum import Enum

from homeassistant.components.number import NumberEntity, NumberMode, NumberDeviceClass
from homeassistant.helpers.entity import EntityCategory
from pymoebot import ZoneConfig, MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_log = logging.getLogger(__package__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [WorkingTimeNumber(moebot), Zone1RatioNumber(moebot), Zone1DistanceNumber(moebot), Zone2RatioNumber(moebot),
         Zone2DistanceNumber(moebot)])


class WorkingTimeNumber(BaseMoeBotEntity, NumberEntity):

    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_mow_time_hrs"
        self._attr_entity_category = EntityCategory.CONFIG

        self._attr_name = f"Mowing Time"

        self._attr_native_min_value = 1
        self._attr_native_max_value = 12
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_device_class = NumberDeviceClass.DURATION
        self._number_option_unit_of_measurement = "hrs"

    @property
    def native_value(self) -> float:
        return self._moebot.mow_time

    def set_native_value(self, value: float) -> None:
        self._moebot.mow_time = int(value)


class ZoneNumberType(Enum):
    RATIO = 'Ratio'
    DISTANCE = 'Distance'


class AbstractZoneNumber(BaseMoeBotEntity, NumberEntity):
    def __init__(self, moebot: MoeBot, zone: int, part: ZoneNumberType):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_zone{zone}_{part.value.lower()}"
        self._attr_entity_category = EntityCategory.CONFIG

        self._attr_name = f"Zone {zone} {part.value}"

        self._attr_native_min_value = 0
        self._attr_native_max_value = 100 if part == ZoneNumberType.RATIO else 200
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        self._number_option_unit_of_measurement = "%" if part == ZoneNumberType.RATIO else "m"
        self._attr_device_class = NumberDeviceClass.DISTANCE if part == ZoneNumberType.DISTANCE else None

        self._attr_entity_registry_enabled_default = False


class Zone1RatioNumber(AbstractZoneNumber):

    def __init__(self, moebot):
        super().__init__(moebot, 1, ZoneNumberType.RATIO)

    @property
    def native_value(self) -> float:
        distance, ratio = self._moebot.zones.zone1
        return ratio

    def set_native_value(self, value: float) -> None:
        zc = ZoneConfig(int(self._moebot.zones.zone1[0]), int(value),
                        int(self._moebot.zones.zone2[0]), int(self._moebot.zones.zone2[1]),
                        int(self._moebot.zones.zone3[0]), int(self._moebot.zones.zone3[1]),
                        int(self._moebot.zones.zone4[0]), int(self._moebot.zones.zone4[1]),
                        int(self._moebot.zones.zone5[0]), int(self._moebot.zones.zone5[1]),
                        )
        self._moebot.zones = zc


class Zone1DistanceNumber(AbstractZoneNumber):

    def __init__(self, moebot):
        super().__init__(moebot, 1, ZoneNumberType.DISTANCE)

    @property
    def native_value(self) -> float:
        distance, ratio = self._moebot.zones.zone1
        return distance

    def set_native_value(self, value: float) -> None:
        zc = ZoneConfig(int(value), int(self._moebot.zones.zone1[1]),
                        int(self._moebot.zones.zone2[0]), int(self._moebot.zones.zone2[1]),
                        int(self._moebot.zones.zone3[0]), int(self._moebot.zones.zone3[1]),
                        int(self._moebot.zones.zone4[0]), int(self._moebot.zones.zone4[1]),
                        int(self._moebot.zones.zone5[0]), int(self._moebot.zones.zone5[1]),
                        )
        self._moebot.zones = zc


class Zone2RatioNumber(AbstractZoneNumber):

    def __init__(self, moebot):
        super().__init__(moebot, 2, ZoneNumberType.RATIO)

    @property
    def native_value(self) -> float:
        distance, ratio = self._moebot.zones.zone2
        return ratio

    def set_native_value(self, value: float) -> None:
        zc = ZoneConfig(int(self._moebot.zones.zone1[0]), int(self._moebot.zones.zone1[1]),
                        int(self._moebot.zones.zone2[0]), int(value),
                        int(self._moebot.zones.zone3[0]), int(self._moebot.zones.zone3[1]),
                        int(self._moebot.zones.zone4[0]), int(self._moebot.zones.zone4[1]),
                        int(self._moebot.zones.zone5[0]), int(self._moebot.zones.zone5[1]),
                        )
        self._moebot.zones = zc


class Zone2DistanceNumber(AbstractZoneNumber):

    def __init__(self, moebot):
        super().__init__(moebot, 2, ZoneNumberType.DISTANCE)

    @property
    def native_value(self) -> float:
        distance, ratio = self._moebot.zones.zone2
        return distance

    def set_native_value(self, value: float) -> None:
        zc = ZoneConfig(int(self._moebot.zones.zone1[0]), int(self._moebot.zones.zone1[1]),
                        int(value), int(self._moebot.zones.zone2[1]),
                        int(self._moebot.zones.zone3[0]), int(self._moebot.zones.zone3[1]),
                        int(self._moebot.zones.zone4[0]), int(self._moebot.zones.zone4[1]),
                        int(self._moebot.zones.zone5[0]), int(self._moebot.zones.zone5[1]),
                        )
        self._moebot.zones = zc
