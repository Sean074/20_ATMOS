# Architecture

This document defines the structure and design principles of the ATMOS codebase.
It is the authoritative reference for where code belongs, how modules interact,
and why the structure is organised the way it is.

---

## Design principles

1. **Strict layering** — each layer depends only on layers below it; no
   upward dependencies.
2. **Single responsibility** — each module has one job; mixing concerns
   (e.g. computation inside display code) is a defect.
3. **Configuration over constants** — tunable parameters live in
   `src/atmos/defaults.json`; physics constants live in `atmos/core.py`.
4. **No framework magic** — explicit function calls, no decorators that hide
   control flow, no global state beyond the selected model path (a context
   variable, so concurrent callers stay independent) and app config.
5. **Installable engine** — everything under `src/atmos/` is the `atmos`
   package (`pyproject.toml`), usable without the TUI (e.g. by a web front-end).
   It must never import `ui`, `menu`, `logger`, `rich` or `prompt_toolkit`.

---

## Layer diagram

```
┌────────────────────────────────────────────────┐
│  Entry point                                   │
│  main.py                                       │
└──────────────────────┬─────────────────────────┘
                       │ calls
┌──────────────────────▼─────────────────────────┐
│  Presentation layer                            │
│  src/ui.py          — display, prompts         │
│  src/menu.py        — handler functions        │
│  src/atmos/plot_speed_alt.py — matplotlib charts │
└──────────────────────┬─────────────────────────┘
                       │ calls
┌──────────────────────▼─────────────────────────┐
│  Computation engine                            │
│  src/atmos/core.py  — atmospheric model + solvers │
│  src/atmos/unit_convert.py — conversion constants │
└──────────────────────┬─────────────────────────┘
                       │ reads
┌──────────────────────▼─────────────────────────┐
│  Cross-cutting services                        │
│  src/atmos/config.py — settings loader         │
│  src/logger.py      — result logger            │
└──────────────────────┬─────────────────────────┘
                       │ reads / writes
┌──────────────────────▼─────────────────────────┐
│  Data files                                    │
│  src/atmos/defaults.json                       │
│  src/atmos/data/models/*.csv    — atmos models │
│  src/atmos/data/envelopes/*.json — envelopes   │
│  data/inputs/*.json     — calculation cases    │
│  data/outputs/          — generated artifacts  │
└────────────────────────────────────────────────┘
```

---

## Directory structure

```
20_ATMOS/
│
├── main.py                  # Entry point — startup, menu loop
├── pyproject.toml           # Packages src/atmos/ as the installable `atmos` engine
│
├── src/
│   ├── menu.py              # Presentation layer — menu handler functions (TUI only)
│   ├── ui.py                # Presentation layer — display and prompt helpers (TUI only)
│   ├── logger.py            # Service — append-mode CSV logger (TUI only)
│   └── atmos/               # Installable package — engine, charts, config, shipped data
│       ├── __init__.py      # Re-exports the public engine API
│       ├── core.py          # Computation engine — atmospheric model and solvers
│       ├── unit_convert.py  # Computation support — unit conversion constants
│       ├── plot_speed_alt.py # Presentation layer — speed-altitude charts
│       ├── config.py        # Service — config file loader
│       ├── version.py       # __version__, __author__
│       ├── defaults.json    # Tunable parameters (axis ranges, solver tolerances)
│       └── data/
│           ├── models/      # Atmospheric model CSVs (selected at startup)
│           │   ├── standard_atmos.csv
│           │   └── standard_atmos_1976.csv
│           └── envelopes/   # Speed envelope JSON files
│               └── speed_envelope_example.json
│
├── data/
│   ├── inputs/              # Calculation case JSON files (TUI)
│   │   ├── example_speed_cases.json
│   │   └── example_atmos_cases.json
│   └── outputs/             # Generated runtime artifacts (not committed)
│       └── AtmosLog.txt
│
├── tests/                   # pytest — engine regression and chart rendering
│
├── doc/                     # Authoritative coding standards
│   ├── architecture.md      # This file
│   ├── analysis_code.md     # Variable naming rules for computation modules
│   └── ui.md                # TUI code standards
│
├── tools/                   # Standalone scripts; not imported by the app
│   ├── gen_ussa76.py        # Generates standard_atmos_1976.csv
│   ├── scrap.py             # Scratch / exploratory work
│   └── atmos.ipynb          # Jupyter notebook for exploratory analysis
│
├── CLAUDE.md                # Claude Code guidance
└── README.md                # Project overview
```

