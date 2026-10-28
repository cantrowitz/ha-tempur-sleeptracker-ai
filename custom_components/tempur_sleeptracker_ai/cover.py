"""Cover platform for Tempur-Pedic Sleeptracker-AI base articulation."""
import logging
from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
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

# Typical maximum elevation angles in degrees
MAX_HEAD_DEGREES = 60.0
MAX_FOOT_DEGREES = 45.0

# Clamp hold duration so a single HA action can't run the motor indefinitely
_MIN_HOLD_SECS = 0.2
_MAX_HOLD_SECS = 45.0


def _hold_duration(delta_pulses: float) -> float:
    """Convert a pulse-count delta to a motor hold duration in seconds.

    Uses the estimated ACTUATOR_PULSES_PER_SEC constant.  The result is
    clamped to a safe range so network jitter or extreme position deltas
    never stall HA or overdrive the motor.
    """
    secs = abs(delta_pulses) / ACTUATOR_PULSES_PER_SEC
    return max(_MIN_HOLD_SECS, min(_MAX_HOLD_SECS, secs))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tempur-Pedic cover platform."""
    data = entry.runtime_data if hasattr(entry, "runtime_data") and entry.runtime_data else hass.data[DOMAIN][entry.entry_id]
    api = data.api if hasattr(data, "api") else data["api"]
    coordinator = data.coordinator if hasattr(data, "coordinator") else data["coordinator"]

    async_add_entities([
        TempurPedicHeadCover(coordinator, api, entry),
        TempurPedicFootCover(coordinator, api, entry),
        TempurPedicLumbarCover(coordinator, api, entry),
    ])


class TempurPedicHeadCover(TempurPedicBaseEntity, CoverEntity):
    """Head elevation cover entity."""

    _attr_name = "Head elevation"
    _attr_icon = "mdi:bed"
    _attr_supported_features = (
        CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the head elevation cover."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_head_elevation"
        ticks_per_deg = entry.data.get(CONF_HEAD_TICKS, 234.0)
        self._max_pulse = ticks_per_deg * MAX_HEAD_DEGREES

    @property
    def current_cover_position(self) -> int:
        """Return current head elevation position (0 = flat, 100 = full upright)."""
        data = self.coordinator.data or {}
        pulse = data.get("head_pulse", 0)
        if self._max_pulse <= 0:
            return 0
        return min(100, max(0, int((pulse / self._max_pulse) * 100)))

    @property
    def is_closed(self) -> bool:
        """A bed is never 'closed' — always report open regardless of position."""
        return False

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Raise head elevation by one nudge (110, stop 107)."""
        await self._api.async_head_up(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Lower head elevation by one nudge (111, stop 107)."""
        await self._api.async_head_down(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop head movement immediately (107 — the dedicated stop, not 'down')."""
        await self._api.async_head_stop()
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move head to the requested position percentage.

        Calculates how long to hold the motor based on the pulse delta between
        current and target positions, then issues the appropriate direction command.
        """
        target_pos = kwargs.get("position", 0)
        current = self.current_cover_position

        if target_pos == current:
            return

        target_pulse = (target_pos / 100.0) * self._max_pulse
        # Use the raw pulse count, not a round-trip through the rounded
        # percentage — the old code lost up to ~1% of full travel of delta.
        current_pulse = float((self.coordinator.data or {}).get("head_pulse", 0))
        delta = target_pulse - current_pulse
        hold = _hold_duration(delta)

        _LOGGER.debug(
            "Head set_position: current=%d%% target=%d%% delta_pulses=%.0f hold=%.2fs",
            current, target_pos, delta, hold,
        )

        if delta > 0:
            await self._api.async_head_up(hold_secs=hold)
        else:
            await self._api.async_head_down(hold_secs=hold)

        await self.coordinator.async_request_refresh()


class TempurPedicFootCover(TempurPedicBaseEntity, CoverEntity):
    """Foot elevation cover entity."""

    _attr_name = "Foot elevation"
    _attr_icon = "mdi:bed"
    _attr_supported_features = (
        CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the foot elevation cover."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_foot_elevation"
        ticks_per_deg = entry.data.get(CONF_FOOT_TICKS, 306.0)
        self._max_pulse = ticks_per_deg * MAX_FOOT_DEGREES

    @property
    def current_cover_position(self) -> int:
        """Return current foot elevation position (0 = flat, 100 = full upright)."""
        data = self.coordinator.data or {}
        pulse = data.get("foot_pulse", 0)
        if self._max_pulse <= 0:
            return 0
        return min(100, max(0, int((pulse / self._max_pulse) * 100)))

    @property
    def is_closed(self) -> bool:
        """A bed is never 'closed' — always report open regardless of position."""
        return False

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Raise foot elevation by one nudge (112, stop 108)."""
        await self._api.async_foot_up(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Lower foot elevation by one nudge (113, stop 108)."""
        await self._api.async_foot_down(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop foot movement immediately (108 — the dedicated stop, not 'down')."""
        await self._api.async_foot_stop()
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move foot to the requested position percentage.

        Calculates how long to hold the motor based on the pulse delta between
        current and target positions, then issues the appropriate direction command.
        """
        target_pos = kwargs.get("position", 0)
        current = self.current_cover_position

        if target_pos == current:
            return

        target_pulse = (target_pos / 100.0) * self._max_pulse
        # Raw pulse count, as in the head cover — see note there.
        current_pulse = float((self.coordinator.data or {}).get("foot_pulse", 0))
        delta = target_pulse - current_pulse
        hold = _hold_duration(delta)

        _LOGGER.debug(
            "Foot set_position: current=%d%% target=%d%% delta_pulses=%.0f hold=%.2fs",
            current, target_pos, delta, hold,
        )

        if delta > 0:
            await self._api.async_foot_up(hold_secs=hold)
        else:
            await self._api.async_foot_down(hold_secs=hold)

        await self.coordinator.async_request_refresh()


class TempurPedicLumbarCover(TempurPedicBaseEntity, CoverEntity):
    """Lumbar support cover entity — arrows only, no position.

    Unlike head/foot, lumbar has no calibration: nobody has measured its
    full travel in pulses (head/foot convert pulses to a percentage via
    ticks-per-degree x max degrees, and lumbar support isn't an angle).
    Rather than invent a max-travel number — the failure mode behind the
    2026-10-26 actuator bug — this cover advertises only OPEN / CLOSE /
    STOP and reports no position. It gets the same up/down/stop arrow
    controls as head/foot; SET_POSITION can be added once full-extension
    pulses are measured (the Lumbar motor pulse sensor exists for that).
    """

    _attr_name = "Lumbar support"
    _attr_icon = "mdi:bed"
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, api_client, entry: ConfigEntry) -> None:
        """Initialize the lumbar support cover."""
        super().__init__(coordinator, entry)
        self._api = api_client
        serial = entry.data.get(CONF_PROCESSOR_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_lumbar_support"

    @property
    def current_cover_position(self) -> None:
        """Position is unknown until lumbar max travel is calibrated."""
        return None

    @property
    def is_closed(self) -> None:
        """Unknown — follows from the unknown position."""
        return None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Extend lumbar support by one nudge (114, stop 106)."""
        await self._api.async_lumbar_up(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Retract lumbar support by one nudge (115, stop 106)."""
        await self._api.async_lumbar_down(hold_secs=ACTUATOR_NUDGE_SECS)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop lumbar movement immediately (106 — the dedicated stop)."""
        await self._api.async_lumbar_stop()
        await self.coordinator.async_request_refresh()

