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
    print(f"Pressure Altitude [ft]: {point_in_sky['h_press_ft']}")
    print(f"Pressure Static [psf]: {point_in_sky['p_static_psf']}")
    print(f"Density Ratio: {point_in_sky['pho_ratio']}")
    print(f"Air Density: [slug/ft^3]: {point_in_sky['pho_slug_ft3']}")
    print("==================================================\n")


def get_atmos_properties(h_press_ft,p_press_psf):
    df_atmos = select_atmos_data()

    # User Defined altitude h_press_ft
    if p_press_psf == "NA":  
        # Test request is "on table"
        hgeo_min = df_atmos["Hgeo_ft"].min()
        hgeo_max = df_atmos["Hgeo_ft"].max()

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


    else:
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


def mach_alt(speed_defined,alt_defined):
    
    a_0        = 661.47  # kts
    gamma      = 1.4     # ratio of specific heats for air

    aTarget    = math.sqrt(gamma*atmos['p_static_psf']/atmos['pho_slug_ft3'])*0.5924838  # kts, p [], pho []

    MachTarget = speed_defined
    KTASTarget = aTarget*MachTarget
    KEASTarget = KTASTarget*math.sqrt(atmos['pho_ratio'])
    qTarget    = atmos['p_static_psf']*((1+0.2*MachTarget**2)**(7/2)-1)
    KCASTarget = a_0*math.sqrt(5*((qTarget/p_0+1)**(2/7)-1))