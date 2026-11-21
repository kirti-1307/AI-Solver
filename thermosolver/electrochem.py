"""Electrochemical lens: any redox reaction seen as a fuel cell or an electrolyser.

A reaction carried out reversibly in an electrochemical cell at constant T and
P exchanges electrical work equal to the Gibbs energy change (SVN, fuel-cell
section of the chemical-equilibria chapter):

        W_elec = dG                       (work done ON the system)
        Q_rev  = T dS = dH - dG           (heat absorbed by the cell)
        E_rev  = -dG / (n F)              reversible cell voltage
        E_tn   = -dH / (n F)              thermoneutral voltage

n is the number of moles of electrons passed per mole of reaction as written
and F is the Faraday constant.

* dG < 0: galvanic (fuel cell). At most -dG of the reaction enthalpy -dH can
  leave as electricity, so the ideal efficiency is dG/dH. It is compared with
  the Carnot efficiency 1 - Tc/T of a heat engine that burns the same fuel.
* dG > 0: electrolytic. At least dG must be supplied as electricity; the rest
  of dH, T dS, can be supplied as heat. This is why high-temperature
  electrolysis needs less electricity.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from .constants import FARADAY, P0, T0
from .errors import InputError, PhaseError
from .realgas import reaction_at_pressure


def electron_count(rxn) -> Tuple[Optional[float], str]:
    """Electrons transferred per mole of reaction, from the oxidant or reductant.

    Each O2 molecule accepts 4 electrons, each H2 molecule releases 2, each Cl2
    accepts 2. If none of them takes part, n cannot be inferred automatically.

    Hydrogen peroxide needs its own rule, because its oxygen is at oxidation
    state -1, not -2: O2 going to (or coming from) H2O2 exchanges only 2
    electrons per O2. When H2 is the reductant it is counted instead, which is
    right for any oxygen product.
    """
    if rxn.stoich.get("H2O2(g)"):
        for sid, label in (("H2(g)", "2 electrons per H2"),
                           ("O2(g)", "2 electrons per O2, because the other oxygen species is a peroxide"),
                           ("H2O2(g)", "2 electrons per H2O2")):
            nu = rxn.stoich.get(sid)
            if nu:
                return 2.0 * abs(nu), label
    for sid, per_mol, label in (("O2(g)", 4.0, "4 electrons per O2"),
                                ("H2(g)", 2.0, "2 electrons per H2"),
                                ("Cl2(g)", 2.0, "2 electrons per Cl2")):
        nu = rxn.stoich.get(sid)
        if nu:
            return per_mol * abs(nu), label
    return None, "no O2, H2 or Cl2 in the reaction"


def electrochemistry(rxn, T: float, n_electrons: Optional[float] = None,
                     P: float = P0, model: str = "ideal", T_cold: float = T0) -> dict:
    """Reversible and thermoneutral voltages and ideal efficiencies at T, P."""
    auto_n, basis = electron_count(rxn)
    if n_electrons is None:
        if auto_n is None:
            raise InputError(
                "The number of electrons transferred could not be inferred "
                "(the reaction contains no O2, H2 or Cl2). Please enter it."
            )
        n_electrons = auto_n
    else:
        basis = "entered by the user"
    if not isinstance(n_electrons, (int, float)) or isinstance(n_electrons, bool) or n_electrons <= 0:
        raise InputError("The number of electrons must be a positive number.")

    at_P = reaction_at_pressure(rxn, T, P, model)
    if not at_P["gas_phase_valid"]:
        raise PhaseError(
            f"{', '.join(at_P['no_vapour_species'])} has no vapour-like state at {T:g} K and {P:g} bar "
            f"with this real-gas model, so a gas-phase cell voltage cannot be calculated there. "
            f"Use the ideal-gas model, a lower pressure or a higher temperature.")
    dH, dS, dG = at_P["dH_P"], at_P["dS_P"], at_P["dG_P"]
    nF = n_electrons * FARADAY
    E_rev = -dG / nF
    E_tn = -dH / nF
    mode = "galvanic" if dG < 0 else "electrolytic"

    efficiency = None
    if mode == "galvanic" and dH < 0:
        efficiency = dG / dH           # electrical work out / heat of reaction
    elif mode == "electrolytic" and dH > 0:
        efficiency = dG / dH           # share of the energy demand that must be electricity

    carnot = 1.0 - T_cold / T if T > T_cold else 0.0
    return {
        "T": T, "P": P, "model": model,
        "n_electrons": n_electrons, "n_basis": basis, "n_auto": auto_n,
        "dH": dH, "dS": dS, "dG": dG, "TdS": T * dS,
        "E_rev": E_rev,
        "E_tn": E_tn,
        "E_std": -at_P["dG_std"] / nF,
        "nernst_shift": E_rev - (-at_P["dG_std"] / nF),
        "dE_dT": dS / nF,
        "mode": mode,
        "electrical_work": dG,
        "reversible_heat": T * dS,
        "efficiency": efficiency,
        "carnot_efficiency": carnot,
        "T_cold": T_cold,
        "notes": at_P["notes"],
    }


def electrochemistry_sweep(rxn, temperatures: Sequence[float], n_electrons: Optional[float] = None,
                           P: float = P0, model: str = "ideal", T_cold: float = T0) -> dict:
    keys = ("E_rev", "E_tn", "efficiency", "carnot_efficiency", "dG", "dH", "TdS")
    out = {"T": list(temperatures)}
    out.update({k: [] for k in keys})
    for T in temperatures:
        try:
            point = electrochemistry(rxn, T, n_electrons, P, model, T_cold)
        except PhaseError:
            # a species has no vapour state at this temperature: leave a gap
            point = dict.fromkeys(keys)
        for k in keys:
            out[k].append(point[k])
    # Temperature at which the ideal fuel cell and the Carnot engine break even
    out["crossover_T"] = None
    eff, car, Ts = out["efficiency"], out["carnot_efficiency"], out["T"]
    for i in range(1, len(Ts)):
        if None in (eff[i - 1], eff[i], car[i - 1], car[i]):
            continue
        d0 = eff[i - 1] - car[i - 1]
        d1 = eff[i] - car[i]
        if d0 > 0 >= d1:
            out["crossover_T"] = Ts[i - 1] + (Ts[i] - Ts[i - 1]) * d0 / (d0 - d1)
            break
    return out
