import atmos
import pandas as pd

def tas_alt(alt_array, ktas_array):
    
    mach = 12
    mach_array = [{f'0.2 {mach}': [], '0.4': [], '0.6': [], '0.7': []}]

