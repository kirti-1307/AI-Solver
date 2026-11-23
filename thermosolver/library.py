"""Predefined reactions and ready-made examples for the two extra features
(the product slate and the heat lab).

Every species used here is in the SVN-based database, and the test-suite
checks that every equation is balanced and can be evaluated.
"""

from __future__ import annotations

# id, name, equation, category, suggested temperature (K), note
REACTIONS = [
    ("co2_methanol", "CO2 hydrogenation to methanol", "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "One-carbon molecules", 523.15,
     "Exothermic and makes fewer gas molecules: favoured by low temperature and high pressure."),
    ("rwgs", "Reverse water-gas shift", "CO2 + H2 -> CO + H2O(g)", "One-carbon molecules", 873.15,
     "Mildly endothermic, no change in moles: pressure has almost no effect."),
    ("wgs", "Water-gas shift", "CO + H2O(g) -> CO2 + H2", "One-carbon molecules", 623.15,
     "Mildly exothermic. K falls through 1 near 1100 K."),
    ("methanol_synthesis", "Methanol synthesis from CO and H2", "CO + 2 H2 -> CH3OH(g)", "One-carbon molecules", 523.15,
     "SVN worked example: dH = -103,566 J at 800 C."),
    ("smr", "Methane steam reforming", "CH4 + H2O(g) -> CO + 3 H2", "One-carbon molecules", 1073.15,
     "Strongly endothermic; products are favoured above about 900 K."),
    ("dry_reforming", "Methane dry reforming", "CH4 + CO2 -> 2 CO + 2 H2", "One-carbon molecules", 1073.15,
     "Even more endothermic than steam reforming."),
    ("sabatier", "CO2 methanation", "CO2 + 4 H2 -> CH4 + 2 H2O(g)", "One-carbon molecules", 623.15,
     "Strongly exothermic."),
    ("co_methanation", "CO methanation", "CO + 3 H2 -> CH4 + H2O(g)", "One-carbon molecules", 623.15,
     "Reverse of steam reforming."),
    ("pox", "Partial oxidation of methane", "CH4 + 1/2 O2 -> CO + 2 H2", "One-carbon molecules", 1073.15, ""),
    ("methane_pyrolysis", "Methane pyrolysis", "CH4 -> C(s) + 2 H2", "One-carbon molecules", 1273.15,
     "Hydrogen from methane, with solid carbon instead of CO2 as the second product."),
    ("boudouard", "Solid carbon from CO", "2 CO -> C(s) + CO2", "One-carbon molecules", 873.15,
     "Solid carbon (soot) forms. Favoured at low temperature."),
    ("gasification", "Steam gasification of carbon", "C(s) + H2O(g) -> CO + H2", "One-carbon molecules", 1173.15, ""),
    ("ammonia", "Ammonia synthesis (Haber-Bosch)", "N2 + 3 H2 -> 2 NH3", "Nitrogen chemistry", 723.15,
     "Exothermic and makes fewer gas molecules; run hot only to make the reaction fast enough."),
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
     "Water leaves as vapour: the lower heating value of hydrogen."),
    ("hydrogen_combustion_l", "Hydrogen oxidation, water as liquid", "H2 + 1/2 O2 -> H2O(l)", "Combustion", 298.15,
     "Water leaves as liquid: the higher heating value of hydrogen."),
    ("co_oxidation", "CO oxidation", "CO + 1/2 O2 -> CO2", "Combustion", 800.0, ""),
    ("propane_combustion", "Propane combustion", "C3H8 + 5 O2 -> 3 CO2 + 4 H2O(g)", "Combustion", 298.15, ""),
    ("ethanol_combustion", "Ethanol combustion", "C2H5OH(g) + 3 O2 -> 2 CO2 + 3 H2O(g)", "Combustion", 298.15, ""),
    ("h2s_combustion", "H2S combustion", "2 H2S + 3 O2 -> 2 SO2 + 2 H2O(g)", "Sulfur chemistry", 1273.15, ""),
    ("so2_oxidation", "SO2 oxidation (contact process)", "SO2 + 1/2 O2 -> SO3(g)", "Sulfur chemistry", 723.15,
     "Exothermic, so the conversion at equilibrium falls as the temperature rises."),
    ("ethylene_hydration", "Ethylene hydration to ethanol", "C2H4 + H2O(g) -> C2H5OH(g)", "Petrochemicals", 593.15,
     "SVN worked example: K = 2.942e-3 at 320 C."),
    ("ethanol_dehydrogenation", "Ethanol dehydrogenation", "C2H5OH(g) -> CH3CHO + H2", "Petrochemicals", 573.15, ""),
    ("ethane_cracking", "Ethane dehydrogenation", "C2H6 -> C2H4 + H2", "Petrochemicals", 1123.15,
     "Endothermic and makes more gas molecules: favoured hot and at low pressure."),
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
    ("iron_reduction_h2", "Iron oxide (Fe2O3) reduction with hydrogen", "Fe2O3 + 3 H2 -> 2 Fe + 3 H2O(g)", "Inorganic", 900.0,
     "Iron made with hydrogen instead of carbon. Cp of Fe2O3 is valid only to 960 K."),
    ("water_vaporisation", "Vaporisation of water", "H2O(l) -> H2O(g)", "Phase change", 373.15,
     "A phase change treated as a reaction: K = 1 near the normal boiling point."),
    ("acetic_acid", "Acetaldehyde oxidation to acetic acid", "CH3CHO + 1/2 O2 -> CH3COOH(l)", "Petrochemicals", 298.15,
     "Liquid acetic acid: formation data from SVN, constant Cp from NIST (valid 290 to 320 K)."),
    ("carbonylation", "Methanol carbonylation to acetic acid", "CH3OH(g) + CO -> CH3COOH(g)", "Petrochemicals", 453.15,
     "An industrial route to acetic acid. Acetic acid vapour uses NIST data."),
    ("h2o2_synthesis", "Direct synthesis of hydrogen peroxide", "H2 + O2 -> H2O2(g)", "Inorganic", 298.15,
     "H2O2 uses NIST data. Products are favoured, but water is far more stable: see the Product slate tab."),
    ("h2o2_decomposition", "Hydrogen peroxide decomposition", "2 H2O2(g) -> 2 H2O(g) + O2", "Inorganic", 400.0,
     "H2O2 uses NIST data. Strongly exothermic; products are favoured at every temperature."),
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
        "name": "CO2 methanation = reverse water-gas shift - steam reforming",
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

