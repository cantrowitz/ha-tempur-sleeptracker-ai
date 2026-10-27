"""Number platform for Tempur-Pedic Sleeptracker-AI base elevation control."""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTUATOR_NUDGE_SECS,
    ACTUATOR_PULSES_PER_SEC,
    CONF_FOOT_TICKS,
    CONF_HEAD_TICKS,
    CONF_PROCESSOR_SERIAL,
    DOMAIN,
)
from .entity import TempurPedicBaseEntity

_LOGGER = logging.getLogger(__name__)

MAX_HEAD_DEGREES = 60.0
MAX_FOOT_DEGREES = 45.0

_MIN_HOLD_SECS = 0.2
_MAX_HOLD_SECS = 45.0


def _hold_duration(delta_pulses: float) -> float:
    """Convert a pulse-count delta to a motor hold duration in seconds."""
    secs = abs(delta_pulses) / ACTUATOR_PULSES_PER_SEC
    return max(_MIN_HOLD_SECS, min(_MAX_HOLD_SECS, secs))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic number platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    api = data.api if hasattr(data, "api") else data["api"]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([
        TempurPedicHeadElevation(coordinator, api, entry),
        TempurPedicFootElevation(coordinator, api, entry),
    ])


class TempurPedicHeadElevation(TempurPedicBaseEntity, NumberEntity):
    """Head elevation as a 0–100 % slider.

    Uses the press-and-hold protocol: the hold duration is derived from the
    pulse delta between current and target positions so the motor runs just
    long enough to reach the desired angle.
    """

    _attr_name = "Head elevation"
    _attr_icon = "mdi:bed"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize head elevation number entity."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_head_elevation"
        ticks_per_deg = entry.data.get(CONF_HEAD_TICKS, 234.0)
        self._max_pulse = ticks_per_deg * MAX_HEAD_DEGREES

    def _pulse_to_pct(self, pulse: float) -> float:
        """Convert a raw pulse count to a 0–100 percentage."""
        if self._max_pulse <= 0:
            return 0.0
        return min(100.0, max(0.0, round((pulse / self._max_pulse) * 100, 1)))

    @property
    def native_value(self) -> float:
        """Return current head elevation as a percentage."""
        data = self.coordinator.data or {}
        return self._pulse_to_pct(data.get("head_pulse", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Move head to the requested elevation percentage."""
        current = self.native_value
        if value == current:
            return

        target_pulse = (value / 100.0) * self._max_pulse
        current_pulse = (current / 100.0) * self._max_pulse
        delta = target_pulse - current_pulse
        hold = _hold_duration(delta)

        _LOGGER.debug(
            "Head elevation: %.0f%% → %.0f%% (delta_pulses=%.0f, hold=%.2fs)",
            current, value, delta, hold,
        )

        if delta > 0:
            await self._api.async_head_up(hold_secs=hold)
        else:
            await self._api.async_head_down(hold_secs=hold)

        await self.coordinator.async_request_refresh()


class TempurPedicFootElevation(TempurPedicBaseEntity, NumberEntity):
    """Foot elevation as a 0–100 % slider.

    Uses the press-and-hold protocol: the hold duration is derived from the
    pulse delta between current and target positions so the motor runs just
    long enough to reach the desired angle.
    """

    _attr_name = "Foot elevation"
    _attr_icon = "mdi:bed"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize foot elevation number entity."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_foot_elevation"
        ticks_per_deg = entry.data.get(CONF_FOOT_TICKS, 306.0)
        self._max_pulse = ticks_per_deg * MAX_FOOT_DEGREES

    def _pulse_to_pct(self, pulse: float) -> float:
        """Convert a raw pulse count to a 0–100 percentage."""
        if self._max_pulse <= 0:
            return 0.0
        return min(100.0, max(0.0, round((pulse / self._max_pulse) * 100, 1)))

    @property
    def native_value(self) -> float:
        """Return current foot elevation as a percentage."""
        data = self.coordinator.data or {}
        return self._pulse_to_pct(data.get("foot_pulse", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Move foot to the requested elevation percentage."""
        current = self.native_value
        if value == current:
            return

        target_pulse = (value / 100.0) * self._max_pulse
        current_pulse = (current / 100.0) * self._max_pulse
        delta = target_pulse - current_pulse
        hold = _hold_duration(delta)

        _LOGGER.debug(
            "Foot elevation: %.0f%% → %.0f%% (delta_pulses=%.0f, hold=%.2fs)",
            current, value, delta, hold,
        )

        if delta > 0:
            await self._api.async_foot_up(hold_secs=hold)
        else:
            await self._api.async_foot_down(hold_secs=hold)

        await self.coordinator.async_request_refresh()
