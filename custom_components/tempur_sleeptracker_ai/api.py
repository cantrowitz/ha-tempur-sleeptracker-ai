"""API Client for Tempur-Pedic Sleeptracker-AI cloud services."""
import asyncio
import base64
import logging
import time
from typing import Any, Dict, List, Optional
import aiohttp

from .const import (
    AUTH_URL,
    CLIENT_ID,
    CLIENT_VERSION,
    CMD_FOOT_DOWN,
    CMD_FOOT_STOP,
    CMD_FOOT_UP,
    CMD_HEAD_DOWN,
    CMD_HEAD_STOP,
    CMD_HEAD_UP,
    CMD_LUMBAR_DOWN,
    CMD_LUMBAR_STOP,
    CMD_LUMBAR_UP,
    CMD_POLL_STATUS,
    CMD_PRESET_FLAT,
    CMD_PRESET_ZERO_G,
    CMD_STOP_WIND_DOWN,
    CMD_TOGGLE_LIGHT,
    ENDPOINT_BASE_CONTROLS,
    ENDPOINT_GET_BY_TYPE,
    ENDPOINT_WEBUI,
)

_LOGGER = logging.getLogger(__name__)


class TempurPedicError(Exception):
    """Base exception for Tempur-Pedic Sleeptracker errors."""


class TempurPedicAuthError(TempurPedicError):
    """Exception for authentication failures."""


class TempurPedicConnectionError(TempurPedicError):
    """Exception for network and communication failures."""


