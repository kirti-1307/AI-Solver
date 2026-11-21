"""Predefined reactions and ready-made examples for the two extra features.

Every species used here is in the SVN-based database, and the test-suite
checks that every equation is balanced and can be evaluated.
"""

from __future__ import annotations

# id, name, equation, category, suggested temperature (K), note
REACTIONS = [
    ("co2_methanol", "CO2 hydrogenation to methanol", "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "C1 chemistry", 523.15,
     "Exothermic and mole-reducing: favoured by low temperature and high pressure."),
    ("rwgs", "Reverse water-gas shift", "CO2 + H2 -> CO + H2O(g)", "C1 chemistry", 873.15,
     "Mildly endothermic, no change in moles: pressure has almost no effect."),
    ("wgs", "Water-gas shift", "CO + H2O(g) -> CO2 + H2", "C1 chemistry", 623.15,
     "Mildly exothermic. K falls through 1 near 1100 K."),
    ("methanol_synthesis", "Methanol synthesis from syngas", "CO + 2 H2 -> CH3OH(g)", "C1 chemistry", 523.15,
     "SVN worked example: dH = -103,566 J at 800 C."),
    ("smr", "Methane steam reforming", "CH4 + H2O(g) -> CO + 3 H2", "C1 chemistry", 1073.15,
     "Strongly endothermic; becomes favourable above about 900 K."),
    ("dry_reforming", "Methane dry reforming", "CH4 + CO2 -> 2 CO + 2 H2", "C1 chemistry", 1073.15,
     "Even more endothermic than steam reforming."),
    ("sabatier", "CO2 methanation (Sabatier)", "CO2 + 4 H2 -> CH4 + 2 H2O(g)", "C1 chemistry", 623.15,
     "Strongly exothermic."),
    ("co_methanation", "CO methanation", "CO + 3 H2 -> CH4 + H2O(g)", "C1 chemistry", 623.15,
     "Reverse of steam reforming."),
    ("pox", "Partial oxidation of methane", "CH4 + 1/2 O2 -> CO + 2 H2", "C1 chemistry", 1073.15, ""),
    ("methane_pyrolysis", "Methane pyrolysis", "CH4 -> C(s) + 2 H2", "C1 chemistry", 1273.15,
     "Turquoise hydrogen: solid carbon instead of CO2."),
    ("boudouard", "Boudouard reaction", "2 CO -> C(s) + CO2", "C1 chemistry", 873.15,
     "Coke formation. Favoured at low temperature."),
    ("gasification", "Steam gasification of carbon", "C(s) + H2O(g) -> CO + H2", "C1 chemistry", 1173.15, ""),
    ("ammonia", "Ammonia synthesis (Haber-Bosch)", "N2 + 3 H2 -> 2 NH3", "Nitrogen chemistry", 723.15,
     "Exothermic and mole-reducing; run hot only for kinetics."),
    ("ammonia_oxidation", "Ammonia oxidation (Ostwald)", "4 NH3 + 5 O2 -> 4 NO + 6 H2O(g)", "Nitrogen chemistry", 1123.15, ""),
    ("no_formation", "Thermal NO formation", "N2 + O2 -> 2 NO", "Nitrogen chemistry", 1800.0,
     "Endothermic; only matters at flame temperatures."),
    ("no_oxidation", "NO oxidation", "2 NO + O2 -> 2 NO2", "Nitrogen chemistry", 400.0, ""),
    ("n2o4", "NO2 dimerisation", "2 NO2 -> N2O4", "Nitrogen chemistry", 320.0,
     "N2O4 and NO2 are not in SVN Table B.1: ideal gas only."),
    ("n2o_decomposition", "N2O decomposition", "2 N2O -> 2 N2 + O2", "Nitrogen chemistry", 773.15, ""),
    ("methane_combustion_g", "Methane combustion, water as vapour (LHV)", "CH4 + 2 O2 -> CO2 + 2 H2O(g)", "Combustion", 298.15,
     "Lower heating value."),
    ("methane_combustion_l", "Methane combustion, water as liquid (HHV)", "CH4 + 2 O2 -> CO2 + 2 H2O(l)", "Combustion", 298.15,
     "Higher heating value. Compare with the vapour case."),
    ("hydrogen_combustion_g", "Hydrogen oxidation, water as vapour", "H2 + 1/2 O2 -> H2O(g)", "Combustion", 1073.15,
     "The hydrogen fuel-cell reaction. SVN fuel-cell section: 1.184 V at 25 C."),
    ("hydrogen_combustion_l", "Hydrogen oxidation, water as liquid", "H2 + 1/2 O2 -> H2O(l)", "Combustion", 298.15,
     "With liquid water the reversible voltage at 25 C is 1.229 V."),
    ("co_oxidation", "CO oxidation", "CO + 1/2 O2 -> CO2", "Combustion", 800.0, ""),
    ("propane_combustion", "Propane combustion", "C3H8 + 5 O2 -> 3 CO2 + 4 H2O(g)", "Combustion", 298.15, ""),
    ("ethanol_combustion", "Ethanol combustion", "C2H5OH(g) + 3 O2 -> 2 CO2 + 3 H2O(g)", "Combustion", 298.15, ""),
    ("h2s_combustion", "H2S combustion", "2 H2S + 3 O2 -> 2 SO2 + 2 H2O(g)", "Sulfur chemistry", 1273.15, ""),
    ("so2_oxidation", "SO2 oxidation (contact process)", "SO2 + 1/2 O2 -> SO3(g)", "Sulfur chemistry", 723.15,
     "Exothermic equilibrium: the classic multi-bed converter."),
    ("ethylene_hydration", "Ethylene hydration to ethanol", "C2H4 + H2O(g) -> C2H5OH(g)", "Petrochemicals", 593.15,
     "SVN worked example: K = 2.942e-3 at 320 C."),
    ("ethanol_dehydrogenation", "Ethanol dehydrogenation", "C2H5OH(g) -> CH3CHO + H2", "Petrochemicals", 573.15, ""),
    ("ethane_cracking", "Ethane dehydrogenation", "C2H6 -> C2H4 + H2", "Petrochemicals", 1123.15,
     "Endothermic and mole-increasing: hot and at low pressure."),
    ("pdh", "Propane dehydrogenation", "C3H8 -> C3H6 + H2", "Petrochemicals", 873.15, ""),
    ("butane_dehydrogenation", "n-Butane dehydrogenation", "n-C4H10 -> C4H8 + H2", "Petrochemicals", 873.15, ""),
    ("acetylene_hydrogenation", "Acetylene hydrogenation", "C2H2 + H2 -> C2H4", "Petrochemicals", 373.15, ""),
    ("benzene_hydrogenation", "Benzene hydrogenation", "C6H6(g) + 3 H2 -> C6H12(g)", "Petrochemicals", 473.15, ""),
    ("styrene", "Ethylbenzene dehydrogenation to styrene", "C8H10 -> C8H8 + H2", "Petrochemicals", 873.15, ""),
    ("methanol_dehydrogenation", "Methanol dehydrogenation to formaldehyde", "CH3OH(g) -> CH2O + H2", "Petrochemicals", 923.15, ""),
    ("ethylene_oxide", "Ethylene epoxidation", "C2H4 + 1/2 O2 -> (CH2)2O", "Petrochemicals", 523.15, ""),
    ("deacon", "Deacon process", "4 HCl + O2 -> 2 Cl2 + 2 H2O(g)", "Inorganic", 673.15,
     "SVN worked example: dH0 = -114,408 J at 25 C."),
    ("calcination", "Limestone calcination", "CaCO3 -> CaO + CO2", "Inorganic", 1150.0,
     "Gas-solid: the CO2 pressure at equilibrium equals K."),
    ("iron_reduction_h2", "Hematite reduction with hydrogen", "Fe2O3 + 3 H2 -> 2 Fe + 3 H2O(g)", "Inorganic", 900.0,
     "Hydrogen direct reduction (green steel). Cp of Fe2O3 is valid only to 960 K."),
    ("water_vaporisation", "Vaporisation of water", "H2O(l) -> H2O(g)", "Phase change", 373.15,
     "A phase change treated as a reaction: K = 1 near the normal boiling point."),
    ("acetic_acid", "Acetaldehyde oxidation to acetic acid", "CH3CHO + 1/2 O2 -> CH3COOH(l)", "Petrochemicals", 298.15,
     "Liquid acetic acid: formation data from SVN, constant Cp from NIST (valid 290 to 320 K)."),
    ("carbonylation", "Methanol carbonylation to acetic acid", "CH3OH(g) + CO -> CH3COOH(g)", "Petrochemicals", 453.15,
     "The Monsanto/Cativa route. Acetic acid vapour uses NIST data (ideal-gas monomer)."),
    ("h2o2_synthesis", "Direct synthesis of hydrogen peroxide", "H2 + O2 -> H2O2(g)", "Inorganic", 298.15,
     "H2O2 uses NIST data. Favourable, but water is far more stable: see the Product slate tab."),
    ("h2o2_decomposition", "Hydrogen peroxide decomposition", "2 H2O2(g) -> 2 H2O(g) + O2", "Inorganic", 400.0,
     "H2O2 uses NIST data. Strongly exothermic and favourable at every temperature."),
]

