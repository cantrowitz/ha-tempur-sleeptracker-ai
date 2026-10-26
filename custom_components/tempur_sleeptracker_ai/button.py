from homeassistant.components.button import ButtonEntity
from .const import DOMAIN
from .entity import TempurPedicBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TempurPedicStopWindDownButton(data["coordinator"], data["api"], entry.entry_id)
    ])

class TempurPedicStopWindDownButton(TempurPedicBaseEntity, ButtonEntity):
    _attr_name = "Stop Wind Down"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator, api_client, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._api = api_client
        self._attr_unique_id = f"{entry_id}_stop_wind_down"

    async def async_press(self) -> None:
        await self._api.async_stop_wind_down()
        await self.coordinator.async_request_refresh()
