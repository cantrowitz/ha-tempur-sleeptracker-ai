"""Preset and massage command tests.

Command table verified from Sleeptracker app captures (Adam, 2026-10-27):

    Presets (massageAdjustment 0, requestStatus false):
        0 Zero-G | 2 Flat | 3 TV-in-Bed | 4 QuietMode
        6 Favorite 1 | 9 Favorite 2
    Massage (massageAdjustment 1, requestStatus true):
        210 head strength step | 211 foot strength step
        212 Wave Form 28 Hz    | 213 Wave Form 40 Hz
        226 cycle Wave Form pattern

Capture semantics worth pinning down:
  * Head strength stepped +2 per 210 press (4 -> 6 -> 8); foot likewise.
  * 212/213 reset both zones to strength 4, pattern 0, timer 30:00.
  * 226 stepped the snapshot pattern 1 -> 2 -> 3 across presses.
"""
import asyncio

import pytest

from tempur_sleeptracker_ai import button, const, sensor
from tempur_sleeptracker_ai.api import TempurPedicApiClient

from conftest import FakeApi, FakeCoordinator, make_entry


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Constant table
# ---------------------------------------------------------------------------
def test_preset_command_table():
    assert const.CMD_PRESET_ZERO_G == 0
    assert const.CMD_PRESET_FLAT == 2
    assert const.CMD_PRESET_TV == 3
    assert const.CMD_PRESET_QUIET_MODE == 4
    assert const.CMD_PRESET_FAVORITE_1 == 6
    assert const.CMD_PRESET_FAVORITE_2 == 9


def test_massage_command_table():
    assert const.CMD_MASSAGE_HEAD_STRENGTH == 210
    assert const.CMD_MASSAGE_FOOT_STRENGTH == 211
    assert const.CMD_MASSAGE_FREQ_28HZ == 212
    assert const.CMD_MASSAGE_FREQ_40HZ == 213
    assert const.CMD_MASSAGE_CYCLE_PATTERN == 226
    assert const.MASSAGE_ADJUSTMENT_ACTIVE == 1


def test_new_commands_do_not_collide_with_existing():
    new = {
        const.CMD_PRESET_TV,
        const.CMD_PRESET_QUIET_MODE,
        const.CMD_PRESET_FAVORITE_1,
        const.CMD_PRESET_FAVORITE_2,
        const.CMD_MASSAGE_HEAD_STRENGTH,
        const.CMD_MASSAGE_FOOT_STRENGTH,
        const.CMD_MASSAGE_FREQ_28HZ,
        const.CMD_MASSAGE_FREQ_40HZ,
        const.CMD_MASSAGE_CYCLE_PATTERN,
    }
    existing = {
        const.CMD_PRESET_ZERO_G,
        const.CMD_PRESET_FLAT,
        const.CMD_TOGGLE_LIGHT,
        const.CMD_POLL_STATUS,
        const.CMD_STOP_WIND_DOWN,
        const.CMD_HEAD_UP,
        const.CMD_HEAD_DOWN,
        const.CMD_HEAD_STOP,
        const.CMD_FOOT_UP,
        const.CMD_FOOT_DOWN,
        const.CMD_FOOT_STOP,
        const.CMD_LUMBAR_UP,
        const.CMD_LUMBAR_DOWN,
        const.CMD_LUMBAR_STOP,
    }
    assert len(new) == 9
    assert not (new & existing)


# ---------------------------------------------------------------------------
# API dispatch: (command, massageAdjustment, requestStatus) per method
# ---------------------------------------------------------------------------
@pytest.fixture()
def api():
    client = TempurPedicApiClient(session=object())
    sent = []

    async def record(cmd, massage_adjustment=0, request_status=True):
        sent.append((cmd, massage_adjustment, request_status))
        return {}

    client.async_send_command = record
    client.sent = sent
    return client


@pytest.mark.parametrize(
    "method,expected",
    [
        ("async_preset_tv", (3, 0, False)),
        ("async_preset_quiet_mode", (4, 0, False)),
        ("async_preset_favorite_1", (6, 0, False)),
        ("async_preset_favorite_2", (9, 0, False)),
        ("async_massage_head_strength_step", (210, 1, True)),
        ("async_massage_foot_strength_step", (211, 1, True)),
        ("async_massage_freq_28hz", (212, 1, True)),
        ("async_massage_freq_40hz", (213, 1, True)),
        ("async_massage_cycle_pattern", (226, 1, True)),
    ],
)
def test_api_dispatch(api, method, expected):
    run(getattr(api, method)())
    assert api.sent == [expected]


# ---------------------------------------------------------------------------
# Button dispatch
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cls_name,expected",
    [
        ("TempurPedicTVPresetButton", ("preset_tv", None)),
        ("TempurPedicQuietModePresetButton", ("preset_quiet_mode", None)),
        ("TempurPedicFavorite1PresetButton", ("preset_favorite_1", None)),
        ("TempurPedicFavorite2PresetButton", ("preset_favorite_2", None)),
        ("TempurPedicMassageHeadStrengthButton", ("massage_head_strength", None)),
        ("TempurPedicMassageFootStrengthButton", ("massage_foot_strength", None)),
        ("TempurPedicMassageFreq28Button", ("massage_freq_28hz", None)),
        ("TempurPedicMassageFreq40Button", ("massage_freq_40hz", None)),
        ("TempurPedicMassageCyclePatternButton", ("massage_cycle_pattern", None)),
    ],
)
def test_new_buttons_dispatch(cls_name, expected):
    api = FakeApi()
    entity = getattr(button, cls_name)(FakeCoordinator(), api, make_entry())
    run(entity.async_press())
    assert api.calls == [expected]


def test_new_button_unique_ids_are_distinct():
    classes = [
        "TempurPedicTVPresetButton",
        "TempurPedicQuietModePresetButton",
        "TempurPedicFavorite1PresetButton",
        "TempurPedicFavorite2PresetButton",
        "TempurPedicMassageHeadStrengthButton",
        "TempurPedicMassageFootStrengthButton",
        "TempurPedicMassageFreq28Button",
        "TempurPedicMassageFreq40Button",
        "TempurPedicMassageCyclePatternButton",
    ]
    ids = set()
    for cls_name in classes:
        entity = getattr(button, cls_name)(FakeCoordinator(), FakeApi(), make_entry())
        ids.add(entity._attr_unique_id)
    assert len(ids) == len(classes)


# ---------------------------------------------------------------------------
# Massage strength sensors read the keys the status parser produces
# ---------------------------------------------------------------------------
def test_massage_strength_sensors():
    data = {"online": True, "head_massage_strength": 6, "foot_massage_strength": 4}
    head = sensor.TempurPedicHeadMassageStrengthSensor(FakeCoordinator(data), make_entry())
    foot = sensor.TempurPedicFootMassageStrengthSensor(FakeCoordinator(data), make_entry())
    assert head.native_value == 6
    assert foot.native_value == 4
