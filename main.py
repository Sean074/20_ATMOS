import pandas as pd
import menue

MENU_PROMPT = """-- Menue --

Atmospheric Properties
1.1) Given alt

Speed Conversion
2.1) Alt and Mach
2.2) Alt and True
2.3) Alt and Calibrated
2.4) Alt and Equivilent

Exit/Quit
q) Quit/Exit

Enter your choice: """

def menue_func():
    while (selection := input(MENU_PROMPT)) != "q":
        try:
            MENUE_OPTIONS[selection]()
        except KeyError:
            print("Invlaid input selected. Please try again.")


MENUE_OPTIONS = {
    "1.1": menue.air_data,
    "2.1": menue.alt_mach,
    "2.2": menue.alt_true,
    "2.3": menue.alt_cal,
    "2.4": menue.alt_equiv,
}


menue_func()