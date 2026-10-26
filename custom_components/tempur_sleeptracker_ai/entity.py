from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MANUFACTURER

class TempurPedicBaseEntity(CoordinatorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        snapshot = coordinator.data or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Tempur-Pedic Smart Base",
            manufacturer=MANUFACTURER,
            model=snapshot.get("model", "Ergo Smart Base"),
            sw_version=snapshot.get("firmware_version", "3.0.21"),
        )
