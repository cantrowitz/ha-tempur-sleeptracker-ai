from homeassistant.components.select import SelectEntity
from .const import DOMAIN, WIND_DOWN_PROGRAMS, WIND_DOWN_MODES
from .entity import TempurPedicBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TempurPedicWindDownSelect(data["coordinator"], data["api"], entry.entry_id)
    ])

class TempurPedicWindDownSelect(TempurPedicBaseEntity, SelectEntity):
    _attr_name = "Wind Down Program"
    _attr_options = ["Off"] + list(WIND_DOWN_PROGRAMS.keys())

    def __init__(self, coordinator, api_client, entry_id: str):
        super().__init__(coordinator, entry_id)
        self._api = api_client
        self._attr_unique_id = f"{entry_id}_wind_down_select"

    @property
    def current_option(self) -> str:
        mode_id = self.coordinator.data.get("wind_down_mode", 0)
        return WIND_DOWN_MODES.get(mode_id, "Off")

    async def async_select_option(self, option: str) -> None:
        if option == "Off":
            await self._api.async_stop_wind_down()
        else:
            prog = WIND_DOWN_PROGRAMS.get(option)
            if prog:
                await self._api.async_start_wind_down(prog["command"])
        await self.coordinator.async_request_refresh()
