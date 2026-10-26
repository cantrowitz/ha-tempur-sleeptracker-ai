"""Sensor platform for Tempur-Pedic Sleeptracker-AI."""
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FOOT_TICKS,
    CONF_HEAD_TICKS,
    CONF_PROCESSOR_SERIAL,
    DOMAIN,
    WIND_DOWN_MODES,
)
from .entity import TempurPedicBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic sensor platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([
        # Bed Articulation & Status
        TempurPedicHeadAngleSensor(coordinator, entry),
        TempurPedicFootAngleSensor(coordinator, entry),
        TempurPedicWindDownStatusSensor(coordinator, entry),
        TempurPedicMassageFrequencySensor(coordinator, entry),
        TempurPedicMassageTimerSensor(coordinator, entry),
        TempurPedicHeadPulseSensor(coordinator, entry),
        TempurPedicFootPulseSensor(coordinator, entry),

        # Environmental Sensors
        TempurPedicTemperatureSensor(coordinator, entry),
        TempurPedicHumiditySensor(coordinator, entry),
        TempurPedicCo2Sensor(coordinator, entry),
        TempurPedicVocSensor(coordinator, entry),
        TempurPedicAqiSensor(coordinator, entry),

        # Sleep & Biometric Telemetry
        TempurPedicSleepScoreSensor(coordinator, entry),
        TempurPedicRestingHeartRateSensor(coordinator, entry),
        TempurPedicAvgHeartRateSensor(coordinator, entry),
        TempurPedicRestingRespirationSensor(coordinator, entry),
        TempurPedicAvgRespirationSensor(coordinator, entry),
        TempurPedicTotalSleepSensor(coordinator, entry),
        TempurPedicDeepSleepSensor(coordinator, entry),
        TempurPedicRemSleepSensor(coordinator, entry),
        TempurPedicSnoreDurationSensor(coordinator, entry),
        TempurPedicSleepEfficiencySensor(coordinator, entry),
    ])


# -------------------------------------------------------------
# Bed Articulation & Operational Sensors
# -------------------------------------------------------------

class TempurPedicHeadAngleSensor(TempurPedicBaseEntity, SensorEntity):
    """Sensor reporting head elevation in degrees."""

    _attr_name = "Head angle"
    _attr_icon = "mdi:angle-acute"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_head_angle"
        self._ticks = entry.data.get(CONF_HEAD_TICKS, 234.0)

    @property
    def native_value(self) -> float:
        """Return head angle in degrees."""
        data = self.coordinator.data or {}
        pulse = data.get("head_pulse", 0)
        return round(pulse / self._ticks, 1) if self._ticks > 0 else 0.0


class TempurPedicFootAngleSensor(TempurPedicBaseEntity, SensorEntity):
    """Sensor reporting foot elevation in degrees."""

    _attr_name = "Foot angle"
    _attr_icon = "mdi:angle-acute"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_foot_angle"
        self._ticks = entry.data.get(CONF_FOOT_TICKS, 306.0)

    @property
    def native_value(self) -> float:
        """Return foot angle in degrees."""
        data = self.coordinator.data or {}
        pulse = data.get("foot_pulse", 0)
        return round(pulse / self._ticks, 1) if self._ticks > 0 else 0.0


class TempurPedicWindDownStatusSensor(TempurPedicBaseEntity, SensorEntity):
    """Sensor reporting active wind down mode."""

    _attr_name = "Wind down status"
    _attr_icon = "mdi:bed-clock"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_wind_down_status"

    @property
    def native_value(self) -> str:
        """Return human-readable wind down mode."""
        data = self.coordinator.data or {}
        mode_id = data.get("wind_down_mode", 0)
        return WIND_DOWN_MODES.get(mode_id, f"Unknown ({mode_id})")


class TempurPedicMassageFrequencySensor(TempurPedicBaseEntity, SensorEntity):
    """Sensor reporting massage vibration frequency in Hz."""

    _attr_name = "Massage frequency"
    _attr_icon = "mdi:vibrate"
    _attr_native_unit_of_measurement = "Hz"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_frequency"

    @property
    def native_value(self) -> int:
        """Return vibration frequency in Hz."""
        data = self.coordinator.data or {}
        return data.get("massage_frequency_hz", 0)


class TempurPedicMassageTimerSensor(TempurPedicBaseEntity, SensorEntity):
    """Sensor reporting remaining massage timer in minutes."""

    _attr_name = "Massage timer"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_massage_timer"

    @property
    def native_value(self) -> int:
        """Return remaining massage timer in minutes."""
        data = self.coordinator.data or {}
        return data.get("massage_timer_mins", 0)


class TempurPedicHeadPulseSensor(TempurPedicBaseEntity, SensorEntity):
    """Diagnostic sensor reporting raw head motor pulse count."""

    _attr_name = "Head motor pulse"
    _attr_icon = "mdi:counter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_head_motor_pulse"

    @property
    def native_value(self) -> int:
        """Return raw pulse count."""
        data = self.coordinator.data or {}
        return data.get("head_pulse", 0)


class TempurPedicFootPulseSensor(TempurPedicBaseEntity, SensorEntity):
    """Diagnostic sensor reporting raw foot motor pulse count."""

    _attr_name = "Foot motor pulse"
    _attr_icon = "mdi:counter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_foot_motor_pulse"

    @property
    def native_value(self) -> int:
        """Return raw pulse count."""
        data = self.coordinator.data or {}
        return data.get("foot_pulse", 0)


# -------------------------------------------------------------
# Environmental Sensors
# -------------------------------------------------------------

