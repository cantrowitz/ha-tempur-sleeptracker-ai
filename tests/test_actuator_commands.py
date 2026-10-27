"""Actuator command tests — the regression suite for the 2026-10-26 bug.

The bug: const.py conflated STOP with DOWN (CMD_HEAD_DOWN was 107 and
CMD_FOOT_DOWN was 108; both are actually the stop commands). Every
"down" movement therefore sent [stop, ..., up-start]: the bed did
nothing, then the motor was left running UP. Head/foot "up" only worked
by accident, because the misnamed constant happened to be the right
stop.

Verified command table (Adam, 2026-10-26):

    Head:   up 110 -> stop 107 | down 111 -> stop 107
    Foot:   up 112 -> stop 108 | down 113 -> stop 108
    Lumbar: up 114 -> stop 106 | down 115 -> stop 106
"""
import asyncio

import pytest

from tempur_sleeptracker_ai import const
from tempur_sleeptracker_ai.api import TempurPedicApiClient

EXPECTED = {
    # method name: (start command, stop command)
    "async_head_up": (110, 107),
    "async_head_down": (111, 107),
    "async_foot_up": (112, 108),
    "async_foot_down": (113, 108),
    "async_lumbar_up": (114, 106),
    "async_lumbar_down": (115, 106),
}

STARTS = {start for start, _ in EXPECTED.values()}
STOPS = {stop for _, stop in EXPECTED.values()}


def run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def client():
    api = TempurPedicApiClient(session=object())
    sent = []

    async def record(cmd, massage_adjustment=0, request_status=True):
        sent.append(cmd)
        return {}

    api.async_send_command = record
    api.sent = sent
    return api


# ---------------------------------------------------------------------------
# Constant-level invariants
# ---------------------------------------------------------------------------
def test_constants_match_verified_table():
    assert (const.CMD_HEAD_UP, const.CMD_HEAD_DOWN, const.CMD_HEAD_STOP) == (110, 111, 107)
    assert (const.CMD_FOOT_UP, const.CMD_FOOT_DOWN, const.CMD_FOOT_STOP) == (112, 113, 108)
    assert (const.CMD_LUMBAR_UP, const.CMD_LUMBAR_DOWN, const.CMD_LUMBAR_STOP) == (114, 115, 106)


def test_stops_are_not_starts():
    """The core invariant the bug violated: no stop may equal any start."""
    assert STARTS.isdisjoint(STOPS)
    assert const.CMD_HEAD_DOWN != const.CMD_HEAD_STOP
    assert const.CMD_FOOT_DOWN != const.CMD_FOOT_STOP
    assert const.CMD_LUMBAR_DOWN != const.CMD_LUMBAR_STOP


def test_all_starts_unique_and_stops_unique_per_actuator():
    assert len(STARTS) == 6
    assert len(STOPS) == 3


def test_pulses_per_sec_matches_observation():
    # Observed 2026-10-26: head moved 494 -> 565 pulses in ~1s.
    # Update this together with the const.py comment when re-measured.
    assert const.ACTUATOR_PULSES_PER_SEC == 71.0


# ---------------------------------------------------------------------------
# API-level command sequences
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,expected", EXPECTED.items())
def test_actuation_sends_start_then_dedicated_stop(client, method, expected):
    run(getattr(client, method)(hold_secs=0.01))
    assert client.sent == list(expected)


@pytest.mark.parametrize(
    "method,stop_cmd",
    [
        ("async_head_stop", 107),
        ("async_foot_stop", 108),
        ("async_lumbar_stop", 106),
    ],
)
def test_stop_methods_send_only_the_stop(client, method, stop_cmd):
    run(getattr(client, method)())
    assert client.sent == [stop_cmd]


def test_head_down_never_sends_head_up(client):
    """Regression: the old head-down sequence was [107, 110] — it ended
    by starting the motor UP."""
    run(client.async_head_down(hold_secs=0.01))
    assert 110 not in client.sent
    assert client.sent[-1] == 107


def test_foot_down_never_sends_foot_up(client):
    """Regression: the old foot-down sequence was [108, 112]."""
    run(client.async_foot_down(hold_secs=0.01))
    assert 112 not in client.sent
    assert client.sent[-1] == 108


@pytest.mark.parametrize("method", EXPECTED)
def test_every_sequence_ends_with_a_stop(client, method):
    """No movement may ever leave the motor running."""
    run(getattr(client, method)(hold_secs=0.01))
    assert client.sent[-1] in STOPS
    assert client.sent[-1] not in STARTS


def test_cancelled_hold_still_sends_stop(client):
    """If HA cancels mid-hold, the finally block must still stop the motor."""

    async def scenario():
        task = asyncio.create_task(client._async_actuate(110, 107, 30))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    run(scenario())
    assert client.sent == [110, 107]


def test_send_command_builds_payload_with_command():
    api = TempurPedicApiClient(session=object())
    captured = {}

    async def fake_post(url, payload):
        captured["payload"] = payload
        return {}

    api._async_post_authorized = fake_post
    run(api.async_send_command(111, request_status=False))
    assert captured["payload"]["bedControlCommand"] == 111
    assert captured["payload"]["requestStatus"] is False
