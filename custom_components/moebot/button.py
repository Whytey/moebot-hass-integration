from homeassistant.components.button import ButtonEntity, ButtonDeviceClass

from . import BaseMoeBotEntity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    moebot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([UpdateButton(moebot)])


class UpdateButton(BaseMoeBotEntity, ButtonEntity):

    def __init__(self, moebot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_update"

        self._attr_device_class = ButtonDeviceClass.UPDATE
        self._attr_name = "Update"

    def press(self) -> None:
        self._moebot.poll()
