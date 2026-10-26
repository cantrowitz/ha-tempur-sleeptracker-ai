"""Binary sensor platform for Tempur-Pedic Sleeptracker-AI."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the Tempur-Pedic binary sensor platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([
        TempurPedicSleepRecordingBinarySensor(coordinator, entry),
        TempurPedicOnlineBinarySensor(coordinator, entry),
        TempurPedicHeadMassageBinarySensor(coordinator, entry),
        TempurPedicFootMassageBinarySensor(coordinator, entry),
        TempurPedicBusyBinarySensor(coordinator, entry),
    ])


class TempurPedicSleepRecordingBinarySensor(TempurPedicBaseEntity, BinarySensorEntity):
    """Binary sensor indicating if a sleep recording is actively ongoing."""

    _attr_name = "Sleep recording"
    _attr_icon = "mdi:bed"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_sleep_recording"

    @property
    def is_on(self) -> bool:
        """Return True if sleep recording is active."""
        data = self.coordinator.data or {}
        return bool(data.get("env", {}).get("sleep_recording_active", False))


class TempurPedicOnlineBinarySensor(TempurPedicBaseEntity, BinarySensorEntity):
    """Binary sensor indicating cloud connectivity."""

    _attr_name = "Cloud connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_cloud_connection"

    @property
    def is_on(self) -> bool:
        """Return True if base is connected to cloud."""
        data = self.coordinator.data or {}
        return bool(data.get("online", True))


class TempurPedicHeadMassageBinarySensor(TempurPedicBaseEntity, BinarySensorEntity):
    """Binary sensor for active head massage."""

    _attr_name = "Head massage active"
    _attr_icon = "mdi:vibrate"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_head_massage_active"

    @property
    def is_on(self) -> bool:
        """Return True if head massage is running."""
        data = self.coordinator.data or {}
        return bool(data.get("head_massage_active", False))


class TempurPedicFootMassageBinarySensor(TempurPedicBaseEntity, BinarySensorEntity):
    """Binary sensor for active foot massage."""

    _attr_name = "Foot massage active"
    _attr_icon = "mdi:vibrate"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_foot_massage_active"

    @property
    def is_on(self) -> bool:
        """Return True if foot massage is running."""
        data = self.coordinator.data or {}
        return bool(data.get("foot_massage_active", False))


class TempurPedicBusyBinarySensor(TempurPedicBaseEntity, BinarySensorEntity):
    """Binary sensor indicating actuators are moving."""

    _attr_name = "Bed moving"
    _attr_device_class = BinarySensorDeviceClass.MOVING

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_bed_moving"

    @property
    def is_on(self) -> bool:
        """Return True if base motors are moving."""
        data = self.coordinator.data or {}
        return bool(data.get("busy_with_command", False))
