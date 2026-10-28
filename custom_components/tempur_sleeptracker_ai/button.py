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
        # No elevation buttons at all: head, foot and lumbar are all
        # controlled from their cover entities (up / stop / down arrows).
        # Head/foot nudge buttons were removed 2026-10-26 and the lumbar
        # pair on 2026-10-27, both as duplicates of the covers.
        # Presets
        TempurPedicFlatPresetButton(coordinator, api, entry),
        TempurPedicZeroGPresetButton(coordinator, api, entry),
        TempurPedicTVPresetButton(coordinator, api, entry),
        TempurPedicQuietModePresetButton(coordinator, api, entry),
        TempurPedicFavorite1PresetButton(coordinator, api, entry),
        TempurPedicFavorite2PresetButton(coordinator, api, entry),
        # Massage (Wave Form)
        TempurPedicMassageHeadStrengthButton(coordinator, api, entry),
        TempurPedicMassageFootStrengthButton(coordinator, api, entry),
        TempurPedicMassageFreq28Button(coordinator, api, entry),
        TempurPedicMassageFreq40Button(coordinator, api, entry),
        TempurPedicMassageCyclePatternButton(coordinator, api, entry),
        # Wind down
        TempurPedicStopWindDownButton(coordinator, api, entry),
        # Diagnostic
        TempurPedicRefreshStatusButton(coordinator, entry),
    ])


# ---------------------------------------------------------------------------
# Preset buttons
# ---------------------------------------------------------------------------

class TempurPedicFlatPresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to return entire bed to flat position."""

    _attr_name = "Flat preset"
    _attr_icon = "mdi:bed-empty"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_flat"

    async def async_press(self) -> None:
        await self._api.async_preset_flat()
        await self.coordinator.async_request_refresh()


class TempurPedicZeroGPresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to position bed in Zero-G."""

    _attr_name = "Zero-G preset"
    _attr_icon = "mdi:human-handsdown"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_zero_g"

    async def async_press(self) -> None:
        await self._api.async_preset_zero_g()
        await self.coordinator.async_request_refresh()


class TempurPedicTVPresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to position bed in TV-in-Bed preset (command 3)."""

    _attr_name = "TV in bed preset"
    _attr_icon = "mdi:television"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_tv"

    async def async_press(self) -> None:
        await self._api.async_preset_tv()
        await self.coordinator.async_request_refresh()


class TempurPedicQuietModePresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to position bed in QuietMode (anti-snore) preset (command 4)."""

    _attr_name = "QuietMode preset"
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_quiet_mode"

    async def async_press(self) -> None:
        await self._api.async_preset_quiet_mode()
        await self.coordinator.async_request_refresh()


class TempurPedicFavorite1PresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to recall Favorite 1 (user-saved) preset (command 6)."""

    _attr_name = "Favorite 1 preset"
    _attr_icon = "mdi:star"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_favorite_1"

    async def async_press(self) -> None:
        await self._api.async_preset_favorite_1()
        await self.coordinator.async_request_refresh()


class TempurPedicFavorite2PresetButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to recall Favorite 2 (user-saved) preset (command 9)."""

    _attr_name = "Favorite 2 preset"
    _attr_icon = "mdi:star-outline"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_preset_favorite_2"

    async def async_press(self) -> None:
        await self._api.async_preset_favorite_2()
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Massage (Wave Form) buttons
# ---------------------------------------------------------------------------

class TempurPedicMassageHeadStrengthButton(TempurPedicBaseEntity, ButtonEntity):
    """Step head-zone massage strength up one level (command 210)."""

    _attr_name = "Head massage strength"
    _attr_icon = "mdi:arrow-up-bold-circle-outline"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_head_strength"

    async def async_press(self) -> None:
        await self._api.async_massage_head_strength_step()
        await self.coordinator.async_request_refresh()


class TempurPedicMassageFootStrengthButton(TempurPedicBaseEntity, ButtonEntity):
    """Step foot-zone massage strength up one level (command 211)."""

    _attr_name = "Foot massage strength"
    _attr_icon = "mdi:arrow-up-bold-circle-outline"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_foot_strength"

    async def async_press(self) -> None:
        await self._api.async_massage_foot_strength_step()
        await self.coordinator.async_request_refresh()


class TempurPedicMassageFreq28Button(TempurPedicBaseEntity, ButtonEntity):
    """Start/switch massage to Wave Form 28 Hz (command 212)."""

    _attr_name = "Massage 28 Hz"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_freq_28hz"

    async def async_press(self) -> None:
        await self._api.async_massage_freq_28hz()
        await self.coordinator.async_request_refresh()


class TempurPedicMassageFreq40Button(TempurPedicBaseEntity, ButtonEntity):
    """Start/switch massage to Wave Form 40 Hz (command 213)."""

    _attr_name = "Massage 40 Hz"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_freq_40hz"

    async def async_press(self) -> None:
        await self._api.async_massage_freq_40hz()
        await self.coordinator.async_request_refresh()


class TempurPedicMassageCyclePatternButton(TempurPedicBaseEntity, ButtonEntity):
    """Cycle the Wave Form massage pattern (command 226)."""

    _attr_name = "Massage pattern"
    _attr_icon = "mdi:waveform"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_cycle_pattern"

    async def async_press(self) -> None:
        await self._api.async_massage_cycle_pattern()
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Wind down / diagnostic
# ---------------------------------------------------------------------------

class TempurPedicStopWindDownButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to immediately cancel wind down."""

    _attr_name = "Stop wind down"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_stop_wind_down"

    async def async_press(self) -> None:
        await self._api.async_stop_wind_down()
        await self.coordinator.async_request_refresh()


class TempurPedicRefreshStatusButton(TempurPedicBaseEntity, ButtonEntity):
    """Button to force a telemetry refresh from the cloud."""

    _attr_name = "Refresh status"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_refresh_status"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


