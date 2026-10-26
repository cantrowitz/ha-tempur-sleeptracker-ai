DOMAIN = "tempur_sleeptracker_ai"
MANUFACTURER = "Tempur-Pedic"
PLATFORMS = ["select", "button", "sensor", "cover", "light"]

ENDPOINT_URL = "https://app.tsi.sleeptracker.com/actrack-client/v2/fpcsiot/processor/adjustableBaseControls"

CMD_POLL_STATUS = 500
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
