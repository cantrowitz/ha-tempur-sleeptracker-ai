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
# START and STOP are different commands — a STOP is NOT the opposite
# direction. Each actuator has two start commands (up/down) and ONE stop
# command that halts it regardless of which way it is moving:
#
#   Actuator   Up (start)   Down (start)   Stop
#   --------   ----------   ------------   ----
#   Head          110           111        107
#   Foot          112           113        108
#   Lumbar        114           115        106
#
# Verified 2026-10-26. The previous code conflated stop with down
# (CMD_HEAD_DOWN was 107 and CMD_FOOT_DOWN was 108 — both are actually
# the stop commands), so every "down" movement started with a stop,
# did nothing, and then ended by sending the UP start command.
CMD_HEAD_UP   = 110
CMD_HEAD_DOWN = 111
CMD_HEAD_STOP = 107

CMD_FOOT_UP   = 112
CMD_FOOT_DOWN = 113
CMD_FOOT_STOP = 108

CMD_LUMBAR_UP   = 114
CMD_LUMBAR_DOWN = 115
CMD_LUMBAR_STOP = 106

# Other commands
CMD_PRESET_ZERO_G  = 0
CMD_PRESET_FLAT    = 2
CMD_TOGGLE_LIGHT   = 230
CMD_POLL_STATUS    = 500

# Wind Down Program Definitions
CMD_STOP_WIND_DOWN = 31
WIND_DOWN_PROGRAMS = {
    "Prepare for Sleep": {"command": 22, "mode_id": 32},
    "Destress in Bed":   {"command": 21, "mode_id": 17},
}

WIND_DOWN_MODES = {
    0:  "Off",
    17: "Destress in Bed",
    32: "Prepare for Sleep",
}

# Actuator timing
# The Sleeptracker base uses a press-and-hold protocol: send the movement command
# to start the motor, then send that actuator's dedicated stop command to halt it.
ACTUATOR_NUDGE_SECS: float = 1.5        # seconds to hold for a plain open/close press
# Calibrated 2026-10-26 from an observed head move: 494 -> 565 pulses
# (71 pulses) in a ~1 second window, i.e. ~71 pulses/sec — not the
# 200/sec originally estimated, which made set_position holds ~2.8x
# too short. Foot rate is assumed the same until a foot move is
# measured the same way. If the observed window was actually the full
# 1.5s nudge, the true rate is ~47/sec and this needs revisiting.
ACTUATOR_PULSES_PER_SEC: float = 71.0

# Configuration Keys
CONF_DEVICE_ID        = "device_id"
CONF_PROCESSOR_SERIAL = "processor_serial"
CONF_BED_NAME         = "bed_name"
CONF_MODEL            = "model"
CONF_HEAD_TICKS       = "head_ticks_per_degree"
CONF_FOOT_TICKS       = "foot_ticks_per_degree"

