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
    """Select entity for active wind-down program.

    Program options are loaded dynamically from the coordinator snapshot
    (``wind_down_programs`` key populated by the API client when the cloud
    returns a program list). The hardcoded ``WIND_DOWN_PROGRAMS`` constant
    is used as a fallback when the API does not provide the list.
    """

    _attr_name = "Wind down program"
    _attr_icon = "mdi:bed-clock"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_wind_down_select"

    def _active_programs(self) -> dict:
        """Return the best available program dict.

        Prefers the dynamic list returned by the cloud (stored in coordinator
        data under ``wind_down_programs``). Falls back to the hardcoded
        ``WIND_DOWN_PROGRAMS`` constant if the API did not provide one.
        """
        data = self.coordinator.data or {}
        dynamic = data.get("wind_down_programs", {})
        return dynamic if dynamic else WIND_DOWN_PROGRAMS

    @property
    def options(self) -> list[str]:
        """Return the current list of selectable options."""
        return ["Off"] + list(self._active_programs().keys())

    @property
    def current_option(self) -> str:
        """Return the currently active wind-down option.

        Looks up the active ``mode_id`` from the snapshot in both the dynamic
        program list and the static ``WIND_DOWN_MODES`` map so the label always
        matches an available option.
        """
        data = self.coordinator.data or {}
        mode_id = data.get("wind_down_mode", 0)
        if mode_id == 0:
            return "Off"
        # Check dynamic programs first
        for name, prog in self._active_programs().items():
            if prog.get("mode_id") == mode_id:
                return name
        # Fallback to static mode name map
        return WIND_DOWN_MODES.get(mode_id, "Off")

    async def async_select_option(self, option: str) -> None:
        """Activate the chosen wind-down program or stop if 'Off'."""
        if option == "Off":
            await self._api.async_stop_wind_down()
        else:
            prog = self._active_programs().get(option)
            if prog:
                await self._api.async_start_wind_down(prog["command"])
        await self.coordinator.async_request_refresh()