# Reactions built from other reactions (Hess's law). Multiplier -1 reverses a step.
COMBINATIONS = [
    {
        "id": "co2_methanol_from_steps",
        "name": "CO2 to methanol = reverse water-gas shift + methanol synthesis",
        "steps": [("CO2 + H2 -> CO + H2O(g)", 1), ("CO + 2 H2 -> CH3OH(g)", 1)],
        "T": 523.15,
    },
    {
        "id": "dry_reforming_from_steps",
        "name": "Dry reforming = steam reforming - water-gas shift",
        "steps": [("CH4 + H2O(g) -> CO + 3 H2", 1), ("CO + H2O(g) -> CO2 + H2", -1)],
        "T": 1073.15,
    },
    {
        "id": "sabatier_from_steps",
        "name": "Sabatier = reverse water-gas shift - steam reforming",
        "steps": [("CO2 + H2 -> CO + H2O(g)", 1), ("CH4 + H2O(g) -> CO + 3 H2", -1)],
        "T": 623.15,
    },
    {
        "id": "methane_combustion_from_formation",
        "name": "Methane combustion from three formation reactions",
        "steps": [("C(s) + O2 -> CO2", 1), ("H2 + 1/2 O2 -> H2O(g)", 2), ("C(s) + 2 H2 -> CH4", -1)],
        "T": 298.15,
    },
    {
        "id": "smr_wgs_overall",
        "name": "Overall hydrogen plant = steam reforming + water-gas shift",
        "steps": [("CH4 + H2O(g) -> CO + 3 H2", 1), ("CO + H2O(g) -> CO2 + H2", 1)],
        "T": 1073.15,
    },
    {
        "id": "h2o2_decomposition_from_steps",
        "name": "H2O2 decomposition = 2 x water formation - 2 x peroxide formation",
        "steps": [("H2 + 1/2 O2 -> H2O(g)", 2), ("H2 + O2 -> H2O2(g)", -2)],
        "T": 400.0,
    },
    {
        "id": "gasification_combo",
        "name": "CO2 gasification of carbon = steam gasification - water-gas shift",
        "steps": [("C(s) + H2O(g) -> CO + H2", 1), ("CO + H2O(g) -> CO2 + H2", -1)],
        "T": 1173.15,
    },
]

