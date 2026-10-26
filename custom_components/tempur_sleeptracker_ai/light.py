from homeassistant.components.light import ColorMode, LightEntity
from .const import DOMAIN
from .entity import TempurPedicBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TempurPedicPanelLight(data["coordinator"], data["api"], entry.entry_id)
    ])

class TempurPedicPanelLight(TempurPedicBaseEntity, LightEntity):
    _attr_name = "Underbed Lighting"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, api_client, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._api = api_client
        self._attr_unique_id = f"{entry_id}_underbed_light"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("panel_light", False)
