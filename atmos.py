import pandas as pd
import numpy as np
import math


def select_atmos_data():
    df_atmos = pd.read_csv('./instance/standard_atmos.csv', comment="#")

    return df_atmos


def print_atmos(point_in_sky):
    # TODO Let the user pick output units
    print("\n======== ATMOS ==================================")
    print("Point in the sky properties:")
    print(f"Pressure Altitude [ft]: {point_in_sky['h_press_ft']:.1f}")
    print(f"Pressure Static [psf]: {point_in_sky['p_static_psf']:.3f}")
    print(f"Density Ratio: {point_in_sky['pho_ratio']:.3f}")
    print(f"Air Density: [slug/ft^3]: {point_in_sky['pho_slug_ft3']:.3e}")
    print(f"Air temperature: [degR]: {point_in_sky['temp_degR']:.1f}")
    print("==================================================\n")

    return


def print_speed(speeds):
    print("\n======== ATMOS ==================================")
    print("Speeds")
    print(f"Mach: {speeds['Mach']:.3f}")
    print(f"KTAS: {speeds['ktas']:.1f} kts")
    print(f"KEAS: {speeds['keas']:.1f} kts")
    print(f"KCAS: {speeds['kcas']:.1f} kts")
    print(f"Dynamic pressure: {speeds['q_c']:.3f} psf")
    print("==================================================\n")

    return    


def get_atmos_prop_alt(h_press_ft):
    df_atmos = select_atmos_data()

    # Test request is "on table"
    hgeo_min = df_atmos["Hgeo_ft"].min()
    hgeo_max = df_atmos["Hgeo_ft"].max()

    print(f"hgeo_min {hgeo_min} and h_press_ft {h_press_ft}")

    # Test h within table
    if hgeo_min >= h_press_ft:
        print(f"ERROR: Altitude {h_press_ft} ft too low out of range {hgeo_min} to {hgeo_max} ft")
        output_df = "ERROR"
    elif hgeo_max <= h_press_ft:
        print(f"ERROR: Altitude {h_press_ft} ft too high out of range {hgeo_max} to {hgeo_max} ft")
        output_df = "ERROR"
    else:
        p_press_psf  = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["P_lb/ft2"])
        pho_ratio = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho/pho0"])
        pho_slug_ft3 = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho_slug/ft3"])
        temp_degR = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["T_degR"])
        
        output_df = {
            'h_press_ft':   h_press_ft,
            'p_static_psf': p_press_psf,
            'pho_ratio':    pho_ratio,
            'pho_slug_ft3': pho_slug_ft3,
            'temp_degR':    temp_degR,
        }
    return output_df


def get_atmos_prop_pres(p_press_psf):
    df_atmos = select_atmos_data()
    # Test request is "on table"

    press_min = df_atmos["P_lb/ft2"].min()
    press_max = df_atmos["P_lb/ft2"].max()

    if press_min >= p_press_psf:
        print(f"ERROR: Altitude {p_press_psf} psf too low out of range {press_min} to {press_max} psf")
        output_df = "ERROR"
    elif press_max <= p_press_psf:
        print(f"ERROR: Altitude {p_press_psf} psf too low out of range {press_min} to {press_max} psf")
        output_df = "ERROR"      
    else:
        # Interp requires the x value ot be asending.
        df_atmos_sort_p = df_atmos.sort_values(by=["P_lb/ft2"])
        h_press_ft  = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["H_ft"])
        pho_ratio = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["pho/pho0"])
        pho_slug_ft3 = np.interp(p_press_psf, df_atmos_sort_p["P_lb/ft2"], df_atmos_sort_p["pho_slug/ft3"])

        output_df = {
            'h_press_ft':   h_press_ft,
            'p_static_psf': p_press_psf,
            'pho_ratio':    pho_ratio,
            'pho_slug_ft3': pho_slug_ft3,
        }

    return output_df

def vcas_super(q_c, delta = 10, error_percent = 0.001):
    # Finds the vcas from the compressible dynamic pressure for supersonic
    # note only valid vcas > sea level Mach = 1

    # Constants
    # TODO make these be defined outside these functions
    GAMMA = 1.4
    Mach_ref = 661.4745 # reference Mach in kts at sea level
    p_ref = 2116.2 # refernce pressure in psi at sea level

    vcas_guess = Mach_ref
    error_target = error_percent*q_c
    error = error_target + 1
    count = 0

    while abs(error) >= error_target:
        count = count + 1

        q_a = (GAMMA+1)/2 * (vcas_guess/Mach_ref)**2
        q_b = (((1+GAMMA)**2) / (4*GAMMA - 2*(GAMMA-1)*(Mach_ref/vcas_guess)**2))**(1/(GAMMA-1))
        q_guess = (q_a * q_b - 1) * p_ref
        
        error = q_c - q_guess
        
        if abs(error) <= error_target:
            vcas_guess = vcas_guess
        elif error > 0:  # march up
            delta = delta
            vcas_guess = vcas_guess + delta
        else:  # bracket
            delta = delta/2
            vcas_guess = vcas_guess - delta

        vcas_est = vcas_guess

        if vcas_est < Mach_ref:
            print('ERROR: VCAS calculation erronious')
            exit()

    return vcas_est
        
