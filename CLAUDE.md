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

Key dependencies: `pandas`, `numpy`, `matplotlib`, `plotly`.

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point. Menu loop and dispatch table. |
| `menu.py` | One function per menu option. Handles user prompts, unit conversion, and calls into `atmos.py`. |
| `atmos.py` | Core atmosphere and airspeed math. Interpolates from `instance/standard_atmos.csv`. |
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

## Key Physics / Implementation Notes

- Atmospheric properties (pressure, density, temperature) are looked up by **linear interpolation** from the CSV table, not from closed-form equations.
- Speed conversions handle both **subsonic and supersonic** regimes:
  - Subsonic dynamic pressure: `q = p_static * ((1 + 0.2*M²)^(7/2) - 1)`
  - Supersonic dynamic pressure uses the Rayleigh Pitot formula.
  - `vcas_super()` and `mach_super()` in `atmos.py` use an iterative marching/bracketing solver for the supersonic CAS and Mach back-calculations.
- Sea-level speed of sound reference: `a_0 = 661.4745 kts`
- Sea-level pressure reference: read from CSV at `Hgeo_ft == 0`
- `GAMMA = 1.4` (ratio of specific heats for air) — currently defined inside each function (TODO: hoist to module-level constant).

## Known Bugs / Active TODOs

- **`unit_convert.py`**: `MS_KTS = 3` is a placeholder — the correct value is ~1.94384. Speed inputs in m/s will be wrong until this is fixed.
- **`unit_convert.py`**: `PA_PS` should be named `PA_PSF` for consistency.
- **`atmos.py`**: `eas_alt()` is defined twice (lines ~272 and ~317). The second definition (which lacks supersonic handling) silently shadows the first.
- **`menu.py` `speed_alt_ktas()`**: Uses `speed_max - speed_max` instead of `speed_max - speed_min` for increment calculation — the chart arrays will always be empty.
- **`logger.py`**: Completely unimplemented; log saving referenced in `main.py` TODO is not yet wired up.
- **Speed-altitude chart menu options** (3.1, 3.2, 3.3): Functions in `menu.py` are stubs (`pass`).

## Menu Options

```
1.1  Atmospheric properties given pressure altitude (m or ft input)
1.2  Atmospheric properties given static pressure (psf/psi/Pa/atm/bar input)
2.1  Speed conversion given altitude + Mach
2.2  Speed conversion given altitude + KTAS
2.3  Speed conversion given altitude + KCAS
2.4  Speed conversion given altitude + KEAS
3.1  Speed-altitude chart: KTAS vs Alt      [in development]
3.2  Speed-altitude chart: KCAS vs Alt      [in development]
3.3  Speed-altitude chart: KEAS vs Alt      [in development]
q    Quit
```
