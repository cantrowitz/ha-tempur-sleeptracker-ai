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
  - **Head Elevation** (`cover.<bed_name>_head_elevation`): Scaled via calibrated ticks per degree (`234.0 ticks/deg`).
  - **Foot Elevation** (`cover.<bed_name>_foot_elevation`): Scaled via calibrated ticks per degree (`306.0 ticks/deg`).
- **Underbed Lighting (Light)**:
  - **Underbed Light** (`light.<bed_name>_underbed_light`): Toggle underbed panel and safety lighting on/off.
- **Wind Down Programs (Select & Button)**:
  - **Wind Down Program** (`select.<bed_name>_wind_down_program`): Switch between *Prepare for Sleep*, *Destress in Bed*, or *Off*.
  - **Stop Wind Down** (`button.<bed_name>_stop_wind_down`): Immediately stop active wind down routine.
- **Telemetry & Diagnostics (Sensors)**:
  - **Wind Down Status**: Current operational mode of the base.
  - **Massage Frequency**: Real-time vibration frequency in Hz.
  - **Massage Timer**: Remaining minutes on massage cycle.
  - **Head & Foot Motor Pulses**: Live diagnostic telemetry on motor encoders.
  - **Refresh Status Button**: Force immediate telemetry refresh.

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

1. Download the latest release from the [Releases](https://github.com/cantrowitz/ha-tempur-sleeptracker-ai/releases) page.
2. Copy the `custom_components/tempur_sleeptracker_ai` directory to your Home Assistant `<config_dir>/custom_components/` directory:
   ```text
   config/
   └── custom_components/
       └── tempur_sleeptracker_ai/
           ├── __init__.py
           ├── api.py
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
