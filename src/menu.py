import json

import atmos
import ui
import logger
import plot_speed_alt
import unit_convert as u_c
from config import APP_CONFIG

_INSTANCE_DIR = APP_CONFIG["instance_dir"]

# Maps speed_type field in input JSON → atmos calculation function
_SPEED_CALC = {
    "mach": atmos.mach_alt,
    "ktas": atmos.tas_alt,
    "kcas": atmos.cas_alt,
    "keas": atmos.eas_alt,
}


# ---------------------------------------------------------------------------
# Manual input helpers
# ---------------------------------------------------------------------------

def _ask_alt():
    """Prompt for a pressure altitude and return the value in feet."""
    value = ui.prompt_float("Input pressure altitude: ")
    unit  = ui.ask_unit("Input altitude units (ft/m): ", ["ft", "m"])
    return value * u_c.M_FT if unit == "m" else value


def _ask_speed(label):
    """Prompt for an airspeed and return the value in knots."""
    value = ui.prompt_float(f"Input {label}: ")
    unit  = ui.ask_unit("Input speed units (kts/m/s): ", ["kts", "m/s"])
    return value * u_c.MS_KTS if unit == "m/s" else value


def _pressure_to_psf(value, unit):
    """Convert a pressure value (or altitude) to psf."""
    conversions = {
        "psf": 1.0,
        "psi": u_c.PSI_PSF,
        "pa":  u_c.PA_PSF,
        "atm": u_c.ATM_PSF,
        "bar": u_c.BAR_PSF,
    }
    if unit in conversions:
        return value * conversions[unit]
    # altitude-based: look up static pressure at that altitude
    h_press_ft = value * u_c.M_FT if unit == "m" else value
    return atmos.get_atmos_prop_alt(h_press_ft=h_press_ft)['p_static_psf']


# ---------------------------------------------------------------------------
# JSON batch runners
# ---------------------------------------------------------------------------

def _run_speed_cases():
    """Select an input JSON and run speed conversions for all cases in it."""
    path = ui.select_input_file(_INSTANCE_DIR)
    if path is None:
        return

    with open(path) as f:
        data = json.load(f)

    cases = data.get("cases", [])
    if not cases:
        ui.console.print("[yellow]No cases found in file.[/yellow]")
        return

    results = []
    for case in cases:
        alt_ft      = float(case["alt_ft"])
        speed_type  = case["speed_type"].lower()
        speed_value = float(case["speed_value"])

        calc_fn = _SPEED_CALC.get(speed_type)
        if calc_fn is None:
            ui.console.print(f"[red]Unknown speed_type '{speed_type}' — skipping.[/red]")
            continue

        try:
            result = calc_fn(speed_value, alt_ft)
        except atmos.AtmosRangeError as e:
            ui.console.print(f"[red]Error for alt={alt_ft} ft: {e}[/red]")
            continue

        logger.log_speed_result(alt_ft, result)
        results.append({"alt_ft": alt_ft, **result})

    if results:
        ui.print_speed_table(results)


def _run_atmos_cases():
    """Select an input JSON and retrieve atmospheric properties for all cases in it."""
    path = ui.select_input_file(_INSTANCE_DIR)
    if path is None:
        return

    with open(path) as f:
        data = json.load(f)

    cases = data.get("cases", [])
    if not cases:
        ui.console.print("[yellow]No cases found in file.[/yellow]")
        return

    results = []
    for case in cases:
        input_type = case["input_type"].lower()
        try:
            if input_type == "altitude":
                result = atmos.get_atmos_prop_alt(float(case["value_ft"]))
            elif input_type == "pressure":
                result = atmos.get_atmos_prop_pres(float(case["value_psf"]))
            else:
                ui.console.print(f"[red]Unknown input_type '{input_type}' — skipping.[/red]")
                continue
        except atmos.AtmosRangeError as e:
            ui.console.print(f"[red]{e}[/red]")
            continue

        logger.log_atmos_result(result)
        results.append(result)

    if results:
        ui.print_atmos_table(results)


# ---------------------------------------------------------------------------
# Menu handlers — manual input
# ---------------------------------------------------------------------------

def air_data_alt():
    h_press_ft = _ask_alt()
    try:
        result = atmos.get_atmos_prop_alt(h_press_ft=h_press_ft)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_atmos_result(result)
        ui.print_atmos(result)
    ui.press_enter_to_continue()


def air_data_pres():
    press_user = ui.prompt_float("Input pressure: ")
    press_unit = ui.ask_unit(
        "Input units (psf/psi/pa/atm/bar/ft/m): ",
        ["psf", "psi", "pa", "atm", "bar", "ft", "m"],
    )
    press_psf = _pressure_to_psf(press_user, press_unit)
    try:
        result = atmos.get_atmos_prop_pres(p_press_psf=press_psf)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_atmos_result(result)
        ui.print_atmos(result)
    ui.press_enter_to_continue()


def alt_mach():
    h_press_ft = _ask_alt()
    mach = ui.prompt_float("Input Mach: ")
    try:
        result = atmos.mach_alt(mach, h_press_ft)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_speed_result(h_press_ft, result)
        ui.print_speed(result)
    ui.press_enter_to_continue()


def alt_true():
    h_press_ft = _ask_alt()
    ktas = _ask_speed("True Air Speed (TAS)")
    try:
        result = atmos.tas_alt(ktas, h_press_ft)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_speed_result(h_press_ft, result)
        ui.print_speed(result)
    ui.press_enter_to_continue()


def alt_cal():
    h_press_ft = _ask_alt()
    kcas = _ask_speed("Calibrated Air Speed (CAS)")
    try:
        result = atmos.cas_alt(kcas, h_press_ft)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_speed_result(h_press_ft, result)
        ui.print_speed(result)
    ui.press_enter_to_continue()


def alt_equiv():
    h_press_ft = _ask_alt()
    keas = _ask_speed("Equivalent Air Speed (EAS)")
    try:
        result = atmos.eas_alt(keas, h_press_ft)
    except atmos.AtmosRangeError as e:
        ui.console.print(f"[red]{e}[/red]")
    else:
        logger.log_speed_result(h_press_ft, result)
        ui.print_speed(result)
    ui.press_enter_to_continue()


# ---------------------------------------------------------------------------
# Menu handlers — JSON file input
# ---------------------------------------------------------------------------

def air_data_from_file():
    _run_atmos_cases()
    ui.press_enter_to_continue()


def speed_from_file():
    _run_speed_cases()
    ui.press_enter_to_continue()


# ---------------------------------------------------------------------------
# Menu handlers — charts
# ---------------------------------------------------------------------------

def speed_alt_ktas():
    envelope_path = ui.select_envelope_file(_INSTANCE_DIR)
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_ktas(envelope_json=envelope_path)
    ui.press_enter_to_continue()


def speed_alt_kcas():
    envelope_path = ui.select_envelope_file(_INSTANCE_DIR)
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_kcas(envelope_json=envelope_path)
    ui.press_enter_to_continue()


def speed_alt_keas():
    envelope_path = ui.select_envelope_file(_INSTANCE_DIR)
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_keas(envelope_json=envelope_path)
    ui.press_enter_to_continue()
