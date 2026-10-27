"""Test harness for the Tempur-Pedic Sleeptracker-AI integration.

These tests run WITHOUT a Home Assistant installation. conftest installs
minimal stub modules for the pieces of HA / aiohttp that the integration
imports, then loads the integration package from custom_components/
without executing its __init__.py (which would need a real HA core).

IMPORTANT — stub fidelity rule: stubs must mirror the REAL Home
Assistant API surface (same attribute names), never the names the code
under test happens to use. A stub that invents attributes to match the
code hides exactly the bugs these tests exist to catch — e.g. the
2026-10-26 incident where cover.py referenced
CoverEntityFeature.STOP_COVER (does not exist in HA; the real member is
CoverEntityFeature.STOP) and the cover platform failed to import in HA,
while a stub with an invented STOP_COVER member would have passed it.
"""
import enum
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "tempur_sleeptracker_ai"


def _module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


# ---------------------------------------------------------------------------
# aiohttp stub (api.py only touches these names)
# ---------------------------------------------------------------------------
class _ClientResponseError(Exception):
    def __init__(self, *args, status=0, **kwargs):
        super().__init__(*args)
        self.status = status


class _ClientError(Exception):
    pass


_module(
    "aiohttp",
    ClientSession=object,
    ClientError=_ClientError,
    ClientResponseError=_ClientResponseError,
)

# ---------------------------------------------------------------------------
# homeassistant stubs — attribute names mirror real HA
# ---------------------------------------------------------------------------
class Platform(str, enum.Enum):
    COVER = "cover"
    LIGHT = "light"
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    SELECT = "select"
    BUTTON = "button"
    NUMBER = "number"


class EntityCategory(str, enum.Enum):
    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


_module("homeassistant")
_module("homeassistant.const", Platform=Platform, EntityCategory=EntityCategory)
_module("homeassistant.config_entries", ConfigEntry=type("ConfigEntry", (), {}))
_module("homeassistant.core", HomeAssistant=type("HomeAssistant", (), {}))


class CoverEntityFeature(enum.IntFlag):
    """Mirror of homeassistant.components.cover.CoverEntityFeature."""

    OPEN = 1
    CLOSE = 2
    SET_POSITION = 4
    STOP = 8
    OPEN_TILT = 16
    CLOSE_TILT = 32
    STOP_TILT = 64
    SET_TILT_POSITION = 128


_module("homeassistant.components")
_module(
    "homeassistant.components.cover",
    CoverEntity=type("CoverEntity", (), {}),
    CoverEntityFeature=CoverEntityFeature,
)
_module(
    "homeassistant.components.button",
    ButtonEntity=type("ButtonEntity", (), {}),
)


class CoordinatorEntity:
    """Mirror of the parts of CoordinatorEntity the base entity relies on."""

    available = True

    def __init__(self, coordinator, context=None):
        self.coordinator = coordinator


def _device_info(**kwargs):
    return kwargs


_module("homeassistant.helpers")
_module(
    "homeassistant.helpers.device_registry",
    CONNECTION_NETWORK_MAC="mac",
    DeviceInfo=_device_info,
)
_module(
    "homeassistant.helpers.update_coordinator",
    CoordinatorEntity=CoordinatorEntity,
)
_module(
    "homeassistant.helpers.entity_platform",
    AddEntitiesCallback=object,
)

# ---------------------------------------------------------------------------
# Load the integration package without running its __init__.py
# ---------------------------------------------------------------------------
_pkg = types.ModuleType("tempur_sleeptracker_ai")
_pkg.__path__ = [str(PKG_DIR)]
sys.modules["tempur_sleeptracker_ai"] = _pkg


# ---------------------------------------------------------------------------
# Shared fakes
# ---------------------------------------------------------------------------
class FakeCoordinator:
    """Stand-in for the DataUpdateCoordinator."""

    def __init__(self, data=None):
        self.data = data if data is not None else {"online": True}
        self.refresh_calls = 0

    async def async_request_refresh(self):
        self.refresh_calls += 1


class FakeApi:
    """Records every actuator call a platform entity makes."""

    def __init__(self):
        self.calls = []

    async def async_head_up(self, hold_secs=None):
        self.calls.append(("head_up", hold_secs))

    async def async_head_down(self, hold_secs=None):
        self.calls.append(("head_down", hold_secs))

    async def async_head_stop(self):
        self.calls.append(("head_stop", None))

    async def async_foot_up(self, hold_secs=None):
        self.calls.append(("foot_up", hold_secs))

    async def async_foot_down(self, hold_secs=None):
        self.calls.append(("foot_down", hold_secs))

    async def async_foot_stop(self):
        self.calls.append(("foot_stop", None))

    async def async_lumbar_up(self, hold_secs=None):
        self.calls.append(("lumbar_up", hold_secs))

    async def async_lumbar_down(self, hold_secs=None):
        self.calls.append(("lumbar_down", hold_secs))


def make_entry(extra_data=None):
    """A minimal config-entry stand-in (entity code only reads .data/.entry_id)."""
    data = {"processor_serial": "TESTSERIAL", "device_info": {}}
    if extra_data:
        data.update(extra_data)
    return types.SimpleNamespace(data=data, entry_id="test-entry-id")
