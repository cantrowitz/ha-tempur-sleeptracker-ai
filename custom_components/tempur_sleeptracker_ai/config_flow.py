"""Config flow for Tempur-Pedic Sleeptracker-AI integration."""
import logging
from typing import Any, Dict, List, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    TempurPedicApiClient,
    TempurPedicAuthError,
    TempurPedicConnectionError,
    TempurPedicError,
)
from .const import (
    CONF_BED_NAME,
    CONF_DEVICE_ID,
    CONF_FOOT_TICKS,
    CONF_HEAD_TICKS,
    CONF_MODEL,
    CONF_PROCESSOR_SERIAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class TempurPedicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tempur-Pedic Sleeptracker-AI."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._email: Optional[str] = None
        self._password: Optional[str] = None
        self._api: Optional[TempurPedicApiClient] = None
        self._devices: List[Dict[str, Any]] = []
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> config_entries.ConfigFlowResult:
        """Handle the initial user login step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip().lower()
            self._password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            self._api = TempurPedicApiClient(
                session=session,
                email=self._email,
                password=self._password,
            )

            try:
                await self._api.async_login()
                self._devices = await self._api.async_get_devices()
            except TempurPedicAuthError:
                errors["base"] = "invalid_auth"
            except TempurPedicConnectionError:
                errors["base"] = "cannot_connect"
            except TempurPedicError as err:
                _LOGGER.exception("Unexpected error during login: %s", err)
                errors["base"] = "unknown"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

            if not errors:
                if not self._devices:
                    errors["base"] = "no_devices"
                elif len(self._devices) == 1:
                    return await self._async_create_bed_entry(self._devices[0])
                else:
                    return await self.async_step_select_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        """Handle device selection when multiple beds are found."""
        errors: Dict[str, str] = {}
        device_options = {
            str(dev.get("processorSerialNumber", dev.get("deviceID"))): (
                f"{dev.get('name', 'Bed')} - "
                f"{dev.get('powerBase', {}).get('modelDescription', dev.get('modelID', 'Smart Base'))} "
                f"({dev.get('processorSerialNumber', 'Unknown')})"
            )
            for dev in self._devices
        }

        if user_input is not None:
            selected_serial = user_input["device"]
            for dev in self._devices:
                if str(dev.get("processorSerialNumber", dev.get("deviceID"))) == selected_serial:
                    return await self._async_create_bed_entry(dev)

        schema = vol.Schema(
            {
                vol.Required("device", default=list(device_options.keys())[0]): vol.In(device_options)
            }
        )

        return self.async_show_form(
            step_id="select_device",
            data_schema=schema,
            errors=errors,
        )

    async def _async_create_bed_entry(self, device: Dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Create entry for a discovered bed device."""
        serial = (
            device.get("processorSerialNumber")
            or device.get("macAddress")
            or str(device.get("deviceID", self._email))
        )
        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured()

        bed_name = device.get("name", "Tempur-Pedic Smart Base")
        power_base = device.get("powerBase", {}) or {}
        model_desc = power_base.get("modelDescription") or device.get("modelID", "Ergo Smart Base")

        return self.async_create_entry(
            title=f"{bed_name} ({model_desc})",
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_DEVICE_ID: device.get("deviceID") or device.get("sleeptrackerID"),
                CONF_PROCESSOR_SERIAL: serial,
                CONF_BED_NAME: bed_name,
                CONF_MODEL: model_desc,
                CONF_HEAD_TICKS: power_base.get("headAngleTicksPerDegree", 234.0),
                CONF_FOOT_TICKS: power_base.get("footAngleTicksPerDegree", 306.0),
                "device_info": device,
                "token": self._api.token if self._api else "",
                "token_expiration": self._api.token_expiration if self._api else 0,
            },
        )

    async def async_step_reauth(
        self, entry_data: Dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication when token is invalidated."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm reauth with new credentials."""
        errors: Dict[str, str] = {}
        existing_email = (
            self._reauth_entry.data.get(CONF_EMAIL, "") if self._reauth_entry else ""
        )

        if user_input is not None:
            email = user_input.get(CONF_EMAIL, existing_email).strip().lower()
            password = user_input[CONF_PASSWORD]
            session = async_get_clientsession(self.hass)
            api = TempurPedicApiClient(session=session, email=email, password=password)

            try:
                await api.async_login()
                if self._reauth_entry:
                    self.hass.config_entries.async_update_entry(
                        self._reauth_entry,
                        data={
                            **self._reauth_entry.data,
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                            "token": api.token,
                            "token_expiration": api.token_expiration,
                        },
                    )
                    await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
            except TempurPedicAuthError:
                errors["base"] = "invalid_auth"
            except TempurPedicConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL, default=existing_email): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )
