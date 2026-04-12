# Analysis Code Standards — Variable Naming

Applies to all computation modules: `atmos.py`, any future engine files,
and helper functions called from them.  UI and menu code is excluded.

---

## Core rules

1. **Use the standard symbol where one exists.**  Aeronautical and
   thermodynamic quantities have established symbols from ICAO, ISO 2533, or
   common textbook convention (e.g. Anderson, Nelson).  Prefer the symbol over
   an English description.

2. **Append the unit as a suffix, separated by `_`.**  The suffix makes the
   unit visible at every point of use without reading the function signature or
   docstring.

Combined, the pattern is:

```
<symbol>_<unit>
```

---

## Unit suffix reference

| Dimension | Suffix | Notes |
|---|---|---|
| Length / altitude | `_ft`, `_m` | `_ft` is primary; `_m` only at user-input boundary |
| Pressure | `_psf`, `_psi`, `_pa`, `_atm`, `_bar` | `_psf` is primary throughout the engine |
| Density | `_slug_ft3` | slug per cubic foot |
| Temperature | `_degR`, `_degK`, `_degC`, `_degF` | `_degR` is primary (Rankine) |
| Speed | `_kts`, `_ms` | `_kts` is primary; `_ms` only at conversion boundary |
| Dimensionless | _(no suffix)_ | Mach, ratios, pure coefficients |

When a quantity has no unit (ratio, Mach number, exponent intermediate), omit
the suffix entirely — do not write `_nd` or `_ratio` unless `ratio` is part of
the standard symbol itself (e.g. `pho_ratio`).

---

## Standard symbol table

### Atmospheric state

| Quantity | Variable name | Standard symbol |
|---|---|---|
| Geopotential pressure altitude | `h_press_ft` | *H* (geopotential) |
| Geometric altitude | `h_geo_ft` | *h* |
| Static pressure | `p_static_psf` | *p* |
| Sea-level reference pressure | `p_0_psf` | *p*₀ |
| Air density | `rho_slug_ft3` | *ρ* |
| Sea-level reference density | `rho_0_slug_ft3` | *ρ*₀ |
| Density ratio | `rho_ratio` | *σ* = *ρ*/*ρ*₀ |
| Temperature | `T_degR` | *T* |
| Sea-level reference temperature | `T_0_degR` | *T*₀ |

> **Note on legacy names:** `atmos.py` currently uses `pho_ratio` and
> `pho_slug_ft3`.  New code must use `rho_ratio` and `rho_slug_ft3`.  Rename
> existing names when a function is substantively rewritten; do not rename
> opportunistically.

### Speed

| Quantity | Variable name | Standard symbol |
|---|---|---|
| True airspeed | `V_TAS_kts` | *V*_TAS |
| Calibrated airspeed | `V_CAS_kts` | *V*_CAS |
| Equivalent airspeed | `V_EAS_kts` | *V*_EAS |
| Mach number | `M` | *M* |
| Local speed of sound | `a_kts` | *a* |
| Sea-level speed of sound | `a_0_kts` | *a*₀ |

> The short aliases `ktas`, `keas`, `kcas` are retained in **dict keys** and
> **return values** of public functions for backward compatibility.  Inside
> function bodies, use the full names above.

### Compressible flow

| Quantity | Variable name | Standard symbol |
|---|---|---|
| Impact (compressible dynamic) pressure | `q_c_psf` | *q*_c |
| Ratio of specific heats | `GAMMA` (module constant) | *γ* |

---

## Intermediate / helper variables

Short-lived algebraic intermediates that correspond to no single aeronautical
symbol use a descriptive name that still carries units where applicable.
Prefer two or three components separated by `_`:

```python
# good — describes what it holds
q_numerator   = ...
q_denominator = ...

# bad — cryptic single letters that are not established symbols
a = ...
b = ...
```

If an intermediate is truly a sub-expression of a larger formula with no
independent meaning, a single-letter name (`q_a`, `q_b`) is acceptable only
inside a tightly scoped helper function (fewer than ~15 lines).

---

## Function signatures

Apply the same symbol-and-unit rule to parameter names:

```python
# correct
def get_atmos_prop_alt(h_press_ft: float) -> dict: ...
def mach_alt(M: float, h_press_ft: float) -> dict: ...

# incorrect — no unit, generic name
def mach_alt(speed, alt_defined): ...
```

Return dicts use the short key aliases (`Mach`, `ktas`, `keas`, `kcas`,
`q_c`) for backward compatibility with callers and the UI layer.

---

## Module-level constants

Constants that are physical facts use `ALL_CAPS` with a unit suffix:

```python
GAMMA    = 1.4            # dimensionless — no suffix
A_0_KTS  = 661.4745       # sea-level speed of sound
P_0_PSF  = 2116.224       # sea-level static pressure
```

Tunable solver parameters belong in `config/defaults.json`, not as
module-level constants.

---

## Conversion constants (`unit_convert.py`)

Conversion factors follow the pattern `<FROM>_<TO>` in `ALL_CAPS`, where
`<FROM>` and `<TO>` are unit abbreviations:

```python
M_FT   = 3.28084    # metres to feet
FT_M   = 1 / M_FT
PA_PSF = 0.020885   # pascals to psf
PSF_PA = 1 / PA_PSF
MS_KTS = 1.94384    # m/s to knots
```

Do not embed conversion factors as bare literals inside analysis functions.
Import from `unit_convert` and use the named constant.

---

## Quick reference

```python
# Atmospheric lookup — parameter and locals
def get_atmos_prop_alt(h_press_ft: float) -> dict:
    p_static_psf  = ...   # static pressure at altitude
    rho_slug_ft3  = ...   # air density
    rho_ratio     = ...   # density ratio sigma
    T_degR        = ...   # temperature

# Speed conversion — parameter and locals
def mach_alt(M: float, h_press_ft: float) -> dict:
    a_kts         = ...   # local speed of sound
    V_TAS_kts     = M * a_kts
    V_EAS_kts     = V_TAS_kts * math.sqrt(rho_ratio)
    q_c_psf       = _dynamic_pressure(M, p_static_psf)
    V_CAS_kts     = _kcas_from_qc(q_c_psf)
    return {"Mach": M, "ktas": V_TAS_kts, "keas": V_EAS_kts,
            "kcas": V_CAS_kts, "q_c": q_c_psf}
```
