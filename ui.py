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
# Input helpers
# ---------------------------------------------------------------------------

class _NumberValidator(Validator):
    def validate(self, document):
        text = document.text.strip()
        try:
            float(text)
        except ValueError:
            raise ValidationError(
                message="Please enter a number",
                cursor_position=len(text),
            )


def prompt_float(prompt_text):
    """Prompt for a number, validating inline before accepting."""
    result = prompt(prompt_text, validator=_NumberValidator(), validate_while_typing=False)
    return float(result.strip())


def press_enter_to_continue():
    """Pause and wait for the user to press Enter before returning to the menu."""
    prompt("\nPress Enter to return to the main menu...")


def select_model(instance_dir):
    """Prompt the user to select an atmospheric model CSV from instance_dir."""
    csv_files = sorted(glob.glob(os.path.join(instance_dir, "*.csv")))
    if not csv_files:
        console.print("[red]No CSV model files found in instance directory.[/red]")
        raise SystemExit(1)

    names = [os.path.basename(f) for f in csv_files]
    keys = [str(i) for i in range(1, len(names) + 1)]

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Model")
    for key, name in zip(keys, names):
        table.add_row(key, name)
    console.print()
    console.print(Panel(table, title="[bold]Select Atmospheric Model[/bold]", border_style="cyan"))

    completer = WordCompleter(keys + names, ignore_case=True, sentence=True)
    while True:
        try:
            choice = prompt("Model: ", completer=completer).strip()
        except (KeyboardInterrupt, EOFError):
            raise
        if choice in keys:
            return csv_files[int(choice) - 1]
        if choice in names:
            return csv_files[names.index(choice)]
        console.print(f"[red]Invalid selection.[/red] Enter a number (1\u2013{len(names)}) or filename.")


def ask_unit(prompt_text, valid_choices):
    """Prompt for a unit with tab-completion, re-prompting on invalid input."""
    completer = WordCompleter(valid_choices, ignore_case=True, sentence=True)
    while True:
        choice = prompt(prompt_text, completer=completer).lower().strip()
        if choice in valid_choices:
            return choice
        console.print(f"[red]Invalid input.[/red] Choose from: {', '.join(valid_choices)}")


# ---------------------------------------------------------------------------
# Output helpers
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
    table.add_row("Mach",              f"{speeds['Mach']:.4f}")
    table.add_row("KTAS",              f"{speeds['ktas']:.1f} kts")
    table.add_row("KEAS",              f"{speeds['keas']:.1f} kts")
    table.add_row("KCAS",              f"{speeds['kcas']:.1f} kts")
    table.add_row("Dynamic Pressure",  f"{speeds['q_c']:.3f} psf")
    console.print(Panel(table, title="[bold cyan]Speed Conversion[/bold cyan]", border_style="cyan"))
