import glob
import os

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# File-selection helpers
# ---------------------------------------------------------------------------

def _select_file(directory, pattern, panel_title):
    """Generic file-selection prompt. Returns the chosen file path."""
    files = sorted(glob.glob(os.path.join(directory, pattern)))
    if not files:
        console.print(f"[red]No files matching '{pattern}' found in {directory}.[/red]")
        return None

    names = [os.path.basename(f) for f in files]
    keys  = [str(i) for i in range(1, len(names) + 1)]

    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for k, n in zip(keys, names):
        tbl.add_row(k, n)
    console.print()
    console.print(Panel(tbl, title=f"[bold]{panel_title}[/bold]", border_style="cyan"))

    completer = WordCompleter(keys + names, ignore_case=True, sentence=True)
    while True:
        try:
            choice = prompt(f"Select file: ", completer=completer).strip()
        except (KeyboardInterrupt, EOFError):
            raise
        if choice in keys:
            return files[int(choice) - 1]
        if choice in names:
            return files[names.index(choice)]
        console.print(f"[red]Invalid.[/red] Enter a number (1–{len(names)}) or filename.")


def select_model(data_dir):
    """Prompt the user to select an atmospheric model CSV."""
    return _select_file(os.path.join(data_dir, "models"), "*.csv", "Select Atmospheric Model")


def select_input_file(data_dir):
    """Prompt the user to select a calculation input JSON from data/inputs/."""
    return _select_file(os.path.join(data_dir, "inputs"), "*.json", "Select Input File")


def select_envelope_file(data_dir):
    """Prompt the user to optionally select a speed envelope JSON, or no envelope."""
    json_files = sorted(glob.glob(os.path.join(data_dir, "envelopes", "*.json")))
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
    console.print()
    console.print(Panel(tbl, title="[bold]Speed Envelope JSON[/bold]", border_style="cyan"))

    completer = WordCompleter(["0"] + keys, sentence=True)
    while True:
        choice = prompt("Select envelope file: ", completer=completer).strip()
        if choice == "0":
            return None
        if choice in keys:
            return json_files[int(choice) - 1]
        console.print(f"[red]Invalid.[/red] Enter 0–{len(names)}.")


def press_enter_to_continue():
    """Pause and wait for the user to press Enter before returning to the menu."""
    prompt("\nPress Enter to return to the main menu...")


# ---------------------------------------------------------------------------
# Manual numeric input helpers
# ---------------------------------------------------------------------------

class _NumberValidator(Validator):
    """prompt_toolkit inline validator that rejects non-numeric input."""
    def validate(self, document):
        text = document.text.strip()
        try:
            float(text)
        except ValueError:
            raise ValidationError(message="Please enter a number",
                                  cursor_position=len(text))


_number_validator = _NumberValidator()


def prompt_float(prompt_text):
    """Prompt for a number, validating inline before accepting."""
    result = prompt(prompt_text,
                    validator=_number_validator,
                    validate_while_typing=False)
    return float(result.strip())


def ask_unit(prompt_text, valid_choices):
    """Prompt for a unit with tab-completion, re-prompting on invalid input."""
    completer = WordCompleter(valid_choices, ignore_case=True, sentence=True)
    while True:
        choice = prompt(prompt_text, completer=completer).lower().strip()
        if choice in valid_choices:
            return choice
        console.print(f"[red]Invalid input.[/red] Choose from: {', '.join(valid_choices)}")


# ---------------------------------------------------------------------------
# Output helpers — single result
# ---------------------------------------------------------------------------

def print_atmos(point_in_sky):
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Property", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Pressure Altitude", f"{point_in_sky['h_press_ft']:.1f} ft")
    table.add_row("Static Pressure",   f"{point_in_sky['p_static_psf']:.3f} psf")
    table.add_row("Density Ratio",     f"{point_in_sky['pho_ratio']:.4f}")
    table.add_row("Air Density",       f"{point_in_sky['pho_slug_ft3']:.4e} slug/ft\u00b3")
    table.add_row("Temperature",       f"{point_in_sky['temp_degR']:.1f} \u00b0R")
    console.print(Panel(table, title="[bold cyan]Atmospheric Properties[/bold cyan]", border_style="cyan"))


def print_speed(speeds):
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Speed", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Mach",             f"{speeds['Mach']:.4f}")
    table.add_row("KTAS",             f"{speeds['ktas']:.1f} kts")
    table.add_row("KEAS",             f"{speeds['keas']:.1f} kts")
    table.add_row("KCAS",             f"{speeds['kcas']:.1f} kts")
    table.add_row("Dynamic Pressure", f"{speeds['q_c']:.3f} psf")
    console.print(Panel(table, title="[bold cyan]Speed Conversion[/bold cyan]", border_style="cyan"))


# ---------------------------------------------------------------------------
# Output helpers — batch results (multiple cases)
# ---------------------------------------------------------------------------

def print_speed_table(rows):
    """Display a list of speed conversion results as a single multi-row table.

    Each row is a dict: {alt_ft, Mach, ktas, keas, kcas, q_c}.
    """
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Alt (ft)",       style="cyan",  justify="right")
    table.add_column("Mach",                          justify="right")
    table.add_column("KTAS",                          justify="right")
    table.add_column("KEAS",                          justify="right")
    table.add_column("KCAS",                          justify="right")
    table.add_column("q_c (psf)",                     justify="right")
    for r in rows:
        table.add_row(
            f"{r['alt_ft']:,.0f}",
            f"{r['Mach']:.4f}",
            f"{r['ktas']:.1f}",
            f"{r['keas']:.1f}",
            f"{r['kcas']:.1f}",
            f"{r['q_c']:.3f}",
        )
    console.print(Panel(table, title="[bold cyan]Speed Conversion Results[/bold cyan]", border_style="cyan"))


def print_atmos_table(rows):
    """Display a list of atmospheric property results as a single multi-row table.

    Each row is a dict: {h_press_ft, p_static_psf, pho_ratio, pho_slug_ft3, temp_degR}.
    """
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Alt (ft)",         style="cyan", justify="right")
    table.add_column("P static (psf)",                 justify="right")
    table.add_column("Density ratio",                  justify="right")
    table.add_column("Density (slug/ft\u00b3)",        justify="right")
    table.add_column("Temp (\u00b0R)",                 justify="right")
    for r in rows:
        table.add_row(
            f"{r['h_press_ft']:,.1f}",
            f"{r['p_static_psf']:.3f}",
            f"{r['pho_ratio']:.4f}",
            f"{r['pho_slug_ft3']:.4e}",
            f"{r['temp_degR']:.1f}",
        )
    console.print(Panel(table, title="[bold cyan]Atmospheric Properties Results[/bold cyan]", border_style="cyan"))
