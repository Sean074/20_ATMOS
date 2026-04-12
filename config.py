"""Thin loader for config/defaults.json.  Import APP_CONFIG from here."""
import json
import pathlib

_CONFIG_PATH = pathlib.Path(__file__).parent / "config" / "defaults.json"

# Hardcoded fallback used only if defaults.json is missing.
_FALLBACK = {
    "chart_defaults": {
        "alt_min_ft": 0, "alt_max_ft": 46000,
        "ktas": {"x_min": 80, "x_max": 600},
        "kcas": {"x_min": 80, "x_max": 500},
        "keas": {"x_min": 80, "x_max": 500},
        "mach_grid":  [0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.80, 0.84, 0.88, 0.92],
        "kcas_grid":  [100, 150, 200, 250, 300, 350, 400],
        "keas_grid":  [100, 150, 200, 250, 300, 350, 400],
        "ktas_grid":  [100, 150, 200, 250, 300, 350, 400, 450, 500],
        "n_altitude_points": 300,
    },
    "solver": {
        "intersection_tolerance_ft":    1.0,
        "intersection_max_iterations":  60,
        "intersection_early_exit_keas": 0.05,
        "vcas_super_initial_delta_kts": 10.0,
        "vcas_super_error_percent":     0.001,
        "mach_super_initial_delta":     0.1,
        "mach_super_error_percent":     0.001,
    },
    "instance_dir": "./instance",
    "log_file":     "AtmosLog.txt",
}

try:
    with open(_CONFIG_PATH) as _f:
        APP_CONFIG = json.load(_f)
except FileNotFoundError:
    print(f"[ATMOS] Warning: {_CONFIG_PATH} not found — using built-in defaults.")
    APP_CONFIG = _FALLBACK
