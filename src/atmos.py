import pandas as pd
import numpy as np
import math


# ---------------------------------------------------------------------------
# Exception types
# ---------------------------------------------------------------------------

class AtmosRangeError(ValueError):
    """Raised when input altitude or pressure is outside the model's valid range."""


# ---------------------------------------------------------------------------
# Physical constants — do not edit; these are thermodynamic facts, not settings.
# Tunable solver parameters live in config/defaults.json.
# ---------------------------------------------------------------------------
GAMMA = 1.4           # ratio of specific heats for dry air
A_0_KTS = 661.4745    # sea-level speed of sound, knots (ISA)
P_0_PSF = 2116.224    # sea-level reference pressure, psf (ISA)
_KTS_FACTOR = 0.5924838  # converts sqrt(psf / (slug/ft³)) → knots

_atmos_csv_path = './instance/standard_atmos.csv'


def set_atmos_model(path):
    global _atmos_csv_path
    _atmos_csv_path = path


def select_atmos_data():
    return pd.read_csv(_atmos_csv_path, comment="#")


# ---------------------------------------------------------------------------
# Private formula helpers
# ---------------------------------------------------------------------------

def _dynamic_pressure(mach, p_static):
    """Compressible dynamic pressure q_c (psf), valid subsonic and supersonic."""
    if mach <= 1.0:
        return p_static * ((1 + 0.2 * mach ** 2) ** (7 / 2) - 1)
    q_a = (GAMMA + 1) / 2 * mach ** 2
    q_b = (((1 + GAMMA) ** 2 * mach ** 2) / (4 * GAMMA * mach ** 2 - 2 * (GAMMA - 1))) ** (1 / (GAMMA - 1))
    return (q_a * q_b - 1) * p_static


def _kcas_from_qc(q_c):
    """KCAS from impact pressure q_c (psf). Handles supersonic CAS automatically."""
    kcas = A_0_KTS * math.sqrt(5 * ((q_c / P_0_PSF + 1) ** (2 / 7) - 1))
    if kcas > A_0_KTS:
        kcas = vcas_super(q_c)
    return kcas


# ---------------------------------------------------------------------------
# Atmospheric property lookups
# ---------------------------------------------------------------------------

def get_atmos_prop_alt(h_press_ft):
    df = select_atmos_data()

    hgeo_min = df["Hgeo_ft"].min()
    hgeo_max = df["Hgeo_ft"].max()

    if h_press_ft <= hgeo_min:
        raise AtmosRangeError(
            f"Altitude {h_press_ft} ft too low — valid range {hgeo_min} to {hgeo_max} ft"
        )
    if h_press_ft >= hgeo_max:
        raise AtmosRangeError(
            f"Altitude {h_press_ft} ft too high — valid range {hgeo_min} to {hgeo_max} ft"
        )

    return {
        'h_press_ft':   h_press_ft,
        'p_static_psf': np.interp(h_press_ft, df["Hgeo_ft"], df["P_lb/ft2"]),
        'pho_ratio':    np.interp(h_press_ft, df["Hgeo_ft"], df["pho/pho0"]),
        'pho_slug_ft3': np.interp(h_press_ft, df["Hgeo_ft"], df["pho_slug/ft3"]),
        'temp_degR':    np.interp(h_press_ft, df["Hgeo_ft"], df["T_degR"]),
    }


def get_atmos_prop_pres(p_press_psf):
    df = select_atmos_data()

    press_min = df["P_lb/ft2"].min()
    press_max = df["P_lb/ft2"].max()

    if p_press_psf <= press_min:
        raise AtmosRangeError(
            f"Pressure {p_press_psf} psf too low — valid range {press_min} to {press_max} psf"
        )
    if p_press_psf >= press_max:
        raise AtmosRangeError(
            f"Pressure {p_press_psf} psf too high — valid range {press_min} to {press_max} psf"
        )

    # interp requires x values to be ascending; pressure decreases with altitude
    df_sorted = df.sort_values(by=["P_lb/ft2"])
    return {
        'h_press_ft':   np.interp(p_press_psf, df_sorted["P_lb/ft2"], df_sorted["H_ft"]),
        'p_static_psf': p_press_psf,
        'pho_ratio':    np.interp(p_press_psf, df_sorted["P_lb/ft2"], df_sorted["pho/pho0"]),
        'pho_slug_ft3': np.interp(p_press_psf, df_sorted["P_lb/ft2"], df_sorted["pho_slug/ft3"]),
        'temp_degR':    np.interp(p_press_psf, df_sorted["P_lb/ft2"], df_sorted["T_degR"]),
    }


# ---------------------------------------------------------------------------
# Supersonic iterative solvers
# ---------------------------------------------------------------------------

