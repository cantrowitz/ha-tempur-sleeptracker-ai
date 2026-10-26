"""Light platform for Tempur-Pedic Sleeptracker-AI."""
import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PROCESSOR_SERIAL, DOMAIN
from .entity import TempurPedicBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic light platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    api = data.api if hasattr(data, "api") else data["api"]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([TempurPedicPanelLight(coordinator, api, entry)])


class TempurPedicPanelLight(TempurPedicBaseEntity, LightEntity):
    """Underbed panel lighting entity."""

    _attr_name = "Underbed light"
    _attr_icon = "mdi:lightbulb-night"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the light."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_underbed_light"

    @property
    def is_on(self) -> bool:
        """Return True if underbed light is on."""
        data = self.coordinator.data or {}
        return bool(data.get("panel_light") or data.get("safety_light"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the underbed light."""
        if not self.is_on:
            await self._api.async_toggle_light()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the underbed light."""
        if self.is_on:
            await self._api.async_toggle_light()
            await self.coordinator.async_request_refresh()
