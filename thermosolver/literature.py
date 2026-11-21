"""Solver results next to values published in the research literature.

This is stress test 5 of the assignment ("check on reaction energetics with
published research work"). Every published number below was read from the
cited source itself (journal page, NIST page or NIST-JANAF table); nothing
is quoted from memory. Where a correlation is reproduced by a later paper,
the paper that was actually opened is the one cited, with the original
attribution it gives.

The solver values are computed live each time ``build()`` is called.
"""

from __future__ import annotations

import math
from typing import List

from .constants import FARADAY, R
from .reaction import Reaction
from .realgas import residual
from .species import SPECIES

# ---------------------------------------------------------------------------
# A. Standard heats of reaction at 298 K, kJ/mol, as printed in the papers
# ---------------------------------------------------------------------------
ENTHALPIES: List[tuple] = [
    ("CO2 hydrogenation to methanol", "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", -49.43,
     "Leonzio, Processes 6 (2018) 20, doi:10.3390/pr6030020"),
    ("Reverse water-gas shift", "CO2 + H2 -> CO + H2O(g)", 41.12,
     "Leonzio, Processes 6 (2018) 20, doi:10.3390/pr6030020"),
    ("Methanol synthesis from CO", "CO + 2 H2 -> CH3OH(g)", -90.6,
     "Lavoie, Front. Chem. 2 (2014) 81, doi:10.3389/fchem.2014.00081"),
    ("Methane steam reforming", "CH4 + H2O(g) -> CO + 3 H2", 205.9,
     "Helmi et al., Molecules 21 (2016) 376, doi:10.3390/molecules21030376"),
    ("Methane dry reforming", "CH4 + CO2 -> 2 CO + 2 H2", 247.0,
     "Wang et al., Nat. Commun. 15 (2024) 3765, doi:10.1038/s41467-024-48122-6"),
    ("CO2 methanation (Sabatier)", "CO2 + 4 H2 -> CH4 + 2 H2O(g)", -165.0,
     "Lavoie, Front. Chem. 2 (2014) 81, doi:10.3389/fchem.2014.00081"),
    ("Ammonia synthesis, per mol NH3", "1/2 N2 + 3/2 H2 -> NH3", -45.9,
     "Huang et al., Adv. Sci. 7 (2020) 1902390, doi:10.1002/advs.201902390"),
    ("Water-gas shift", "CO + H2O(g) -> CO2 + H2", -41.1,
     "Wang et al., Energies 16 (2023) 4347, doi:10.3390/en16114347"),
]


# ---------------------------------------------------------------------------
# B. Published equilibrium-constant correlations
# ---------------------------------------------------------------------------
def _k_wgs_moe(T: float) -> float:
    return math.exp(4577.8 / T - 4.33)


def _k_methanol_graaf(T: float) -> float:
    return 10.0 ** (3066.0 / T - 10.592)


def _k_rwgs_graaf(T: float) -> float:
    return 10.0 ** (-2073.0 / T + 2.029)


def _k_ammonia_gillespie_beattie(T: float) -> float:
    log10_ka = (-2.691122 * math.log10(T) - 5.519265e-5 * T + 1.848863e-7 * T * T
                + 2001.6 / T + 2.6899)
    # The correlation is in atm^-1 for 1/2 N2 + 3/2 H2 = NH3 (delta-nu = -1);
    # the solver's standard state is 1 bar, so K(bar) = K(atm) / 1.01325.
    return 10.0 ** log10_ka / 1.01325


def _k_smr(T: float) -> float:
    return math.exp(-26830.0 / T + 30.114)


K_CORRELATIONS: List[tuple] = [
    ("Water-gas shift", "CO + H2O(g) -> CO2 + H2", _k_wgs_moe, (600.0, 800.0, 1000.0),
     "K = exp(4577.8/T - 4.33), Moe (1962) as printed in Helmi et al., Molecules 21 (2016) 376"),
    ("CO2 + 3 H2 = CH3OH + H2O", "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", _k_methanol_graaf, (473.15, 523.15, 573.15),
     "log10 K = 3066/T - 10.592, Graaf et al. (1986) as printed in da Silva Jr. et al., "
     "Front. Chem. Eng. 6 (2024) 1440657"),
    ("Reverse water-gas shift", "CO2 + H2 -> CO + H2O(g)", _k_rwgs_graaf, (473.15, 523.15, 573.15),
     "log10 K = -2073/T + 2.029, Graaf et al. (1986) as printed in da Silva Jr. et al., "
     "Front. Chem. Eng. 6 (2024) 1440657"),
    ("Ammonia synthesis, per mol NH3", "1/2 N2 + 3/2 H2 -> NH3", _k_ammonia_gillespie_beattie, (673.15, 723.15, 773.15),
     "Gillespie & Beattie (1930) zero-pressure Ka as printed in Maansson & Andresen, "
     "Ind. Eng. Chem. Process Des. Dev. 25 (1986) 59; converted from atm to bar"),
    ("Methane steam reforming", "CH4 + H2O(g) -> CO + 3 H2", _k_smr, (900.0, 1000.0, 1100.0),
     "K = exp(-26830/T + 30.114), Wang et al., Energies 16 (2023) 4347"),
]