def vcas_super(q_c):
    """VCAS (kts) from compressible dynamic pressure — supersonic only (VCAS > Mach 1)."""
    from config import APP_CONFIG
    cfg = APP_CONFIG["solver"]
    delta = cfg["vcas_super_initial_delta_kts"]
    error_percent = cfg["vcas_super_error_percent"]

    vcas_guess = A_0_KTS
    error_target = error_percent * q_c
    error = error_target + 1

    while abs(error) >= error_target:
        q_a = (GAMMA + 1) / 2 * (vcas_guess / A_0_KTS) ** 2
        q_b = (((1 + GAMMA) ** 2) / (4 * GAMMA - 2 * (GAMMA - 1) * (A_0_KTS / vcas_guess) ** 2)) ** (1 / (GAMMA - 1))
        q_guess = (q_a * q_b - 1) * P_0_PSF

        error = q_c - q_guess

        if abs(error) <= error_target:
            pass
        elif error > 0:
            vcas_guess += delta
        else:
            delta /= 2
            vcas_guess -= delta

        if vcas_guess < A_0_KTS:
            raise RuntimeError("vcas_super: iteration diverged below Mach 1")

    return vcas_guess


def mach_super(q_c, p_static):
    """Mach from compressible dynamic pressure — supersonic only (Mach > 1)."""
    from config import APP_CONFIG
    cfg = APP_CONFIG["solver"]
    delta = cfg["mach_super_initial_delta"]
    error_percent = cfg["mach_super_error_percent"]

    Mach_guess = 1.0
    error_target = error_percent * q_c
    error = error_target + 1

    while abs(error) >= error_target:
        q_a = (GAMMA + 1) / 2 * Mach_guess ** 2
        q_b = (((1 + GAMMA) ** 2) / (4 * GAMMA - 2 * (GAMMA - 1) * (1 / Mach_guess) ** 2)) ** (1 / (GAMMA - 1))
        q_guess = (q_a * q_b - 1) * p_static

        error = q_c - q_guess

        if abs(error) <= error_target:
            pass
        elif error > 0:
            Mach_guess += delta
        else:
            delta /= 2
            Mach_guess -= delta

        if Mach_guess < 1.0:
            raise RuntimeError("mach_super: iteration diverged below Mach 1")

    return Mach_guess


# ---------------------------------------------------------------------------
# Speed conversions — each returns {Mach, ktas, keas, kcas, q_c}
# ---------------------------------------------------------------------------

def mach_alt(speed, alt_defined):
    """Given Mach and pressure altitude (ft), return all airspeeds."""
    atmos = get_atmos_prop_alt(alt_defined)
    p_static = atmos['p_static_psf']
    pho = atmos['pho_slug_ft3']
    pho_ratio = atmos['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * _KTS_FACTOR

    Mach = speed
    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)
    q_ = _dynamic_pressure(Mach, p_static)
    kcas = _kcas_from_qc(q_)

    return {"Mach": Mach, "ktas": ktas, "keas": keas, "q_c": q_, "kcas": kcas}


def tas_alt(speed, alt_defined):
    """Given KTAS and pressure altitude (ft), return all airspeeds."""
    atmos = get_atmos_prop_alt(alt_defined)
    p_static = atmos['p_static_psf']
    pho = atmos['pho_slug_ft3']
    pho_ratio = atmos['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * _KTS_FACTOR

    ktas = speed
    Mach = ktas / a_local
    keas = ktas * math.sqrt(pho_ratio)
    q_ = _dynamic_pressure(Mach, p_static)
    kcas = _kcas_from_qc(q_)

    return {"Mach": Mach, "ktas": ktas, "keas": keas, "q_c": q_, "kcas": kcas}


def eas_alt(speed, alt_defined):
    """Given KEAS and pressure altitude (ft), return all airspeeds."""
    atmos = get_atmos_prop_alt(alt_defined)
    p_static = atmos['p_static_psf']
    pho = atmos['pho_slug_ft3']
    pho_ratio = atmos['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * _KTS_FACTOR

    keas = speed
    ktas = keas / math.sqrt(pho_ratio)
    Mach = ktas / a_local
    q_ = _dynamic_pressure(Mach, p_static)
    kcas = _kcas_from_qc(q_)

    return {"Mach": Mach, "ktas": ktas, "keas": keas, "q_c": q_, "kcas": kcas}


def cas_alt(speed, alt_defined):
    """Given KCAS and pressure altitude (ft), return all airspeeds."""
    atmos = get_atmos_prop_alt(alt_defined)
    p_static = atmos['p_static_psf']
    pho = atmos['pho_slug_ft3']
    pho_ratio = atmos['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * _KTS_FACTOR

    kcas = speed
    if kcas <= A_0_KTS:
        q_ = P_0_PSF * ((0.2 * (kcas / A_0_KTS) ** 2 + 1) ** (7 / 2) - 1)
    else:
        q_a = (GAMMA + 1) / 2 * (kcas / A_0_KTS) ** 2
        q_b = (((1 + GAMMA) ** 2) / (4 * GAMMA - 2 * (GAMMA - 1) * (A_0_KTS / kcas) ** 2)) ** (1 / (GAMMA - 1))
        q_ = (q_a * q_b - 1) * P_0_PSF

    Mach = math.sqrt(5 * ((q_ / p_static + 1) ** (2 / 7) - 1))
    if Mach > 1.0:
        Mach = mach_super(q_, p_static)

    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)

    return {"Mach": Mach, "ktas": ktas, "keas": keas, "q_c": q_, "kcas": kcas}