class TempurPedicApiClient:
    """Async API Client for Tempur-Pedic Sleeptracker-AI."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        token_expiration: Optional[int] = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._token = token
        self._token_expiration = token_expiration
        self._user_id_token: Optional[str] = None
        self._cached_env_data: Dict[str, Any] = {}
        self._last_env_fetch_time: float = 0.0

    @property
    def token(self) -> Optional[str]:
        """Return the current auth token."""
        return self._token

    @property
    def token_expiration(self) -> Optional[int]:
        """Return the token expiration timestamp."""
        return self._token_expiration

    async def async_login(self, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate with TSI authentication service and retrieve session token."""
        if email:
            self._email = email
        if password:
            self._password = password

        if not self._email or not self._password:
            raise TempurPedicAuthError("Email and password are required for authentication.")

        auth_str = f"{self._email}:{self._password}"
        b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 17; sdk_gphone64_arm64 Build/CE2A.260420.051.A3)",
        }
        payload = {
            "clientID": CLIENT_ID,
            "clientVersion": CLIENT_VERSION,
            "id": "Android: getNewSession",
        }

        try:
            async with asyncio.timeout(15):
                res = await self._session.post(AUTH_URL, json=payload, headers=headers)
                if res.status in (401, 403):
                    raise TempurPedicAuthError("Invalid credentials provided.")
                res.raise_for_status()
                data = await res.json()
        except TimeoutError as err:
            raise TempurPedicConnectionError("Timeout connecting to TSI auth server") from err
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise TempurPedicAuthError("Invalid credentials provided.") from err
            raise TempurPedicConnectionError(f"HTTP error during authentication: {err.status}") from err
        except aiohttp.ClientError as err:
            raise TempurPedicConnectionError(f"Connection error during authentication: {err}") from err

        if data.get("statusCode") != 0 or "token" not in data:
            msg = data.get("statusMessage", "Unknown authentication error")
            raise TempurPedicAuthError(f"Authentication failed: {msg}")

        self._token = data["token"]
        self._token_expiration = data.get("expirationTimeSecs")
        self._user_id_token = data.get("userIDToken")

        _LOGGER.debug(
            "Authenticated successfully with TSI Sleeptracker. Expiration: %s",
            self._token_expiration,
        )
        return data

    async def async_ensure_authenticated(self) -> None:
        """Ensure client has an active token, re-authenticating if needed."""
        now = int(time.time())
        if not self._token or (self._token_expiration and (self._token_expiration - now) < 300):
            _LOGGER.debug("Token missing or near expiration; refreshing session...")
            await self.async_login()

    async def _async_post_authorized(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send an authorized POST request, refreshing token if expired."""
        await self.async_ensure_authenticated()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 17; sdk_gphone64_arm64 Build/CE2A.260420.051.A3)",
        }

        try:
            async with asyncio.timeout(15):
                res = await self._session.post(url, json=payload, headers=headers)
                if res.status in (401, 403):
                    _LOGGER.debug("Received %s. Attempting to refresh token...", res.status)
                    await self.async_login()
                    headers["Authorization"] = f"Bearer {self._token}"
                    res = await self._session.post(url, json=payload, headers=headers)

                res.raise_for_status()
                return await res.json()
        except TimeoutError as err:
            raise TempurPedicConnectionError(f"Timeout calling endpoint: {url}") from err
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise TempurPedicAuthError("Authorization denied by Sleeptracker API") from err
            raise TempurPedicConnectionError(f"HTTP error {err.status} from {url}") from err
        except aiohttp.ClientError as err:
            raise TempurPedicConnectionError(f"Connection error calling {url}: {err}") from err

    async def async_get_devices(self) -> List[Dict[str, Any]]:
        """Discover all registered bed devices and processors for the user."""
        payload = {
            "types": [1, 2, 4, 6, 7],
            "clientID": CLIENT_ID,
            "clientVersion": CLIENT_VERSION,
            "id": "TEST_ANDROID_cloudIoTDevicesGetByType",
        }
        data = await self._async_post_authorized(ENDPOINT_GET_BY_TYPE, payload)
        device_list = data.get("deviceList", [])
        _LOGGER.debug("Discovered %d Sleeptracker device(s)", len(device_list))
        return device_list

    async def async_get_bed_status(self) -> Dict[str, Any]:
        """Fetch current telemetry and snapshot for the adjustable base."""
        payload = {
            "bedControlCommand": CMD_POLL_STATUS,
            "massageAdjustment": 0,
            "requestStatus": True,
            "clientID": CLIENT_ID,
            "clientVersion": CLIENT_VERSION,
            "id": "TEST_ANDROID_adjustableBaseControls",
        }
        data = await self._async_post_authorized(ENDPOINT_BASE_CONTROLS, payload)
        body = data.get("body", {})
        snapshots = body.get("snapshots", [{}])
        snapshot = snapshots[0] if snapshots else {}

        _LOGGER.debug("Raw bed status snapshot: %s", snapshot)

        # Extract dynamic wind-down program list when the API returns it.
        # The cloud may return a list like:
        #   [{"name": "Prepare for Sleep", "command": 22, "modeId": 32}, ...]
        # We normalise it to the same shape as the hardcoded WIND_DOWN_PROGRAMS
        # constant so the select entity can use either source transparently.
        raw_programs = snapshot.get("windDownPrograms", [])
        dynamic_programs = {
            prog["name"]: {"command": prog["command"], "mode_id": prog["modeId"]}
            for prog in raw_programs
            if "name" in prog and "command" in prog and "modeId" in prog
        }

        return {
            "online": body.get("connectionStatus") == "online",
            "wind_down_mode": snapshot.get("windDownMode", 0),
            "wind_down_programs": dynamic_programs,  # empty dict if API does not provide them
            "massage_frequency_hz": snapshot.get("massageFrequency", 0),
            "massage_timer_mins": snapshot.get("massageTimerMins", 0),
            "massage_timer_secs": snapshot.get("massageTimerSecs", 0),
            "massage_pattern": snapshot.get("massagePattern", 0),
            "panel_light": snapshot.get("panelLightOn", False),
            "safety_light": snapshot.get("safetyLightOn", False),
            "head_pulse": snapshot.get("head", {}).get("motor", {}).get("pulseCount", 0),
            "foot_pulse": snapshot.get("foot", {}).get("motor", {}).get("pulseCount", 0),
            "head_tilt_pulse": snapshot.get("headTilt", {}).get("motor", {}).get("pulseCount", 0),
            "lumbar_pulse": snapshot.get("lumbar", {}).get("motor", {}).get("pulseCount", 0),
            "head_massage_active": snapshot.get("head", {}).get("massage", {}).get("active", False),
            "foot_massage_active": snapshot.get("foot", {}).get("massage", {}).get("active", False),
            "busy_with_command": snapshot.get("busyWithCommand", False),
            "raw_snapshot": snapshot,
        }

    async def async_get_environmental_and_sleep_data(self, cache_ttl: int = 300) -> Dict[str, Any]:
        """Fetch environment conditions and sleep metrics from actrack/webui (cached)."""
        now = time.time()
        if self._cached_env_data and (now - self._last_env_fetch_time) < cache_ttl:
            return self._cached_env_data

        today_str = time.strftime("%Y%m%d")
        payload = {
            "version": "v2",
            "clientVersion": "3.6.2",
            "command": "fetch",
            "dataClass": "activities",
            "resultLimitSize": 10,
            "returnEmptySummaryFlag": False,
            "includeSleepsDailySummary": True,
            "sleepsDailyStartDayYYYYMMDD": "20100101",
            "sleepsDailyEndDayYYYYMMDD": today_str,
            "sleepZSleepsSummaries": True,
            "currentRecordingStatus": True,
            "newestToOldest": True,
        }

        try:
            data = await self._async_post_authorized(ENDPOINT_WEBUI, payload)
            summary = data.get("summary", {})
            dailies = summary.get("sleepsDailySummary", {}).get("sleepSummaryDailyDetails", [])
            _LOGGER.debug("actrack/webui returned %d daily summary records", len(dailies))

            # Find the newest entry that contains environmental telemetry
            latest_env_entry = None
            for entry in dailies:
                if entry.get("environment"):
                    latest_env_entry = entry
                    break

            latest = latest_env_entry or (dailies[0] if dailies else {})
            env = latest.get("environment", {})

            def _get_latest_value(metric_obj: Dict[str, Any]) -> Optional[float]:
                vals = metric_obj.get("values", [])
                return round(float(vals[-1]), 1) if vals else None

            temp_c = _get_latest_value(env.get("degreesCelsius", {}))
            humidity = _get_latest_value(env.get("humidityPercentage", {}))
            co2 = _get_latest_value(env.get("co2Ppm", {}))
            voc = _get_latest_value(env.get("vocPpb", {}))
            iaq = _get_latest_value(env.get("iaq", {}))

            user_metrics = latest.get("userSleepMetrics", {})
            snore_secs = user_metrics.get("snoreDurationSecs", latest.get("snoreDurationSecs", 0))

            parsed = {
                "temperature_celsius": temp_c,
                "humidity_percentage": humidity,
                "co2_ppm": co2,
                "voc_ppb": voc,
                "iaq": iaq,
                "sleep_score": latest.get("sleepScore"),
                "hr_avg": latest.get("hrAvg"),
                "hr_resting": latest.get("hrResting"),
                "rr_avg": latest.get("rrAvg"),
                "rr_resting": latest.get("rrResting"),
                "sleep_total_mins": (latest.get("sleepTotalSecs") or 0) // 60,
                "deep_total_mins": (latest.get("deepTotalSecs") or 0) // 60,
                "rem_total_mins": (latest.get("remTotalSecs") or 0) // 60,
                "light_total_mins": (latest.get("lightTotalSecs") or 0) // 60,
                "awake_total_mins": (latest.get("awakeTotalSecs") or 0) // 60,
                "snore_duration_mins": (snore_secs or 0) // 60,
                "sleep_efficiency": latest.get("sleepEfficiencyPercentage"),
                "last_off_bed_time_secs": latest.get("lastOffBedTimeSecs"),
                "last_on_bed_time_secs": latest.get("firstOnBedTimeSecs"),
                "sleep_recording_active": (
                    bool(summary.get("currentRecordingStatus"))
                    or any(r.get("status") == "Active" and r.get("sleepRecordingStopSecs", 0) > now for r in latest.get("sleepRecordings", []))
                ),
            }

            self._cached_env_data = parsed
            self._last_env_fetch_time = now
            _LOGGER.debug("Fetched environmental & sleep telemetry: %s", parsed)
            return parsed
        except Exception as err:
            _LOGGER.warning("Could not fetch environmental/sleep data: %s", err, exc_info=True)
            return self._cached_env_data or {}

    async def async_toggle_light(self) -> Dict[str, Any]:
        """Toggle underbed / safety light (Command 230)."""
        return await self.async_send_command(CMD_TOGGLE_LIGHT, request_status=False)

    async def _async_actuate(
        self,
        start_cmd: int,
        stop_cmd: int,
        hold_secs: float,
    ) -> None:
        """Drive an actuator motor using the press-and-hold protocol.

        Sending ``start_cmd`` starts the motor, and sending that
        actuator's dedicated ``stop_cmd`` halts it — the stop command is
        NOT the opposite direction's start command:

            Head:   up 110 -> stop 107 | down 111 -> stop 107
            Foot:   up 112 -> stop 108 | down 113 -> stop 108
            Lumbar: up 114 -> stop 106 | down 115 -> stop 106

        The motor runs for ``hold_secs`` between the two calls. The stop
        is sent from a finally block so the motor is halted even if the
        hold is cancelled (e.g. HA shutting down or the caller being
        cancelled) or the sleep raises.
        """
        await self.async_send_command(start_cmd, request_status=False)
        try:
            await asyncio.sleep(hold_secs)
        finally:
            await self.async_send_command(stop_cmd, request_status=False)

    async def async_head_up(self, hold_secs: float = 1.5) -> None:
        """Move head elevation up (110), then stop (107) after hold_secs."""
        await self._async_actuate(CMD_HEAD_UP, CMD_HEAD_STOP, hold_secs)

    async def async_head_down(self, hold_secs: float = 1.5) -> None:
        """Move head elevation down (111), then stop (107) after hold_secs."""
        await self._async_actuate(CMD_HEAD_DOWN, CMD_HEAD_STOP, hold_secs)

    async def async_head_stop(self) -> None:
        """Stop head movement immediately (107), whichever way it's moving."""
        await self.async_send_command(CMD_HEAD_STOP, request_status=False)

    async def async_foot_up(self, hold_secs: float = 1.5) -> None:
        """Move foot elevation up (112), then stop (108) after hold_secs."""
        await self._async_actuate(CMD_FOOT_UP, CMD_FOOT_STOP, hold_secs)

    async def async_foot_down(self, hold_secs: float = 1.5) -> None:
        """Move foot elevation down (113), then stop (108) after hold_secs."""
        await self._async_actuate(CMD_FOOT_DOWN, CMD_FOOT_STOP, hold_secs)

    async def async_foot_stop(self) -> None:
        """Stop foot movement immediately (108), whichever way it's moving."""
        await self.async_send_command(CMD_FOOT_STOP, request_status=False)

    async def async_lumbar_up(self, hold_secs: float = 1.5) -> None:
        """Move lumbar up (114), then stop (106) after hold_secs."""
        await self._async_actuate(CMD_LUMBAR_UP, CMD_LUMBAR_STOP, hold_secs)

    async def async_lumbar_down(self, hold_secs: float = 1.5) -> None:
        """Move lumbar down (115), then stop (106) after hold_secs."""
        await self._async_actuate(CMD_LUMBAR_DOWN, CMD_LUMBAR_STOP, hold_secs)

    async def async_lumbar_stop(self) -> None:
        """Stop lumbar movement immediately (106), whichever way it's moving."""
        await self.async_send_command(CMD_LUMBAR_STOP, request_status=False)

    async def async_preset_flat(self) -> Dict[str, Any]:
        """Move base to flat preset (Command 2)."""
        return await self.async_send_command(CMD_PRESET_FLAT, request_status=False)

    async def async_preset_zero_g(self) -> Dict[str, Any]:
        """Move base to Zero-G preset (Command 0)."""
        return await self.async_send_command(CMD_PRESET_ZERO_G, request_status=False)

    async def async_start_wind_down(self, command_id: int, massage_adjustment: int = 0) -> Dict[str, Any]:
        """Start a wind down preset program."""
        return await self.async_send_command(command_id, massage_adjustment=massage_adjustment, request_status=True)

    async def async_stop_wind_down(self) -> Dict[str, Any]:
        """Stop active wind down program (Command 31)."""
        return await self.async_send_command(CMD_STOP_WIND_DOWN, request_status=True)

    async def async_send_command(
        self,
        bed_control_command: int,
        massage_adjustment: int = 0,
        request_status: bool = True,
    ) -> Dict[str, Any]:
        """Send an arbitrary bed control command."""
        payload = {
            "bedControlCommand": bed_control_command,
            "massageAdjustment": massage_adjustment,
            "requestStatus": request_status,
            "clientID": CLIENT_ID,
            "clientVersion": CLIENT_VERSION,
            "id": "TEST_ANDROID_adjustableBaseControls",
        }
        return await self._async_post_authorized(ENDPOINT_BASE_CONTROLS, payload)