---

## Module responsibilities

### `main.py` — Entry point

Owns the application lifecycle: model selection on startup, the top-level menu
loop, and clean shutdown. It is the only place that renders the main menu panel.

**Allowed to import:** `atmos`, `menu`, `ui`

**Must not contain:** computation logic, display formatting, or file I/O beyond
what is required to start the app.

---

### `menu.py` — Menu handlers

One function per menu item. Each handler follows the strict
**input → analysis → output** pattern defined in `doc/ui.md`:

1. Collect all inputs (via `ui` helpers or JSON file selection).
2. Call the computation engine (`atmos.*`).
3. Log the result (`logger.*`).
4. Display via `ui.print_*_table()` or `plot_speed_alt.*`.
5. Call `ui.press_enter_to_continue()`.

**Allowed to import:** `atmos`, `ui`, `logger`, `atmos.plot_speed_alt`,
`atmos.unit_convert`, `atmos.config`

**Must not contain:** raw `print()`/`input()` calls, physics calculations, or
direct file reads outside of JSON case iteration.

---

### `ui.py` — Display and prompts

All terminal I/O lives here. Exposes a single shared `Console` instance used by
both `ui.py` and `menu.py`. See `doc/ui.md` for full conventions.

**Allowed to import:** `rich`, `prompt_toolkit`, `config`

**Must not contain:** computation logic or direct calls to `atmos`.

---

### `atmos/plot_speed_alt.py` — Speed-altitude charts

`draw_speed_alt(fig, x_type, envelope_json=None)` draws the chart onto a
matplotlib `Figure` the caller supplies, without touching pyplot — this is the
entry point for non-interactive use (saving to SVG/PNG, web servers). Three TUI
entry points — `plot_speed_alt_ktas`, `plot_speed_alt_kcas`,
`plot_speed_alt_keas` — create a pyplot figure, call `draw_speed_alt`, and
`plt.show()` it.

Chart axis defaults come from `APP_CONFIG["chart_defaults"]`; a speed envelope
JSON overrides them. Envelope boundary intersections are computed via binary
search in KEAS space.

**Allowed to import:** `atmos`, `config`, `unit_convert`, `matplotlib`

**Must not contain:** user prompts or display logic outside of chart rendering.

---

### `atmos/core.py` — Computation engine

The core physics module, re-exported as `atmos.*`. The active atmospheric model
CSV is selected with `set_atmos_model(path)` (the TUI, once at startup) or the
`use_model(path)` context manager (per call or request); it is held in a
`contextvars.ContextVar`, so threads and async tasks each keep their own choice.
Parsed CSVs are cached per path. `list_models()` / `list_envelopes()` return the
shipped files, and `MODELS_DIR` / `ENVELOPES_DIR` point at them.

Key public functions:

| Function | Input | Returns |
|---|---|---|
| `get_atmos_prop_alt(h_press_ft)` | Pressure altitude (ft) | `{h_press_ft, p_static_psf, pho_ratio, pho_slug_ft3, temp_degR}` |
| `get_atmos_prop_pres(p_press_psf)` | Static pressure (psf) | same dict |
| `mach_alt(M, h_press_ft)` | Mach + altitude | `{Mach, ktas, keas, kcas, q_c}` |
| `tas_alt(ktas, h_press_ft)` | KTAS + altitude | same dict |
| `eas_alt(keas, h_press_ft)` | KEAS + altitude | same dict |
| `cas_alt(kcas, h_press_ft)` | KCAS + altitude | same dict |

Raises `AtmosRangeError` (subclass of `ValueError`) when input is outside the
loaded model's range.

**Allowed to import:** `pandas`, `numpy`, stdlib, `config` (solver params only),
`unit_convert`

**Must not contain:** display logic, logging, or file-path assumptions beyond the
model CSV.

Variable naming follows `doc/analysis_code.md` strictly.

---

### `unit_convert.py` — Conversion constants

