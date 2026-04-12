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

…and optionally overlay speed envelopes loaded from a JSON file.

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
    "envelope_boundaries": [
        {
            "label":       "Vmo/Mmo",
            "color":       "black",
            "linewidth":   2.5,
            "linestyle":   "-",
            "alt_ceiling": 43100,
            "alt_floor":   0,
            "segments": [
                {"type": "mach", "value": 0.89, "label": "Mmo"},
                {"type": "keas", "value": 360,  "label": "Vmo"}
            ]
        },
        ...
    ]
}

Each boundary traces from alt_ceiling downward through its segments in order.
The intersection altitude between each pair of adjacent segments is computed
automatically by finding where the two speed limits are equal (compared in KEAS).
A horizontal ceiling line is drawn from the chart left edge to the first segment's
speed at alt_ceiling — so neither the ceiling line nor any segment curve can extend
past the speed limit that is active at that altitude.

Legacy "speed_limits" key is still accepted for backward compatibility.
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
        'ktas': None,   # vertical line on KTAS chart
    },
    'kcas': {
        'mach': _safe(lambda v, a: atmos.mach_alt(v, a)['kcas']),
        'kcas': None,   # vertical line on KCAS chart
        'keas': _safe(lambda v, a: atmos.eas_alt(v, a)['kcas']),
        'ktas': _safe(lambda v, a: atmos.tas_alt(v, a)['kcas']),
    },
    'keas': {
        'mach': _safe(lambda v, a: atmos.mach_alt(v, a)['keas']),
        'kcas': _safe(lambda v, a: atmos.cas_alt(v, a)['keas']),
        'keas': None,   # vertical line on KEAS chart
        'ktas': _safe(lambda v, a: atmos.tas_alt(v, a)['keas']),
    },
}

# Default axis limits per x_type
_DEFAULTS = {
    'ktas': dict(x_min=80,  x_max=600,  xlabel='True Airspeed — KTAS (knots)',        title='Speed-Altitude Chart (KTAS)', x_min_key='ktas_min', x_max_key='ktas_max'),
    'kcas': dict(x_min=80,  x_max=500,  xlabel='Calibrated Airspeed — KCAS (knots)',  title='Speed-Altitude Chart (KCAS)', x_min_key='kcas_min', x_max_key='kcas_max'),
    'keas': dict(x_min=80,  x_max=500,  xlabel='Equivalent Airspeed — KEAS (knots)',  title='Speed-Altitude Chart (KEAS)', x_min_key='keas_min', x_max_key='keas_max'),
}


# ---------------------------------------------------------------------------
# Generic line helpers
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
# Envelope boundary helpers
# ---------------------------------------------------------------------------

def _seg_to_keas(seg_type, seg_value, alt_ft):
    """
    Convert a speed-limit segment to KEAS at the given altitude.
    Used as a common currency when finding intersection altitudes.
    """
    try:
        st = seg_type.lower()
        if st == 'keas':
            return float(seg_value)
        elif st == 'mach':
            return atmos.mach_alt(seg_value, alt_ft)['keas']
        elif st == 'kcas':
            return atmos.cas_alt(seg_value, alt_ft)['keas']
        elif st == 'ktas':
            return atmos.tas_alt(seg_value, alt_ft)['keas']
        return None
    except Exception:
        return None


def _find_intersection_alt(type1, val1, type2, val2, alt_low, alt_high, tol=1.0):
    """
    Binary-search for the altitude where two speed limits are equal (compared in KEAS).

    Returns the intersection altitude, or None if no sign change is found in the
    search interval (meaning the two limits do not cross within the given range).
    """
    guard = 100  # stay clear of CSV altitude boundaries

    def diff(alt):
        k1 = _seg_to_keas(type1, val1, alt)
        k2 = _seg_to_keas(type2, val2, alt)
        if k1 is None or k2 is None:
            return None
        return k1 - k2

    lo, hi = alt_low + guard, alt_high - guard
    if lo >= hi:
        return None

    d_lo = diff(lo)
    d_hi = diff(hi)
    if d_lo is None or d_hi is None:
        return None
    if d_lo * d_hi > 0:
        return None  # no sign change → limits do not cross in this range

    for _ in range(60):
        if hi - lo < tol:
            break
        mid = (lo + hi) / 2
        d_mid = diff(mid)
        if d_mid is None:
            break
        if abs(d_mid) < 0.05:
            return mid
        if d_lo * d_mid <= 0:
            hi = mid
            d_hi = d_mid
        else:
            lo = mid
            d_lo = d_mid

    return (lo + hi) / 2


