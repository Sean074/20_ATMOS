import pandas as pd
import numpy as np


def select_atmos_data():
    df_atmos = pd.read_csv('./instance/standard_atmos.csv', comment="#")

    return df_atmos


def get_atmos_properties(h_press_ft):
    df_atmos = select_atmos_data()
        
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

    p_static_psf  = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["P_lb/ft3"])
    pho_ratio = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho/pho0"])
    pho_slug_ft3 = np.interp(h_press_ft, df_atmos["Hgeo_ft"], df_atmos["pho_slug/ft3"])

    output_df = {
        'h_press_ft':   h_press_ft,
        'p_static_psf': p_static_psf,
        'pho_ratio':    pho_ratio,
        'pho_slug_ft3': pho_slug_ft3,
    }

    return output_df