# Species sets for the product slate ("what actually forms?").
NETWORKS = [
    {
        "id": "co2_hydrogenation",
        "name": "CO2 hydrogenation: methanol, CO or methane?",
        "species": ["CO2(g)", "H2(g)", "CH3OH(g)", "CO(g)", "H2O(g)", "CH4(g)"],
        "feed": {"CO2(g)": 1, "H2(g)": 3},
        "T_range": [400, 900], "P": 50,
        "T": 523,              # the tab opens here: the temperature of methanol synthesis
        "optional": ["CH4(g)"],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Methane takes almost all the carbon. Methanol and CO get nothing, so their switches do nothing yet."},
            {"label": "Methane off", "off": ["CH4(g)"],
             "say": "A catalyst that cannot make methane. Now methanol and CO share the carbon, and their switches wake up."},
            {"label": "Methane and CO off", "off": ["CH4(g)", "CO(g)"],
             "say": "Only methanol can form: the most a perfectly selective methanol catalyst could reach."},
        ],
        "note": "Switch CH4 off to see what a catalyst that cannot make methane is limited to.",
    },
    {
        "id": "steam_reforming",
        "name": "Methane steam reforming with water-gas shift",
        "species": ["CH4(g)", "H2O(g)", "CO(g)", "CO2(g)", "H2(g)"],
        "feed": {"CH4(g)": 2, "H2O(g)": 3},
        "T_range": [600, 1300], "P": 1,
        "optional": [],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Reforming and the water-gas shift run together: the carbon ends up as CO and CO2."},
            {"label": "CO2 off", "off": ["CO2(g)"],
             "say": "No water-gas shift: every converted carbon atom ends up as CO."},
            {"label": "CO off", "off": ["CO(g)"],
             "say": "Reforming straight to CO2. Less methane converts, because this route needs more steam."},
        ],
        "note": "SVN solves this system at 1000 K and 1 bar; the Validation tab compares the mole fractions.",
    },
    {
        "id": "dry_reforming",
        "name": "Dry reforming of methane",
        "species": ["CH4(g)", "CO2(g)", "CO(g)", "H2(g)", "H2O(g)"],
        "feed": {"CH4(g)": 1, "CO2(g)": 1},
        "T_range": [700, 1400], "P": 1,
        "optional": [],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Besides reforming, some hydrogen reacts with CO2 to water (the reverse water-gas shift)."},
            {"label": "Water off", "off": ["H2O(g)"],
             "say": "No reverse shift: methane and CO2 now convert to exactly the same extent."},
        ],
        "note": "Watch the solid-carbon card: at the lower temperatures solid carbon (soot) can form.",
    },
    {
        "id": "ammonia",
        "name": "Ammonia synthesis",
        "species": ["N2(g)", "H2(g)", "NH3(g)"],
        "feed": {"N2(g)": 1, "H2(g)": 3},
        "T_range": [500, 900], "P": 200,
        "optional": [],
        "tour": [],
        "note": "One reaction only, so the result must match the single-reaction solver.",
    },
    {
        "id": "syngas_to_methanol",
        "name": "CO and H2 to methanol, with water-gas shift",
        "species": ["CO(g)", "H2(g)", "CO2(g)", "CH3OH(g)", "H2O(g)"],
        "feed": {"CO(g)": 1, "H2(g)": 2, "CO2(g)": 0.1},
        "T_range": [450, 700], "P": 80,
        "optional": [],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Methanol synthesis and a little water-gas shift run together."},
            {"label": "Methanol off", "off": ["CH3OH(g)"],
             "say": "Only the shift reaction is left: hardly any CO converts."},
        ],
        "note": "",
    },
    {
        "id": "h2_o2",
        "name": "H2 + O2: water or hydrogen peroxide?",
        "species": ["H2(g)", "O2(g)", "H2O(g)", "H2O2(g)"],
        "feed": {"H2(g)": 1, "O2(g)": 1},
        "T_range": [300, 1200], "P": 1,
        "optional": ["H2O(g)"],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Water is so stable that it takes all the hydrogen. The peroxide switch does nothing."},
            {"label": "Water off", "off": ["H2O(g)"],
             "say": "A catalyst that stops at the peroxide: now hydrogen peroxide is what forms."},
        ],
        "note": "Switch H2O off to see what a catalyst that stops at the peroxide could reach. H2O2 uses NIST data.",
    },
    {
        "id": "nox",
        "name": "NOx from hot air",
        "species": ["N2(g)", "O2(g)", "NO(g)", "NO2(g)", "N2O(g)"],
        "feed": {"N2(g)": 0.79, "O2(g)": 0.21},
        "T_range": [1000, 2000], "P": 1,
        "optional": [],
        "tour": [
            {"label": "Everything allowed", "off": [],
             "say": "Hot air makes a little NO and almost nothing else. Drag the temperature up to see it grow."},
            {"label": "NO off", "off": ["NO(g)"],
             "say": "Without NO practically nothing forms: NO2 and N2O are far less stable at flame temperatures."},
        ],
        "note": "Shows why NO only appears in flames.",
    },
]

