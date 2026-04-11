import pandas as pd
import numpy as np
import math


def select_atmos_data():
    df_atmos = pd.read_csv('./instance/standard_atmos.csv', comment="#")
    return df_atmos


def get_atmos_prop_alt(h_press_ft):
    df_atmos = select_atmos_data()

    hgeo_min = df_atmos["Hgeo_ft"].min()
    hgeo_max = df_atmos["Hgeo_ft"].max()

    if hgeo_min >= h_press_ft:
        print(f"ERROR: Altitude {h_press_ft} ft too low — valid range {hgeo_min} to {hgeo_max} ft")
        return "ERROR"
    elif hgeo_max <= h_press_ft:
        print(f"ERROR: Altitude {h_press_ft} ft too high — valid range {hgeo_min} to {hgeo_max} ft")
        return "ERROR"

    p_press_psf  = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["P_lb/ft2"])
    pho_ratio    = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho/pho0"])
    pho_slug_ft3 = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho_slug/ft3"])
    temp_degR    = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["T_degR"])

    return {
        'h_press_ft':   h_press_ft,
        'p_static_psf': p_press_psf,
        'pho_ratio':    pho_ratio,
        'pho_slug_ft3': pho_slug_ft3,
        'temp_degR':    temp_degR,
    }


def get_atmos_prop_pres(p_press_psf):
    df_atmos = select_atmos_data()

    press_min = df_atmos["P_lb/ft2"].min()
    press_max = df_atmos["P_lb/ft2"].max()

    if press_min >= p_press_psf:
        print(f"ERROR: Pressure {p_press_psf} psf too low — valid range {press_min} to {press_max} psf")
        return "ERROR"
    elif press_max <= p_press_psf:
        print(f"ERROR: Pressure {p_press_psf} psf too high — valid range {press_min} to {press_max} psf")
        return "ERROR"

    # interp requires x values to be ascending; pressure decreases with altitude
    df_atmos_sort_p = df_atmos.sort_values(by=["P_lb/ft2"])
    h_press_ft   = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["H_ft"])
    pho_ratio    = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["pho/pho0"])
    pho_slug_ft3 = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["pho_slug/ft3"])
    temp_degR    = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["T_degR"])

    return {
        'h_press_ft':   h_press_ft,
        'p_static_psf': p_press_psf,
        'pho_ratio':    pho_ratio,
        'pho_slug_ft3': pho_slug_ft3,
        'temp_degR':    temp_degR,
    }


def vcas_super(q_c, delta=10, error_percent=0.001):
    # Finds vcas from compressible dynamic pressure for supersonic.
    # Only valid when vcas > sea-level Mach 1.

    # TODO make these be defined outside these functions
    GAMMA = 1.4
    Mach_ref = 661.4745  # reference speed of sound at sea level in kts
    p_ref = 2116.2       # sea-level reference pressure in psf

    vcas_guess = Mach_ref
    error_target = error_percent * q_c
    error = error_target + 1

    while abs(error) >= error_target:
        q_a = (GAMMA + 1) / 2 * (vcas_guess / Mach_ref) ** 2
        q_b = (((1 + GAMMA) ** 2) / (4 * GAMMA - 2 * (GAMMA - 1) * (Mach_ref / vcas_guess) ** 2)) ** (1 / (GAMMA - 1))
        q_guess = (q_a * q_b - 1) * p_ref

        error = q_c - q_guess

        if abs(error) <= error_target:
            pass
        elif error > 0:
            vcas_guess = vcas_guess + delta
        else:
            delta = delta / 2
            vcas_guess = vcas_guess - delta

        if vcas_guess < Mach_ref:
            print('ERROR: VCAS calculation erroneous')
            exit()

    return vcas_guess


