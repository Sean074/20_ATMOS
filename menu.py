import numpy as np

import unit_convert as u_c
import atmos
import ui


# ---------------------------------------------------------------------------
# Private input helpers
# ---------------------------------------------------------------------------

def _ask_alt():
    """Prompt for a pressure altitude and return the value in feet."""
    value = ui.prompt_float("Input pressure altitude: ")
    unit = ui.ask_unit("Input altitude units (ft/m): ", ["ft", "m"])
    return value * u_c.M_FT if unit == "m" else value


def _ask_speed(label):
    """Prompt for an airspeed and return the value in knots."""
    value = ui.prompt_float(f"Input {label}: ")
    unit = ui.ask_unit("Input speed units (kts/m/s): ", ["kts", "m/s"])
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
    point_in_sky = atmos.get_atmos_prop_alt(h_press_ft=h_press_ft)
    return point_in_sky['p_static_psf']


# ---------------------------------------------------------------------------
# Menu functions
# ---------------------------------------------------------------------------

def air_data_alt():
    h_press_ft = _ask_alt()
    point_in_sky = atmos.get_atmos_prop_alt(h_press_ft=h_press_ft)
    if point_in_sky != "ERROR":
        ui.print_atmos(point_in_sky)
    ui.press_enter_to_continue()


def air_data_pres():
    press_user = ui.prompt_float("Input pressure: ")
    press_unit = ui.ask_unit(
        "Input units (psf/psi/pa/atm/bar/ft/m): ",
        ["psf", "psi", "pa", "atm", "bar", "ft", "m"],
    )
    press_psf = _pressure_to_psf(press_user, press_unit)
    point_in_sky = atmos.get_atmos_prop_pres(p_press_psf=press_psf)
    if point_in_sky != "ERROR":
        ui.print_atmos(point_in_sky)
    ui.press_enter_to_continue()


def alt_mach():
    h_press_ft = _ask_alt()
    mach = ui.prompt_float("Input Mach: ")
    speeds = atmos.mach_alt(mach, h_press_ft)
    ui.print_speed(speeds)
    ui.press_enter_to_continue()


def alt_true():
    h_press_ft = _ask_alt()
    ktas = _ask_speed("True Air Speed (TAS)")
    speeds = atmos.tas_alt(ktas, h_press_ft)
    ui.print_speed(speeds)
    ui.press_enter_to_continue()


def alt_cal():
    h_press_ft = _ask_alt()
    kcas = _ask_speed("Calibrated Air Speed (CAS)")
    speeds = atmos.cas_alt(kcas, h_press_ft)
    ui.print_speed(speeds)
    ui.press_enter_to_continue()


def alt_equiv():
    h_press_ft = _ask_alt()
    keas = _ask_speed("Equivalent Air Speed (EAS)")
    speeds = atmos.eas_alt(keas, h_press_ft)
    ui.print_speed(speeds)
    ui.press_enter_to_continue()


def speed_alt_ktas():
    speed_min = ui.prompt_float("Speed range minimum (knots): ")
    speed_max = ui.prompt_float("Speed range maximum (knots): ")
    speed_inc = (speed_max - speed_min) / 300
    ktas_array = list(np.arange(speed_min, speed_max, speed_inc))

    alt_min = ui.prompt_float("Altitude range minimum (ft): ")
    alt_max = ui.prompt_float("Altitude range maximum (ft): ")
    alt_inc = (alt_max - alt_min) / 300
    alt_array = list(np.arange(alt_min, alt_max, alt_inc))

    ui.console.print(ktas_array)
    ui.console.print(alt_array)


def speed_alt_kcas():
    pass


def speed_alt_keas():
    pass