def mach_super(q_c, p_static, delta = 0.1, error_percent = 0.001):
    # Finds the vcas from the compressible dynamic pressure for supersonic
    # note only valid vcas > sea level Mach = 1

    # Constants
    # TODO make these be defined outside these functions
    GAMMA = 1.4

    Mach_guess = 1.0
    error_target = error_percent*q_c
    error = error_target + 1
    count = 0

    while abs(error) >= error_target:
        count = count + 1

        q_a = (GAMMA+1)/2 * (Mach_guess)**2
        q_b = (((1+GAMMA)**2) / (4*GAMMA - 2*(GAMMA-1)*(1/Mach_guess)**2))**(1/(GAMMA-1))
        q_guess = (q_a * q_b - 1) * p_static
        
        error = q_c - q_guess
        
        if abs(error) <= error_target:
            Mach_guess = Mach_guess
        elif error > 0:  # march up
            delta = delta
            Mach_guess = Mach_guess + delta
        else:  # bracket
            delta = delta/2
            MAch_guess = Mach_guess - delta

        Mach_est = Mach_guess

        if Mach_est < 1.0:
            print('ERROR: Mach calculation erronious')
            exit()

    return Mach_est


def mach_alt(speed,alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data
    # TODO get the constants out of the function, set them global

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # sealevel speed of sound kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0]
    print(f"ref Pressure sea level {p_0}")
    GAMMA = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    Mach = speed
    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)

    # Need to determine if Super or Sub Sonic dynamic pressure used.
    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach**2)**(7/2)-1)
    else:
        q_a = (GAMMA+1)/2 * Mach**2
        q_b = (((1+GAMMA)**2 * Mach**2) / (4*GAMMA*Mach**2 - 2*(GAMMA-1)))**(1/(GAMMA-1))
        q_ = (q_a * q_b - 1) * p_static

    # Note vcas calibration is based on vcas > sea level speed of sound (not local) calibration
    kcas = a_0 * math.sqrt(5*((q_/p_0+1)**(2/7)-1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    speed_df = {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c": q_,
        "kcas": kcas,
    }

    return speed_df

def tas_alt(speed, alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    GAMMA = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    ktas = speed
    Mach = ktas / a_local
    keas = ktas * math.sqrt(pho_ratio)

    # Need to determine if Super or Sub Sonic dynamic pressure used.
    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach**2)**(7/2)-1)
    else:
        q_a = (GAMMA+1)/2 * Mach**2
        q_b = (((1+GAMMA)**2 * Mach**2) / (4*GAMMA*Mach**2 - 2*(GAMMA-1)))**(1/(GAMMA-1))
        q_ = (q_a * q_b - 1) * p_static

    # Note vcas calibration is based on vcas > sea level speed of sound (not local) calibration
    kcas = a_0 * math.sqrt(5*((q_/p_0+1)**(2/7)-1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    speed_df = {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c": q_,
        "kcas": kcas,
    }

    return speed_df

def eas_alt(speed, alt_defined):
    # TODO convert a_0 to calculated from user supplied atmos data
  
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    GAMMA = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    keas = speed
    ktas = keas / math.sqrt(pho_ratio)
    Mach = ktas / a_local

    # Need to determine if Super or Sub Sonic dynamic pressure used.
    if Mach <= 1.0:
        q_ = p_static * ((1 + 0.2 * Mach**2)**(7/2)-1)
    else:
        q_a = (GAMMA+1)/2 * Mach**2
        q_b = (((1+GAMMA)**2 * Mach**2) / (4*GAMMA*Mach**2 - 2*(GAMMA-1)))**(1/(GAMMA-1))
        q_ = (q_a * q_b - 1) * p_static

    # Note vcas calibration is based on vcas > sea level speed of sound (not local) calibration
    kcas = a_0 * math.sqrt(5*((q_/p_0+1)**(2/7)-1))
    if kcas > a_0:
        kcas = vcas_super(q_)

    speed_df = {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q_c": q_,
        "kcas": kcas,
    }

    return speed_df

def eas_alt(speed, alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
   
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    GAMMA = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    keas = speed
    ktas = keas / math.sqrt(pho_ratio)
    Mach = ktas / a_local
    q_ = p_static * ((1 + 0.2 * Mach**2)**(7/2)-1)
    kcas = a_0 * math.sqrt(5*((q_/p_0+1)**(2/7)-1))

    speed_df = {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q": q_,
        "kcas": kcas,
    }

    return speed_df

def cas_alt(speed, alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
     
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.4745  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    GAMMA = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(GAMMA*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    kcas = speed
    # Check if the supersonics or subsonic verion of vcas q_c is used
    if kcas <= a_0:
        q_ =  p_0*((0.2*(kcas/a_0)**2+1)**(7/2)-1)
    else:
        q_a = (GAMMA+1)/2 * (kcas/a_0)**2
        q_b = (((1+GAMMA)**2) / (4*GAMMA - 2*(GAMMA-1)*(a_0/kcas)**2))**(1/(GAMMA-1))
        q_= (q_a * q_b - 1) * p_0

    # Check of the superonic or subsonic verion of Mach and vtas is used
    Mach = math.sqrt(5*((q_/p_static+1)**(2/7)-1))
    if Mach <= 1.0:
        Mach = math.sqrt(5*((q_/p_static+1)**(2/7)-1))
    else:
        Mach = mach_super(q_, p_static)

    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)

    speed_df = {
        "Mach": Mach,
        "ktas": ktas,
        "keas": keas,
        "q": q_,
        "kcas": kcas,
    }

    return speed_df