# Species sets for the Gibbs-minimisation feature ("what actually forms?").
NETWORKS = [
    {
        "id": "co2_hydrogenation",
        "name": "CO2 hydrogenation: methanol, CO or methane?",
        "species": ["CO2(g)", "H2(g)", "CH3OH(g)", "CO(g)", "H2O(g)", "CH4(g)"],
        "feed": {"CO2(g)": 1, "H2(g)": 3},
        "T_range": [400, 900], "P": 50,
        "optional": ["CH4(g)"],
        "note": "Untick CH4 to see what a catalyst that cannot make methane is limited to.",
    },
    {
        "id": "steam_reforming",
        "name": "Methane steam reforming with water-gas shift",
        "species": ["CH4(g)", "H2O(g)", "CO(g)", "CO2(g)", "H2(g)"],
        "feed": {"CH4(g)": 2, "H2O(g)": 3},
        "T_range": [600, 1300], "P": 1,
        "optional": [],
        "note": "SVN solves this system at 1000 K and 1 bar by Gibbs minimisation.",
    },
    {
        "id": "dry_reforming",
        "name": "Dry reforming of methane",
        "species": ["CH4(g)", "CO2(g)", "CO(g)", "H2(g)", "H2O(g)"],
        "feed": {"CH4(g)": 1, "CO2(g)": 1},
        "T_range": [700, 1400], "P": 1,
        "optional": [],
        "note": "Watch the carbon activity: coke is predicted at the lower temperatures.",
    },
    {
        "id": "ammonia",
        "name": "Ammonia synthesis loop",
        "species": ["N2(g)", "H2(g)", "NH3(g)"],
        "feed": {"N2(g)": 1, "H2(g)": 3},
        "T_range": [500, 900], "P": 200,
        "optional": [],
        "note": "One reaction only, so the result must match the single-reaction solver.",
    },
    {
        "id": "syngas_to_methanol",
        "name": "Syngas to methanol with shift",
        "species": ["CO(g)", "H2(g)", "CO2(g)", "CH3OH(g)", "H2O(g)"],
        "feed": {"CO(g)": 1, "H2(g)": 2, "CO2(g)": 0.1},
        "T_range": [450, 700], "P": 80,
        "optional": [],
        "note": "",
    },
    {
        "id": "h2_o2",
        "name": "H2 + O2: water or hydrogen peroxide?",
        "species": ["H2(g)", "O2(g)", "H2O(g)", "H2O2(g)"],
        "feed": {"H2(g)": 1, "O2(g)": 1},
        "T_range": [300, 1200], "P": 1,
        "optional": ["H2O(g)"],
        "note": "Untick H2O to see what a catalyst that stops at the peroxide could reach. H2O2 uses NIST data.",
    },
    {
        "id": "nox",
        "name": "NOx from hot air",
        "species": ["N2(g)", "O2(g)", "NO(g)", "NO2(g)", "N2O(g)"],
        "feed": {"N2(g)": 0.79, "O2(g)": 0.21},
        "T_range": [1000, 2000], "P": 1,
        "optional": [],
        "note": "Shows why NO only appears in flames.",
    },
]

# Reactions that make good examples for the electrochemical lens.
ELECTRO_EXAMPLES = [
    ("hydrogen_combustion_g", "Hydrogen fuel cell / steam electrolysis"),
    ("hydrogen_combustion_l", "Low-temperature hydrogen fuel cell (liquid water)"),
    ("co_oxidation", "CO fuel cell / CO2 electrolysis"),
    ("methane_combustion_g", "Direct methane fuel cell"),
    ("ammonia", "Electrochemical ammonia synthesis"),
    ("co2_methanol", "CO2 electro-reduction to methanol"),
    ("h2o2_synthesis", "Two-electron oxygen reduction to H2O2"),
]


def reaction_by_id(rid: str):
    for row in REACTIONS:
        if row[0] == rid:
            return row
    return None
