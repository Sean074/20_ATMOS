import unit_convert as u_c
import atmos





def pressure_convert(press_user,press_unit):

    flag = False

    while flag != True:
        if press_unit.lower() == "psi":
            press_psf = press_user * u_c.PSI_PSF
            flag = True
        elif press_unit.lower() == "psf":
            press_psf = press_user * 1.0
            flag = True
        elif press_unit.lower() == "pa":
            press_psf = press_user * u_c.PA_PSF
            flag = True
        elif press_unit.lower() == "atm":
            press_psf = press_user * u_c.ATM_PSF
            flag = True
        elif press_unit.lower() == "bar":
            press_psf = press_user * u_c.BAR_PSF
            flag = True
        elif press_unit.lower() == "m":
            h_press_ft = press_user * u_c.M_FT
            point_in_sky = atmos.get_atmos_properties(h_press_ft=h_press_ft,p_press_psf="NA")
            press_psf = point_in_sky['p_static_psf']
            flag = True
        elif press_unit.lower() == "ft":
            h_press_ft = press_user
            point_in_sky = atmos.get_atmos_properties(h_press_ft=h_press_ft,p_press_psf="NA")
            press_psf = point_in_sky['p_static_psf']
            flag = True
        else:
            print("Input error: Select pfs/psi/pa/atm/bar")
            press_unit = input("Input units pfs/psi/pa/atm/bar: ")

    return (press_psf)


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

    point_in_sky = atmos.get_atmos_properties(h_press_ft=h_press_ft, p_press_psf="NA")

    if point_in_sky == "ERROR":
        pass
    else:
        atmos.print_atmos(point_in_sky)

    return


def air_data_pres():
    press_user = float(input("Input pressure: "))
    press_unit = input("Input units psf/psi/pa/atm/bar: ")

    press_psf = pressure_convert(press_user,press_unit)

    print(f"Pressure {press_psf}")

    point_in_sky = atmos.get_atmos_properties(h_press_ft="NA",p_press_psf=press_psf)

    if point_in_sky == "ERROR":
        pass
    else:
        atmos.print_atmos(point_in_sky)

    return

def alt_mach():
    # TODO Make this valid supersonic

    # Request user input
    alt = input("Input the pressure altitude: ")
    alt_units = input("Input the pressure altitude units: ")
    mach  = input() 

    return


def alt_true():
    pass

def alt_cal():
    pass


def alt_equiv():
    pass