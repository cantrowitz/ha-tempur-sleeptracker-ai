"""UnitOfRatio import fallback: HA < 2026.11 has no UnitOfRatio in
homeassistant.const, only the older CONCENTRATION_PARTS_PER_* constants.

Simulates old HA by removing UnitOfRatio from the stub const module,
reloading the sensor platform, and asserting the CO2/VOC sensors still
report ppm/ppb via the fallback shim — then restores the stub and
reloads again so later tests see the normal module.
"""

import importlib
import sys

import tempur_sleeptracker_ai.sensor as sensor_mod


def test_concentration_units_fall_back_on_old_ha():
    const_mod = sys.modules["homeassistant.const"]
    saved = getattr(const_mod, "UnitOfRatio", None)
    assert saved is not None, "stub const module lost UnitOfRatio"
    try:
        delattr(const_mod, "UnitOfRatio")
        const_mod.CONCENTRATION_PARTS_PER_MILLION = "ppm"
        const_mod.CONCENTRATION_PARTS_PER_BILLION = "ppb"
        importlib.reload(sensor_mod)
        assert (
            sensor_mod.TempurPedicCo2Sensor._attr_native_unit_of_measurement
            == "ppm"
        )
        assert (
            sensor_mod.TempurPedicVocSensor._attr_native_unit_of_measurement
            == "ppb"
        )
    finally:
        const_mod.UnitOfRatio = saved
        delattr(const_mod, "CONCENTRATION_PARTS_PER_MILLION")
        delattr(const_mod, "CONCENTRATION_PARTS_PER_BILLION")
        importlib.reload(sensor_mod)
    # Restored module uses UnitOfRatio again.
    assert (
        sensor_mod.TempurPedicCo2Sensor._attr_native_unit_of_measurement
        == "ppm"
    )
    assert (
        sensor_mod.TempurPedicVocSensor._attr_native_unit_of_measurement
        == "ppb"
    )
