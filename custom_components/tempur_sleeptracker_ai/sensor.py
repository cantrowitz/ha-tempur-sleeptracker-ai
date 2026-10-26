from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN, WIND_DOWN_MODES
from .entity import TempurPedicBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TempurPedicWindDownStatusSensor(data["coordinator"], entry.entry_id)
    ])

class TempurPedicWindDownStatusSensor(TempurPedicBaseEntity, SensorEntity):
    _attr_name = "Wind Down Status"
    _attr_icon = "mdi:bed-clock"

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_wind_down_status"

    @property
    def native_value(self) -> str:
        mode_id = self.coordinator.data.get("wind_down_mode", 0)
        return WIND_DOWN_MODES.get(mode_id, f"Unknown ({mode_id})")
