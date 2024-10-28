import menu

MENU_PROMPT = """-- Menu --

Atmospheric Properties
1.1) Given pressure altitude
1.2) Given static pressure

Speed Conversion (Subsonic or Supersonic)
2.1) Alt and Mach
2.2) Alt and True
2.3) Alt and Calibrated
2.4) Alt and Equivilent

Create Speed Altitude Chart (in development)
3.1) KTAS vs Alt
3.2) KCAS vs Alt
3.3) KEAS vs Alt

Exit/Quit
q) Quit/Exit

Enter your choice: """

def menu_func():
    while (selection := input(MENU_PROMPT)) != "q":
        try:
            MENU_OPTIONS[selection]()
            # TODO save some data to a log
        except KeyError:
            print("Invalid input selected. Please try again.")


MENU_OPTIONS = {
    "1.1": menu.air_data_alt,
    "1.2": menu.air_data_pres,
    "2.1": menu.alt_mach,
    "2.2": menu.alt_true,
    "2.3": menu.alt_cal,
    "2.4": menu.alt_equiv,
    "3.1": menu.speed_alt_ktas,
    "3.2": menu.speed_alt_kcas,
    "3.3": menu.speed_alt_keas,
}

# TODO open a new log file
menu_func()
print("Hope this was useful. Bye now, see you soon.")
