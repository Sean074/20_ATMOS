import unit_convert as u_c
import atmos


def air_data_alt():
    h_press_user = float(input("Input pressure altitude: "))
    h_unit = input("Input units m/ft: ")

    flag = False

    while flag != True:
        if h_unit.lower() == "m":
            h_press_ft = h_press_user * u_c.M_FT
            flag = True
        elif h_unit.lower() == "ft":
            h_press_ft = h_press_user
            flag = True
        else:
            print("Input error: Select m or ft")
            h_unit = input("Input units m/ft: ")

    point_in_sky = atmos.get_atmos_properties(h_press_ft=h_press_ft,p_press_psf=False)

    # TODO Make this look pretty
    print(point_in_sky)

    return

def air_data_pres():
    press_user = float(input("Input pressure: "))
    press_unit = input("Input units pfs/psi/pa/atm/bar: ")

    flag = False

    while flag != True:
        if press_unit.lower() == "psi":
            press_psi = press_user * u_c.PSI_PSF
            flag = True
        elif press_unit.lower() == "pa":
            press_psi = press_user * u_c.PA_PSF
            flag = True
        elif press_unit.lower() == "atm":
            press_psi = press_user * u_c.ATM_PSF
            flag = True
        elif press_unit.lower() == "bar":
            press_psi = press_user * u_c.BAR_PSF
            flag = True
        else:
            print("Input error: Select pfs/psi/pa/atm/bar")
            press_unit = input("Input units pfs/psi/pa/atm/bar: ")

    point_in_sky = atmos.get_atmos_properties(h_press_ft=False,p_press_psf=press_psi)

    # TODO Make this look pretty
    print(point_in_sky)

    return

def alt_mach():
    pass


def alt_true():
    pass

def alt_cal():
    pass


def alt_equiv():
    pass