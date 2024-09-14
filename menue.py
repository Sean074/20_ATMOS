import unit_convert as u_c
import atmos


def air_data():
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

    point_in_sky = atmos.get_atmos_properties(h_press_ft)

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