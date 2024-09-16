import menue

MENU_PROMPT = """-- Menue --

Atmospheric Properties
1.1) Given pressure altitude
1.2) GIven static pressure

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
            # TODO save some data to a log
        except KeyError:
            print("Invlaid input selected. Please try again.")


MENUE_OPTIONS = {
    "1.1": menue.air_data_alt,
    "1.2": menue.air_data_pres,
    "2.1": menue.alt_mach,
    "2.2": menue.alt_true,
    "2.3": menue.alt_cal,
    "2.4": menue.alt_equiv,
}

# TODO open a new log file
menue_func()
print("Hope this was useful. Bye now see you soon.")
