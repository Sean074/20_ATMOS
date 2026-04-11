"""
Generate US Standard Atmosphere 1976 data table in imperial units.
Produces instance/standard_atmos_1976.csv matching the format of
instance/standard_atmos.csv.

Source: US Standard Atmosphere 1976 (USSA 1976), identical below 86 km
to the 1962 standard. Layer equations from PDAS (pdas.com/atmos.html).
"""
import math
import csv
import os

# ── Constants ────────────────────────────────────────────────────────────────
R_e   = 20_855_531.0   # ft  – Earth mean radius (for H↔Z conversion)
g0    = 32.17405       # ft/s²  – standard gravity
R_air = 1716.49        # ft²/(s²·°R)  – specific gas constant for air

# Sea-level reference values (USSA 1976)
T0_R  = 518.67         # °R
P0    = 2116.224       # lb/ft²  (= 101325 Pa)
rho0  = P0 / (R_air * T0_R)   # slug/ft³

# ── Layer definitions (geopotential altitude H in ft) ────────────────────────
# Each entry: (H_base_ft, T_base_R, lapse_R_per_ft)
# Layers are evaluated in order; the matching layer is the one whose H_base
# is ≤ H < next layer's H_base.
LAYERS = [
    # Layer 0 – troposphere: 0 to 11 000 m (36 089.24 ft)
    #   L = −6.5 K/km → −6.5/1000 K/m * 3.28084 ft/m * 9/5 R/K = −0.003566 R/ft
    (-1e9,          518.67,  -0.003566),
    # Layer 1 – lower stratosphere: 11 000 to 20 000 m (65 616.80 ft), isothermal
    (36_089.24,     389.97,   0.0),
    # Layer 2 – middle stratosphere: 20 000 to 32 000 m (104 986.88 ft)
    #   L = +1.0 K/km → +1.0/1000 * 3.28084 * 9/5 = +0.0005905 R/ft
    (65_616.80,     389.97,  +0.0005905),
]

# Pre-compute base pressures at each layer boundary
def _base_pressure(layer_idx):
    """Recursively compute pressure at the base of a layer."""
    if layer_idx == 0:
        return P0
    H_base, _, _ = LAYERS[layer_idx]
    H_prev, T_prev_base, L_prev = LAYERS[layer_idx - 1]
    P_prev_base = _base_pressure(layer_idx - 1)
    T_at_boundary = T_prev_base + L_prev * (H_base - max(H_prev, 0.0))
    if L_prev == 0.0:
        # For layer 0 the "base" is sea level (H=0), but H_prev is -∞;
        # the effective base for the calculation below is sea level.
        pass
    # Temperature at this layer's base
    H_eff_prev = max(H_prev, 0.0) if layer_idx > 1 else 0.0
    if layer_idx == 1:
        H_eff_prev = 0.0
    T_at_boundary = T_prev_base + L_prev * (H_base - H_eff_prev)
    if L_prev == 0.0:
        return P_prev_base * math.exp(-g0 * (H_base - H_eff_prev) / (R_air * T_prev_base))
    else:
        return P_prev_base * (T_at_boundary / T_prev_base) ** (-g0 / (R_air * L_prev))

# Cache base pressures and temperatures
_layer_bases = []
H_eff_bases = [0.0, 36_089.24, 65_616.80]  # geopotential H at each layer base
for i, (H_base, T_base, L) in enumerate(LAYERS):
    P_base = _base_pressure(i)
    _layer_bases.append((H_eff_bases[i], T_base, L, P_base))


def geopotential(Z_ft):
    """Geometric altitude Z [ft] → geopotential altitude H [ft]."""
    return R_e * Z_ft / (R_e + Z_ft)


def atmosphere(Z_ft):
    """
    Return (H_ft, T_R, P_psf, rho_slug_ft3) for geometric altitude Z [ft].
    """
    H = geopotential(Z_ft)

    # Find the appropriate layer (walk in reverse to find highest base ≤ H)
    layer_idx = 0
    for i in range(len(_layer_bases) - 1, -1, -1):
        if H >= _layer_bases[i][0]:
            layer_idx = i
            break

    H_base, T_base, L, P_base = _layer_bases[layer_idx]
    dH = H - H_base
    T = T_base + L * dH

    if L == 0.0:
        P = P_base * math.exp(-g0 * dH / (R_air * T_base))
    else:
        P = P_base * (T / T_base) ** (-g0 / (R_air * L))

    rho = P / (R_air * T)
    return H, T, P, rho


# ── Generate table ────────────────────────────────────────────────────────────
def main():
    altitudes_ft = range(-2500, 102501, 2500)
    out_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'standard_atmos_1976.csv')
    out_path = os.path.normpath(out_path)

    with open(out_path, 'w', newline='') as f:
        f.write('# US Standard Atmosphere 1976 (equations from pdas.com/atmos.html)\n')
        writer = csv.writer(f)
        writer.writerow(['Hgeo_ft', 'H_ft', 'T_degR', 'P_lb/ft2', 'P/P0', 'pho_slug/ft3', 'pho/pho0'])
        for Z in altitudes_ft:
            H, T, P, rho = atmosphere(Z)
            row = [
                Z,
                round(H, 4),
                round(T, 6),
                round(P, 5),
                round(P / P0, 7),
                round(rho, 9),
                round(rho / rho0, 7),
            ]
            writer.writerow(row)

    print(f"Written {len(list(altitudes_ft))} rows to {out_path}")
    print(f"\nSea-level check (Z=0):")
    H, T, P, rho = atmosphere(0)
    print(f"  T = {T:.4f} R  (expect 518.67)")
    print(f"  P = {P:.4f} psf  (expect 2116.224)")
    print(f"  rho = {rho:.9f} slug/ft³  (expect ~0.002376892)")
    print(f"\n35000 ft check:")
    H, T, P, rho = atmosphere(35000)
    print(f"  T = {T:.4f} R  (expect ~394.1)")
    print(f"  P = {P:.4f} psf  (expect ~499)")
    print(f"\n37500 ft check (isothermal layer):")
    H, T, P, rho = atmosphere(37500)
    print(f"  T = {T:.4f} R  (expect 389.97)")
    print(f"  P = {P:.4f} psf  (expect ~443)")


if __name__ == '__main__':
    main()
