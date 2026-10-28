# Tempur-Pedic Sleeptracker-AI for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/cantrowitz/ha-tempur-sleeptracker-ai)](https://github.com/cantrowitz/ha-tempur-sleeptracker-ai/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A native Home Assistant custom component for **Tempur-Pedic Smart Bases** powered by **Sleeptracker-AI®** (Fullpower Technologies).

Connects directly to the Sleeptracker cloud using your standard app credentials (email and password)—no extra hardware, MQTT broker, or Bluetooth bridges required.

---

## Features

- **Native UI Config Flow**: Log in directly with your Sleeptracker-AI credentials from *Settings > Devices & Services*.
- **Automatic Smart Bed Discovery**: Automatically detects your bed model (e.g., *2023 Ergo Pro Smart*, *STS60*), serial numbers, and foundation hardware. Supports multi-bed selection if multiple bases exist on your account.
- **Elevation Articulation (Covers)**:
  - **Head Elevation** (`cover.<bed_name>_head_elevation`): Position control, scaled via calibrated ticks per degree (`234.0 ticks/deg`). Open / close / stop.
  - **Foot Elevation** (`cover.<bed_name>_foot_elevation`): Position control, scaled via calibrated ticks per degree (`306.0 ticks/deg`). Open / close / stop.
  - **Lumbar Support** (`cover.<bed_name>_lumbar_support`): Open / close / stop (position reporting is not available for lumbar).
- **Position Presets (Buttons)**: Flat, Zero-G, TV in Bed, Quiet Mode (anti-snore), Favourite 1, Favourite 2.
- **Wave Form Massage (Buttons & Sensors)**:
  - Head and foot zone strength step buttons (cycle: off → 4 → 6 → 8 → off).
  - Wave Form frequency buttons: 28 Hz (low) and 40 Hz (high), plus a pattern-cycle button (patterns 1–3).
  - Per-zone massage strength sensors, massage frequency and remaining-time sensors, per-zone massage on/off binary sensors.
- **Underbed Lighting (Light)**:
  - **Underbed Light** (`light.<bed_name>_underbed_light`): Toggle underbed panel and safety lighting on/off.
- **Wind Down Programs (Select & Button)**:
  - **Wind Down Program** (`select.<bed_name>_wind_down_program`): Switch between *Prepare for Sleep*, *Destress in Bed*, or *Off*.
  - **Stop Wind Down** (`button.<bed_name>_stop_wind_down`): Immediately stop active wind down routine.
- **Sleep & Environment (Sensors)**:
  - Sleep score, total / deep / REM sleep duration, sleep efficiency, snore duration.
  - Resting and average heart rate, resting and average respiration rate.
  - Room temperature, humidity, CO₂, VOC and air quality index (bases with environmental sensors).
- **Telemetry & Diagnostics (Sensors)**:
  - **Wind Down Status**: Current operational mode of the base.
  - **Head, Foot & Lumbar Motor Pulses**: Live diagnostic telemetry on motor encoders.
  - Sleep recording, online and busy binary sensors.
  - **Refresh Status Button**: Force immediate telemetry refresh.

---

## Compatibility & Limitations

- **Developed and tested with a TEMPUR-Ergo® ProSmart™ base** (Sleeptracker-AI). Other Sleeptracker-AI powered bases (Ergo Smart Base, Ergo Extend, and Sleeptracker-AI equipped models from other brands) are expected to work, but have not been tested yet — issue reports with your model and a debug log are very welcome.
- **Cloud polling**: the integration talks to the Sleeptracker cloud (the same backend as the Sleeptracker-AI app) using your app account credentials. There is no local control; if the cloud or your internet connection is down, control is unavailable.
- **Hardware-dependent features**: entities are provided for the features Sleeptracker-AI bases commonly expose. A base without a given motor or sensor (e.g. no lumbar motor, no massage, no environmental sensors) may show entities that never update — the status feed is parsed for your base's reported capabilities, and narrowing entity creation per model is ongoing work.
- Position percentages for head and foot are calibrated for the tested base; other models may need different ticks-per-degree values.
- Not all Sleeptracker app features are covered (e.g. alarm configuration and SoundScape/music mode are not currently supported).

---

## Installation

### Method 1: Via HACS (Recommended)

1. Open **HACS** in your Home Assistant dashboard.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Enter the repository URL:
   ```text
   https://github.com/cantrowitz/ha-tempur-sleeptracker-ai
   ```
4. Select category **Integration** and click **Add**.
5. Find **Tempur-Pedic Sleeptracker-AI** in HACS and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/cantrowitz/ha-tempur-sleeptracker-ai/releases) page and unzip it (release zips contain the integration files at the top level).
2. Copy the files into a `tempur_sleeptracker_ai` directory under your Home Assistant `<config_dir>/custom_components/` directory:
   ```text
   config/
   └── custom_components/
       └── tempur_sleeptracker_ai/
           ├── __init__.py
           ├── brand/
           │   ├── icon.png
           │   └── icon@2x.png
           ├── api.py
           ├── binary_sensor.py
           ├── button.py
           ├── config_flow.py
           ├── const.py
           ├── cover.py
           ├── entity.py
           ├── light.py
           ├── manifest.json
           ├── select.py
           ├── sensor.py
           └── strings.json
   ```
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom-right corner.
3. Search for **Tempur-Pedic Sleeptracker-AI**.
4. Enter your Sleeptracker-AI **Email** and **Password**.
5. If you have more than one bed or side registered, choose the bed you want to add.
6. Click **Submit**!

---

## Discovering Entities & Telemetry (Debug Logging)

To see the complete raw JSON snapshots and sensor feeds returned by your Sleeptracker processor, enable debug logging in your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tempur_sleeptracker_ai: debug
```

Check your logs under **Settings** > **System** > **Logs** to view the full telemetry tree.

---

## Disclaimer

This custom integration is not affiliated with, endorsed by, or associated with Tempur-Pedic or Fullpower Technologies. All product names, logos, and brands are property of their respective owners.
