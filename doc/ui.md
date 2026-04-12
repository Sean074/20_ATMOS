# TUI Code Standards — `ui.py`

## Overview

The TUI follows a linear **input → analysis → output** workflow driven by
`rich` for display and `prompt_toolkit` for input.  The aesthetic is
deliberately spartan: a 1990s engineering-program look — monochrome panels,
plain ASCII box art, no animations.

Compatibility target: macOS Terminal and Windows cmd/PowerShell (via
`rich`'s auto-detected color fallback).

---

## Dependency roles

| Library | Role |
|---|---|
| `rich` | All display output — panels, tables, styled text |
| `prompt_toolkit` | All user input — prompts, tab-completion, inline validation |

Never use `print()` or `input()` directly.  Route everything through the two
libraries above so colour stripping and cross-platform encoding are handled
consistently.

---

## Workflow pattern: input → analysis → output

Every operation follows three stages in strict order.  No stage is skipped or
combined with another.

```
1. INPUT      — collect everything the calculation needs before any computation
2. ANALYSIS   — call the computation engine; may chain (analysis 1, 2, … n)
3. OUTPUT     — display results; never interleaved with input prompts
```

A handler function maps cleanly onto this pattern:

```python
def alt_mach():
    # --- INPUT ---
    h_press_ft = _ask_alt()
    mach       = ui.prompt_float("Input Mach: ")

    # --- ANALYSIS ---
    result = atmos.mach_alt(mach, h_press_ft)

    # --- OUTPUT ---
    ui.print_speed(result)
    ui.press_enter_to_continue()
```

When multiple analysis steps depend on each other, run them sequentially and
accumulate results before any `print_*` call.

---

## Color palette

Use at most **two** named Rich colors throughout the entire application.

| Token | Rich markup | Purpose |
|---|---|---|
| Primary | `[cyan]` | Labels, column headers, active panel borders, section titles |
| Warning | `[yellow]` | Non-fatal notices (empty result set, cancelled action) |
| Error | `[red]` | Validation failures, range errors, unknown input types |
| Dim | `[dim]` | Supplemental hints in menu text only |
| Bold | `[bold]` | Panel titles only |

Do **not** introduce additional colors (green, magenta, blue, etc.).  If a new
semantic category is needed, use a combination of the tokens above (e.g.,
`[bold red]`).

---

## Symbolic elements

Keep decoration minimal.  The only structural symbol used is the `rich` Panel
border, which renders as plain ASCII `+--+` on terminals that do not support
Unicode box-drawing.

Allowed:

- `Panel` — one per logical result block, border in `cyan`
- `Table` — inside panels; `box=None`, `show_header=True` for data tables,
  `show_header=False` for selection lists

Not allowed:

- Progress bars, spinners, live displays, or any animated element
- Emoji or pictographic characters
- Custom box styles (keep `box=None` on tables)
- Nested panels

---

## Panel conventions

```python
console.print(Panel(
    content,                          # Rich renderable (Table, str, markup str)
    title="[bold]Title[/bold]",       # Short noun phrase; bold only
    border_style="cyan",              # Always cyan; never change per-panel
))
```

Panel titles are noun phrases, not sentences.  Examples:

- `"Select Atmospheric Model"` — correct
- `"Please select your atmospheric model below:"` — incorrect

---

## Table conventions

**Selection lists** (file pickers):

```python
tbl = Table(show_header=False, box=None, padding=(0, 2))
tbl.add_column("Key", style="cyan")   # numeric key, cyan
tbl.add_column("File")                # filename, unstyled
```

**Result tables** (data output):

```python
tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
tbl.add_column("Label", style="cyan", justify="right")   # first col, labels
tbl.add_column("Value",               justify="right")   # data cols, right-aligned
```

Right-align all numeric columns.  Label the first column with `style="cyan"`.
Do not apply per-cell styles.

---

## Prompt conventions

All prompts are written in `prompt_toolkit`.  Format:

```
Noun phrase: <cursor>
```

- End with `: ` (colon-space), no trailing newline
- Lowercase except proper nouns and acronyms
- No question marks; use imperative noun phrases

Examples:

| Correct | Incorrect |
|---|---|
| `"Input pressure altitude: "` | `"Enter your pressure altitude? "` |
| `"Select file: "` | `"Which file do you want?"` |
| `"Input Mach: "` | `"Mach number:"` |

Tab completion via `WordCompleter` is required on all selection prompts.
Numeric prompts use `_NumberValidator` for inline validation.

---

## Error and status messages

Print inline before returning control, not inside a panel.

```python
# range / computation error
console.print(f"[red]Error for alt={alt_ft} ft: {e}[/red]")

# non-fatal / informational
console.print("[yellow]No cases found in file.[/yellow]")

# action in progress (single line, no panel)
console.print("[cyan]Generating chart...[/cyan]")
```

Never raise a dialog or prompt after an error — print the message and return
to the menu loop.

---

## Navigation

Every handler that shows output must end with:

```python
ui.press_enter_to_continue()
```

This holds the result on screen until the user is ready to return to the menu.
Handlers that only select a file and hand off (e.g., chart handlers) still
call this after the chart is launched.

The main menu loop is the only place that renders the menu panel.  Submenu
state does not exist; every operation returns to the top-level menu.

---

## Module structure (`ui.py`)

Organise functions in this order, separated by comment banners:

```
# File-selection helpers       — _select_file, select_model, select_input_file, select_envelope_file
# Manual numeric input helpers — _NumberValidator, prompt_float, ask_unit
# Output helpers — single      — print_atmos, print_speed
# Output helpers — batch       — print_atmos_table, print_speed_table
```

The module exposes a single `Console` instance (`console`) used by both
`ui.py` and `menu.py`.  Do not instantiate additional consoles.

---

## Cross-platform notes

- `rich` detects terminal capabilities at import time.  Do not force color
  depth or unicode — let the library negotiate with the host terminal.
- Windows `cmd` does not support Unicode box-drawing; `rich` falls back to
  ASCII automatically when `TERM` or `COLORTERM` are absent.
- Avoid `os.get_terminal_size()` calls; `rich` handles width negotiation
  internally.
- `prompt_toolkit` handles readline-style editing on both platforms without
  additional configuration.
