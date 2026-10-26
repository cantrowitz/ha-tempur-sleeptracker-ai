"""Button platform for Tempur-Pedic Sleeptracker-AI."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PROCESSOR_SERIAL, DOMAIN
from .entity import TempurPedicBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic button platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    api = data.api if hasattr(data, "api") else data["api"]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([
        TempurPedicFlatPresetButton(coordinator, api, entry),
        TempurPedicZeroGPresetButton(coordinator, api, entry),
        TempurPedicStopWindDownButton(coordinator, api, entry),
        TempurPedicRefreshStatusButton(coordinator, entry),
    ])


class TempurPedicFlatPresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to return entire bed to flat position."""

    _attr_name = "Flat preset"
    _attr_icon = "mdi:bed-empty"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_flat"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._api.async_preset_flat()
        await self.coordinator.async_request_refresh()


class TempurPedicZeroGPresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to position bed in Zero-G."""

    _attr_name = "Zero-G preset"
    _attr_icon = "mdi:human-handsdown"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_zero_g"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._api.async_preset_zero_g()
        await self.coordinator.async_request_refresh()


class TempurPedicStopWindDownButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to immediately cancel wind down."""

    _attr_name = "Stop wind down"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_stop_wind_down"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._api.async_stop_wind_down()
        await self.coordinator.async_request_refresh()


class TempurPedicRefreshStatusButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to force a telemetry refresh from the cloud."""

    _attr_name = "Refresh status"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_refresh_status"

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.async_request_refresh()
