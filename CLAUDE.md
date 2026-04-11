# ATMOS — Atmospheric Properties Calculator

A Terminal User Interface (TUI) for computing standard atmosphere properties and airspeed conversions. Intended for aerospace/flight test use.

## Running the Program

```bash
python main.py
```

Must be run from the project root (the directory containing `main.py`), because `atmos.py` loads data from the relative path `./instance/standard_atmos.csv`.

### Environment

Python 3.9 virtualenv at `.venv/`. Activate before running:

```bash
source .venv/bin/activate
```

Key dependencies: `pandas`, `numpy`, `prompt_toolkit`, `rich`.

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point. Renders menu with Rich, dispatches selections via prompt_toolkit. |
| `menu.py` | One function per menu option. Calls `ui` for input/output, calls `atmos.py` for math. |
| `atmos.py` | Core atmosphere and airspeed math only — no print calls. Interpolates from `instance/standard_atmos.csv`. |
| `ui.py` | All user-facing I/O: `prompt_float()`, `ask_unit()`, `print_atmos()`, `print_speed()`. Uses `prompt_toolkit` for input and `Rich` for output. |
| `unit_convert.py` | Unit conversion constants (imperial base units internally). |
| `logger.py` | Stub — not yet implemented. |
| `plot_speed_alt.py` | Stub — speed/altitude chart generation, not yet implemented. |
| `scrap.py` | Working scratch script for speed-altitude chart development (not part of the TUI). |
| `atmos.ipynb` | Jupyter notebook companion for exploration. |
| `instance/standard_atmos.csv` | Tabular standard atmosphere data (source of truth for interpolation). |
| `AtmosLog.txt` | Output log file written by the program. |

## Internal Units

All calculations use imperial units internally:

- Altitude: **feet (ft)**
- Pressure: **pounds per square foot (psf)**
- Density: **slug/ft³**
- Temperature: **degrees Rankine (°R)**
- Speed: **knots (kts)**

User input in metric (m, m/s, Pa, etc.) is converted to these base units before any calculation.

## TUI Layer (prompt_toolkit + Rich)

The UI layer lives entirely in `ui.py`. `atmos.py` contains no `print()` calls.

- **`ui.prompt_float(prompt_text)`** — prompts for a number with inline validation via `prompt_toolkit`; re-prompts on non-numeric input without crashing.
- **`ui.ask_unit(prompt_text, valid_choices)`** — prompts for a unit string with tab-completion via `prompt_toolkit`'s `WordCompleter`; re-prompts on invalid input.
- **`ui.print_atmos(point_in_sky)`** — renders atmospheric properties in a Rich `Panel`/`Table`.
- **`ui.print_speed(speeds)`** — renders speed conversion results in a Rich `Panel`/`Table`.
- **`ui.console`** — module-level `rich.console.Console` instance; use `ui.console.print()` anywhere Rich markup is needed outside `ui.py`.

In `main.py`, the menu is rendered with Rich and the selection prompt uses `prompt_toolkit` with a `WordCompleter` over the valid menu keys. `KeyboardInterrupt` (Ctrl+C) and `EOFError` (Ctrl+D) are caught at both the menu level and within each menu function, so the user can abort an in-progress calculation gracefully.

## Key Physics / Implementation Notes

- Atmospheric properties (pressure, density, temperature) are looked up by **linear interpolation** from the CSV table, not from closed-form equations.
- Speed conversions handle both **subsonic and supersonic** regimes:
  - Subsonic dynamic pressure: `q = p_static * ((1 + 0.2*M²)^(7/2) - 1)`
  - Supersonic dynamic pressure uses the Rayleigh Pitot formula.
  - `vcas_super()` and `mach_super()` in `atmos.py` use an iterative marching/bracketing solver for the supersonic CAS and Mach back-calculations.
- Sea-level speed of sound reference: `a_0 = 661.4745 kts`
- Sea-level pressure reference: read from CSV at `Hgeo_ft == 0`
- `GAMMA = 1.4` (ratio of specific heats for air) — currently defined inside each function (TODO: hoist to module-level constant).

## Known TODOs

- **`atmos.py`**: `GAMMA = 1.4` and `a_0 = 661.4745` are repeated inside every speed function — should be hoisted to module-level constants.
- **`atmos.py`**: `a_0` is hardcoded rather than derived from the CSV data at `Hgeo_ft == 0` (same for `p_0` which is already read from CSV but `a_0` is not).
- **`logger.py`**: Completely unimplemented; log saving referenced in `main.py` TODO is not yet wired up.
- **Speed-altitude chart menu options** (3.1, 3.2, 3.3): Functions in `menu.py` are stubs (`pass`).

## Menu Options

```
1.1  Atmospheric properties given pressure altitude (m or ft input)
1.2  Atmospheric properties given static pressure (psf/psi/Pa/atm/bar/ft/m input)
2.1  Speed conversion given altitude + Mach
2.2  Speed conversion given altitude + KTAS
2.3  Speed conversion given altitude + KCAS
2.4  Speed conversion given altitude + KEAS
3.1  Speed-altitude chart: KTAS vs Alt      [in development]
3.2  Speed-altitude chart: KCAS vs Alt      [in development]
3.3  Speed-altitude chart: KEAS vs Alt      [in development]
q    Quit
```
