"""Property database. Every number in this file is transcribed from the
appendices of Smith, Van Ness & Abbott, *Introduction to Chemical Engineering
Thermodynamics* (SVN):

* Table B.1  Characteristic properties of pure species (M, omega, Tc, Pc, Zc, Vc, Tn)
* Table C.1  Heat capacities of gases in the ideal-gas state
* Table C.2  Heat capacities of solids
* Table C.3  Heat capacities of liquids
* Table C.4  Standard enthalpies and Gibbs energies of formation at 298.15 K

Units: Cp/R is dimensionless, temperatures are in K, pressures in bar,
volumes in cm^3/mol, energies in J/mol.

The heat-capacity tables also print Cp/R at 298.15 K. That column is stored
here as ``cp298_tab`` and is never used in a calculation. It is a checksum:
the test-suite recomputes Cp/R at 298.15 K from A, B, C, D and compares it with
the printed value, which catches a mistyped constant.

The elements in their standard states (H2, O2, N2, Cl2 gas, graphite, alpha
iron) have zero enthalpy and Gibbs energy of formation by definition.

Two species from the assignment's suggested list are not fully covered by SVN.
For these, and only these, data from the NIST Chemistry WebBook are used; they
are kept in separate tables further down (NIST_...), with the exact source:
* Acetic acid: Table C.4 lists only the liquid and SVN gives no heat capacity
  for it. NIST supplies a heat capacity for the liquid and all data for the
  vapour.
* Hydrogen peroxide: absent from Tables B.1 and C.1 to C.4 (the 8th edition
  only mentions it in its aqueous-solution table and in one problem
  statement). The gas is taken from NIST.

SVN's heat capacities start at 298 K. From 200 K to 298.15 K the heat
capacities of the gases and of six solids come from NIST tables (JANAF_LOW_T
and WEBBOOK_LOW_T further down). Nothing above 298.15 K is changed by them.

Verification. Every number below was compared with the printed tables (8th
edition appendices, cross-checked against the 6th-edition page scans). Two
oddities belong to the book itself, not to this transcription:
* 1,3-Butadiene: the printed Cp298/R (10.720) does not agree with the printed
  A, B, C, which give 9.931. The constants are used; the checksum test lists
  this species as a known exception.
* Chlorine and carbon monoxide: the printed Zc differs slightly from
  Pc*Vc/(R*Tc). Zc is displayed but never used in a calculation.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Table C.1 + Table C.4: gases (ideal-gas state)
# Cp/R = A + B*T + C*T^2 + D*T^-2, valid from 298 K to Tmax
# columns: id, name, formula, Tmax, Cp298/R (printed), A, 1e3*B, 1e6*C, 1e-5*D,
#          dHf298 (J/mol), dGf298 (J/mol)
# ---------------------------------------------------------------------------
GASES = [
    # Paraffins
    ("CH4(g)", "Methane", "CH4", 1500, 4.217, 1.702, 9.081, -2.164, 0.0, -74520, -50460),
    ("C2H6(g)", "Ethane", "C2H6", 1500, 6.369, 1.131, 19.225, -5.561, 0.0, -83820, -31855),
    ("C3H8(g)", "Propane", "C3H8", 1500, 9.011, 1.213, 28.785, -8.824, 0.0, -104680, -24290),
    ("n-C4H10(g)", "n-Butane", "C4H10", 1500, 11.928, 1.935, 36.915, -11.402, 0.0, -125790, -16570),
    ("n-C5H12(g)", "n-Pentane", "C5H12", 1500, 14.731, 2.464, 45.351, -14.111, 0.0, -146760, -8650),
    ("n-C6H14(g)", "n-Hexane", "C6H14", 1500, 17.550, 3.025, 53.722, -16.791, 0.0, -166920, 150),
    ("n-C7H16(g)", "n-Heptane", "C7H16", 1500, 20.361, 3.570, 62.127, -19.486, 0.0, -187780, 8260),
    ("n-C8H18(g)", "n-Octane", "C8H18", 1500, 23.174, 4.108, 70.567, -22.208, 0.0, -208750, 16260),
    # 1-Alkenes
    ("C2H4(g)", "Ethylene", "C2H4", 1500, 5.325, 1.424, 14.394, -4.392, 0.0, 52510, 68460),
    ("C3H6(g)", "Propylene", "C3H6", 1500, 7.792, 1.637, 22.706, -6.915, 0.0, 19710, 62205),
    ("C4H8(g)", "1-Butene", "C4H8", 1500, 10.520, 1.967, 31.630, -9.873, 0.0, -540, 70340),
    # Miscellaneous organics
    ("CH3CHO(g)", "Acetaldehyde", "C2H4O", 1000, 6.506, 1.693, 17.978, -6.158, 0.0, -166190, -128860),
    ("C2H2(g)", "Acetylene", "C2H2", 1500, 5.253, 6.132, 1.952, 0.0, -1.299, 227480, 209970),
    ("C6H6(g)", "Benzene", "C6H6", 1500, 10.259, -0.206, 39.064, -13.301, 0.0, 82930, 129665),
    ("C4H6(g)", "1,3-Butadiene", "C4H6", 1500, 10.720, 2.734, 26.786, -8.882, 0.0, 109240, 149795),
    ("C6H12(g)", "Cyclohexane", "C6H12", 1500, 13.121, -3.876, 63.249, -20.928, 0.0, -123140, 31920),
    ("C2H5OH(g)", "Ethanol", "C2H6O", 1500, 8.948, 3.518, 20.001, -6.002, 0.0, -235100, -168490),
    ("C8H10(g)", "Ethylbenzene", "C8H10", 1500, 15.993, 1.124, 55.380, -18.476, 0.0, 29920, 130890),
    ("(CH2)2O(g)", "Ethylene oxide", "C2H4O", 1000, 5.784, -0.385, 23.463, -9.296, 0.0, -52630, -13010),
    ("CH2O(g)", "Formaldehyde", "CH2O", 1500, 4.191, 2.264, 7.022, -1.877, 0.0, -108570, -102530),
    ("CH3OH(g)", "Methanol", "CH4O", 1500, 5.547, 2.211, 12.216, -3.450, 0.0, -200660, -161960),
    ("C8H8(g)", "Styrene", "C8H8", 1500, 15.534, 2.050, 50.192, -16.662, 0.0, 147360, 213900),
    ("C7H8(g)", "Toluene", "C7H8", 1500, 12.922, 0.290, 47.052, -15.716, 0.0, 50170, 122050),
    # Miscellaneous inorganics
    # dGf of ammonia is the one value that differs between editions: -16,400 in
    # the 8th and 9th editions (used here), -16,450 in the 6th edition.
    ("NH3(g)", "Ammonia", "NH3", 1800, 4.269, 3.578, 3.020, 0.0, -0.186, -46110, -16400),
    ("CO(g)", "Carbon monoxide", "CO", 2500, 3.507, 3.376, 0.557, 0.0, -0.031, -110525, -137169),
    ("CO2(g)", "Carbon dioxide", "CO2", 2000, 4.467, 5.457, 1.045, 0.0, -1.157, -393509, -394359),
    ("Cl2(g)", "Chlorine", "Cl2", 3000, 4.082, 4.442, 0.089, 0.0, -0.344, 0, 0),
    ("H2(g)", "Hydrogen", "H2", 3000, 3.468, 3.249, 0.422, 0.0, 0.083, 0, 0),
    ("H2S(g)", "Hydrogen sulfide", "H2S", 2300, 4.114, 3.931, 1.490, 0.0, -0.232, -20630, -33560),
    ("HCl(g)", "Hydrogen chloride", "HCl", 2000, 3.512, 3.156, 0.623, 0.0, 0.151, -92307, -95299),
    ("HCN(g)", "Hydrogen cyanide", "HCN", 2500, 4.326, 4.736, 1.359, 0.0, -0.725, 135100, 124700),
    ("N2(g)", "Nitrogen", "N2", 2000, 3.502, 3.280, 0.593, 0.0, 0.040, 0, 0),
    ("N2O(g)", "Nitrous oxide", "N2O", 2000, 4.646, 5.328, 1.214, 0.0, -0.928, 82050, 104200),
    ("NO(g)", "Nitric oxide", "NO", 2000, 3.590, 3.387, 0.629, 0.0, 0.014, 90250, 86550),
    ("NO2(g)", "Nitrogen dioxide", "NO2", 2000, 4.447, 4.982, 1.195, 0.0, -0.792, 33180, 51310),
    ("N2O4(g)", "Dinitrogen tetroxide", "N2O4", 2000, 9.198, 11.660, 2.257, 0.0, -2.787, 9160, 97540),
    ("O2(g)", "Oxygen", "O2", 2000, 3.535, 3.639, 0.506, 0.0, -0.227, 0, 0),
    ("SO2(g)", "Sulfur dioxide", "SO2", 2000, 4.796, 5.699, 0.801, 0.0, -1.015, -296830, -300194),
    ("SO3(g)", "Sulfur trioxide", "SO3", 2000, 6.094, 8.060, 1.056, 0.0, -2.028, -395720, -371060),
    ("H2O(g)", "Water", "H2O", 2000, 4.038, 3.470, 1.450, 0.0, 0.121, -241818, -228572),
]

# ---------------------------------------------------------------------------
# Table C.3 + Table C.4: liquids
# Cp/R = A + B*T + C*T^2, valid from 273.15 K to 373.15 K
# columns: id, name, formula, Cp298/R (printed), A, 1e3*B, 1e6*C, dHf298, dGf298
# ---------------------------------------------------------------------------
LIQUIDS = [
    ("H2O(l)", "Water", "H2O", 9.069, 8.712, 1.25, -0.18, -285830, -237129),
    ("CH3OH(l)", "Methanol", "CH4O", 9.798, 13.431, -51.28, 131.13, -238660, -166270),
    ("C2H5OH(l)", "Ethanol", "C2H6O", 13.444, 33.866, -172.60, 349.17, -277690, -174780),
    ("C6H6(l)", "Benzene", "C6H6", 16.157, -0.747, 67.96, -37.78, 49080, 124520),
    ("C6H12(l)", "Cyclohexane", "C6H12", 18.737, -9.048, 141.38, -161.62, -156230, 26850),
    ("C7H8(l)", "Toluene", "C7H8", 18.611, 15.133, 6.79, 16.35, 12180, 113630),
]

# Liquids listed in Table C.4 for which SVN gives no heat capacity. On SVN
# data alone they can be used at 298.15 K only; NIST_LIQUID_CONSTANT_CP below
# supplies a heat capacity from the NIST WebBook.
LIQUIDS_298_ONLY = [
    # id, name, formula, dHf298, dGf298
    ("CH3COOH(l)", "Acetic acid", "C2H4O2", -484500, -389900),
]

# ---------------------------------------------------------------------------
# Species that SVN does not cover, from the NIST Chemistry WebBook
# (webbook.nist.gov, NIST Standard Reference Database 69). They are kept in
# their own tables so that SVN data and outside data are never mixed silently,
# and every one of them is labelled with its source in the app.
#
# NIST gives the enthalpy of formation and the absolute entropy. The Gibbs
# energy of formation follows from them and the entropies of the elements:
#       dGf298 = dHf298 - 298.15 * (S298 - sum of element entropies)
#
# Hydrogen peroxide gas (NIST species page C7722841; data from the NIST-JANAF
# Thermochemical Tables, Chase 1998):
#       dHf298 = -136.11 kJ/mol,  S298 = 232.95 J/(mol K)
#       Shomate equation, 298 to 1500 K, Cp in J/(mol K), t = T/1000:
#       Cp = A + B t + C t^2 + D t^3 + E/t^2
# Acetic acid gas, ideal-gas monomer (NIST species page C64197):
#       dHf298 = -432.9 kJ/mol: the liquid value of Lebedeva (1964), -484.5,
#                which is also the SVN Table C.4 value, plus the enthalpy of
#                vaporisation to the monomer, 51.6 kJ/mol (Konicek & Wadso 1970)
#       S298   = 282.84 J/(mol K) (Weltner 1955)
#       Cp     = tabulated values of Chao (1986), 298.15 to 1500 K, listed in
#                ACETIC_ACID_GAS_CP_TABLE below. NIST gives no equation, so the
#                table was fitted by least squares with
#                Cp/R = A + B T + C T^2 + E T^3; the largest deviation from the
#                table is 0.21 %, and the test-suite checks every point.
# Acetic acid liquid: Cp = 123.1 J/(mol K) at 298.15 K (Martin & Andon 1982, via
#       NIST). It is used as a constant near room temperature only, because the
#       heat capacity of the liquid rises noticeably with temperature.
# ---------------------------------------------------------------------------
# columns: id, name, formula, dHf298 (J/mol), S298 (J/(mol K)), Shomate (A, B, C, D, E), Tmin, Tmax
NIST_GASES_SHOMATE = [
    ("H2O2(g)", "Hydrogen peroxide", "H2O2", -136110.0, 232.95,
     (34.25667, 55.18445, -35.15443, 9.087440, -0.422157), 298.0, 1500.0),
]

# columns: id, name, formula, dHf298, S298, (A, 1e3*B, 1e6*C, 1e-5*D, 1e9*E) of Cp/R, Tmin, Tmax
NIST_GASES_FITTED = [
    ("CH3COOH(g)", "Acetic acid", "C2H4O2", -432900.0, 282.84,
     (0.181025, 29.4877, -16.1226, 0.0, 3.20774), 298.0, 1500.0),
]

# NIST WebBook, ideal-gas heat capacity of acetic acid (Chao 1986): T (K), Cp (J/(mol K))
ACETIC_ACID_GAS_CP_TABLE = [
    (298.15, 63.44), (300.0, 63.74), (400.0, 79.66), (500.0, 93.93), (600.0, 106.18),
    (700.0, 116.63), (800.0, 125.50), (900.0, 132.99), (1000.0, 139.26), (1100.0, 144.46),
    (1200.0, 148.76), (1300.0, 152.30), (1400.0, 155.22), (1500.0, 157.63),
]

# Constant liquid heat capacities from NIST for liquids that SVN lists in
# Table C.4 without a heat capacity: id -> (Cp in J/(mol K), Tmin, Tmax)
NIST_LIQUID_CONSTANT_CP = {
    "CH3COOH(l)": (123.1, 290.0, 320.0),
}

# NIST gas species whose critical constants ARE in SVN Table B.1 (looked up by
# name), so real-gas models can be applied to them. Hydrogen peroxide is not in
# Table B.1 and is treated as an ideal gas in pressure calculations.
NIST_USE_SVN_CRITICAL = {"Acetic acid"}

# One-line remarks shown whenever a species is used.
SPECIES_REMARKS = {
    "H2O2(g)": "formation data and heat capacity are from the NIST Chemistry WebBook (NIST-JANAF), not from SVN.",
    "CH3COOH(g)": ("formation data and heat capacity are from the NIST Chemistry WebBook, not from SVN. "
                   "The values are for the ideal-gas monomer; real acetic acid vapour is partly dimerised."),
    "CH3COOH(l)": ("formation data are from SVN Table C.4; the heat capacity is a constant 123.1 J/(mol K) "
                   "from the NIST Chemistry WebBook, valid near room temperature only."),
}

# ---------------------------------------------------------------------------
# Heat capacities BELOW 298.15 K (not from SVN)
#
# SVN Tables C.1 and C.2 start at 298 K. Below that the printed constants
# cannot be used: the D/T^2 term takes over, and for CO2 at 200 K it gives a
# heat capacity 29 % too low. The standard state itself exists at any
# temperature (it fixes the pressure at 1 bar, not the temperature), so the
# range from 200 K to 298.15 K is covered with tabulated values from NIST.
#
# Only the rows that were read are stored here. The constants of
# Cp/R = A + B*T + C*T^2 are computed from these rows when the package is
# loaded (species.py), so no fitted number is typed in by hand:
#
# * NIST-JANAF rows: the quadratic takes the tabulated Cp at 200 K and at
#   298.15 K, and its integral between them equals the tabulated enthalpy
#   difference H(200 K) - H(298.15 K). The tabulated entropy, and the 250 K
#   row where the table has one, are not used for the fit; the test-suite
#   checks that they are reproduced.
# * NIST WebBook rows: the quadratic passes through the three tabulated Cp.
#
# Below 200 K nothing is stored: hydrogen then needs its ortho/para forms
# treated separately and several solids have transitions.
# ---------------------------------------------------------------------------
LOW_T_MIN = 200.0   # K, lower limit of the low-temperature heat capacities

# NIST-JANAF Thermochemical Tables, 4th edition (Chase 1998), janaf.nist.gov,
# read on 22 November 2026.
# id: (JANAF table, rows of (T in K, Cp in J/(mol K), S in J/(mol K), H - H(298.15 K) in kJ/mol))
JANAF_LOW_T = {
    "HCN(g)": ("C-052", ((200.0, 31.719, 188.377, -3.318), (298.15, 35.857, 201.828, 0.0))),
    "CH2O(g)": ("C-061", ((200.0, 33.502, 205.292, -3.363), (250.0, 34.194, 212.831, -1.673), (298.15, 35.402, 218.950, 0.0))),
    "CH4(g)": ("C-067", ((200.0, 33.473, 172.577, -3.368), (250.0, 34.216, 180.113, -1.679), (298.15, 35.639, 186.251, 0.0))),
    "CO(g)": ("C-093", ((200.0, 29.108, 186.025, -2.858), (298.15, 29.142, 197.653, 0.0))),
    "CO2(g)": ("C-095", ((200.0, 32.359, 199.975, -3.414), (298.15, 37.129, 213.795, 0.0))),
    "C2H2(g)": ("C-127", ((200.0, 35.585, 185.097, -3.925), (298.15, 44.095, 200.958, 0.0))),
    "C2H4(g)": ("C-128", ((200.0, 35.359, 203.955, -3.804), (250.0, 38.645, 212.172, -1.960), (298.15, 42.886, 219.330, 0.0))),
    "HCl(g)": ("Cl-026", ((200.0, 29.124, 175.270, -2.859), (250.0, 29.130, 181.770, -1.403), (298.15, 29.136, 186.901, 0.0))),
    "H2(g)": ("H-050", ((200.0, 27.447, 119.412, -2.774), (250.0, 28.344, 125.640, -1.378), (298.15, 28.836, 130.680, 0.0))),
    "H2O(g)": ("H-064", ((200.0, 33.349, 175.485, -3.282), (298.15, 33.590, 188.834, 0.0))),
    "H2S(g)": ("H-080", ((200.0, 33.380, 192.038, -3.310), (298.15, 34.192, 205.757, 0.0))),
    "NH3(g)": ("H-083", ((200.0, 33.757, 178.990, -3.394), (298.15, 35.652, 192.774, 0.0))),
    "NO(g)": ("N-005", ((200.0, 30.420, 198.747, -2.951), (250.0, 30.025, 205.488, -1.441), (298.15, 29.845, 210.758, 0.0))),
    "NO2(g)": ("N-007", ((200.0, 34.385, 225.852, -3.495), (250.0, 35.593, 233.649, -1.746), (298.15, 36.974, 240.034, 0.0))),
    "N2(g)": ("N-023", ((200.0, 29.107, 179.985, -2.857), (250.0, 29.111, 186.481, -1.402), (298.15, 29.124, 191.609, 0.0))),
    "N2O(g)": ("N-026", ((200.0, 33.610, 205.571, -3.553), (250.0, 36.290, 213.362, -1.805), (298.15, 38.617, 219.957, 0.0))),
    "N2O4(g)": ("N-032", ((200.0, 63.206, 276.398, -6.923), (250.0, 70.825, 291.339, -3.568), (298.15, 77.256, 304.376, 0.0))),
    "O2(g)": ("O-029", ((200.0, 29.126, 193.485, -2.868), (250.0, 29.201, 199.990, -1.410), (298.15, 29.376, 205.147, 0.0))),
    "SO2(g)": ("O-034", ((200.0, 36.372, 233.033, -3.736), (298.15, 39.878, 248.212, 0.0))),
    "SO3(g)": ("O-058", ((200.0, 42.336, 238.259, -4.577), (250.0, 46.784, 248.192, -2.348), (298.15, 50.661, 256.769, 0.0))),
    "Cl2(g)": ("Cl-073", ((200.0, 31.720, 209.964, -3.231), (250.0, 32.988, 217.183, -1.613), (298.15, 33.949, 223.079, 0.0))),
    # solids
    "C(s)": ("C-002", ((200.0, 5.006, 3.082, -0.665), (250.0, 6.816, 4.394, -0.369), (298.15, 8.517, 5.740, 0.0))),
    "CaO(s)": ("Ca-027", ((200.0, 33.677, 23.041, -3.757), (298.15, 42.120, 38.212, 0.0))),
    "Ca(OH)2(s)": ("Ca-020", ((200.0, 68.576, 52.183, -7.736), (298.15, 87.487, 83.387, 0.0))),
    "Fe(s)": ("Fe-003", ((200.0, 21.588, 17.949, -2.315), (298.15, 25.094, 27.321, 0.0))),
    "Fe2O3(s)": ("Fe-030", ((200.0, 76.567, 51.279, -8.970), (298.15, 103.763, 87.400, 0.0))),
    "Fe3O4(s)": ("Fe-032", ((200.0, 116.945, 92.367, -13.101), (298.15, 147.235, 145.266, 0.0))),
}

# NIST Chemistry WebBook (webbook.nist.gov), "Constant pressure heat capacity
# of gas", the recommended ideal-gas values at 1 bar, read on 22 November 2026.
# id: (WebBook species ID, reference named by NIST, three rows of (T in K, Cp in J/(mol K)))
WEBBOOK_LOW_T = {
    "CH3OH(g)": ("C67561", "Thermodynamics Research Center (1997)", ((200.0, 39.71), (273.15, 42.59), (298.15, 44.06))),
    "C2H5OH(g)": ("C64175", "Thermodynamics Research Center (1997)", ((200.0, 52.02), (273.15, 61.46), (298.15, 65.21))),
    "CH3CHO(g)": ("C75070", "Thermodynamics Research Center (1997)", ((200.0, 46.47), (273.15, 52.80), (298.15, 55.32))),
    "(CH2)2O(g)": ("C75218", "Dorofeeva (1992)", ((200.0, 36.19), (273.15, 43.71), (298.15, 47.0))),
    "CH3COOH(g)": ("C64197", "Chao (1986)", ((200.0, 48.34), (273.15, 59.38), (298.15, 63.44))),
    # NIST lists no value for ethane between 200 K and 298.15 K, so its 100 K
    # value is the third point. See ETHANE_MEASURED_CP below.
    "C2H6(g)": ("C74840", "Gurvich, Veyts et al. (1989)", ((100.0, 35.70), (200.0, 42.30), (298.15, 52.49))),
    "C3H8(g)": ("C74986", "Chao (1973)", ((200.0, 56.07), (273.15, 68.74), (298.15, 73.60))),
    "n-C4H10(g)": ("C106978", "Chen (1975)", ((200.0, 76.44), (273.15, 92.30), (298.15, 98.49))),
    "n-C5H12(g)": ("C109660", "Scott (1974)", ((200.0, 93.55), (273.15, 112.55), (298.15, 120.0))),
    "n-C6H14(g)": ("C110543", "Scott (1974)", ((200.0, 110.58), (273.15, 133.55), (298.15, 142.6))),
    "n-C7H16(g)": ("C142825", "Scott (1974)", ((200.0, 127.65), (273.15, 154.64), (298.15, 165.2))),
    "n-C8H18(g)": ("C111659", "Scott (1974)", ((200.0, 144.77), (273.15, 175.69), (298.15, 187.8))),
    "C3H6(g)": ("C115071", "Thermodynamics Research Center (1997)", ((200.0, 50.24), (273.15, 60.47), (298.15, 64.32))),
    "C4H8(g)": ("C106989", "Thermodynamics Research Center (1997)", ((200.0, 65.19), (273.15, 80.03), (298.15, 85.56))),
    "C4H6(g)": ("C106990", "Thermodynamics Research Center (1997)", ((200.0, 57.14), (273.15, 73.70), (298.15, 79.81))),
    "C6H6(g)": ("C71432", "Thermodynamics Research Center (1997)", ((200.0, 53.17), (273.15, 74.55), (298.15, 82.44))),
    "C6H12(g)": ("C110827", "Dorofeeva (1986)", ((200.0, 69.05), (273.15, 95.20), (298.15, 105.3))),
    "C7H8(g)": ("C108883", "Draeger (1985)", ((200.0, 69.85), (273.15, 94.68), (298.15, 103.7))),
    "C8H10(g)": ("C100414", "Thermodynamics Research Center (1997)", ((200.0, 88.54), (273.15, 116.88), (298.15, 127.40))),
    "C8H8(g)": ("C100425", "Thermodynamics Research Center (1997)", ((200.0, 81.77), (273.15, 110.03), (298.15, 120.19))),
}

# Measured heat capacities of ethane gas listed on the same WebBook page
# (Halford 1957 and the work cited with it): T (K), Cp (J/(mol K)). They are
# not used for the fit; the test-suite compares the ethane curve with them.
ETHANE_MEASURED_CP = [(209.30, 43.25), (229.65, 45.08), (249.90, 47.27), (272.07, 49.51), (292.00, 52.14)]

# Species deliberately left without low-temperature data, with the reason.
LOW_T_NOT_COVERED = {
    "H2O2(g)": ("the NIST-JANAF table (H-070) is not consistent with itself between 200 K and 298.15 K: its "
                "heat capacities give an entropy rise of about 16 J/(mol K) over that interval, its entropy "
                "column gives 22.4"),
    "CaCO3(s)": "not in the NIST-JANAF tables",
    "CaC2(s)": "not in the NIST-JANAF tables",
}

# The NIST-JANAF entropy of H2S at 200 K (192.038) is 0.26 J/(mol K) away from
# what the table's own heat capacities give from its 298.15 K entropy. The
# enthalpy column agrees with the heat capacities to 1 J/mol, and only Cp and
# the enthalpy are used, so the species is kept; the entropy check skips it.
LOW_T_ENTROPY_EXCEPTIONS = {"H2S(g)": "tabulated S(200 K) is 0.26 J/(mol K) off the table's own heat capacities"}

# ---------------------------------------------------------------------------
# Table C.2 + Table C.4: solids
# Cp/R = A + B*T + D*T^-2, valid from 298 K to Tmax
# columns: id, name, formula, Tmax, Cp298/R (printed), A, 1e3*B, 1e-5*D, dHf298, dGf298
# ---------------------------------------------------------------------------
SOLIDS = [
    ("C(s)", "Carbon (graphite)", "C", 2000, 1.026, 1.771, 0.771, -0.867, 0, 0),
    ("CaO(s)", "Calcium oxide", "CaO", 2000, 5.058, 6.104, 0.443, -1.047, -635090, -604030),
    ("CaCO3(s)", "Calcium carbonate", "CaCO3", 1200, 9.848, 12.572, 2.637, -3.120, -1206920, -1128790),
    ("Ca(OH)2(s)", "Calcium hydroxide", "Ca(OH)2", 700, 11.217, 9.597, 5.435, 0.0, -986090, -898490),
    ("CaC2(s)", "Calcium carbide", "CaC2", 720, 7.508, 8.254, 1.429, -1.042, -59800, -64900),
    ("Fe(s)", "Iron (alpha)", "Fe", 1043, 3.005, -0.111, 6.111, 1.150, 0, 0),
    ("Fe2O3(s)", "Iron oxide (hematite)", "Fe2O3", 960, 12.480, 11.812, 9.697, -1.976, -824200, -742200),
    ("Fe3O4(s)", "Iron oxide (magnetite)", "Fe3O4", 850, 18.138, 9.594, 27.112, 0.409, -1118400, -1015400),
]

# ---------------------------------------------------------------------------
# Table B.1: characteristic properties of pure species
# key = chemical name used above
# columns: molar mass (g/mol), acentric factor, Tc (K), Pc (bar), Zc,
#          Vc (cm^3/mol), Tn normal boiling point (K) or None
# ---------------------------------------------------------------------------
CRITICAL = {
    "Methane": (16.043, 0.012, 190.6, 45.99, 0.286, 98.6, 111.4),
    "Ethane": (30.070, 0.100, 305.3, 48.72, 0.279, 145.5, 184.6),
    "Propane": (44.097, 0.152, 369.8, 42.48, 0.276, 200.0, 231.1),
    "n-Butane": (58.123, 0.200, 425.1, 37.96, 0.274, 255.0, 272.7),
    "n-Pentane": (72.150, 0.252, 469.7, 33.70, 0.270, 313.0, 309.2),
    "n-Hexane": (86.177, 0.301, 507.6, 30.25, 0.266, 371.0, 341.9),
    "n-Heptane": (100.204, 0.350, 540.2, 27.40, 0.261, 428.0, 371.6),
    "n-Octane": (114.231, 0.400, 568.7, 24.90, 0.256, 486.0, 398.8),
    "Ethylene": (28.054, 0.087, 282.3, 50.40, 0.281, 131.0, 169.4),
    "Propylene": (42.081, 0.140, 365.6, 46.65, 0.289, 188.4, 225.5),
    "1-Butene": (56.108, 0.191, 420.0, 40.43, 0.277, 239.3, 266.9),
    "Acetaldehyde": (44.053, 0.291, 466.0, 55.50, 0.221, 154.0, 294.0),
    "Acetylene": (26.038, 0.187, 308.3, 61.39, 0.271, 113.0, 189.4),
    "Benzene": (78.114, 0.210, 562.2, 48.98, 0.271, 259.0, 353.2),
    "1,3-Butadiene": (54.092, 0.190, 425.2, 42.77, 0.267, 220.4, 268.7),
    "Cyclohexane": (84.161, 0.210, 553.6, 40.73, 0.273, 308.0, 353.9),
    "Ethanol": (46.069, 0.645, 513.9, 61.48, 0.240, 167.0, 351.4),
    "Ethylbenzene": (106.167, 0.303, 617.2, 36.06, 0.263, 374.0, 409.4),
    "Formaldehyde": (30.026, 0.282, 408.0, 65.90, 0.223, 115.0, 254.1),
    "Methanol": (32.042, 0.564, 512.6, 80.97, 0.224, 118.0, 337.9),
    "Styrene": (104.152, 0.297, 636.0, 38.40, 0.256, 352.0, 418.3),
    "Toluene": (92.141, 0.262, 591.8, 41.06, 0.264, 316.0, 383.8),
    "Ammonia": (17.031, 0.253, 405.7, 112.80, 0.242, 72.5, 239.7),
    "Carbon monoxide": (28.010, 0.048, 132.9, 34.99, 0.299, 93.4, 81.7),
    "Carbon dioxide": (44.010, 0.224, 304.2, 73.83, 0.274, 94.0, None),
    "Chlorine": (70.905, 0.069, 417.2, 77.10, 0.265, 124.0, 239.1),
    "Hydrogen": (2.016, -0.216, 33.19, 13.13, 0.305, 64.1, 20.4),
    "Hydrogen sulfide": (34.082, 0.094, 373.5, 89.63, 0.284, 98.5, 212.8),
    "Hydrogen chloride": (36.461, 0.132, 324.7, 83.10, 0.249, 81.0, 188.2),
    "Hydrogen cyanide": (27.026, 0.410, 456.7, 53.90, 0.197, 139.0, 298.9),
    "Nitrogen": (28.014, 0.038, 126.2, 34.00, 0.289, 89.2, 77.3),
    "Nitrous oxide": (44.013, 0.141, 309.6, 72.45, 0.274, 97.4, 184.7),
    "Nitric oxide": (30.006, 0.583, 180.2, 64.80, 0.251, 58.0, 121.4),
    "Oxygen": (31.999, 0.022, 154.6, 50.43, 0.288, 73.4, 90.2),
    "Sulfur dioxide": (64.065, 0.245, 430.8, 78.84, 0.269, 122.0, 263.1),
    "Sulfur trioxide": (80.064, 0.424, 490.9, 82.10, 0.255, 127.0, 317.9),
    "Water": (18.015, 0.345, 647.1, 220.55, 0.229, 55.9, 373.2),
    "Acetic acid": (60.053, 0.467, 592.0, 57.86, 0.211, 179.7, 391.1),
}

# ---------------------------------------------------------------------------
# Extra names a user may type for a species. Formulas are case-sensitive
# (CO is not Co); plain names are matched case-insensitively.
# ---------------------------------------------------------------------------
ALIASES = {
    "CH4(g)": ["methane"],
    "C2H6(g)": ["ethane", "CH3CH3"],
    "C3H8(g)": ["propane"],
    "n-C4H10(g)": ["C4H10", "nC4H10", "n-butane", "butane"],
    "n-C5H12(g)": ["C5H12", "nC5H12", "n-pentane", "pentane"],
    "n-C6H14(g)": ["C6H14", "nC6H14", "n-hexane", "hexane"],
    "n-C7H16(g)": ["C7H16", "nC7H16", "n-heptane", "heptane"],
    "n-C8H18(g)": ["C8H18", "nC8H18", "n-octane", "octane"],
    "C2H4(g)": ["ethylene", "ethene", "CH2CH2"],
    "C3H6(g)": ["propylene", "propene"],
    "C4H8(g)": ["1-butene", "butene"],
    "CH3CHO(g)": ["acetaldehyde", "ethanal"],
    "C2H2(g)": ["acetylene", "ethyne"],
    "C6H6(g)": ["benzene"],
    "C4H6(g)": ["butadiene", "1,3-butadiene"],
    "C6H12(g)": ["cyclohexane"],
    "C2H5OH(g)": ["ethanol", "C2H6O", "CH3CH2OH"],
    "C8H10(g)": ["ethylbenzene", "C6H5C2H5"],
    "(CH2)2O(g)": ["ethylene oxide", "oxirane"],
    "CH2O(g)": ["formaldehyde", "HCHO"],
    "CH3OH(g)": ["methanol", "CH4O"],
    "C8H8(g)": ["styrene", "C6H5C2H3"],
    "C7H8(g)": ["toluene", "C6H5CH3"],
    "NH3(g)": ["ammonia"],
    "CO(g)": ["carbon monoxide"],
    "CO2(g)": ["carbon dioxide"],
    "Cl2(g)": ["chlorine"],
    "H2(g)": ["hydrogen"],
    "H2S(g)": ["hydrogen sulfide", "hydrogen sulphide"],
    "HCl(g)": ["hydrogen chloride"],
    "HCN(g)": ["hydrogen cyanide"],
    "N2(g)": ["nitrogen"],
    "N2O(g)": ["nitrous oxide"],
    "NO(g)": ["nitric oxide"],
    "NO2(g)": ["nitrogen dioxide"],
    "N2O4(g)": ["dinitrogen tetroxide"],
    "O2(g)": ["oxygen"],
    "SO2(g)": ["sulfur dioxide", "sulphur dioxide"],
    "SO3(g)": ["sulfur trioxide", "sulphur trioxide"],
    "H2O(g)": ["water", "steam"],
    "H2O(l)": ["water"],
    "CH3OH(l)": ["methanol", "CH4O"],
    "C2H5OH(l)": ["ethanol", "C2H6O", "CH3CH2OH"],
    "C6H6(l)": ["benzene"],
    "C6H12(l)": ["cyclohexane"],
    "C7H8(l)": ["toluene", "C6H5CH3"],
    "CH3COOH(l)": ["acetic acid", "C2H4O2", "ethanoic acid"],
    "CH3COOH(g)": ["acetic acid", "C2H4O2", "ethanoic acid"],
    "H2O2(g)": ["hydrogen peroxide", "HOOH"],
    "C(s)": ["graphite", "carbon"],
    "CaO(s)": ["calcium oxide", "lime"],
    "CaCO3(s)": ["calcium carbonate", "limestone"],
    "Ca(OH)2(s)": ["calcium hydroxide", "CaO2H2"],
    "CaC2(s)": ["calcium carbide"],
    "Fe(s)": ["iron"],
    "Fe2O3(s)": ["hematite"],
    "Fe3O4(s)": ["magnetite"],
}

# Elements in their standard states at 298.15 K and 1 bar (formation reference).
# Only elements whose standard-state heat capacity is tabulated in SVN appear.
ELEMENT_REFERENCE = {
    "H": ("H2(g)", 2),
    "O": ("O2(g)", 2),
    "N": ("N2(g)", 2),
    "Cl": ("Cl2(g)", 2),
    "C": ("C(s)", 1),
    "Fe": ("Fe(s)", 1),
}

# ---------------------------------------------------------------------------
# Entropies of the elements (NOT from SVN). SVN tabulates dHf and dGf but not
# absolute entropies. For every SVN species the entropy of formation follows
# from SVN alone,
#       dSf298 = (dHf298 - dGf298) / 298.15
# and these element entropies are used only to display the familiar absolute
# (third-law) entropy S298 and to cross-check the transcription. They cancel
# exactly in any balanced reaction among SVN species.
# For the NIST species above the direction is reversed: NIST gives S298, and
# the element entropies are needed to obtain dGf298.
# These are the CODATA Key Values for
# Thermodynamics (Cox, Wagman & Medvedev, 1989), in J/(mol K) per mole of
# atoms as written; iron is not a CODATA key substance, so its value is the
# NIST-JANAF one.  S298(species) = dSf298 + sum(element entropies).
# ---------------------------------------------------------------------------
ELEMENT_ENTROPY_CODATA = {
    "H": 130.680 / 2,   # 1/2 H2(g)
    "O": 205.152 / 2,   # 1/2 O2(g)
    "N": 191.609 / 2,   # 1/2 N2(g)
    "Cl": 223.081 / 2,  # 1/2 Cl2(g)
    "C": 5.74,          # graphite
    "S": 32.054,        # rhombic sulfur
    "Ca": 41.59,
    "Fe": 27.32,        # NIST-JANAF (Fe, reference state)
}

# Species whose printed Cp298/R does not match their own printed constants
# (see the module docstring). The checksum test skips these, and only these.
CP_CHECKSUM_EXCEPTIONS = {"C4H6(g)": "SVN prints Cp298/R = 10.720; its A, B, C give 9.931"}

SOURCES = {
    "book": "Smith, Van Ness & Abbott, Introduction to Chemical Engineering Thermodynamics, McGraw-Hill.",
    "cp_gas": "SVN Table C.1, Heat Capacities of Gases in the Ideal-Gas State",
    "cp_solid": "SVN Table C.2, Heat Capacities of Solids",
    "cp_liquid": "SVN Table C.3, Heat Capacities of Liquids",
    "formation": "SVN Table C.4, Standard Enthalpies and Gibbs Energies of Formation at 298.15 K",
    "critical": "SVN Table B.1, Characteristic Properties of Pure Species",
    "entropy_elements": ("Element entropies: CODATA Key Values for Thermodynamics (1989), NIST-JANAF for iron. "
                         "Display and cross-check for SVN species; used to obtain the Gibbs energy of formation of the NIST species"),
    "nist": "NIST Chemistry WebBook, NIST Standard Reference Database 69 (webbook.nist.gov)",
    "nist_h2o2": "NIST Chemistry WebBook, hydrogen peroxide gas: NIST-JANAF Thermochemical Tables (Chase 1998), Shomate equation",
    "nist_acetic_gas": ("NIST Chemistry WebBook, acetic acid gas: enthalpy of formation from Lebedeva (1964) and Konicek & Wadso (1970), "
                        "entropy from Weltner (1955), heat capacity table of Chao (1986) fitted by least squares"),
    "nist_acetic_liquid": "NIST Chemistry WebBook, acetic acid liquid: heat capacity at 298.15 K of Martin & Andon (1982), taken as constant",
    "low_T_janaf": ("Heat capacities from 200 K to 298.15 K: NIST-JANAF Thermochemical Tables, 4th edition "
                    "(Chase 1998), janaf.nist.gov"),
    "low_T_webbook": ("Heat capacities from 200 K to 298.15 K: NIST Chemistry WebBook, recommended ideal-gas "
                      "heat capacities (webbook.nist.gov)"),
}
