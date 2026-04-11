from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.panel import Panel

import menu
import ui

_MENU_DISPLAY = """\
[bold cyan]Atmospheric Properties[/bold cyan]
  [cyan]1.1[/cyan]  Given pressure altitude
  [cyan]1.2[/cyan]  Given static pressure

[bold cyan]Speed Conversion[/bold cyan]  [dim](subsonic or supersonic)[/dim]
  [cyan]2.1[/cyan]  Alt and Mach
  [cyan]2.2[/cyan]  Alt and True Airspeed
  [cyan]2.3[/cyan]  Alt and Calibrated Airspeed
  [cyan]2.4[/cyan]  Alt and Equivalent Airspeed

[bold cyan]Speed-Altitude Charts[/bold cyan]  [dim](in development)[/dim]
  [cyan]3.1[/cyan]  KTAS vs Alt
  [cyan]3.2[/cyan]  KCAS vs Alt
  [cyan]3.3[/cyan]  KEAS vs Alt

  [cyan]q[/cyan]   Quit\
"""

MENU_OPTIONS = {
    "1.1": menu.air_data_alt,
    "1.2": menu.air_data_pres,
    "2.1": menu.alt_mach,
    "2.2": menu.alt_true,
    "2.3": menu.alt_cal,
    "2.4": menu.alt_equiv,
    "3.1": menu.speed_alt_ktas,
    "3.2": menu.speed_alt_kcas,
    "3.3": menu.speed_alt_keas,
}

_completer = WordCompleter(list(MENU_OPTIONS.keys()) + ["q"], sentence=True)


def menu_func():
    while True:
        ui.console.print()
        ui.console.print(Panel(_MENU_DISPLAY, title="[bold]ATMOS[/bold]", border_style="cyan"))

        try:
            selection = prompt("Selection: ", completer=_completer).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if selection == "q":
            break

        if selection in MENU_OPTIONS:
            try:
                MENU_OPTIONS[selection]()
            except (KeyboardInterrupt, EOFError):
                ui.console.print("\n[yellow]Cancelled.[/yellow]")
        else:
            ui.console.print("[red]Invalid selection — use tab to see options.[/red]")

    ui.console.print("\n[cyan]Hope this was useful. Bye now, see you soon.[/cyan]\n")


# TODO open a new log file
menu_func()
