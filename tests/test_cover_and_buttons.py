"""Cover and button platform logic tests.

Also an import test: importing every platform module under stubs that
mirror the real HA API is what guards against referencing HA attributes
that do not exist (see the conftest stub-fidelity note — cover.py's
CoverEntityFeature.STOP_COVER incident, 2026-10-26).
"""
import asyncio

import pytest

from tempur_sleeptracker_ai import button, cover
from tempur_sleeptracker_ai.const import ACTUATOR_NUDGE_SECS

from conftest import FakeApi, FakeCoordinator, make_entry


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Hold-duration conversion (uses ACTUATOR_PULSES_PER_SEC = 71)
# ---------------------------------------------------------------------------
def test_hold_duration_conversion():
    assert cover._hold_duration(71) == pytest.approx(1.0)
    assert cover._hold_duration(710) == pytest.approx(10.0)
    assert cover._hold_duration(-71) == pytest.approx(1.0)  # direction-agnostic


def test_hold_duration_clamps():
    assert cover._hold_duration(0) == 0.2          # never zero-length
    assert cover._hold_duration(71 * 1000) == 45.0  # never run away


# ---------------------------------------------------------------------------
# Head cover (ticks set to 10/deg so max travel = 600 pulses)
# ---------------------------------------------------------------------------
@pytest.fixture()
def head():
    api = FakeApi()
    coord = FakeCoordinator({"head_pulse": 0, "online": True})
    entity = cover.TempurPedicHeadCover(coord, api, make_entry({"head_ticks_per_degree": 10.0}))
    return entity, api, coord


def test_head_position_mapping(head):
    entity, _, coord = head
    assert entity.current_cover_position == 0
    coord.data["head_pulse"] = 300
    assert entity.current_cover_position == 50
    coord.data["head_pulse"] = 999999  # past max clamps to 100
    assert entity.current_cover_position == 100


def test_head_open_close_stop_dispatch(head):
    entity, api, _ = head
    run(entity.async_open_cover())
    run(entity.async_close_cover())
    run(entity.async_stop_cover())
    assert api.calls == [
        ("head_up", ACTUATOR_NUDGE_SECS),
        ("head_down", ACTUATOR_NUDGE_SECS),
        ("head_stop", None),
    ]


def test_head_set_position_up_uses_raw_pulse_delta(head):
    entity, api, coord = head
    coord.data["head_pulse"] = 100
    run(entity.async_set_cover_position(position=50))
    # target = 50% of 600 = 300 pulses; delta = 200; hold = 200/71 s
    assert api.calls == [("head_up", pytest.approx(200 / 71))]


def test_head_set_position_down(head):
    entity, api, coord = head
    coord.data["head_pulse"] = 500
    run(entity.async_set_cover_position(position=0))
    assert api.calls[0][0] == "head_down"
    assert api.calls[0][1] == pytest.approx(500 / 71)


def test_head_set_position_noop_when_already_there(head):
    entity, api, coord = head
    coord.data["head_pulse"] = 300  # exactly 50%
    run(entity.async_set_cover_position(position=50))
    assert api.calls == []


def test_head_cover_advertises_stop_feature(head):
    entity, _, _ = head
    from homeassistant.components.cover import CoverEntityFeature

    assert entity._attr_supported_features & CoverEntityFeature.STOP


# ---------------------------------------------------------------------------
# Foot cover (ticks 10/deg, max travel = 450 pulses)
# ---------------------------------------------------------------------------
@pytest.fixture()
def foot():
    api = FakeApi()
    coord = FakeCoordinator({"foot_pulse": 0, "online": True})
    entity = cover.TempurPedicFootCover(coord, api, make_entry({"foot_ticks_per_degree": 10.0}))
    return entity, api, coord


def test_foot_open_close_stop_dispatch(foot):
    entity, api, _ = foot
    run(entity.async_open_cover())
    run(entity.async_close_cover())
    run(entity.async_stop_cover())
    assert api.calls == [
        ("foot_up", ACTUATOR_NUDGE_SECS),
        ("foot_down", ACTUATOR_NUDGE_SECS),
        ("foot_stop", None),
    ]


def test_foot_set_position_up(foot):
    entity, api, _ = foot
    run(entity.async_set_cover_position(position=100))
    assert api.calls == [("foot_up", pytest.approx(450 / 71))]


# ---------------------------------------------------------------------------
# Buttons, including the lumbar pair added with the fix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cls_name,expected",
    [
        ("TempurPedicLumbarUpButton", ("lumbar_up", ACTUATOR_NUDGE_SECS)),
        ("TempurPedicLumbarDownButton", ("lumbar_down", ACTUATOR_NUDGE_SECS)),
    ],
)
def test_elevation_buttons_dispatch(cls_name, expected):
    api = FakeApi()
    entity = getattr(button, cls_name)(FakeCoordinator(), api, make_entry())
    run(entity.async_press())
    assert api.calls == [expected]


def test_head_foot_nudge_buttons_removed():
    """Head/foot are cover-only controls (up/stop/down on the cover).
    Their separate nudge buttons were removed 2026-10-26 as duplicates —
    if one comes back, the device page grows a third control for the
    same motor again."""
    for cls_name in (
        "TempurPedicHeadUpButton",
        "TempurPedicHeadDownButton",
        "TempurPedicFootUpButton",
        "TempurPedicFootDownButton",
    ):
        assert not hasattr(button, cls_name), cls_name


def test_number_platform_not_enabled():
    """The number sliders duplicated the covers (same names AND the same
    unique_ids, *_head_elevation / *_foot_elevation). The platform was
    removed 2026-10-26; it must not be re-enabled."""
    from homeassistant.const import Platform

    from tempur_sleeptracker_ai.const import PLATFORMS

    assert Platform.NUMBER not in PLATFORMS
    assert Platform.COVER in PLATFORMS
    assert Platform.BUTTON in PLATFORMS


def test_platform_modules_import():
    """Every platform module must import cleanly (stub API = real HA names)."""
    import tempur_sleeptracker_ai.api  # noqa: F401
    import tempur_sleeptracker_ai.button  # noqa: F401
    import tempur_sleeptracker_ai.const  # noqa: F401
    import tempur_sleeptracker_ai.cover  # noqa: F401
    import tempur_sleeptracker_ai.entity  # noqa: F401
    import tempur_sleeptracker_ai.sensor  # noqa: F401


def test_no_duplicate_class_definitions():
    """No top-level class may be defined twice in an integration module.

    button.py once defined FlatPreset / ZeroG / StopWindDown /
    RefreshStatus twice; the second definition silently shadowed the
    first, so edits to the first copy would have done nothing at
    runtime. Runtime imports cannot see this — parse the source AST.
    Removed 2026-10-27; guard against it returning in any module.
    """
    import ast
    from collections import Counter
    from pathlib import Path

    # Locate the package from this test file's location: the stub package
    # module used in these tests has no __file__ of its own.
    pkg_dir = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "tempur_sleeptracker_ai"
    )
    for path in sorted(pkg_dir.glob("*.py")):
        tree = ast.parse(path.read_text())
        names = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        dupes = [name for name, count in Counter(names).items() if count > 1]
        assert not dupes, f"{path.name} defines classes more than once: {dupes}"
