from __future__ import annotations

import asyncio
import homeassistant.helpers.config_validation as cv
import ipaddress
import logging
import pymoebot
import voluptuous as vol
from functools import partial
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector
from pymoebot import MoeBot
from typing import Any

from .const import DEVICE_ID, DOMAIN, IP_ADDRESS, LOCAL_KEY, TUYA_VERSION

_LOGGER = logging.getLogger(__name__)

TUYA_VERSION_OPTIONS = {
    "auto": "Auto",
    "3.3": "3.3",
    "3.4": "3.4",
    "3.5": "3.5",
}

TUYA_DATA_CENTER_OPTIONS = {
    "cn": "China",
    "us": "Western US",
    "us-e": "Eastern US",
    "eu": "Central Europe",
    "eu-w": "Western Europe",
    "in": "India",
    "sg": "Singapore",
}


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class NotMoeBot(HomeAssistantError):
    """Error to indicate the device is not a MoeBot."""


class MalformedIP(HomeAssistantError):
    """Error to indicate the provided IP address is malformed."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    # Validate the provided IP address is 'Auto' or a valid IPv4 address
    ip_address = data.get(IP_ADDRESS).strip()
    if ip_address != "Auto":
        try:
            ipaddress.IPv4Address(ip_address.strip())
        except ValueError:
            raise MalformedIP("Invalid IP address")

    # Map the version to None if 'auto' is selected
    tuya_version = data.get(TUYA_VERSION)
    if tuya_version == "auto":
        tuya_version = None

    device_id = data.get(DEVICE_ID)
    local_key = data.get(LOCAL_KEY)

    """Validate the user input allows us to connect."""
    try:
        # Create a MoeBot instance
        _LOGGER.debug(
            f"Creating MoeBot instance with IP: {ip_address}, Device ID: {device_id}, Local Key: {local_key}, Tuya Version: {tuya_version}")
        d = await hass.async_add_executor_job(
            partial(
                MoeBot,
                device_id=device_id,
                device_ip=ip_address,
                local_key=local_key,
                tuya_version=tuya_version
            )
        )
    except Exception as e:
        _LOGGER.error("Caught an exception when trying to create a MoeBot device: %s", e)
        raise CannotConnect("Cannot connect to device") from e

    # Poll the device to ensure it looks like a MoeBot
    await hass.async_add_executor_job(d.poll)

    # If we haven't been able to determine the battery level, this isn't a MoeBot device.
    if d.battery is None:
        raise NotMoeBot("Device does not appear to be a MoeBot")

    return {"title": f"MoeBot ({d.id})", "id": d.id}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoeBot."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize class properties."""
        self.task_one: asyncio.Task | None = None
        self.task_two: asyncio.Task | None = None
        self._discovered_devices: list = []  # Data pipeline storage

        # Method 1: Persistent origin tracking variable
        self._previous_step: str | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Initial Menu Selection Step."""
        if user_input is not None:
            selection = user_input.get("menu_options")

            if selection == "cloud":
                self._previous_step = "user"
                return await self.async_step_cloud()

            if selection == "lookup_local_devices":
                self._previous_step = "user"
                return await self.async_step_lookup_local_devices()

            if selection == "device_details":
                self._previous_step = "user"
                return await self.async_step_device_details()

        return self.async_show_menu(
            step_id="user",
            menu_options=["cloud", "lookup_local_devices", "device_details"],
        )

    async def async_step_cloud(self, user_input=None) -> FlowResult:
        """Tuya Cloud Credentials Step."""
        if user_input is not None:
            self._cloud_credentials = user_input
            self._previous_step = "cloud"
            return await self.async_step_lookup_cloud_devices()

        dropdown_options = [
            {"value": key, "label": f"{value} ({key})"}
            for key, value in TUYA_DATA_CENTER_OPTIONS.items()
        ]

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required("region"): selector(
                        {
                            "select": {
                                "options": dropdown_options,
                                "mode": "dropdown",
                                "multiple": False,
                            }
                        }
                    ),
                    vol.Required("api_key"): cv.string,
                    vol.Required("api_secret"): cv.string,
                }
            )
        )

    async def async_step_lookup_cloud_devices(self, user_input=None) -> FlowResult:
        """Background Progress Step managing the Tuya Cloud device discovery query."""
        if not self.task_two:
            self.async_update_progress(25)

            async def _cloud_fetch_devices():
                _LOGGER.debug(f"Cloud credentials: {self._cloud_credentials}")
                region = self._cloud_credentials.get("region")
                api_key = self._cloud_credentials.get("api_key")
                api_secret = self._cloud_credentials.get("api_secret")

                # Execute the second blocking call using the object from Stage 1
                return await self.hass.async_add_executor_job(pymoebot.scan_cloud_devices, region, api_key, api_secret)

            self.task_two = self.hass.async_create_task(_cloud_fetch_devices())

            return self.async_show_progress(
                step_id="lookup_cloud_devices",
                progress_action="cloud_fetch",
                progress_task=self.task_two,
            )

        # Keep showing spinner if Stage 2 is still running
        if self.task_two and not self.task_two.done():
            return self.async_show_progress(
                step_id="lookup_cloud_devices",
                progress_action="cloud_fetch",
                progress_task=self.task_two,
            )

        # Capture Stage 2 results
        try:
            cloud_devices = self.task_two.result() or []
            _LOGGER.debug("Cloud devices: %s", cloud_devices)

            configured_unique_ids = {
                entry.unique_id
                for entry in self._async_current_entries()
                if entry.unique_id is not None
            }
            self._discovered_devices = [
                {
                    "name": device.get("name") or f"Unnamed Device",
                    "id": device.get("id"),
                    "local_key": device.get("local_key"),
                    "ip": "Auto",
                    "version": "Unknown Version",
                    "mac": device.get("mac") or "Unknown MAC",
                }
                for device in cloud_devices["result"]
                if device.get("online") and device.get("id") not in configured_unique_ids
            ]
        except Exception as err:
            _LOGGER.error("Failed to fetch cloud account devices: %s", err)
            self._discovered_devices = []
        finally:
            self.task_two = None  # Clear task_two
            if hasattr(self, "_cloud_obj"):
                delattr(self, "_cloud_obj")  # Clean up internal object reference

        # Exit progress state safely
        self._previous_step = "lookup_cloud_devices"
        return self.async_show_progress_done(next_step_id="device_select")

    async def async_step_lookup_local_devices(self, user_input=None) -> FlowResult:
        """Background Progress Step managing the local TinyTuya network scan."""
        import tinytuya  # Inline import helper context

        if not self.task_one:
            async def _scan():
                return await self.hass.async_add_executor_job(pymoebot.scan_local_devices)

            self.task_one = self.hass.async_create_task(_scan())

            return self.async_show_progress(
                step_id="lookup_local_devices",
                progress_action="local_scan",
                progress_task=self.task_one,
            )

        if not self.task_one.done():
            return self.async_show_progress(
                step_id="lookup_local_devices",
                progress_action="local_scan",
                progress_task=self.task_one,
            )

        try:
            local_devices = self.task_one.result() or {}
            configured_unique_ids = {
                entry.unique_id
                for entry in self._async_current_entries()
                if entry.unique_id is not None
            }

            self._discovered_devices = [
                {
                    "name": device.get("name") or f"Unnamed Device",
                    "id": device["id"],
                    "ip": device["ip"],
                    "version": device["version"],
                    "mac": device.get("mac") or "Unknown MAC",
                }
                for device in local_devices.values()
                if device["id"] not in configured_unique_ids
            ]
        except Exception as err:
            _LOGGER.error("Failed to run local tinytuya network scan: %s", err)
            self._discovered_devices = []
        finally:
            self.task_one = None

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        self._previous_step = "lookup_local_devices"
        return self.async_show_progress_done(next_step_id="device_select")

    async def async_step_device_select(self, user_input=None) -> FlowResult:
        """Dropdown Selection Step for Discovered Devices."""
        if user_input is not None:
            self._previous_step = "device_select"
            return await self.async_step_device_details(user_input)

        dropdown_options = [
            {
                "value": device["id"],
                "label": f"{device['ip']} — {device['id']} ({device['version']})"
            }
            for device in self._discovered_devices
        ]

        return self.async_show_form(
            step_id="device_select",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_device"): selector(
                        {
                            "select": {
                                "options": dropdown_options,
                                "mode": "dropdown",
                                "multiple": False,
                            }
                        }
                    )
                }
            )
        )

    async def async_step_device_details(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        initial_device_id = ""
        suggested_ip = "192.168.0."
        suggested_local_key = ""
        suggested_version = "auto"

        errors = {}

        # Use history tracking to extract variables from the automated branches
        if self._previous_step == "device_select" and user_input is not None:
            if "selected_device" in user_input:
                initial_device_id = user_input["selected_device"]

                selected_device_data = next(
                    (d for d in self._discovered_devices if d["id"] == initial_device_id),
                    None
                )

                if selected_device_data:
                    suggested_ip = selected_device_data.get("ip", suggested_ip)
                    suggested_local_key = selected_device_data.get("local_key", "")
                    suggested_version = selected_device_data.get("version", "auto")
                    if suggested_version == "":
                        suggested_version = "auto"

                # Clear user_input reference so the form displays with the prefilled values
                user_input = None

        # Are we ready to create the entry?
        if self._previous_step == "device_details" and user_input is not None:
            # Validate our inputs to check they are all valid
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(info["id"])
                self._abort_if_unique_id_configured()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except NotMoeBot:
                errors["base"] = "not_a_moebot"
            except MalformedIP:
                errors[IP_ADDRESS] = "invalid_ip"
            except Exception:
                _LOGGER.exception("Unexpected exception during configuration")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(DEVICE_ID, default=initial_device_id): cv.string,
                vol.Optional(
                    IP_ADDRESS,
                    description={"suggested_value": suggested_ip}
                ): cv.string,
                vol.Required(
                    LOCAL_KEY,
                    description={"suggested_value": suggested_local_key}
                ): cv.string,
                vol.Required(
                    TUYA_VERSION,
                    default=suggested_version
                ): vol.In(TUYA_VERSION_OPTIONS),
            }
        )

        self._previous_step = "device_details"
        return self.async_show_form(
            step_id="device_details",
            data_schema=data_schema,
            errors=errors,
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
                schema_data = {**entry.data, **user_input}
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except NotMoeBot:
                errors["base"] = "not_a_moebot"
            except MalformedIP:
                errors[IP_ADDRESS] = "invalid_ip"
            except Exception:
                _LOGGER.exception("Unexpected exception during configuration")
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
                    vol.Optional(IP_ADDRESS, default=entry.data.get(IP_ADDRESS)): cv.string,
                    vol.Required(LOCAL_KEY, default=entry.data.get(LOCAL_KEY)): cv.string,
                    vol.Required(
                        TUYA_VERSION,
                        default=entry.data.get(TUYA_VERSION, "auto")
                    ): vol.In(TUYA_VERSION_OPTIONS),
                }
            ),
            errors=errors,
        )
