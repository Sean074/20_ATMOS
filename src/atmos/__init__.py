"""ATMOS computation engine — standard atmosphere lookups and airspeed conversions.

The chart module is not imported here (it pulls in matplotlib); use
``from atmos import plot_speed_alt`` when charts are needed.
"""
from .core import (
    A_0_KTS,
    ENVELOPES_DIR,
    GAMMA,
    MODELS_DIR,
    P_0_PSF,
    AtmosRangeError,
    cas_alt,
    eas_alt,
    get_atmos_prop_alt,
    get_atmos_prop_pres,
    list_envelopes,
    list_models,
    mach_alt,
    mach_super,
    select_atmos_data,
    set_atmos_model,
    tas_alt,
    use_model,
    vcas_super,
)
from .version import __author__, __version__
