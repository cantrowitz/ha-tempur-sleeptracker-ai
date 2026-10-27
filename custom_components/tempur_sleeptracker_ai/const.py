"""Constants for the Tempur-Pedic Sleeptracker-AI integration."""
from homeassistant.const import Platform

DOMAIN = "tempur_sleeptracker_ai"
MANUFACTURER = "Tempur-Pedic"

PLATFORMS: list[Platform] = [
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
]

# API Endpoints
AUTH_URL = "https://auth.tsi.sleeptracker.com/v1/app/user/session"
ENDPOINT_BASE_CONTROLS = "https://app.tsi.sleeptracker.com/actrack-client/v2/fpcsiot/processor/adjustableBaseControls"
ENDPOINT_GET_BY_TYPE = "https://app.tsi.sleeptracker.com/actrack-client/v2/fpcsiot/processor/getByType"
ENDPOINT_GET_ACTIVE = "https://app.tsi.sleeptracker.com/actrack-client/v2/fpcsiot/processor/getActiveSleeptracker"
ENDPOINT_WEBUI = "https://app.tsi.sleeptracker.com/actrack-client/v2/actrack/webui"

# Client Identifiers
CLIENT_ID = "sleeptracker-android-tsi"
CLIENT_VERSION = "H-3.6.2"

# Bed Control Commands
CMD_PRESET_ZERO_G = 0
CMD_PRESET_FLAT = 2
CMD_HEAD_DOWN = 107
CMD_FOOT_UP = 108
CMD_HEAD_UP = 110
CMD_FOOT_DOWN = 113
CMD_TOGGLE_LIGHT = 230
CMD_POLL_STATUS = 500

# Wind Down Program Definitions
CMD_STOP_WIND_DOWN = 31
WIND_DOWN_PROGRAMS = {
    "Prepare for Sleep": {"command": 22, "mode_id": 32},
    "Destress in Bed": {"command": 21, "mode_id": 17},
}

WIND_DOWN_MODES = {
    0: "Off",
    17: "Destress in Bed",
    32: "Prepare for Sleep",
}

# Actuator timing
# The Sleeptracker base uses a press-and-hold protocol: send the movement command
# to start the motor, then send the opposing command to stop it.  These constants
# control how long the motor runs for simple open/close button presses and the
# estimated pulse rate used to derive a hold duration for set_cover_position.
ACTUATOR_NUDGE_SECS: float = 1.5        # seconds to hold for a plain open/close press
ACTUATOR_PULSES_PER_SEC: float = 200.0  # estimated motor speed (pulses/sec); tune if needed

# Configuration Keys
CONF_DEVICE_ID = "device_id"
CONF_PROCESSOR_SERIAL = "processor_serial"
CONF_BED_NAME = "bed_name"
CONF_MODEL = "model"
CONF_HEAD_TICKS = "head_ticks_per_degree"
CONF_FOOT_TICKS = "foot_ticks_per_degree"