def mach_super(q_c, p_static, delta=0.1, error_percent=0.001):
    # Finds Mach from compressible dynamic pressure for supersonic.
    # Only valid when Mach > 1.

    # TODO make these be defined outside these functions
    GAMMA = 1.4

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
            Mach_guess = Mach_guess + delta
        else:
            delta = delta / 2
            Mach_guess = Mach_guess - delta

        if Mach_guess < 1.0:
            print('ERROR: Mach calculation erroneous')
            exit()

    return Mach_guess


def mach_alt(speed, alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data
    # TODO get the constants out of the function, set them global

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # sea-level speed of sound in kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"] == 0, "P_lb/ft2"].values[0]
    GAMMA = 1.4     # ratio of specific heats for air

    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * 0.5924838  # kts

    Mach = speed
    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)

    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach ** 2) ** (7 / 2) - 1)
    else:
        q_a = (GAMMA + 1) / 2 * Mach ** 2
        q_b = (((1 + GAMMA) ** 2 * Mach ** 2) / (4 * GAMMA * Mach ** 2 - 2 * (GAMMA - 1))) ** (1 / (GAMMA - 1))
        q_ = (q_a * q_b - 1) * p_static

    kcas = a_0 * math.sqrt(5 * ((q_ / p_0 + 1) ** (2 / 7) - 1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    return {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c":  q_,
        "kcas": kcas,
    }


def tas_alt(speed, alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"] == 0, "P_lb/ft2"].values[0]
    GAMMA = 1.4     # ratio of specific heats for air

    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * 0.5924838  # kts

    ktas = speed
    Mach = ktas / a_local
    keas = ktas * math.sqrt(pho_ratio)

    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach ** 2) ** (7 / 2) - 1)
    else:
        q_a = (GAMMA + 1) / 2 * Mach ** 2
        q_b = (((1 + GAMMA) ** 2 * Mach ** 2) / (4 * GAMMA * Mach ** 2 - 2 * (GAMMA - 1))) ** (1 / (GAMMA - 1))
        q_ = (q_a * q_b - 1) * p_static

    kcas = a_0 * math.sqrt(5 * ((q_ / p_0 + 1) ** (2 / 7) - 1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    return {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c":  q_,
        "kcas": kcas,
    }


def eas_alt(speed, alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"] == 0, "P_lb/ft2"].values[0]
    GAMMA = 1.4     # ratio of specific heats for air

    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * 0.5924838  # kts

    keas = speed
    ktas = keas / math.sqrt(pho_ratio)
    Mach = ktas / a_local

    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach ** 2) ** (7 / 2) - 1)
    else:
        q_a = (GAMMA + 1) / 2 * Mach ** 2
        q_b = (((1 + GAMMA) ** 2 * Mach ** 2) / (4 * GAMMA * Mach ** 2 - 2 * (GAMMA - 1))) ** (1 / (GAMMA - 1))
        q_ = (q_a * q_b - 1) * p_static

    kcas = a_0 * math.sqrt(5 * ((q_ / p_0 + 1) ** (2 / 7) - 1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    return {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c":  q_,
        "kcas": kcas,
    }


def cas_alt(speed, alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"] == 0, "P_lb/ft2"].values[0]
    GAMMA = 1.4     # ratio of specific heats for air

    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA * p_static / pho) * 0.5924838  # kts

    kcas = speed
    if kcas <= a_0:
        q_ = p_0 * ((0.2 * (kcas / a_0) ** 2 + 1) ** (7 / 2) - 1)
    else:
        q_a = (GAMMA + 1) / 2 * (kcas / a_0) ** 2
        q_b = (((1 + GAMMA) ** 2) / (4 * GAMMA - 2 * (GAMMA - 1) * (a_0 / kcas) ** 2)) ** (1 / (GAMMA - 1))
        q_ = (q_a * q_b - 1) * p_0

    Mach = math.sqrt(5 * ((q_ / p_static + 1) ** (2 / 7) - 1))
    if Mach > 1.0:
        Mach = mach_super(q_, p_static)

    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)

    return {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c":  q_,
        "kcas": kcas,
    }
