from homeassistant.components.lawn_mower import LawnMowerEntity, LawnMowerEntityEntityDescription, \
    LawnMowerEntityFeature, LawnMowerActivity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pymoebot import MoeBot

from custom_components.moebot import BaseMoeBotEntity
from .const import DOMAIN

_STATUS_TO_HA = {
    "STANDBY": LawnMowerActivity.DOCKED,
    "MOWING": LawnMowerActivity.MOWING,
    "CHARGING": LawnMowerActivity.DOCKED,
    "EMERGENCY": LawnMowerActivity.ERROR,
    "LOCKED": LawnMowerActivity.ERROR,
    "PAUSED": LawnMowerActivity.PAUSED,
    "PARK": LawnMowerActivity.MOWING,
    "CHARGING_WITH_TASK_SUSPEND": LawnMowerActivity.DOCKED,
    "FIXED_MOWING": LawnMowerActivity.MOWING,
    "ERROR": LawnMowerActivity.ERROR,
}


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up MoeBot from a config entry."""
    moebot = hass.data[DOMAIN][entry.entry_id]

    moebot_entity = MoeBotMowerEntity(moebot)
    async_add_entities([moebot_entity])


class MoeBotMowerEntity(BaseMoeBotEntity, LawnMowerEntity):
    entity_description: LawnMowerEntityEntityDescription
    _attr_supported_features = (
            LawnMowerEntityFeature.DOCK
            | LawnMowerEntityFeature.PAUSE
            | LawnMowerEntityFeature.START_MOWING
    )

    def __init__(self, moebot: MoeBot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_mower"

        self._attr_name = f"MoeBot Mower"

        self.__attr_icon = "mdi:robot-mower"
        # The Lawn Mower Entity is actually the Device for the MoeBot integration. Therefore, we can provide the
        # other supporting metadata about the Device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._moebot.id)},
            manufacturer="MoeBot",
            name=f"{self.name} ({self._moebot.id})",
            sw_version=self._moebot.tuya_version
        )

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return the state of the mower."""
        mb_state = self._moebot.state
        return _STATUS_TO_HA[mb_state]

    def start_mowing(self) -> None:
        self._moebot.start()

    def dock(self) -> None:
        self._moebot.dock()

    def pause(self) -> None:
        self._moebot.pause()
