"""Base entity class for Tempur-Pedic Sleeptracker-AI integration."""
from typing import Any, Dict
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_BED_NAME,
    CONF_MODEL,
    CONF_PROCESSOR_SERIAL,
    DOMAIN,
    MANUFACTURER,
)


class TempurPedicBaseEntity(CoordinatorEntity):
    """Base entity for Tempur-Pedic Sleeptracker-AI devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._entry = entry
        device_data = entry.data.get("device_info", {}) or {}
        power_base = device_data.get("powerBase", {}) or {}

        serial = entry.data.get(CONF_PROCESSOR_SERIAL) or device_data.get("processorSerialNumber", entry.entry_id)
        bed_name = entry.data.get(CONF_BED_NAME) or device_data.get("name", "Tempur-Pedic Smart Base")
        model = entry.data.get(CONF_MODEL) or power_base.get("modelDescription") or "Smart Base"
        firmware = (
            device_data.get("processorVersionFirmware")
            or str(power_base.get("powerbaseControllerFirmwareID", "3.0.21"))
        )

        connections = set()
        mac = device_data.get("macAddress")
        if mac:
            connections.add((CONNECTION_NETWORK_MAC, mac))

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial))},
            connections=connections,
            name=bed_name,
            manufacturer=MANUFACTURER,
            model=model,
            sw_version=firmware,
            serial_number=str(serial),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get("online", True)
        )
