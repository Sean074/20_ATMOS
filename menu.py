import glob
import os

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.completion import WordCompleter

import unit_convert as u_c
import atmos
import ui
import plot_speed_alt


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


def _select_envelope():
    """Prompt the user to choose a JSON envelope file from ./instance/. Returns path or None."""
    from rich.table import Table
    from rich.panel import Panel

    instance_dir = './instance'
    json_files = sorted(glob.glob(os.path.join(instance_dir, '*.json')))
    if not json_files:
        return None

    names = [os.path.basename(f) for f in json_files]
    keys  = [str(i) for i in range(1, len(names) + 1)]

    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for k, n in zip(keys, names):
        tbl.add_row(k, n)
    tbl.add_row("0", "(no envelope — basic chart)")
    ui.console.print()
    ui.console.print(Panel(tbl, title="[bold]Speed Envelope JSON[/bold]", border_style="cyan"))

    completer = WordCompleter(['0'] + keys, sentence=True)
    while True:
        choice = pt_prompt("Select envelope file: ", completer=completer).strip()
        if choice == '0':
            return None
        if choice in keys:
            return json_files[int(choice) - 1]
        ui.console.print(f"[red]Invalid.[/red] Enter 0–{len(names)}.")


def speed_alt_ktas():
    envelope_path = _select_envelope()
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_ktas(envelope_json=envelope_path)
    ui.press_enter_to_continue()


def speed_alt_kcas():
    envelope_path = _select_envelope()
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_kcas(envelope_json=envelope_path)
    ui.press_enter_to_continue()


def speed_alt_keas():
    envelope_path = _select_envelope()
    ui.console.print("[cyan]Generating chart…[/cyan]")
    plot_speed_alt.plot_speed_alt_keas(envelope_json=envelope_path)
    ui.press_enter_to_continue()
