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

    point_in_sky = atmos.get_atmos_prop_alt(h_press_ft=h_press_ft)

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

    point_in_sky = atmos.get_atmos_prop_pres(p_press_psf=press_psf)

    if point_in_sky == "ERROR":
        pass
    else:
        atmos.print_atmos(point_in_sky)

    return


def alt_mach():
    # Request user input
    alt_user = float(input("Input the pressure altitude: "))
    alt_unit = input("Input the pressure altitude units (ft/m): ")
    mach  = float(input("Input the Mach: "))
    
    flag = False

    while flag != True:
        if alt_unit.lower() == "m":
            h_press_ft = alt_user * u_c.M_FT
            flag = True
        elif alt_unit.lower() == "ft":
            h_press_ft = alt_user
            flag = True
        else:
            print("Input error: Select m or ft")
            alt_unit = input("Input units m/ft: ")

    speeds = atmos.mach_alt(mach,h_press_ft)

    atmos.print_speed(speeds)

    return


def alt_true():
    # Request user input
    alt_user = float(input("Input the pressure altitude: "))
    alt_unit = input("Input the pressure altitude units (ft, m): ")
    tas  = float(input("Input the True Air Speed TAS: "))
    tas_unit = input("Input speed units (kts, m/s): ")

    # Convert altitude to base units
    flag = False
    while flag != True:
        if alt_unit.lower() == "m":
            h_press_ft = alt_user * u_c.M_FT
            flag = True
        elif alt_unit.lower() == "ft":
            h_press_ft = alt_user
            flag = True
        else:
            print("Input error: Select m or ft")
            alt_unit = input("Input units (m, ft): ")

    # Convert speed to kts
    flag = False
    while flag != True:
        if tas_unit.lower() == "m/s":
            ktas = tas * u_c.MS_KTS
            flag = True
        elif tas_unit.lower() == "kts":
            ktas = tas
            flag = True
        else:
            print("Input error: Select m/s or kts")
            alt_unit = input("Input units (m/s, kts): ")

    speeds = atmos.tas_alt(ktas,h_press_ft)

    atmos.print_speed(speeds)

    return

def alt_cal():
    # Request user input
    alt_user = float(input("Input the pressure altitude: "))
    alt_unit = input("Input the pressure altitude units (ft, m): ")
    cas  = float(input("Input the Calibrated Air Speed CAS: "))
    cas_unit = input("Input speed units (kts, m/s): ")

    # Convert altitude to base units
    flag = False
    while flag != True:
        if alt_unit.lower() == "m":
            h_press_ft = alt_user * u_c.M_FT
            flag = True
        elif alt_unit.lower() == "ft":
            h_press_ft = alt_user
            flag = True
        else:
            print("Input error: Select m or ft")
            alt_unit = input("Input units (m, ft): ")

    # Convert speed to kts
    flag = False
    while flag != True:
        if cas_unit.lower() == "m/s":
            kcas = cas * u_c.MS_KTS
            flag = True
        elif cas_unit.lower() == "kts":
            kcas = cas
            flag = True
        else:
            print("Input error: Select m/s or kts")
            alt_unit = input("Input units (m/s, kts): ")

    speeds = atmos.cas_alt(kcas,h_press_ft)

    atmos.print_speed(speeds)

    return


def alt_equiv():
    # Request user input
    alt_user = float(input("Input the pressure altitude: "))
    alt_unit = input("Input the pressure altitude units (ft, m): ")
    eas  = float(input("Input the Equiv Air Speed EAS: "))
    eas_unit = input("Input speed units (kts, m/s): ")

    # Convert altitude to base units
    flag = False
    while flag != True:
        if alt_unit.lower() == "m":
            h_press_ft = alt_user * u_c.M_FT
            flag = True
        elif alt_unit.lower() == "ft":
            h_press_ft = alt_user
            flag = True
        else:
            print("Input error: Select m or ft")
            alt_unit = input("Input units (m, ft): ")

    # Convert speed to kts
    flag = False
    while flag != True:
        if eas_unit.lower() == "m/s":
            keas = eas * u_c.MS_KTS
            flag = True
        elif eas_unit.lower() == "kts":
            keas = eas
            flag = True
        else:
            print("Input error: Select m/s or kts")
            alt_unit = input("Input units (m/s, kts): ")

    speeds = atmos.eas_alt(keas,h_press_ft)

    atmos.print_speed(speeds)

    return

def speed_alt_ktas():

    speed_min, speed_max = input("Define the speed range (min max) in knots: ").split()
    speed_min = float(speed_min)
    speed_max = float(speed_max)
    speed_inc = (speed_max - speed_min)/300

    ktas_array = []

    for speed in range(speed_min, speed_max, speed_inc):
        ktas_array = speed
    
    alt_min, alt_max = input("Define the altitude range (min max) in ft: ").split()
    alt_min = float(alt_min)
    alt_max = float(alt_max)
    alt_inc = (speed_max - speed_max)/300

    alt_array = []

    for altitude in range(alt_min, alt_max, alt_inc):
        alt_array = altitude

    print(ktas_array)
    print(alt_array)

    
    return


def speed_alt_kcas():
    pass

def speed_alt_keas():
    pass