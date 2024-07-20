"""Config flow for MoeBot integration."""
from __future__ import annotations

import logging
from functools import partial
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from pymoebot import MoeBot

from .const import DOMAIN, DEVICE_ID, IP_ADDRESS, LOCAL_KEY

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(DEVICE_ID): str,
        vol.Required(IP_ADDRESS): str,
        vol.Required(LOCAL_KEY): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    try:
        d = await hass.async_add_executor_job(partial(MoeBot,
                                                      device_id=data["device_id"],
                                                      device_ip=data["ip_address"],
                                                      local_key=data["local_key"]))
    except Exception as e:
        _LOGGER.error("Caught an exception when trying to create a MoeBot device.", e)
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": "MoeBot (%s)" % d.id, "id": d.id}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoeBot."""

    VERSION = 1

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

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry
        print("entry: {}".format(entry))

        if user_input is not None:
            errors = {}

            try:
                info = await validate_input(self.hass, user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:

                assert isinstance(entry, ConfigEntry)
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        DEVICE_ID: user_input[DEVICE_ID],
                        IP_ADDRESS: user_input[IP_ADDRESS],
                        LOCAL_KEY: user_input[LOCAL_KEY],
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(DEVICE_ID, default=entry.data.get(DEVICE_ID)): str,
                    vol.Required(IP_ADDRESS, default=entry.data.get(IP_ADDRESS)): str,
                    vol.Required(LOCAL_KEY, default=entry.data.get(LOCAL_KEY)): str,
                }
            ))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
