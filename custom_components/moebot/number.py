import logging
from dataclasses import dataclass
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

    entities = [WorkingTimeNumber(moebot)]
    for zone in range(1, 6):
        for part in ZoneNumberType:
            entities.append(ZoneConfigNumber(moebot, zone, part))

    async_add_entities(entities)


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


@dataclass
class ZoneTypeDataMixin:
    type_name: str
    position: int


class ZoneNumberType(ZoneTypeDataMixin, Enum):
    DISTANCE = 'Distance', 0
    RATIO = 'Ratio', 1


class ZoneConfigNumber(BaseMoeBotEntity, NumberEntity):
    def __init__(self, moebot: MoeBot, zone: int, part: ZoneNumberType):
        super().__init__(moebot)
        self.zone = zone
        self.part = part

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_zone{self.zone}_{self.part.value.type_name.lower()}"
        self._attr_entity_category = EntityCategory.CONFIG

        self._attr_name = f"Zone {self.zone} {self.part.value.type_name}"

        self._attr_native_min_value = 0
        self._attr_native_max_value = 100 if self.part == ZoneNumberType.RATIO else 200
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        self._number_option_unit_of_measurement = "%" if self.part == ZoneNumberType.RATIO else "m"
        self._attr_device_class = NumberDeviceClass.DISTANCE if self.part == ZoneNumberType.DISTANCE else None

        self._attr_entity_registry_enabled_default = False

    @classmethod
    def zone_config_to_list(cls, zc: ZoneConfig):
        return [int(zc.zone1[0]), int(zc.zone1[1]),
                int(zc.zone2[0]), int(zc.zone2[1]),
                int(zc.zone3[0]), int(zc.zone3[1]),
                int(zc.zone4[0]), int(zc.zone4[1]),
                int(zc.zone5[0]), int(zc.zone5[1]),
                ]

    @property
    def native_value(self) -> float:
        if not self._moebot.zones:
            _log.debug("Zone data hasn't been retrieved, can't provide values")
            return

        zone_values = ZoneConfigNumber.zone_config_to_list(self._moebot.zones)

        return zone_values[(2 * (self.zone - 1)) + self.part.value.position]

    def set_native_value(self, value: float) -> None:
        new_zone_values = ZoneConfigNumber.zone_config_to_list(self._moebot.zones)
        new_zone_values[(2 * (self.zone - 1)) + self.part.value.position] = int(value)

        zc = ZoneConfig(*new_zone_values)
        self._moebot.zones = zc
