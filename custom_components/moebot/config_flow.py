from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import ipaddress
import logging
import voluptuous as vol
from functools import partial
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from pymoebot import MoeBot
from typing import Any

from .const import DOMAIN, DEVICE_ID, IP_ADDRESS, LOCAL_KEY, TUYA_VERSION

_LOGGER = logging.getLogger(__name__)

TUYA_VERSION_OPTIONS = {
    "auto": "Auto",
    "3.3": "3.3",
    "3.4": "3.4",
    "3.5": "3.5",
}

# cv.string is explicitly supported by Home Assistant's frontend serializer
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(DEVICE_ID): cv.string,
        vol.Required(IP_ADDRESS): cv.string,
        vol.Required(LOCAL_KEY): cv.string,
        vol.Required(TUYA_VERSION, default="auto"): vol.In(TUYA_VERSION_OPTIONS),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    try:
        d = await hass.async_add_executor_job(
            partial(
                MoeBot,
                device_id=data[DEVICE_ID],
                device_ip=data[IP_ADDRESS],
                local_key=data[LOCAL_KEY],
            )
        )
    except Exception as e:
        _LOGGER.error("Caught an exception when trying to create a MoeBot device: %s", e)
        raise CannotConnect from e

    return {"title": f"MoeBot ({d.id})", "id": d.id}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoeBot."""

    VERSION = 2

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            ipaddress.IPv4Address(user_input[IP_ADDRESS].strip())
        except ValueError:
            errors[IP_ADDRESS] = "invalid_ip"

        if not errors:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(info["id"])
                self._abort_if_unique_id_configured()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of an existing MoeBot entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry

        errors = {}

        if user_input is not None:
            try:
                ipaddress.IPv4Address(user_input[IP_ADDRESS].strip())
            except ValueError:
                errors[IP_ADDRESS] = "invalid_ip"

            if not errors:
                try:
                    schema_data = {**entry.data, **user_input}
                    await validate_input(self.hass, schema_data)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data=schema_data
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(DEVICE_ID, default=entry.data.get(DEVICE_ID)): cv.string,
                    vol.Required(IP_ADDRESS, default=entry.data.get(IP_ADDRESS)): cv.string,
                    vol.Required(LOCAL_KEY, default=entry.data.get(LOCAL_KEY)): cv.string,
                    vol.Required(
                        TUYA_VERSION,
                        default=entry.data.get(TUYA_VERSION, "auto")
                    ): vol.In(TUYA_VERSION_OPTIONS),
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
