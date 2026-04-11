"""
Speed-altitude chart generation.

Three public entry points share one generic implementation:
  plot_speed_alt_ktas(envelope_json)   — x-axis: KTAS
  plot_speed_alt_kcas(envelope_json)   — x-axis: KCAS
  plot_speed_alt_keas(envelope_json)   — x-axis: KEAS

All three draw a grid of:
  - Constant Mach lines     (gray, solid)
  - Constant KCAS lines     (steel-blue, solid)
  - Constant KEAS lines     (sea-green, dashed)

…and optionally overlay a speed envelope loaded from a JSON file.

JSON schema
-----------
{
    "name": "Chart title",
    "chart": {
        "ktas_min": 80,  "ktas_max": 600,
        "kcas_min": 80,  "kcas_max": 500,
        "keas_min": 80,  "keas_max": 500,
        "alt_min":  0,   "alt_max":  46000
    },
    "max_altitude_ft": 43100,
    "mach_grid": [0.3, 0.4, ..., 0.92],
    "kcas_grid": [100, 150, 200, ...],
    "keas_grid": [100, 150, 200, ...],
    "speed_limits": [
        {
            "label":     "Vmo",
            "type":      "keas",      // "keas" | "kcas" | "mach"
            "value":     360,
            "color":     "black",
            "linewidth": 2.5,
            "linestyle": "-"
        },
        ...
    ]
}
"""

import json
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D

import atmos


# ---------------------------------------------------------------------------
# Converter dispatch tables
#   _CONVERTERS[x_type][source_type](value, alt_ft) -> x-axis speed (or None)
#   A None entry means the line is vertical (x = value) on that chart.
# ---------------------------------------------------------------------------

def _safe(fn):
    """Wrap a converter so it returns None on any exception."""
    def wrapper(value, alt_ft):
        try:
            result = fn(value, alt_ft)
            return result if (result is not None and math.isfinite(result)) else None
        except Exception:
            return None
    return wrapper


_CONVERTERS = {
    'ktas': {
        'mach': _safe(lambda v, a: atmos.mach_alt(v, a)['ktas']),
        'kcas': _safe(lambda v, a: atmos.cas_alt(v, a)['ktas']),
        'keas': _safe(lambda v, a: atmos.eas_alt(v, a)['ktas']),
    },
    'kcas': {
        'mach': _safe(lambda v, a: atmos.mach_alt(v, a)['kcas']),
        'kcas': None,   # vertical line on KCAS chart
        'keas': _safe(lambda v, a: atmos.eas_alt(v, a)['kcas']),
    },
    'keas': {
        'mach': _safe(lambda v, a: atmos.mach_alt(v, a)['keas']),
        'kcas': _safe(lambda v, a: atmos.cas_alt(v, a)['keas']),
        'keas': None,   # vertical line on KEAS chart
    },
}

