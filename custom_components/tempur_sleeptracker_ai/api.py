import logging
from typing import Any, Dict
from .const import ENDPOINT_URL

_LOGGER = logging.getLogger(__name__)

class TempurPedicApiClient:
    def __init__(self, session, host: str, token: str):
        self._session = session
        self._host = host
        self._token = token

    async def async_get_bed_status(self) -> Dict[str, Any]:
        payload = {
            "bedControlCommand": 500,
            "clientID": "sleeptracker-android-tsi",
            "clientVersion": "H-3.6.2",
            "id": "TEST_ANDROID_adjustableBaseControls",
        }
        res = await self._session.post(
            ENDPOINT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
        )
        data = await res.json()
        snapshot = data.get("body", {}).get("snapshots", [{}])[0]
        return {
            "wind_down_mode": snapshot.get("windDownMode", 0),
            "massage_frequency_hz": snapshot.get("massageFrequency", 0),
            "massage_timer_mins": snapshot.get("massageTimerMins", 0),
            "panel_light": snapshot.get("panelLightOn", False),
            "head_pulse": snapshot.get("head", {}).get("motor", {}).get("pulseCount", 0),
            "foot_pulse": snapshot.get("foot", {}).get("motor", {}).get("pulseCount", 0),
        }

    async def async_start_wind_down(self, command_id: int, massage_adjustment: int = 0) -> Dict[str, Any]:
        payload = {
            "bedControlCommand": command_id,
            "massageAdjustment": massage_adjustment,
            "requestStatus": True,
            "clientID": "sleeptracker-android-tsi",
            "clientVersion": "H-3.6.2",
            "id": "TEST_ANDROID_adjustableBaseControls",
        }
        res = await self._session.post(
            ENDPOINT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
        )
        return await res.json()

    async def async_stop_wind_down(self) -> Dict[str, Any]:
        payload = {
            "bedControlCommand": 31,
            "massageAdjustment": 0,
            "requestStatus": True,
            "clientID": "sleeptracker-android-tsi",
            "clientVersion": "H-3.6.2",
            "id": "TEST_ANDROID_adjustableBaseControls",
        }
        res = await self._session.post(
            ENDPOINT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
        )
        return await res.json()
