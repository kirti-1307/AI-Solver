"""Phase change at 1 bar, from the solver's own data.

Seven compounds are in the database both as a liquid and as a gas. For such a
compound the formation data and the heat capacities of the two forms already
fix where it boils, because of two results the course uses (SVN Ch. 6):

* At a given temperature and pressure the stable phase of a pure species is
  the one with the lower Gibbs energy.
* Where two phases are in equilibrium, their Gibbs energies are equal.

With the standard state of the liquid (pure liquid at 1 bar) and of the gas
(ideal gas at 1 bar), the vaporisation  X(l) -> X(g)  has

        dG_vap(T) = G_gas(T) - G_liquid(T) = dH_vap(T) - T * dS_vap(T)

and the boiling point at 1 bar is the temperature where dG_vap = 0. Below it
the liquid is stable, above it the vapour. At that temperature

        dS_vap = dH_vap / T_boil

so a heat of reaction that involves the species jumps by nu * dH_vap there
(the latent heat), the entropy change jumps by nu * dH_vap / T_boil, and the
Gibbs energy change does not jump at all.

The same dG_vap gives the vapour pressure of the liquid. The liquid at T is
in equilibrium with its vapour (taken as an ideal gas) at the pressure where
the Gibbs energy of the vapour, G_gas(T) + R T ln(P/P0), equals that of the
liquid:

        P_sat(T) = P0 * exp(-dG_vap(T) / (R T))

This is the Clausius/Clapeyron equation in integrated form, with the latent
heat allowed to change with temperature through the heat capacities. The
effect of pressure on the liquid itself is neglected, which is safe at the
low pressures where it is used.

Nothing here is new data: every number follows from SVN Tables C.1 to C.4
(and NIST for acetic acid). The boiling points that come out are compared
with the normal boiling points printed in SVN Table B.1. A compound whose two
values are more than BOILING_POINT_TOLERANCE apart is not switched
automatically, because its data do not describe the phase change well enough.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .constants import P0, R
from .reaction import Reaction
from .species import SPECIES

# Largest accepted difference between the boiling point that follows from the
# data and the one printed in SVN Table B.1, in K.
BOILING_POINT_TOLERANCE = 10.0
_SEARCH_MIN = 200.0          # K, limits of the search for the boiling point
_SEARCH_MAX = 800.0


@dataclass(frozen=True)
class Transition:
    """Boiling of one compound at 1 bar, as the database describes it."""

    compound: str
    liquid: str                      # species id of the liquid
    gas: str                         # species id of the gas
    T_boil: Optional[float]          # K, where G(liquid) = G(gas) at 1 bar
    T_boil_table: Optional[float]    # K, normal boiling point of SVN Table B.1
    dH_vap: Optional[float]          # J/mol, latent heat at T_boil
    dS_vap: Optional[float]          # J/(mol K), dH_vap / T_boil
    trusted: bool                    # used for the automatic choice of phase
    reason: Optional[str]            # why not, when it is not trusted

    @property
    def difference(self) -> Optional[float]:
        if self.T_boil is None or self.T_boil_table is None:
            return None
        return self.T_boil - self.T_boil_table

    def to_dict(self) -> dict:
        return {
            "compound": self.compound, "liquid": self.liquid, "gas": self.gas,
            "T_boil": self.T_boil, "T_boil_table": self.T_boil_table, "difference": self.difference,
            "dH_vap": self.dH_vap, "dS_vap": self.dS_vap,
            "trusted": self.trusted, "reason": self.reason,
            "liquid_cp_range": [SPECIES[self.liquid].cp_Tmin, SPECIES[self.liquid].cp_Tmax],
        }


def vaporisation(liquid: str, gas: str) -> Reaction:
    """The reaction X(l) -> X(g)."""
    return Reaction({liquid: -1.0, gas: 1.0})


def _boiling_point(vap: Reaction) -> Optional[float]:
    """Temperature where dG of vaporisation is zero, by bisection. dG_vap
    falls as T rises (dS_vap is positive), so there is one such temperature."""
    lo, hi = _SEARCH_MIN, _SEARCH_MAX
    if vap.dG(lo) <= 0.0 or vap.dG(hi) >= 0.0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if vap.dG(mid) > 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return 0.5 * (lo + hi)


def _build() -> Dict[str, Transition]:
    out: Dict[str, Transition] = {}
    gases = {sp.name: sid for sid, sp in SPECIES.items() if sp.phase == "g"}
    for sid, liquid in SPECIES.items():
        if liquid.phase != "l" or liquid.name not in gases:
            continue
        gas = SPECIES[gases[liquid.name]]
        table = next((sp.critical.Tn for sp in (liquid, gas) if sp.critical and sp.critical.Tn), None)
        T_boil = dH = dS = None
        reason = None
        if liquid.cp is None or gas.cp is None:
            reason = "the database has no heat capacity for one of its two phases"
        else:
            vap = vaporisation(liquid.id, gas.id)
            T_boil = _boiling_point(vap)
            if T_boil is None:
                reason = "its data give no boiling point between 200 and 800 K"
            else:
                dH = vap.dH(T_boil)
                dS = dH / T_boil
                if table is None:
                    reason = "SVN Table B.1 gives no boiling point to check its data against"
                elif abs(T_boil - table) > BOILING_POINT_TOLERANCE:
                    reason = (f"its data put the boiling point at {T_boil:.1f} K, which is "
                              f"{abs(T_boil - table):.0f} K away from the {table:g} K of SVN Table B.1")
        out[liquid.name] = Transition(liquid.name, liquid.id, gas.id, T_boil, table, dH, dS,
                                      reason is None, reason)
    return out


# Every compound that the database holds as a liquid and as a gas, by name.
TRANSITIONS: Dict[str, Transition] = _build()
_BY_SPECIES: Dict[str, Transition] = {sid: t for t in TRANSITIONS.values() for sid in (t.liquid, t.gas)}


def transition_of(sid: str) -> Optional[Transition]:
    """The boiling transition a species belongs to, if it has both phases."""
    return _BY_SPECIES.get(sid)


def stable_id(transition: Transition, T: float) -> str:
    """The species id of the phase that is stable at T and 1 bar."""
    return transition.liquid if T < transition.T_boil else transition.gas


# ---------------------------------------------------------------------------
# a reaction with every species in its stable phase
# ---------------------------------------------------------------------------
def choices(rxn: Reaction) -> Tuple[List[Transition], List[dict]]:
    """Which species of ``rxn`` can change phase automatically.

    Returns (used, skipped). A compound is skipped when its data do not
    describe the boiling point well enough, and when both of its phases are
    written in the reaction (then the reaction is about the phase change
    itself and is left as typed).
    """
    used: List[Transition] = []
    skipped: List[dict] = []
    seen = set()
    for sid in rxn.stoich:
        t = transition_of(sid)
        if t is None or t.compound in seen:
            continue
        seen.add(t.compound)
        if t.liquid in rxn.stoich and t.gas in rxn.stoich:
            skipped.append({**t.to_dict(), "why": "both_phases",
                            "message": (f"{t.liquid} and {t.gas} are both written in the reaction, "
                                        f"so the phases are left as typed.")})
        elif not t.trusted:
            skipped.append({**t.to_dict(), "why": "data",
                            "message": (f"{sid} is left in the phase that is typed: {t.reason}.")})
        else:
            used.append(t)
    return used, skipped


def at_temperature(rxn: Reaction, T: float, used: Optional[List[Transition]] = None) -> Tuple[Reaction, List[dict]]:
    """``rxn`` with every species that can change phase put into the phase
    that is stable at T and 1 bar. Returns the reaction and the list of swaps."""
    if used is None:
        used = choices(rxn)[0]
    targets = {}
    for t in used:
        typed = t.liquid if t.liquid in rxn.stoich else t.gas
        stable = stable_id(t, T)
        if stable != typed:
            targets[typed] = stable
    if not targets:
        return rxn, []
    stoich = {targets.get(sid, sid): nu for sid, nu in rxn.stoich.items()}
    swaps = [{"typed": a, "used": b, "compound": SPECIES[a].name,
              "T_boil": transition_of(a).T_boil} for a, b in targets.items()]
    return Reaction(stoich, rxn.name, list(rxn.notes)), swaps


def segments(rxn: Reaction, used: Optional[List[Transition]] = None) -> List[Tuple[float, float, Reaction]]:
    """The temperature axis cut at the boiling points of the species of
    ``rxn``: a list of (T_from, T_to, reaction in the phases stable there).
    The lower end belongs to the liquid side, T_to itself to the next piece."""
    if used is None:
        used = choices(rxn)[0]
    cuts = sorted({t.T_boil for t in used})
    edges = [0.0] + cuts + [math.inf]
    out = []
    for lo, hi in zip(edges, edges[1:]):
        probe = lo + 1.0 if math.isinf(hi) else 0.5 * (lo + hi)
        out.append((lo, hi, at_temperature(rxn, probe, used)[0]))
    return out


def jumps(rxn: Reaction, used: Optional[List[Transition]] = None) -> List[dict]:
    """What happens to the property changes of ``rxn`` at each boiling point:
    dH jumps by nu * dH_vap, dS by nu * dH_vap / T_boil, dG not at all."""
    if used is None:
        used = choices(rxn)[0]
    out = []
    for t in sorted(used, key=lambda x: x.T_boil):
        nu = rxn.stoich.get(t.liquid, 0.0) + rxn.stoich.get(t.gas, 0.0)
        out.append({**t.to_dict(), "nu": nu, "dH_jump": nu * t.dH_vap, "dS_jump": nu * t.dS_vap})
    return out


# ---------------------------------------------------------------------------
# vapour pressure and the split of water between vapour and liquid
# ---------------------------------------------------------------------------
_VAPORISATION: Dict[str, Reaction] = {}


def vapour_pressure(transition: Transition, T: float) -> float:
    """P_sat(T) = P0 * exp(-dG_vap(T)/(R T)), in bar."""
    vap = _VAPORISATION.get(transition.liquid)
    if vap is None:
        vap = _VAPORISATION[transition.liquid] = vaporisation(transition.liquid, transition.gas)
    x = -vap.dG(T) / (R * T)
    return P0 * math.exp(min(x, 700.0))


def latent_heat(transition: Transition, T: float) -> float:
    """dH_vap(T) = H_gas(T) - H_liquid(T), J/mol."""
    return SPECIES[transition.gas].H(T) - SPECIES[transition.liquid].H(T)


def vapour_moles(n_total: float, n_other_gas: float, P_sat: float, P: float = P0) -> float:
    """How much of ``n_total`` moles of a condensable species is vapour when
    it shares the gas phase with ``n_other_gas`` moles of gases that do not
    condense, at total pressure P.

    The vapour is at most saturated: its partial pressure y*P cannot exceed
    P_sat. With n_v moles of vapour, y = n_v / (n_v + n_other), so the gas
    can hold n_other * P_sat / (P - P_sat) moles. Anything above that is
    liquid. At or above the boiling point (P_sat >= P) everything is vapour.
    """
    if n_total <= 0.0:
        return 0.0
    if P_sat >= P:
        return n_total
    return min(n_total, n_other_gas * P_sat / (P - P_sat))


def dew_point(transition: Transition, y: float, P: float = P0) -> Optional[float]:
    """Temperature at which a gas with mole fraction ``y`` of the species
    starts to condense at total pressure P: P_sat(T_dew) = y * P."""
    if not 0.0 < y <= 1.0:
        return None
    target = y * P
    lo, hi = _SEARCH_MIN, _SEARCH_MAX
    if vapour_pressure(transition, lo) >= target or vapour_pressure(transition, hi) <= target:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if vapour_pressure(transition, mid) < target:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# equilibrium conversion when a species may condense
# ---------------------------------------------------------------------------
def equilibrium(rxn: Reaction, used: List[Transition], T: float, P: float = P0) -> dict:
    """Equilibrium of one reaction (stoichiometric feed, ideal-gas mixture)
    when some of its species can be liquid at T.

    The standard state of a species below its boiling point is the liquid,
    but in a gas mixture the species is not automatically a liquid: it stays
    a vapour as long as its partial pressure is below its vapour pressure.
    So the reaction is first solved with every such species as a vapour. A
    species whose partial pressure then comes out above its vapour pressure
    cannot stay in the gas: part of it is liquid. The liquid is a separate
    pure phase (activity 1, SVN's treatment of a pure condensed phase), and
    its vapour stays in the gas at exactly the vapour pressure. The other
    gases then share what is left of the total pressure, P - P_sat, and the
    reaction is solved again at that pressure with the species as a liquid.
    At the point where condensation starts the two calculations agree, so the
    conversion does not jump there. The loop ends when no further vapour is
    above saturation.

    A species can condense only while P_sat(T) < P and T is below its
    critical temperature. At 1 bar that means below the boiling point. At a
    higher pressure it reaches above the boiling point at 1 bar, where the
    data of the liquid are stretched beyond their range; such a result is
    marked "extrapolated".

    One simplification remains: two liquids are taken as separate pure
    phases, not as a solution.
    """
    from .equilibrium import reaction_equilibrium

    def critical_T(t: Transition) -> float:
        crit = SPECIES[t.gas].critical or SPECIES[t.liquid].critical
        return crit.Tc if crit else math.inf

    P_sat = {t.compound: vapour_pressure(t, T) for t in used}
    can_condense = [t for t in used if T < critical_T(t) and P_sat[t.compound] < P]
    liquid: List[Transition] = []
    result: dict = {}
    P_rest = P
    for _ in range(len(can_condense) + 1):
        target = {}
        for t in used:
            typed = t.liquid if t.liquid in rxn.stoich else t.gas
            target[typed] = t.liquid if t in liquid else t.gas
        variant = Reaction({target.get(sid, sid): nu for sid, nu in rxn.stoich.items()}, rxn.name)
        P_rest = P - sum(P_sat[t.compound] for t in liquid)       # what the other gases share
        result = reaction_equilibrium(variant, T, P_rest, model="ideal")
        wet = [t for t in can_condense if t not in liquid
               and result["y"].get(t.gas, 0.0) * P_rest > P_sat[t.compound] * (1.0 + 1e-9)]
        if not wet:
            break
        liquid += wet
    n_other = sum(n for sid, n in result["moles"].items() if SPECIES[sid].phase == "g")
    saturation = []
    for t in can_condense:
        psat = P_sat[t.compound]
        row = {"species": t.gas, "P_sat": psat, "condensed": t in liquid,
               "extrapolated": T > SPECIES[t.liquid].cp_Tmax + 1.0,
               "partial_pressure": psat if t in liquid else result["y"].get(t.gas, 0.0) * P_rest,
               "vapour_moles": None, "liquid_moles": None}
        if t in liquid:
            total = result["moles"].get(t.liquid, 0.0)
            vapour = min(total, n_other * psat / P_rest)
            row["vapour_moles"], row["liquid_moles"] = vapour, total - vapour
        saturation.append(row)
    result["P"] = P
    result["P_other_gases"] = P_rest
    result["condensed"] = [t.liquid for t in liquid]
    result["extrapolated"] = any(row["condensed"] and row["extrapolated"] for row in saturation)
    result["saturation"] = saturation
    return result


# ---------------------------------------------------------------------------
# independent checks
# ---------------------------------------------------------------------------
def audit(used: List[Transition]) -> List[dict]:
    """Checks on each boiling point that is used. They take other routes than
    the calculation itself: the Gibbs energies of the two phases species by
    species, the entropies, and the slope of the vapour-pressure curve."""
    from .audit import _check

    checks: List[dict] = []
    for t in used:
        liquid, gas, T = SPECIES[t.liquid], SPECIES[t.gas], t.T_boil
        checks.append(_check(f"{t.compound}: same Gibbs energy in both phases at {T:.2f} K",
                             "G of the liquid = G of the vapour at the boiling point",
                             liquid.G(T), gas.G(T), 1e-9, 1e-4))
        checks.append(_check(f"{t.compound}: entropy of vaporisation",
                             "S of the vapour - S of the liquid = dH_vap / T_boil",
                             gas.S(T) - liquid.S(T), t.dH_vap / T, 1e-9, 1e-8))
        h = 0.01
        slope = (math.log(vapour_pressure(t, T + h)) - math.log(vapour_pressure(t, T - h))) / (2 * h)
        checks.append(_check(f"{t.compound}: Clausius/Clapeyron equation",
                             "d(ln P_sat)/dT = dH_vap / (R T^2)",
                             slope, latent_heat(t, T) / (R * T * T), 1e-6, 1e-10))
    return checks
