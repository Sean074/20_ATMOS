def ask_unit(prompt, valid_choices):
    """Prompt for a unit string, re-prompting until a valid choice is entered."""
    while True:
        choice = input(prompt).lower().strip()
        if choice in valid_choices:
            return choice
        print(f"Invalid input. Choose from: {', '.join(valid_choices)}")


def print_atmos(point_in_sky):
    print("\n======== ATMOS ==================================")
    print("Point in the sky properties:")
    print(f"Pressure Altitude [ft]: {point_in_sky['h_press_ft']:.1f}")
    print(f"Pressure Static [psf]: {point_in_sky['p_static_psf']:.3f}")
    print(f"Density Ratio: {point_in_sky['pho_ratio']:.3f}")
    print(f"Air Density [slug/ft^3]: {point_in_sky['pho_slug_ft3']:.3e}")
    print(f"Air temperature [degR]: {point_in_sky['temp_degR']:.1f}")
    print("==================================================\n")


def print_speed(speeds):
    print("\n======== ATMOS ==================================")
    print("Speeds")
    print(f"Mach: {speeds['Mach']:.3f}")
    print(f"KTAS: {speeds['ktas']:.1f} kts")
    print(f"KEAS: {speeds['keas']:.1f} kts")
    print(f"KCAS: {speeds['kcas']:.1f} kts")
    print(f"Dynamic pressure: {speeds['q_c']:.3f} psf")
    print("==================================================\n")