# Industrial reactions at their usual conditions, for the overview on the
# pressure tab: how far the real-gas heat of reaction is from the ideal-gas one.
# Each entry is a reaction of REACTIONS (by id) with a temperature in K and a
# pressure in bar that are typical of the industrial process.
PRESSURE_CASES = [
    {"id": "co2_methanol", "T": 523.15, "P": 50.0},
    {"id": "methanol_synthesis", "T": 523.15, "P": 80.0},
    {"id": "ethylene_hydration", "T": 573.15, "P": 70.0},
    {"id": "ammonia", "T": 723.15, "P": 200.0},
    {"id": "smr", "T": 1100.0, "P": 30.0},
    {"id": "so2_oxidation", "T": 700.0, "P": 10.0},
]

# Ready-made cases for the heat lab (reactor energy balance).
# Fractions: excess 0.2 = 20 % excess; conversion 1.0 = complete.
HEAT_EXAMPLES = [
    {
        "id": "methane_burner",
        "name": "Methane burner with 20 % excess air (flame temperature)",
        "equation": "CH4 + 2 O2 -> CO2 + 2 H2O(g)",
        "mode": "adiabatic", "T_in": 298.15, "conversion": 1.0,
        "excess_species": "O2(g)", "excess": 0.2, "air": True, "side": [],
        "note": "Methane and air enter at 25 C and burn completely with no heat loss. "
                "This is the theoretical flame temperature example of SVN Chapter 4.",
    },
    {
        "id": "hydrogen_burner",
        "name": "Hydrogen burner with 20 % excess air",
        "equation": "H2 + 1/2 O2 -> H2O(g)",
        "mode": "adiabatic", "T_in": 298.15, "conversion": 1.0,
        "excess_species": "O2(g)", "excess": 0.2, "air": True, "side": [],
        "note": "Compare with methane: no carbon, so no CO2 in the flue gas.",
    },
    {
        "id": "propane_burner",
        "name": "Propane burner with 50 % excess air",
        "equation": "C3H8 + 5 O2 -> 3 CO2 + 4 H2O(g)",
        "mode": "adiabatic", "T_in": 298.15, "conversion": 1.0,
        "excess_species": "O2(g)", "excess": 0.5, "air": True, "side": [],
        "note": "Drag the excess air: every extra mole of air has to be heated too, so the flame cools.",
    },
    {
        "id": "condensing_boiler",
        "name": "Condensing boiler: flue gas of a methane burner cooled to 40 C",
        "equation": "CH4 + 2 O2 -> CO2 + 2 H2O(g)",
        "mode": "duty", "T_in": 298.15, "T_out": 313.15, "conversion": 1.0,
        "excess_species": "O2(g)", "excess": 0.2, "air": True, "side": [], "condense": True,
        "note": "The flue gas is cooled to 40 C. Its water vapour becomes saturated at 55.5 C, so below that part "
                "of the water condenses and gives up its latent heat. Drag the outlet temperature across 329 K: "
                "the heat line bends there. Untick the water box to see the answer with all the water kept as vapour.",
    },
    {
        "id": "reformer_duty",
        "name": "Steam reformer: heat that the furnace must supply",
        "equation": "CH4 + H2O(g) -> CO + 3 H2",
        "mode": "duty", "T_in": 600.0, "T_out": 1300.0, "conversion": 1.0,
        "excess_species": "H2O(g)", "excess": 1.0, "air": False,
        "side": [{"equation": "CO + H2O(g) -> CO2 + H2", "extent": 0.13}],
        "note": "2 mol steam per mol methane enter at 600 K, the products leave at 1300 K and part of the CO "
                "reacts on with steam to CO2 (17.4 mol-% CO in the product). The reformer example of SVN Chapter 4.",
    },
    {
        "id": "ammonia_converter",
        "name": "Ammonia converter: temperature rise over one adiabatic bed",
        "equation": "N2 + 3 H2 -> 2 NH3",
        "mode": "adiabatic", "T_in": 673.15, "conversion": 0.15,
        "excess_species": "H2(g)", "excess": 0.0, "air": False, "side": [],
        "note": "Only part of the feed reacts in one pass. Drag the conversion to see how fast the bed heats up.",
    },
    {
        "id": "so2_converter",
        "name": "SO2 oxidation bed (contact process)",
        "equation": "SO2 + 1/2 O2 -> SO3(g)",
        "mode": "adiabatic", "T_in": 693.15, "conversion": 0.7,
        "excess_species": "O2(g)", "excess": 1.0, "air": True, "side": [],
        "note": "The nitrogen of the air soaks up heat and limits the temperature rise.",
    },
    {
        "id": "ethane_cracker",
        "name": "Ethane cracking: heat that the furnace must supply",
        "equation": "C2H6 -> C2H4 + H2",
        "mode": "duty", "T_in": 900.0, "T_out": 1100.0, "conversion": 0.6,
        "excess_species": None, "excess": 0.0, "air": False, "side": [],
        "note": "An endothermic reaction: the furnace supplies both the heat of reaction and the sensible heat.",
    },
    {
        "id": "lime_kiln",
        "name": "Lime kiln: heat needed to calcine limestone",
        "equation": "CaCO3 -> CaO + CO2",
        "mode": "duty", "T_in": 298.15, "T_out": 1173.15, "conversion": 1.0,
        "excess_species": None, "excess": 0.0, "air": False, "side": [],
        "note": "Cold limestone in, hot lime and CO2 out at 900 C.",
    },
]

# Calibration run of the course bomb-calorimeter handout (benzoic acid standard).
# Energies in calories as printed there; the solver converts with 4.184 J/cal.
CALORIMETER_HANDOUT = {
    "standard": "benzoic acid",
    "calorific_value_cal_per_g": 6319.0,
    "mass_g": 1.1942,
    "dT": 2.48,
    "corrections_cal": 41.0,          # cotton thread 20.1 cal + nichrome wire 20.9 cal
    "C_cal_cal_per_K": 3059.33,
}


def reaction_by_id(rid: str):
    for row in REACTIONS:
        if row[0] == rid:
            return row
    return None