Constants only. Pattern: `<FROM>_<TO>` in `ALL_CAPS` (e.g. `M_FT`, `MS_KTS`).
No functions, no imports. See `doc/analysis_code.md` for the full reference.

**Must not contain:** any logic, imports, or mutable state.

---

### `config.py` — Configuration loader

Thin module. `from atmos.config import APP_CONFIG` returns the dict parsed from
`src/atmos/defaults.json`. Falls back to hardcoded values if the file is missing.

**Must not contain:** application logic or direct knowledge of config keys.

---

### `logger.py` — Result logger

Append-mode CSV writer. Two public functions:

- `log_speed_result(alt_ft, result)` — logs a speed-conversion result dict.
- `log_atmos_result(result)` — logs an atmospheric properties result dict.

Log path comes from `APP_CONFIG["log_file"]`.

**Must not contain:** computation logic or display output.

---

## Dependency rules (summary)

| Module | May import |
|---|---|
| `main.py` | `atmos`, `src/menu`, `src/ui` |
| `src/menu.py` | `atmos`, `ui`, `logger`, `atmos.plot_speed_alt`, `atmos.unit_convert`, `atmos.config` |
| `src/ui.py` | `rich`, `prompt_toolkit`, `config` |
| `src/logger.py` | `atmos.config` |
| `src/atmos/plot_speed_alt.py` | `atmos.core`, `atmos.config`, `unit_convert`, `matplotlib` (pyplot only inside the TUI entry points) |
| `src/atmos/core.py` | `pandas`, `numpy`, stdlib, `atmos.config`, `unit_convert` |
| `src/atmos/config.py` | stdlib only (`json`, `pathlib`) |
| `src/atmos/unit_convert.py` | nothing |

No module in the computation layer (`atmos.py`, `unit_convert.py`) may import
from the presentation layer (`ui.py`, `menu.py`, `plot_speed_alt.py`,
`main.py`).

---

## Data flow

```
User selects menu item
        │
        ▼
menu.py handler
  ├── ui.py   ← prompts user for inputs
  ├── atmos.py ← computes result
  ├── logger.py ← appends to AtmosLog.txt
  └── ui.py   ← renders result table
        │
        ▼
ui.press_enter_to_continue()
        │
        ▼
Returns to main menu loop (main.py)
```

For chart operations:

```
menu.py handler
  ├── ui.select_envelope_file() ← user picks envelope JSON
  └── plot_speed_alt.plot_speed_alt_*()
        ├── atmos.*  ← evaluates airspeeds over altitude range
        └── matplotlib ← renders and displays chart
```

---

## Configuration vs. constants

| Type | Location | Examples |
|---|---|---|
| Physics constants | `atmos/core.py` module-level | `GAMMA = 1.4`, `A_0_KTS`, `P_0_PSF` |
| Tunable parameters | `src/atmos/defaults.json` | axis ranges, grid lines, solver tolerances |
| Conversion factors | `unit_convert.py` | `M_FT`, `MS_KTS`, `PA_PSF` |

Never move physics constants to config. Never hardcode conversion factors as
bare literals inside analysis functions.

---

## Adding new features

**New speed type or atmospheric quantity:**
Add to `atmos.py`. Follow the naming conventions in `doc/analysis_code.md`.
Add a menu handler in `menu.py`. Add a display function to `ui.py` if the
output shape differs from existing tables.

**New chart type:**
Add a public entry point to `atmos/plot_speed_alt.py` that delegates to
`_show_chart(x_type, envelope_json)`. Add the menu item in `main.py`'s `MENU_OPTIONS` dict and
`_MENU_DISPLAY` string. Add a handler in `menu.py`.

**New config parameter:**
Add the key and default value to `src/atmos/defaults.json` with a comment. Read it
in the consuming module via `APP_CONFIG`. Do not add a new module-level
constant.

**New standalone tool or script:**
Place it in `tools/`. It must not be imported by any application module.

---

## What does not belong in the source tree

- Generated outputs (`AtmosLog.txt`, `speed_alt_data.csv`) — these are runtime
  artifacts.
- Local atmospheric model CSV files added by users — place in `instance/`.
- Exploratory or scratch notebooks — use `atmos.ipynb` or add to `tools/`.
