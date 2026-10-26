from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from .const import DOMAIN
from .entity import TempurPedicBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TempurPedicHeadCover(data["coordinator"], data["api"], entry.entry_id),
        TempurPedicFootCover(data["coordinator"], data["api"], entry.entry_id),
    ])

class TempurPedicHeadCover(TempurPedicBaseEntity, CoverEntity):
    _attr_name = "Head Elevation"
    _attr_supported_features = (
        CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
    )

    def __init__(self, coordinator, api_client, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._api = api_client
        self._attr_unique_id = f"{entry_id}_head_elevation"

    @property
    def current_cover_position(self) -> int:
        pulse = self.coordinator.data.get("head_pulse", 0)
        return min(100, max(0, int((pulse / 10000) * 100)))

class TempurPedicFootCover(TempurPedicBaseEntity, CoverEntity):
    _attr_name = "Foot Elevation"
    _attr_supported_features = (
        CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
    )

    def __init__(self, coordinator, api_client, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._api = api_client
        self._attr_unique_id = f"{entry_id}_foot_elevation"

    @property
    def current_cover_position(self) -> int:
        pulse = self.coordinator.data.get("foot_pulse", 0)
        return min(100, max(0, int((pulse / 10000) * 100)))
