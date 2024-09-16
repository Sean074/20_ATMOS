import pandas as pd
import numpy as np


def select_atmos_data():
    df_atmos = pd.read_csv('./instance/standard_atmos.csv', comment="#")

    return df_atmos


def get_atmos_properties(h_press_ft,p_press_psf):
    df_atmos = select_atmos_data()

    # User Defined altitude h_press_ft
    if h_press_ft != False:     
        # Test request is "on table"
        hgeo_min = df_atmos["Hgeo_ft"].min()
        hgeo_max = df_atmos["Hgeo_ft"].max()

        # Test h within table
        if hgeo_min >= h_press_ft:
            print("ERROR: Altitude too low out of range")
            exit()
        elif hgeo_max <= h_press_ft:
            print("ERROR: Altitude too high out of range")
            exit()

        p_press_psf  = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["P_lb/ft3"])
        pho_ratio = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho/pho0"])
        pho_slug_ft3 = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho_slug/ft3"])

    else:
        # Test request is "on table"
        press_min = df_atmos["P_lb/ft3"].min()
        press_max = df_atmos["P_lb/ft3"].max()

        if press_min >= p_press_psf:
            print("ERROR: Pressure too low out of range")
            exit()
        elif press_max <= p_press_psf:
            print("ERROR: Pressure too high out of range")
            exit()      
        
        h_press_ft  = np.interp(p_press_psf, df_atmos["P_lb/ft3"], df_atmos["H_ft"])
        pho_ratio = np.interp(p_press_psf, df_atmos["P_lb/ft3"], df_atmos["pho/pho0"])
        pho_slug_ft3 = np.interp(p_press_psf, df_atmos["P_lb/ft3"], df_atmos["pho_slug/ft3"])

    output_df = {
        'h_press_ft':   h_press_ft,
        'p_static_psf': p_press_psf,
        'pho_ratio':    pho_ratio,
        'pho_slug_ft3': pho_slug_ft3,
    }

    return output_df