class TempurPedicTemperatureSensor(TempurPedicBaseEntity, SensorEntity):
    """Room temperature sensor from Sleeptracker base."""

    _attr_name = "Room temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_temperature"

    @property
    def native_value(self) -> Optional[float]:
        """Return current temperature in °C."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("temperature_celsius")


class TempurPedicHumiditySensor(TempurPedicBaseEntity, SensorEntity):
    """Room humidity sensor from Sleeptracker base."""

    _attr_name = "Room humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_humidity"

    @property
    def native_value(self) -> Optional[float]:
        """Return current humidity percentage."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("humidity_percentage")


class TempurPedicCo2Sensor(TempurPedicBaseEntity, SensorEntity):
    """Room CO2 sensor from Sleeptracker base."""

    _attr_name = "Room CO2"
    _attr_device_class = SensorDeviceClass.CO2
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_co2"

    @property
    def native_value(self) -> Optional[float]:
        """Return current CO2 in ppm."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("co2_ppm")


class TempurPedicVocSensor(TempurPedicBaseEntity, SensorEntity):
    """Room VOC sensor from Sleeptracker base."""

    _attr_name = "Room VOC"
    _attr_device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_BILLION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_voc"

    @property
    def native_value(self) -> Optional[float]:
        """Return current VOC in ppb."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("voc_ppb")


class TempurPedicAqiSensor(TempurPedicBaseEntity, SensorEntity):
    """Room Air Quality Index sensor."""

    _attr_name = "Room air quality index"
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_aqi"

    @property
    def native_value(self) -> Optional[float]:
        """Return current IAQ value."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("iaq")


# -------------------------------------------------------------
# Sleep & Biometric Telemetry Sensors
# -------------------------------------------------------------

class TempurPedicSleepScoreSensor(TempurPedicBaseEntity, SensorEntity):
    """Sleep quality score sensor."""

    _attr_name = "Sleep score"
    _attr_icon = "mdi:star-face"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_sleep_score"

    @property
    def native_value(self) -> Optional[int]:
        """Return sleep score."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("sleep_score")


class TempurPedicRestingHeartRateSensor(TempurPedicBaseEntity, SensorEntity):
    """Resting heart rate sensor."""

    _attr_name = "Resting heart rate"
    _attr_icon = "mdi:heart-pulse"
    _attr_native_unit_of_measurement = "bpm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_resting_heart_rate"

    @property
    def native_value(self) -> Optional[int]:
        """Return resting heart rate."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("hr_resting")


class TempurPedicAvgHeartRateSensor(TempurPedicBaseEntity, SensorEntity):
    """Average sleep heart rate sensor."""

    _attr_name = "Average heart rate"
    _attr_icon = "mdi:heart"
    _attr_native_unit_of_measurement = "bpm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_avg_heart_rate"

    @property
    def native_value(self) -> Optional[int]:
        """Return average heart rate."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("hr_avg")


class TempurPedicRestingRespirationSensor(TempurPedicBaseEntity, SensorEntity):
    """Resting respiration rate sensor."""

    _attr_name = "Resting respiration rate"
    _attr_icon = "mdi:lungs"
    _attr_native_unit_of_measurement = "breaths/min"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_resting_respiration_rate"

    @property
    def native_value(self) -> Optional[float]:
        """Return resting respiration rate."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("rr_resting")


class TempurPedicAvgRespirationSensor(TempurPedicBaseEntity, SensorEntity):
    """Average respiration rate sensor."""

    _attr_name = "Average respiration rate"
    _attr_icon = "mdi:lungs"
    _attr_native_unit_of_measurement = "breaths/min"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_avg_respiration_rate"

    @property
    def native_value(self) -> Optional[float]:
        """Return average respiration rate."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("rr_avg")


class TempurPedicTotalSleepSensor(TempurPedicBaseEntity, SensorEntity):
    """Total sleep time sensor."""

    _attr_name = "Total sleep time"
    _attr_icon = "mdi:sleep"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_total_sleep_time"

    @property
    def native_value(self) -> Optional[int]:
        """Return total sleep minutes."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("sleep_total_mins")


class TempurPedicDeepSleepSensor(TempurPedicBaseEntity, SensorEntity):
    """Deep sleep duration sensor."""

    _attr_name = "Deep sleep time"
    _attr_icon = "mdi:sleep"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_deep_sleep_time"

    @property
    def native_value(self) -> Optional[int]:
        """Return deep sleep minutes."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("deep_total_mins")


class TempurPedicRemSleepSensor(TempurPedicBaseEntity, SensorEntity):
    """REM sleep duration sensor."""

    _attr_name = "REM sleep time"
    _attr_icon = "mdi:sleep"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_rem_sleep_time"

    @property
    def native_value(self) -> Optional[int]:
        """Return REM sleep minutes."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("rem_total_mins")


class TempurPedicSnoreDurationSensor(TempurPedicBaseEntity, SensorEntity):
    """Snore duration sensor."""

    _attr_name = "Snore duration"
    _attr_icon = "mdi:sleep-off"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_snore_duration"

    @property
    def native_value(self) -> Optional[int]:
        """Return snore duration minutes."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("snore_duration_mins")


class TempurPedicSleepEfficiencySensor(TempurPedicBaseEntity, SensorEntity):
    """Sleep efficiency percentage sensor."""

    _attr_name = "Sleep efficiency"
    _attr_icon = "mdi:chart-arc"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_sleep_efficiency"

    @property
    def native_value(self) -> Optional[int]:
        """Return sleep efficiency percentage."""
        data = self.coordinator.data or {}
        return data.get("env", {}).get("sleep_efficiency")
