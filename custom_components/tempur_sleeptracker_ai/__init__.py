"""The Tempur-Pedic Sleeptracker-AI integration."""
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TempurPedicApiClient,
    TempurPedicAuthError,
    TempurPedicConnectionError,
    TempurPedicError,
)
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


@dataclass
class TempurPedicData:
    """Runtime data structure for Tempur-Pedic config entry."""

    api: TempurPedicApiClient
    coordinator: DataUpdateCoordinator
    device_info: Dict[str, Any]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tempur-Pedic Sleeptracker-AI from a config entry."""
    session = async_get_clientsession(hass)

    api = TempurPedicApiClient(
        session=session,
        email=entry.data.get(CONF_EMAIL),
        password=entry.data.get(CONF_PASSWORD),
        token=entry.data.get("token"),
        token_expiration=entry.data.get("token_expiration"),
    )

    async def async_update_data() -> Dict[str, Any]:
        """Fetch status data from Sleeptracker API."""
        try:
            status = await api.async_get_bed_status()
            env_sleep = await api.async_get_environmental_and_sleep_data()
            return {**status, "env": env_sleep}
        except TempurPedicAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except TempurPedicConnectionError as err:
            raise UpdateFailed(f"Connection error to Sleeptracker cloud: {err}") from err
        except TempurPedicError as err:
            raise UpdateFailed(f"Error communicating with Sleeptracker API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    runtime_data = TempurPedicData(
        api=api,
        coordinator=coordinator,
        device_info=entry.data.get("device_info", {}),
    )

    # Support modern HA runtime_data
    entry.runtime_data = runtime_data

    # Backwards compatibility with hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "runtime_data": runtime_data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