def _seg_to_x(seg_type, seg_value, x_type, alt_ft):
    """Return the x-axis coordinate for a speed-limit segment on a given chart type."""
    st = seg_type.lower()
    fn = _CONVERTERS[x_type].get(st)
    if fn is None:
        # seg_type IS the x_type → x equals the speed value directly
        return float(seg_value)
    return fn(seg_value, alt_ft)


def _plot_boundary(ax, boundary, x_type, x_min, x_max, alt_min, alt_max, n_pts=300):
    """
    Plot one speed envelope boundary.

    The boundary is described by an ordered list of speed-limit segments.  Starting
    at alt_ceiling the first segment is active; when it intersects the second segment
    control passes to the second, and so on until alt_floor is reached.

    Draws:
      1. A horizontal ceiling line at alt_ceiling from x_min to the first segment's
         x-value at that altitude (so the line cannot extend past the active limit).
      2. Each segment curve/line over its altitude range.
      3. A label at the bottom of the final segment.
    """
    label       = boundary.get('label', '')
    color       = boundary.get('color', 'black')
    lw          = boundary.get('linewidth', 2.0)
    ls          = boundary.get('linestyle', '-')
    alt_ceiling = min(boundary.get('alt_ceiling', alt_max), alt_max)
    alt_floor   = max(boundary.get('alt_floor',   alt_min), alt_min)
    segments    = boundary.get('segments', [])

    if not segments or alt_ceiling <= alt_floor:
        return

    # ── compute intersection altitudes between consecutive segments ──────────
    intersect_alts = []
    for i in range(len(segments) - 1):
        s1, s2 = segments[i], segments[i + 1]
        ix = _find_intersection_alt(
            s1['type'], s1['value'],
            s2['type'], s2['value'],
            alt_floor, alt_ceiling,
        )
        # Fall back to alt_floor if no intersection found in range
        intersect_alts.append(ix if ix is not None else alt_floor)

    # build ordered bands: (segment, bot_alt, top_alt) from ceiling to floor
    seg_bands = []
    top = alt_ceiling
    for i, seg in enumerate(segments):
        bot = intersect_alts[i] if i < len(intersect_alts) else alt_floor
        seg_bands.append((seg, bot, top))
        top = bot

    # ── horizontal ceiling line ──────────────────────────────────────────────
    # Clipped on the right to the first segment's speed at alt_ceiling, so the
    # ceiling line cannot extend past the active Mach/speed limit at that altitude.
    x_ceil = _seg_to_x(segments[0]['type'], segments[0]['value'], x_type, alt_ceiling)
    if x_ceil is not None and math.isfinite(x_ceil):
        x_r = min(x_ceil, x_max)
        if x_r > x_min:
            ax.plot([x_min, x_r], [alt_ceiling, alt_ceiling],
                    color=color, linewidth=lw, linestyle=ls, zorder=5)

    # ── plot each segment ────────────────────────────────────────────────────
    label_placed = False
    last_xs = last_ys = None

    for seg, bot, top_seg in seg_bands:
        # Sample altitudes from top to bottom so the final sample is near alt_floor
        alts_seg = np.linspace(top_seg, max(bot, alt_floor), n_pts)
        st = seg['type'].lower()
        fn = _CONVERTERS[x_type].get(st)

        if fn is None:
            # seg_type == x_type → vertical line
            x_v = float(seg['value'])
            if x_min <= x_v <= x_max:
                y_top = min(top_seg, alt_ceiling)
                y_bot = max(bot,     alt_floor)
                kw = {'label': label} if not label_placed else {}
                ax.plot([x_v, x_v], [y_top, y_bot],
                        color=color, linewidth=lw, linestyle=ls, zorder=5, **kw)
                label_placed = True
                last_xs = np.array([x_v, x_v])
                last_ys = np.array([y_top, y_bot])
        else:
            xs_seg, ys_seg = [], []
            for alt in alts_seg:
                x = fn(seg['value'], alt)
                if x is not None and math.isfinite(x) and x_min <= x <= x_max:
                    xs_seg.append(x)
                    ys_seg.append(alt)
            if len(xs_seg) > 1:
                kw = {'label': label} if not label_placed else {}
                ax.plot(xs_seg, ys_seg,
                        color=color, linewidth=lw, linestyle=ls, zorder=5, **kw)
                label_placed = True
                last_xs = np.array(xs_seg)
                last_ys = np.array(ys_seg)

    # label at the bottom of the final segment
    if last_xs is not None and len(last_xs) > 0:
        _label_end(ax, last_xs, last_ys, f'  {label}',
                   color=color, fontsize=9, offset_x=3)


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
    max_alt_ceiling     = None
    chart_title         = cfg['title']

    mach_grid           = [0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.80, 0.84, 0.88, 0.92]
    kcas_grid           = [100, 150, 200, 250, 300, 350, 400]
    keas_grid           = [100, 150, 200, 250, 300, 350, 400]
    ktas_grid           = [100, 150, 200, 250, 300, 350, 400, 450, 500]
    speed_limits        = []        # legacy
    envelope_boundaries = []        # new segment-based boundaries

    # ---- load JSON ----
    if envelope_json:
        with open(envelope_json) as f:
            envelope = json.load(f)

        chart_title         = envelope.get('name', chart_title)
        chart_cfg           = envelope.get('chart', {})
        x_min               = chart_cfg.get(cfg['x_min_key'], x_min)
        x_max               = chart_cfg.get(cfg['x_max_key'], x_max)
        alt_min             = chart_cfg.get('alt_min', alt_min)
        alt_max             = chart_cfg.get('alt_max', alt_max)
        max_alt_ceiling     = envelope.get('max_altitude_ft', None)
        mach_grid           = envelope.get('mach_grid', mach_grid)
        kcas_grid           = envelope.get('kcas_grid', kcas_grid)
        keas_grid           = envelope.get('keas_grid', keas_grid)
        ktas_grid           = envelope.get('ktas_grid', ktas_grid)
        speed_limits        = envelope.get('speed_limits', [])
        envelope_boundaries = envelope.get('envelope_boundaries', [])

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

    # ---- constant KTAS lines ----
    for ktas in ktas_grid:
        fn = conv['ktas']
        if fn is None:
            # x-axis IS KTAS: draw vertical line
            ax.axvline(x=ktas, color='coral', linewidth=0.9, linestyle=':', zorder=2)
            ax.annotate(f'{ktas}', xy=(ktas, alt_max * 0.97), fontsize=6.5,
                        color='coral', ha='center', va='top', clip_on=True)
        else:
            xs, ys = _compute_line(fn, ktas, alts)
            mask = _in_bounds(xs, ys)
            if mask.sum() > 1:
                ax.plot(xs[mask], ys[mask], color='coral', linewidth=0.9,
                        linestyle=':', zorder=2)
                _label_end(ax, xs[mask], ys[mask], f'{ktas} KTAS',
                           color='coral', fontsize=7)

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

    # ---- envelope boundaries (segment-based) ----
    for boundary in envelope_boundaries:
        _plot_boundary(ax, boundary, x_type, x_min, x_max, alt_min, alt_max)

    # ---- legacy speed_limits ----
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

    # ---- max altitude ceiling annotation ----
    # Each envelope_boundary draws its own ceiling line clipped to its first segment,
    # so we only add an axhline here when no boundary already covers max_alt_ceiling.
    if max_alt_ceiling and alt_min < max_alt_ceiling <= alt_max:
        has_boundary_at_ceiling = any(
            abs(bnd.get('alt_ceiling', alt_max) - max_alt_ceiling) < 500
            for bnd in envelope_boundaries
        )
        if not has_boundary_at_ceiling:
            # Legacy fallback: full-width horizontal ceiling line
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
        Line2D([0], [0], color='coral',     linewidth=1.2, linestyle=':',  label='Constant KTAS'),
        Line2D([0], [0], color='steelblue', linewidth=1.2, linestyle='-',  label='Constant KCAS'),
        Line2D([0], [0], color='seagreen',  linewidth=1.2, linestyle='--', label='Constant KEAS'),
        Line2D([0], [0], color='gray',      linewidth=1.0, linestyle='-',  label='Constant Mach'),
    ]
    for bnd in envelope_boundaries:
        legend_elements.append(Line2D(
            [0], [0],
            color=bnd.get('color', 'black'),
            linewidth=bnd.get('linewidth', 2.0),
            linestyle=bnd.get('linestyle', '-'),
            label=bnd.get('label', ''),
        ))
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