# Default axis limits per x_type
_DEFAULTS = {
    'ktas': dict(x_min=80,  x_max=600,  xlabel='True Airspeed — KTAS (knots)',        title='Speed-Altitude Chart (KTAS)', x_min_key='ktas_min', x_max_key='ktas_max'),
    'kcas': dict(x_min=80,  x_max=500,  xlabel='Calibrated Airspeed — KCAS (knots)',  title='Speed-Altitude Chart (KCAS)', x_min_key='kcas_min', x_max_key='kcas_max'),
    'keas': dict(x_min=80,  x_max=500,  xlabel='Equivalent Airspeed — KEAS (knots)',  title='Speed-Altitude Chart (KEAS)', x_min_key='keas_min', x_max_key='keas_max'),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_line(fn, value, alts):
    """Return (x_vals, alt_vals) arrays for one constant-value line."""
    xs, ys = [], []
    for alt in alts:
        x = fn(value, alt)
        if x is not None:
            xs.append(x)
            ys.append(alt)
    return np.array(xs), np.array(ys)


def _label_end(ax, xs, ys, text, color, fontsize=7, offset_x=2):
    """Annotate the trailing end of a line."""
    if len(xs) == 0:
        return
    ax.annotate(
        text,
        xy=(xs[-1], ys[-1]),
        xytext=(xs[-1] + offset_x, ys[-1]),
        fontsize=fontsize,
        color=color,
        ha='left',
        va='center',
        clip_on=True,
    )


# ---------------------------------------------------------------------------
# Generic chart engine
# ---------------------------------------------------------------------------

def _plot_chart(x_type, envelope_json=None):
    """
    Internal chart renderer.

    x_type : 'ktas' | 'kcas' | 'keas'
        Determines which airspeed is placed on the x-axis.
    envelope_json : str or None
        Path to a JSON speed envelope file.
    """
    cfg = _DEFAULTS[x_type]
    conv = _CONVERTERS[x_type]

    # ---- defaults ----
    x_min   = cfg['x_min']
    x_max   = cfg['x_max']
    alt_min = 0
    alt_max = 46000
    max_alt_ceiling = None
    chart_title = cfg['title']

    mach_grid    = [0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.80, 0.84, 0.88, 0.92]
    kcas_grid    = [100, 150, 200, 250, 300, 350, 400]
    keas_grid    = [100, 150, 200, 250, 300, 350, 400]
    speed_limits = []

    # ---- load JSON ----
    envelope = None
    if envelope_json:
        with open(envelope_json) as f:
            envelope = json.load(f)

        chart_title     = envelope.get('name', chart_title)
        chart_cfg       = envelope.get('chart', {})
        x_min           = chart_cfg.get(cfg['x_min_key'], x_min)
        x_max           = chart_cfg.get(cfg['x_max_key'], x_max)
        alt_min         = chart_cfg.get('alt_min', alt_min)
        alt_max         = chart_cfg.get('alt_max', alt_max)
        max_alt_ceiling = envelope.get('max_altitude_ft', None)
        mach_grid       = envelope.get('mach_grid', mach_grid)
        kcas_grid       = envelope.get('kcas_grid', kcas_grid)
        keas_grid       = envelope.get('keas_grid', keas_grid)
        speed_limits    = envelope.get('speed_limits', [])

    # Append chart type to title so each window is identifiable
    chart_title = f'{chart_title} — {x_type.upper()}'

    alts = np.linspace(alt_min + 50, alt_max - 50, 300)

    # ---- figure ----
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_facecolor('#f8f8f8')

    def _in_bounds(xs, ys):
        return (xs >= x_min) & (xs <= x_max) & (ys >= alt_min) & (ys <= alt_max)

    # ---- constant KCAS lines ----
    for kcas in kcas_grid:
        fn = conv['kcas']
        if fn is None:
            # x-axis IS KCAS: draw vertical line
            ax.axvline(x=kcas, color='steelblue', linewidth=0.9, linestyle='-', zorder=2)
            ax.annotate(f'{kcas}', xy=(kcas, alt_max * 0.97), fontsize=6.5,
                        color='steelblue', ha='center', va='top', clip_on=True)
        else:
            xs, ys = _compute_line(fn, kcas, alts)
            mask = _in_bounds(xs, ys)
            if mask.sum() > 1:
                ax.plot(xs[mask], ys[mask], color='steelblue', linewidth=0.9,
                        linestyle='-', zorder=2)
                _label_end(ax, xs[mask], ys[mask], f'{kcas} KCAS',
                           color='steelblue', fontsize=7)

    # ---- constant KEAS lines ----
    for keas in keas_grid:
        fn = conv['keas']
        if fn is None:
            # x-axis IS KEAS: draw vertical line
            ax.axvline(x=keas, color='seagreen', linewidth=0.9, linestyle='--', zorder=2)
            ax.annotate(f'{keas}', xy=(keas, alt_max * 0.97), fontsize=6.5,
                        color='seagreen', ha='center', va='top', clip_on=True)
        else:
            xs, ys = _compute_line(fn, keas, alts)
            mask = _in_bounds(xs, ys)
            if mask.sum() > 1:
                ax.plot(xs[mask], ys[mask], color='seagreen', linewidth=0.9,
                        linestyle='--', zorder=2)
                _label_end(ax, xs[mask], ys[mask], f'{keas} KEAS',
                           color='seagreen', fontsize=7, offset_x=2)

    # ---- constant Mach lines ----
    fn_mach = conv['mach']
    for mach in mach_grid:
        xs, ys = _compute_line(fn_mach, mach, alts)
        mask = _in_bounds(xs, ys)
        if mask.sum() > 1:
            ax.plot(xs[mask], ys[mask], color='gray', linewidth=0.7,
                    linestyle='-', zorder=1)
            mid = max(0, mask.sum() - max(1, mask.sum() // 4))
            ax.annotate(
                f'M {mach:.2f}',
                xy=(xs[mask][mid], ys[mask][mid]),
                fontsize=6.5, color='dimgray',
                ha='center', va='bottom', clip_on=True,
            )

    # ---- speed envelope limits ----
    for limit in speed_limits:
        label  = limit.get('label', '')
        ltype  = limit.get('type', '').lower()
        value  = limit.get('value')
        color  = limit.get('color', 'black')
        lw     = limit.get('linewidth', 2.0)
        ls     = limit.get('linestyle', '-')

        fn = conv.get(ltype)
        if fn is None and ltype == x_type:
            # Speed limit is the same type as the x-axis → vertical line
            ceiling = max_alt_ceiling if max_alt_ceiling else alt_max
            ax.axvline(x=value, color=color, linewidth=lw, linestyle=ls, zorder=5)
            ax.annotate(f'  {label}', xy=(value, min(ceiling, alt_max) * 0.97),
                        fontsize=9, fontweight='bold', color=color,
                        ha='left', va='top', clip_on=True)
            continue
        if fn is None:
            continue

        xs, ys = _compute_line(fn, value, alts)
        ceiling = max_alt_ceiling if max_alt_ceiling else alt_max
        mask = (xs >= x_min) & (xs <= x_max) & (ys >= alt_min) & (ys <= ceiling)
        if mask.sum() > 1:
            ax.plot(xs[mask], ys[mask], color=color, linewidth=lw, linestyle=ls,
                    zorder=5, label=label)
            _label_end(ax, xs[mask], ys[mask], f'  {label}',
                       color=color, fontsize=9, offset_x=3)

    # ---- max altitude ceiling line ----
    if max_alt_ceiling and alt_min < max_alt_ceiling <= alt_max:
        ax.axhline(y=max_alt_ceiling, color='black', linewidth=2.0,
                   linestyle='-', zorder=5)
        ax.annotate(
            f'Max Alt: {max_alt_ceiling:,.0f} ft',
            xy=(x_min + (x_max - x_min) * 0.02,
                max_alt_ceiling + (alt_max - alt_min) * 0.005),
            fontsize=9, fontweight='bold', color='black',
        )

    # ---- axes ----
    ax.set_xlabel(cfg['xlabel'], fontsize=12)
    ax.set_ylabel('Pressure Altitude (ft)', fontsize=12)
    ax.set_title(chart_title, fontsize=14, fontweight='bold')
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(alt_min, alt_max)
    ax.grid(True, which='major', linestyle=':', linewidth=0.4, color='lightgray', zorder=0)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5000))

    # ---- legend ----
    legend_elements = [
        Line2D([0], [0], color='steelblue', linewidth=1.2, linestyle='-',  label='Constant KCAS'),
        Line2D([0], [0], color='seagreen',  linewidth=1.2, linestyle='--', label='Constant KEAS'),
        Line2D([0], [0], color='gray',      linewidth=1.0, linestyle='-',  label='Constant Mach'),
    ]
    for limit in speed_limits:
        legend_elements.append(Line2D(
            [0], [0],
            color=limit.get('color', 'black'),
            linewidth=limit.get('linewidth', 2.0),
            linestyle=limit.get('linestyle', '-'),
            label=limit.get('label', ''),
        ))
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.85)

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def plot_speed_alt_ktas(envelope_json=None):
    """Altitude vs KTAS chart."""
    _plot_chart('ktas', envelope_json)


def plot_speed_alt_kcas(envelope_json=None):
    """Altitude vs KCAS chart (matches the 777-style V_CAS diagram)."""
    _plot_chart('kcas', envelope_json)


def plot_speed_alt_keas(envelope_json=None):
    """Altitude vs KEAS chart."""
    _plot_chart('keas', envelope_json)