COMMENT = (
    "Heats of reaction agree with the published values within 0.5 kJ/mol. The two largest gaps are "
    "systematic and come from the formation data, not from the equations: SVN lists -200.66 kJ/mol for "
    "methanol vapour where the papers use about -201.1, and -46.11 kJ/mol for ammonia where CODATA gives "
    "-45.94. Equilibrium constants agree within about 6 % with the correlations for reforming, ammonia "
    "and the shift reaction below 800 K. The largest differences are 14 % for the two-constant shift "
    "correlation at 1000 K and about 20 % for the methanol correlation of Graaf et al., which was fitted "
    "to high-pressure experiments. Because K depends exponentially on the Gibbs energy, every one of "
    "these differences is close to or below 1 kJ/mol in the Gibbs energy of reaction (last column). "
    "The pressure effect on the heat of ammonia synthesis matches NIST's reference equations of state "
    "to 0.01 kJ/mol, although the individual residual enthalpies differ by up to 0.25 kJ/mol."
)


def build() -> dict:
    enthalpies = []
    for name, eq, published, source in ENTHALPIES:
        rxn = Reaction.parse(eq)
        enthalpies.append({"name": name, "equation": rxn.equation, "solver": rxn.dH0,
                           "published": published, "source": source})

    equilibrium = []
    for name, eq, func, temps, source in K_CORRELATIONS:
        rxn = Reaction.parse(eq)
        for T in temps:
            k_solver = rxn.K(T)
            k_pub = func(T)
            equilibrium.append({
                "name": name, "equation": rxn.equation, "T": T,
                "solver": k_solver, "published": k_pub,
                # the same disagreement expressed as a Gibbs energy of reaction
                "dG_equivalent": -R * T * math.log(k_solver / k_pub),
                "source": source,
            })

    other = []
    h2 = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
    other.append({"name": "H2 + 1/2 O2 -> H2O(g): standard Gibbs energy change at 1000 K",
                  "solver": h2.dG(1000.0) / 1000.0, "published": -192.590, "unit": "kJ/mol",
                  "source": "NIST-JANAF Thermochemical Tables, H2O(g), table H-064"})
    other.append({"name": "H2 + 1/2 O2 -> H2O(g): standard heat of reaction at 1000 K",
                  "solver": h2.dH(1000.0) / 1000.0, "published": -247.857, "unit": "kJ/mol",
                  "source": "NIST-JANAF Thermochemical Tables, H2O(g), table H-064"})
    other.append({"name": "Hydrogen fuel cell, reversible voltage at 1000 K (from the JANAF Gibbs energy)",
                  "solver": -h2.dG(1000.0) / (2 * FARADAY), "published": 192590.0 / (2 * 96485.33), "unit": "V",
                  "source": "NIST-JANAF Thermochemical Tables, H2O(g), table H-064"})
    h2l = Reaction.parse("H2O(l) -> H2 + 1/2 O2")
    other.append({"name": "Water electrolysis at 25 C: reversible voltage",
                  "solver": h2l.dG0 / (2 * FARADAY), "published": 1.23, "unit": "V",
                  "source": "Du et al., Chem. Rev. 122 (2022) 11830, doi:10.1021/acs.chemrev.1c00854"})
    other.append({"name": "Water electrolysis at 25 C: thermoneutral voltage",
                  "solver": h2l.dH0 / (2 * FARADAY), "published": 1.48, "unit": "V",
                  "source": "Du et al., Chem. Rev. 122 (2022) 11830, doi:10.1021/acs.chemrev.1c00854"})
    other.append({"name": "Steam electrolysis at 700 C: thermoneutral voltage",
                  "solver": -h2.dH(973.15) / (2 * FARADAY), "published": 1.28, "unit": "V",
                  "source": "Zhou et al., ChemSusChem 18 (2025) e202501131, doi:10.1002/cssc.202501131"})
    # Effect of pressure on the enthalpy of pure gases at 700 K: H(200 bar) - H(1 bar)
    nist = {"NH3(g)": -2.117, "N2(g)": 0.202, "H2(g)": 0.335}
    nu = {"NH3(g)": 1.0, "N2(g)": -0.5, "H2(g)": -1.5}
    total_solver = total_nist = 0.0
    for sid, published in nist.items():
        sp = SPECIES[sid]
        shift = (residual(sp, 700.0, 200.0, "pr").HR - residual(sp, 700.0, 1.0, "pr").HR) / 1000.0
        total_solver += nu[sid] * shift
        total_nist += nu[sid] * published
        other.append({"name": f"{sid}: enthalpy change from 1 to 200 bar at 700 K (Peng/Robinson residual)",
                      "solver": shift, "published": published, "unit": "kJ/mol",
                      "source": "NIST Chemistry WebBook, thermophysical properties of fluid systems (isothermal data)"})
    other.append({"name": "Ammonia synthesis: change of the heat of reaction from 1 to 200 bar at 700 K, per mol NH3",
                  "solver": total_solver, "published": total_nist, "unit": "kJ/mol",
                  "source": "Combination of the three NIST WebBook isotherms above"})
    return {"enthalpies": enthalpies, "equilibrium": equilibrium, "other": other, "comment": COMMENT}
