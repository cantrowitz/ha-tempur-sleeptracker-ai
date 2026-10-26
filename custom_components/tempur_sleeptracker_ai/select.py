"""Select platform for Tempur-Pedic Sleeptracker-AI."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PROCESSOR_SERIAL,
    DOMAIN,
    WIND_DOWN_MODES,
    WIND_DOWN_PROGRAMS,
)
from .entity import TempurPedicBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic select platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    api = data.api if hasattr(data, "api") else data["api"]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([TempurPedicWindDownSelect(coordinator, api, entry)])


class TempurPedicWindDownSelect(TempurPedicBaseEntity, SelectEntity):
    """Select entity for active wind down program."""

    _attr_name = "Wind down program"
    _attr_icon = "mdi:bed-clock"
    _attr_options = ["Off"] + list(WIND_DOWN_PROGRAMS.keys())

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_wind_down_select"

    @property
    def current_option(self) -> str:
        """Return currently selected wind down option."""
        data = self.coordinator.data or {}
        mode_id = data.get("wind_down_mode", 0)
        return WIND_DOWN_MODES.get(mode_id, "Off")

    async def async_select_option(self, option: str) -> None:
        """Change the selected wind down option."""
        if option == "Off":
            await self._api.async_stop_wind_down()
        else:
            prog = WIND_DOWN_PROGRAMS.get(option)
            if prog:
                await self._api.async_start_wind_down(prog["command"])
        await self.coordinator.async_request_refresh()
