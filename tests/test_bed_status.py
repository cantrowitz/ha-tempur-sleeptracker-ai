"""Tests for async_get_bed_status parsing of the command-500 response.

The fixture shape is taken verbatim from a real capture (Adam's Ergo
ProSmart base, Oct 27 2026): command 500 returns connectionStatus,
invariants (hardware capability roster) and snapshots (live state).
"""
from __future__ import annotations

import asyncio
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest  # noqa: F401,E402  (installs HA stubs, puts package on path)

from tempur_sleeptracker_ai.api import TempurPedicApiClient  # noqa: E402


def run(coro):
    return asyncio.run(coro)


CAPTURED_RESPONSE = {
    "body": {
        "connectionStatus": "online",
        "invariants": [
            {
                "firmwareVersion": 3000021,
                "firmwareVersionString": "3.0.21",
                "hardwareRevision": 1001,
                "smartCableUnsynchronized": False,
                "type": "coprocessor",
            },
            {
                "memorySlots": 4,
                "model": "BEST",
                "position": {"side": 0},
                "roster": {
                    "fanController": False,
                    "massage": {
                        "foot": True,
                        "head": True,
                        "headTilt": False,
                        "lumbar": False,
                    },
                    "motors": {
                        "foot": True,
                        "head": True,
                        "headTilt": False,
                        "lumbar": True,
                    },
                },
                "type": "controller",
                "version": 84,
            },
        ],
        "snapshots": [
            {
                "busyWithCommand": False,
                "foot": {
                    "massage": {"active": False, "strength": 0},
                    "motor": {"pulseCount": 0},
                },
                "head": {
                    "massage": {"active": False, "strength": 0},
                    "motor": {"pulseCount": 0},
                },
                "headTilt": {
                    "massage": {"active": False, "strength": 0},
                    "motor": {"pulseCount": 0},
                },
                "lumbar": {
                    "massage": {"active": False, "strength": 0},
                    "motor": {"pulseCount": 0},
                },
                "massageFrequency": 0,
                "massagePattern": 4,
                "massageTimerMins": 0,
                "massageTimerSecs": 0,
                "panelLightOn": False,
                "safetyLightOn": False,
                "side": 0,
                "windDownMode": 0,
            }
        ],
        "statusCode": 0,
    },
    "id": "TEST_ANDROID_adjustableBaseControls",
    "statusCode": 0,
}


def _client_returning(response):
    api = TempurPedicApiClient(session=object())

    async def fake_post(url, payload):
        return response

    api._async_post_authorized = fake_post
    return api


def test_capabilities_parsed_from_invariants():
    status = run(_client_returning(copy.deepcopy(CAPTURED_RESPONSE)).async_get_bed_status())
    caps = status["capabilities"]
    assert caps["motors"] == {"foot": True, "head": True, "headTilt": False, "lumbar": True}
    assert caps["massage"] == {"foot": True, "head": True, "headTilt": False, "lumbar": False}
    assert caps["fan_controller"] is False
    assert caps["memory_slots"] == 4
    assert caps["controller_model"] == "BEST"
    assert caps["coprocessor_firmware"] == "3.0.21"


def test_capabilities_default_safely_when_invariants_missing():
    """Older/other bases may return no invariants — parsing must not crash."""
    response = {"body": {"connectionStatus": "online", "snapshots": [{}]}}
    status = run(_client_returning(response).async_get_bed_status())
    caps = status["capabilities"]
    assert caps["motors"] == {}
    assert caps["massage"] == {}
    assert caps["fan_controller"] is False
    assert caps["memory_slots"] is None
    assert status["online"] is True


def test_massage_strength_parsed_per_zone():
    response = copy.deepcopy(CAPTURED_RESPONSE)
    snap = response["body"]["snapshots"][0]
    snap["head"]["massage"] = {"active": True, "strength": 2}
    snap["foot"]["massage"] = {"active": True, "strength": 1}
    snap["massageFrequency"] = 28
    status = run(_client_returning(response).async_get_bed_status())
    assert status["head_massage_active"] is True
    assert status["head_massage_strength"] == 2
    assert status["foot_massage_strength"] == 1
    assert status["massage_frequency_hz"] == 28


def test_status_poll_sends_command_500():
    api = TempurPedicApiClient(session=object())
    captured = {}

    async def fake_post(url, payload):
        captured["payload"] = payload
        return copy.deepcopy(CAPTURED_RESPONSE)

    api._async_post_authorized = fake_post
    run(api.async_get_bed_status())
    assert captured["payload"]["bedControlCommand"] == 500
