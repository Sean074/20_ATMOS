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
    print("==================================================\n")

    return


def print_speed(speeds):
    print("\n======== ATMOS ==================================")
    print("Speeds")
    print(f"Mach: {speeds['Mach']:.3f}")
    print(f"KTAS: {speeds['ktas']:.1f} kts")
    print(f"KEAS: {speeds['keas']:.1f} kts")
    print(f"KCAS: {speeds['kcas']:.1f} kts")
    print(f"Dynamic pressure: {speeds['q']:.3f} psf")
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
        
        output_df = {
            'h_press_ft':   h_press_ft,
            'p_static_psf': p_press_psf,
            'pho_ratio':    pho_ratio,
            'pho_slug_ft3': pho_slug_ft3,
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


def mach_alt(speed,alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    # TODO make it good for supersonic flight

    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.47  # sealevel speed of sound kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    gamma = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(gamma*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    Mach = speed
    ktas = Mach * a_local
    keas = ktas * math.sqrt(pho_ratio)
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

def tas_alt(speed,alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    # TODO make it good for supersonic flight
    
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.47  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    gamma = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(gamma*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    ktas = speed
    Mach = ktas / a_local
    keas = ktas * math.sqrt(pho_ratio)
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

def eas_alt(speed,alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    # TODO make it good for supersonic flight
  
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.47  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    gamma = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(gamma*p_static/pho)*0.5924838  # kts
    
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

def eas_alt(speed,alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    # TODO make it good for supersonic flight
   
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.47  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    gamma = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(gamma*p_static/pho)*0.5924838  # kts
    
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

def cas_alt(speed,alt_defined):
    # TODO convert a_0 to calcualted from user supplied atmos data
    # TODO make it good for supersonic flight
     
    df_atmos = select_atmos_data()

    # Constants
    a_0 = 661.47  # kts
    p_0 = df_atmos.loc[df_atmos["Hgeo_ft"]==0, "P_lb/ft2"].values[0] 
    gamma = 1.4     # ratio of specific heats for air

    # Get the atmos properties for the user selected altitude.
    atmos_alt = get_atmos_prop_alt(alt_defined)
    p_static = atmos_alt['p_static_psf']
    pho = atmos_alt['pho_slug_ft3']
    pho_ratio = atmos_alt['pho_ratio']
    a_local = math.sqrt(gamma*p_static/pho)*0.5924838  # kts
    
    # Calculate speed Sub Sonic
    kcas = speed
    q_ =  p_0*((0.2*(kcas/a_0)**2+1)**(7/2)-1)
    Mach = math.sqrt(5*((q_/p_static+1)**(2/7)-1))
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
