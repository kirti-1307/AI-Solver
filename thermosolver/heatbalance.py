"""Energy balance on a reactor: heat duty and adiabatic outlet temperature
(SVN Chapter 4, "Heat effects of industrial reactions").

The question: a feed enters a reactor at T_in, reacts to a stated extent and
leaves at T_out. How much heat Q has to be added or removed? Or, when Q is
fixed (Q = 0 for an adiabatic reactor), what is T_out? The adiabatic case with
complete combustion is the "theoretical flame temperature" of SVN.

Basis: one mole of the key reactant fed. With no shaft work and negligible
kinetic and potential energy changes, the steady-flow energy balance is

        Q = dH = H_out(T_out) - H_in(T_in)

Enthalpy is a state function, so dH is evaluated along the path SVN uses:

        feed at T_in      --dH_R-->   feed at 298.15 K
        feed at 298.15 K  --dH298-->  products at 298.15 K
        products at 298 K --dH_P-->   products at T_out

        dH_R  = sum n_in,i  * integral from T_in to T0  of Cp_i dT
        dH298 = sum_j xi_j * dH0_298,j         (xi_j = extent of reaction j)
        dH_P  = sum n_out,i * integral from T0 to T_out of Cp_i dT
        Q     = dH_R + dH298 + dH_P

The same Q is H_out - H_in with H_i(T) = dHf_i + integral from T0 to T of
Cp_i dT, because sum n_out dHf - sum n_in dHf = sum_j xi_j dH0_298,j. Both
routes are evaluated and compared in the audit.

Assumptions, the same as in the SVN examples: every species stays in the
phase that is written, the streams are ideal mixtures at low pressure, the
reactions go to the stated extents (no equilibrium limit, no dissociation),
and air is 21 mol-% O2 and 79 mol-% N2.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .constants import R, T0
from .errors import DataUnavailableError, InputError
from .heatcap import combine, cp_over_r, icph, icps, simpson
from .reaction import Reaction
from .species import SPECIES

AIR_O2_FRACTION = 0.21
AIR_N2_PER_O2 = 79.0 / 21.0      # mol N2 that come with each mol O2 in air
T_SEARCH_MIN = 200.0             # K, limits of the outlet-temperature search
T_SEARCH_MAX = 6000.0
MAX_EXCESS = 100.0               # 10,000 %
_TINY = 1e-12

# Products of complete combustion in oxygen
_COMBUSTION_PRODUCTS = {"CO2(g)", "H2O(g)", "H2O(l)", "SO2(g)", "N2(g)"}


# ---------------------------------------------------------------------------
# a stream: moles of each species, with its total enthalpy as one polynomial
# ---------------------------------------------------------------------------
class Stream:
    """A mixture {species id: moles}.

    The heat-capacity coefficients are additive, so the whole stream has one
    set (sum n_i A_i, sum n_i B_i, ...). Its enthalpy on the formation scale is

        H(T) = sum n_i dHf_i + R * integral from T0 to T of (sum n_i Cp_i / R) dT
    """

    def __init__(self, moles: Dict[str, float]):
        self.moles = {s: float(n) for s, n in moles.items() if n > _TINY}
        self.total = sum(self.moles.values())
        self.H298 = sum(n * SPECIES[s].dHf for s, n in self.moles.items())
        self.without_cp = [s for s in self.moles if SPECIES[s].cp is None]
        self.coeffs = combine((n, SPECIES[s].cp) for s, n in self.moles.items()
                              if SPECIES[s].cp is not None)
        self._window: Optional[Tuple[float, float]] = None

    def _need_cp(self) -> None:
        if self.without_cp:
            sid = self.without_cp[0]
            raise DataUnavailableError(
                f"SVN gives no heat-capacity correlation for {sid}, so a stream that contains it "
                f"can only be evaluated at {T0} K.", {"species": sid})

    def sensible(self, T1: float, T2: float) -> float:
        """sum n_i * integral of Cp_i dT from T1 to T2, in J."""
        if abs(T1 - T2) < 1e-12:
            return 0.0
        self._need_cp()
        return R * icph(T1, T2, self.coeffs)

    def H(self, T: float) -> float:
        """Enthalpy of the stream at T on the formation scale, in J."""
        return self.H298 + self.sensible(T0, T)

    def cp(self, T: float) -> float:
        """Total heat capacity sum n_i Cp_i at T, in J/K."""
        self._need_cp()
        return R * cp_over_r(self.coeffs, T)

    def entropy_change(self, T1: float, T2: float) -> float:
        """sum n_i * integral of Cp_i dT/T from T1 to T2 at constant pressure
        and composition, in J/K."""
        if abs(T1 - T2) < 1e-12:
            return 0.0
        self._need_cp()
        return R * icps(T1, T2, self.coeffs)

    def window(self) -> Tuple[float, float]:
        """Temperature interval around 298.15 K in which the total heat
        capacity is positive, so that H(T) rises with T and the energy balance
        has one solution. A polynomial Cp can turn negative far outside the
        range it was fitted to; the outlet-temperature search never goes there."""
        if self._window is None:
            step = 50.0
            lo = hi = T0
            while lo - step >= T_SEARCH_MIN and self.cp(lo - step) > 0.0:
                lo -= step
            while hi + step <= T_SEARCH_MAX and self.cp(hi + step) > 0.0:
                hi += step
            self._window = (lo, hi)
        return self._window


# ---------------------------------------------------------------------------
# feed and outlet from the reaction, conversion, excess and air
# ---------------------------------------------------------------------------
def default_key(rxn: Reaction) -> str:
    """The reactant taken as the basis: the first one that is not oxygen."""
    reactants = rxn.reactant_ids
    for sid in reactants:
        if sid != "O2(g)":
            return sid
    return reactants[0]


def default_excess_species(rxn: Reaction, key: str) -> Optional[str]:
    """The reactant that is normally fed in excess: oxygen, else the next reactant."""
    others = [s for s in rxn.reactant_ids if s != key]
    if "O2(g)" in others:
        return "O2(g)"
    return others[0] if others else None


def build_case(rxn: Reaction, key: Optional[str] = None, conversion: float = 1.0,
               excess_species: Optional[str] = None, excess: float = 0.0, air: bool = False,
               extra: Optional[Dict[str, float]] = None,
               side: Sequence[Tuple[Reaction, float]] = ()) -> dict:
    """Feed and outlet, in mol per mol of key reactant fed.

    conversion      fraction of the key reactant consumed by the main reaction
    excess_species  reactant fed above its stoichiometric amount
    excess          how much above, as a fraction (0.2 = 20 % excess)
    air             if true, 79/21 mol N2 accompany every mol O2 in the feed
    extra           other species fed, {id: mol per mol key}: inerts, steam ...
    side            further reactions, each with its extent in mol per mol key
    """
    reactants = rxn.reactant_ids
    key = key or default_key(rxn)
    if key not in reactants:
        raise InputError(f"{key} is not a reactant of {rxn.equation}.")
    if not 0.0 <= conversion <= 1.0:
        raise InputError("The conversion must be between 0 and 100 %.")
    nu_key = -rxn.stoich[key]

    feed: Dict[str, float] = {s: -rxn.stoich[s] / nu_key for s in reactants}
    notes: List[str] = []
    if excess_species is None:
        excess_species = default_excess_species(rxn, key)
    if excess and excess_species is None:
        raise InputError("This reaction has a single reactant, so nothing can be fed in excess.")
    if excess_species is not None:
        if excess_species not in reactants:
            raise InputError(f"{excess_species} is not a reactant of {rxn.equation}.")
        if excess_species == key:
            raise InputError(f"{key} is the basis of the calculation. Put the excess on another reactant.")
        if not -1.0 < excess <= MAX_EXCESS:
            raise InputError(f"The excess must be above -100 % and at most {100 * MAX_EXCESS:,.0f} %.")
        feed[excess_species] *= 1.0 + excess

    if air and feed.get("O2(g)", 0.0) > 0.0:
        feed["N2(g)"] = feed.get("N2(g)", 0.0) + AIR_N2_PER_O2 * feed["O2(g)"]
        notes.append(f"Air is taken as 21 mol-% O2 and 79 mol-% N2: {AIR_N2_PER_O2:.3f} mol N2 "
                     f"enter with every mol O2.")
    for sid, n in (extra or {}).items():
        if n < 0.0:
            raise InputError(f"The amount of {sid} in the feed cannot be negative.")
        if n > 0.0:
            feed[sid] = feed.get(sid, 0.0) + n

    reactions: List[Tuple[Reaction, float]] = [(rxn, conversion / nu_key)]
    for other, extent in side:
        if extent < 0.0:
            raise InputError("The extent of a side reaction cannot be negative. Write the reaction the other way round.")
        reactions.append((other, extent))

    outlet = dict(feed)
    for r, xi in reactions:
        for sid, nu in r.stoich.items():
            outlet[sid] = outlet.get(sid, 0.0) + nu * xi
    scale = max(1.0, sum(feed.values()))
    for sid, n in outlet.items():
        if n < -1e-9 * scale:
            raise InputError(
                f"With these settings {sid} would end at {n:.4g} mol: the feed does not contain enough of it. "
                f"Lower the conversion or the extent of the side reaction, or feed more {sid}.")
        if n < 0.0:
            outlet[sid] = 0.0
    return {"key": key, "excess_species": excess_species, "feed": feed, "outlet": outlet,
            "reactions": reactions, "notes": notes}


# ---------------------------------------------------------------------------
# the energy balance
# ---------------------------------------------------------------------------
def outlet_temperature(feed: Stream, outlet: Stream, T_in: float, Q: float = 0.0) -> float:
    """T_out from H_out(T_out) = H_in(T_in) + Q, by Newton's method kept inside
    a bracket (the enthalpy rises with T inside the stream's window)."""
    target = feed.H(T_in) + Q
    lo, hi = outlet.window()
    if outlet.H(lo) - target > 0.0:
        raise InputError(
            f"The energy balance puts the outlet below {lo:.0f} K, where the heat-capacity "
            f"correlations no longer apply. Remove less heat, convert less or preheat the feed.")
    if outlet.H(hi) - target < 0.0:
        raise InputError(
            f"The energy balance has no solution below {hi:.0f} K. Complete reaction of this feed would be "
            f"hotter than the heat-capacity correlations can describe (real products dissociate long before). "
            f"Add excess air or an inert, lower the conversion or remove heat.")
    T = T0
    for _ in range(200):
        f = outlet.H(T) - target
        if f > 0.0:
            hi = T
        else:
            lo = T
        if hi - lo < 1e-10:
            break
        T_new = T - f / outlet.cp(T)
        if not lo < T_new < hi:
            T_new = 0.5 * (lo + hi)
        if abs(T_new - T) < 1e-10:
            T = T_new
            break
        T = T_new
    return T


def solve(case: dict, T_in: float, mode: str = "adiabatic", T_out: Optional[float] = None,
          Q: float = 0.0) -> dict:
    """One energy balance.

    mode "adiabatic": Q is given (0 for an adiabatic reactor), T_out is found.
    mode "duty":      T_out is given, the heat duty Q is found.
    All extensive results are per mole of key reactant fed.
    """
    feed, outlet = Stream(case["feed"]), Stream(case["outlet"])
    if mode == "adiabatic":
        T_out = outlet_temperature(feed, outlet, T_in, Q)
    elif mode == "duty":
        if T_out is None:
            raise InputError("Give the outlet temperature.")
        Q = outlet.H(T_out) - feed.H(T_in)
    else:
        raise InputError("The mode must be 'adiabatic' or 'duty'.")

    dH_R = feed.sensible(T_in, T0)
    dH_298 = sum(xi * rxn.dH0 for rxn, xi in case["reactions"])
    dH_P = outlet.sensible(T0, T_out)
    mean_cp = dH_P / (T_out - T0) if abs(T_out - T0) > 1e-9 else outlet.cp(T0)

    rows = []
    for sid in list(case["feed"]) + [s for s in case["outlet"] if s not in case["feed"]]:
        sp = SPECIES[sid]
        n_in = case["feed"].get(sid, 0.0)
        n_out = case["outlet"].get(sid, 0.0)
        rows.append({
            "id": sid, "name": sp.name, "n_in": n_in, "n_out": n_out,
            "y_out": n_out / outlet.total if outlet.total > 0 else None,
            "sensible_in": n_in * sp.sensible_dH(T_in, T0) if n_in > _TINY else 0.0,
            "sensible_out": n_out * sp.sensible_dH(T0, T_out) if n_out > _TINY else 0.0,
            "cp_Tmin": sp.cp_Tmin, "cp_Tmax": sp.cp_Tmax,
        })

    reacting = {sid for rxn, _ in case["reactions"] for sid in rxn.stoich}
    key = SPECIES[case["key"]]
    return {
        "mode": mode, "key": case["key"], "T_in": T_in, "T_out": T_out, "Q": Q,
        # fed species that take part in no reaction: they only carry sensible heat
        "inert": [s for s, n in case["feed"].items() if n > _TINY and s not in reacting],
        "Q_per_kg": Q / (key.molar_mass / 1000.0),
        "feed": dict(case["feed"]), "outlet": dict(case["outlet"]),
        "feed_total": feed.total, "outlet_total": outlet.total,
        "path": {"dH_R": dH_R, "dH_298": dH_298, "dH_P": dH_P, "total": dH_R + dH_298 + dH_P},
        "H_in": feed.H(T_in), "H_out": outlet.H(T_out),
        "mean_cp_products": mean_cp,
        "cp_feed_T_in": feed.cp(T_in), "cp_products_T_out": outlet.cp(T_out),
        "sum_coeffs_products": list(outlet.coeffs),
        "species": rows,
        "reactions": [{"equation": rxn.equation, "extent": xi, "dH0": rxn.dH0, "heat": xi * rxn.dH0}
                      for rxn, xi in case["reactions"]],
        "warnings": range_warnings(case, T_in, T_out),
        "audit": audit(case, T_in, T_out, Q),
    }


def range_warnings(case: dict, T_in: float, T_out: float) -> List[dict]:
    """Species used outside the temperature range of their Cp correlation."""
    out: List[dict] = []
    seen = set()
    for moles, T, where in ((case["feed"], T_in, "feed"), (case["outlet"], T_out, "outlet")):
        for sid, n in moles.items():
            sp = SPECIES[sid]
            if n <= _TINY or sp.cp is None or sp.in_cp_range(T) or (sid, round(T, 6)) in seen:
                continue
            seen.add((sid, round(T, 6)))
            text = (f"{sid}: the {where} temperature of {T:,.0f} K is outside the range of its heat-capacity "
                    f"correlation ({sp.cp_Tmin:g} to {sp.cp_Tmax:g} K); the correlation is extrapolated.")
            if sp.phase != "g" and T > sp.cp_Tmax:
                text += (f" A {'liquid' if sp.phase == 'l' else 'solid'} may not exist at this temperature; "
                         f"no phase change is applied.")
            out.append({"level": "warning", "kind": "cp_extrapolation", "species": sid, "message": text,
                        "where": where, "T": T, "cp_Tmin": sp.cp_Tmin, "cp_Tmax": sp.cp_Tmax,
                        "condensed": sp.phase != "g" and T > sp.cp_Tmax})
    return out


def audit(case: dict, T_in: float, T_out: float, Q: float) -> List[dict]:
    """Independent checks of one energy balance."""
    from .audit import _check

    feed, outlet = Stream(case["feed"]), Stream(case["outlet"])
    checks: List[dict] = []

    atoms_in: Dict[str, float] = {}
    atoms_out: Dict[str, float] = {}
    for moles, atoms in ((case["feed"], atoms_in), (case["outlet"], atoms_out)):
        for sid, n in moles.items():
            for el, k in SPECIES[sid].elements.items():
                atoms[el] = atoms.get(el, 0.0) + n * k
    worst = max((abs(atoms_in.get(el, 0.0) - atoms_out.get(el, 0.0))
                 for el in set(atoms_in) | set(atoms_out)), default=0.0)
    checks.append(_check("Atoms are conserved", "atoms in the feed = atoms in the outlet, every element",
                         worst, 0.0, 0.0, 1e-8 * max(1.0, feed.total)))

    # Route 1: the three-step path of SVN. Route 2: species by species on the formation scale.
    path = (feed.sensible(T_in, T0) + sum(xi * rxn.dH0 for rxn, xi in case["reactions"])
            + outlet.sensible(T0, T_out))
    h_out = [n * SPECIES[s].H(T_out) for s, n in case["outlet"].items() if n > _TINY]
    h_in = [n * SPECIES[s].H(T_in) for s, n in case["feed"].items() if n > _TINY]
    direct = sum(h_out) - sum(h_in)
    # The heat duty is a small difference of large enthalpies when the streams
    # are large (for example a great excess of inert), so the round-off that
    # can be expected scales with the terms that are added, not with their sum.
    slack = 1e-11 * (sum(abs(h) for h in h_out) + sum(abs(h) for h in h_in))
    checks.append(_check("Two routes to the heat duty",
                         "dH_R + dH298 + dH_P = sum n_out H_i(T_out) - sum n_in H_i(T_in)",
                         path, direct, 1e-10, 1e-6 + slack))
    # ... plus, for a solved outlet temperature, the tolerance of the root (1e-9 K)
    checks.append(_check("Energy balance closes", "H_out(T_out) - H_in(T_in) = Q",
                         direct, Q, 1e-9, 1e-5 + 10.0 * slack + 1e-9 * abs(outlet.cp(T_out))))

    # Near absolute zero the D/T^2 term makes the integrand too steep for a
    # fixed-step quadrature, so the numerical cross-check stops at 50 K.
    if abs(T_out - T0) > 1e-9 and T_out >= 50.0:
        numeric = R * simpson(lambda t: cp_over_r(outlet.coeffs, t), T0, T_out)
        checks.append(_check("Sensible heat of the products",
                             "analytical integral of sum n_i Cp_i dT = Simpson quadrature",
                             outlet.sensible(T0, T_out), numeric, 1e-8, 1e-6))
    return checks


def work_potential(case: dict, T_out: float, T_surroundings: float = T0) -> Optional[dict]:
    """Ideal work of cooling the outlet stream to the temperature of the
    surroundings at constant pressure and composition (SVN Chapter 5):

        W_ideal = dH - T_sigma * dS

    with dH and dS of the stream between T_out and T_sigma. It is negative
    when the stream can deliver work. If the heat is simply discarded to the
    surroundings, all of it is lost work. For comparison, a Carnot engine that
    received the same heat at the constant temperature T_out would convert the
    fraction 1 - T_sigma/T_out.
    """
    if T_out <= T_surroundings + 1e-6:
        return None
    outlet = Stream(case["outlet"])
    dH = outlet.sensible(T_out, T_surroundings)
    dS = outlet.entropy_change(T_out, T_surroundings)
    W = dH - T_surroundings * dS
    return {"T_surroundings": T_surroundings, "dH": dH, "dS": dS, "W_ideal": W,
            "fraction": W / dH if dH else None,
            "carnot_at_T_out": 1.0 - T_surroundings / T_out}


# ---------------------------------------------------------------------------
# sweeps and goal seeking
# ---------------------------------------------------------------------------
def excess_for_outlet_temperature(rxn: Reaction, target_T: float, T_in: float, **settings) -> dict:
    """Excess of the chosen reactant at which the adiabatic outlet reaches
    ``target_T`` (bisection: more excess means a cooler outlet)."""
    settings = dict(settings)
    settings.pop("excess", None)
    Q = settings.pop("Q", 0.0)

    def T_out(excess: float) -> float:
        return solve(build_case(rxn, excess=excess, **settings), T_in, "adiabatic", Q=Q)["T_out"]

    try:
        hot = T_out(0.0)
    except InputError:
        hot = float("inf")
    if hot <= target_T:
        return {"target_T": target_T, "excess": None,
                "reason": f"Even with no excess the outlet is at {hot:,.0f} K, already at or below the target."}
    lo, hi = 0.0, MAX_EXCESS
    try:
        cold = T_out(hi)
    except InputError:
        cold = float("-inf")
    if cold > target_T:
        return {"target_T": target_T, "excess": None,
                "reason": "The target cannot be reached by adding excess reactant (the feed is hotter than the target)."}
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        try:
            value = T_out(mid)
        except InputError:
            value = float("inf")
        if value > target_T:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-9:
            break
    return {"target_T": target_T, "excess": 0.5 * (lo + hi), "reason": None}


# ---------------------------------------------------------------------------
# fuel facts for a combustion reaction
# ---------------------------------------------------------------------------
def fuel_facts(rxn: Reaction, key: Optional[str] = None) -> Optional[dict]:
    """Heating values and air demand, if ``rxn`` is the complete combustion of
    one fuel in oxygen. Returns None for any other reaction.

    Lower heating value: water leaves as vapour.  Higher heating value: water
    leaves as liquid.  Both at 298.15 K, per mole and per kilogram of fuel.
    A bomb calorimeter works at constant volume and so measures
    dU = dH - dn_gas * R * T, with water as liquid.
    """
    reactants = rxn.reactant_ids
    if "O2(g)" not in reactants or len(reactants) != 2:
        return None
    fuel_id = next(s for s in reactants if s != "O2(g)")
    if key is not None and key != fuel_id:
        return None
    if not set(rxn.product_ids) <= _COMBUSTION_PRODUCTS:
        return None
    fuel = SPECIES[fuel_id]
    nu_fuel = -rxn.stoich[fuel_id]
    per_fuel = {s: nu / nu_fuel for s, nu in rxn.stoich.items()}

    def with_water(phase: str) -> Reaction:
        stoich: Dict[str, float] = {}
        for sid, nu in per_fuel.items():
            target = f"H2O({phase})" if sid in ("H2O(g)", "H2O(l)") else sid
            stoich[target] = stoich.get(target, 0.0) + nu
        return Reaction(stoich)

    vapour, liquid = with_water("g"), with_water("l")
    o2 = -per_fuel["O2(g)"]
    co2 = per_fuel.get("CO2(g)", 0.0)
    M = fuel.molar_mass
    lhv, hhv = -vapour.dH0, -liquid.dH0
    dn_gas = liquid.delta_n_gas
    air_mass = o2 * SPECIES["O2(g)"].molar_mass + o2 * AIR_N2_PER_O2 * SPECIES["N2(g)"].molar_mass
    return {
        "fuel": fuel_id, "name": fuel.name, "molar_mass": M,
        "equation_lhv": vapour.equation, "equation_hhv": liquid.equation,
        "LHV": lhv, "HHV": hhv,                                   # J per mol of fuel
        "LHV_mass": lhv / M / 1000.0, "HHV_mass": hhv / M / 1000.0,   # MJ per kg of fuel
        "water_formed": per_fuel.get("H2O(g)", 0.0) + per_fuel.get("H2O(l)", 0.0),
        "o2_stoich": o2, "air_stoich": o2 / AIR_O2_FRACTION,     # mol per mol of fuel
        "air_fuel_mass": air_mass / M,                           # kg of air per kg of fuel
        "co2_per_mol": co2,
        "co2_per_MJ": co2 * SPECIES["CO2(g)"].molar_mass / (lhv / 1e6) if lhv > 0 else None,  # g CO2 per MJ (LHV)
        "dn_gas_bomb": dn_gas,
        "dU_bomb": liquid.dH0 - dn_gas * R * T0,                 # J per mol of fuel, constant volume
    }


# ---------------------------------------------------------------------------
# bomb calorimeter (constant-volume combustion)
# ---------------------------------------------------------------------------
JOULE_PER_CAL = 4.184            # thermochemical calorie, as in the course lab handout
_FUEL_ELEMENTS = {"C", "H", "O", "N", "S"}


def combustion_reaction(fuel_id: str, water: str = "l") -> Reaction:
    """Complete combustion of one mole of a fuel made of C, H, O, N and S:

        CxHyOzNwSv + (x + y/4 + v - z/2) O2 -> x CO2 + y/2 H2O + w/2 N2 + v SO2

    ``water`` is "l" (higher heating value) or "g" (lower heating value).
    """
    if fuel_id not in SPECIES:
        raise InputError(f"{fuel_id} is not in the database.")
    elements = SPECIES[fuel_id].elements
    if set(elements) - _FUEL_ELEMENTS:
        raise InputError(f"{fuel_id} contains elements other than C, H, O, N and S, so its "
                         f"combustion products are not defined here.")
    x, y, z = elements.get("C", 0), elements.get("H", 0), elements.get("O", 0)
    w, v = elements.get("N", 0), elements.get("S", 0)
    oxygen = x + y / 4.0 + v - z / 2.0
    if oxygen <= 1e-12 or fuel_id == "O2(g)":
        raise InputError(f"{fuel_id} cannot be burned: it needs no oxygen to reach CO2, H2O, N2 and SO2.")
    stoich: Dict[str, float] = {fuel_id: -1.0, "O2(g)": -oxygen}
    for sid, amount in (("CO2(g)", float(x)), (f"H2O({water})", y / 2.0),
                        ("N2(g)", w / 2.0), ("SO2(g)", float(v))):
        if amount > 0.0:
            stoich[sid] = stoich.get(sid, 0.0) + amount
    rxn = Reaction(stoich)
    rxn.assert_balanced()
    return rxn


def heating_values(fuel_id: str, T: float = T0) -> dict:
    """What a bomb calorimeter measures for one fuel, and what follows from it.

    The bomb is a closed, rigid vessel, so W = 0 and the heat released is the
    change of internal energy, with the water formed as liquid:

        dU_c = dH_c - dn_gas * R * T        (dn_gas counts gaseous species only)

    calorific value (bomb)   = -dU_c / M     per gram of fuel
    higher heating value     = -dH_c / M     water as liquid, constant pressure
    lower heating value      = -dH_c / M     water as vapour, constant pressure
    """
    sp = SPECIES[fuel_id]
    liquid = combustion_reaction(fuel_id, "l")
    vapour = combustion_reaction(fuel_id, "g")
    M = sp.molar_mass
    dn_gas = liquid.delta_n_gas
    dH = liquid.dH0
    dU = dH - dn_gas * R * T
    water = liquid.stoich.get("H2O(l)", 0.0)
    water_mass = water * SPECIES["H2O(l)"].molar_mass / M                 # g of water per g of fuel
    h_fg = (SPECIES["H2O(g)"].dHf - SPECIES["H2O(l)"].dHf) / SPECIES["H2O(l)"].molar_mass  # J/g at 298.15 K
    return {
        "fuel": fuel_id, "name": sp.name, "phase": sp.phase, "molar_mass": M, "T": T,
        "equation": liquid.equation, "equation_vapour": vapour.equation,
        "dn_gas": dn_gas, "dH_c": dH, "dU_c": dU, "dn_RT": dn_gas * R * T,
        "calorific_value": -dU / M,                    # J/g, constant volume, water liquid
        "HHV": -dH / M, "LHV": -vapour.dH0 / M,        # J/g, constant pressure
        "water_per_gram": water_mass, "h_fg_water": h_fg,
        # the shortcut of the lab handout: LHV = HHV - m_w * h_fg, starting from the bomb value
        "LHV_shortcut": -dU / M - water_mass * h_fg,
    }


def calorimeter_constant(mass_standard: float, dT: float, calorific_standard: float,
                         corrections: float = 0.0) -> float:
    """Heat capacity of the calorimeter from a calibration run, J/K:
    C_cal = (m * calorific value of the standard + ignition corrections) / dT."""
    if mass_standard <= 0.0 or dT <= 0.0 or calorific_standard <= 0.0:
        raise InputError("The calibration needs a positive mass, temperature rise and calorific value.")
    return (mass_standard * calorific_standard + corrections) / dT


def calorimeter_run(fuel_id: str, mass: float, C_cal: float, corrections: float = 0.0,
                    T: float = T0) -> dict:
    """Temperature rise when ``mass`` grams of a fuel burn in a bomb whose heat
    capacity is ``C_cal`` (J/K): dT = (m * calorific value + corrections) / C_cal."""
    if mass <= 0.0:
        raise InputError("The sample mass must be positive.")
    if C_cal <= 0.0:
        raise InputError("The calorimeter constant must be positive.")
    values = heating_values(fuel_id, T)
    heat = mass * values["calorific_value"] + corrections
    return {**values, "mass": mass, "C_cal": C_cal, "corrections": corrections,
            "moles": mass / values["molar_mass"], "heat_released": heat, "dT": heat / C_cal}


def combustible_species() -> List[str]:
    """Every species of the database that has a complete-combustion reaction."""
    out = []
    for sid in SPECIES:
        try:
            combustion_reaction(sid)
        except InputError:
            continue
        out.append(sid)
    return out


def identify_fuel(mass: float, dT: float, C_cal: float, corrections: float = 0.0,
                  T: float = T0, limit: int = 6, include_gases: bool = False) -> dict:
    """From a measured temperature rise: the calorific value of the sample and
    the fuels of the database that lie closest to it. A bomb sample is weighed
    into a crucible, so only liquids and solids are compared unless
    ``include_gases`` is set."""
    if mass <= 0.0 or dT <= 0.0 or C_cal <= 0.0:
        raise InputError("The sample mass, temperature rise and calorimeter constant must be positive.")
    measured = (C_cal * dT - corrections) / mass
    if measured <= 0.0:
        raise InputError("The ignition corrections are larger than the heat measured.")
    candidates = []
    for sid in combustible_species():
        if SPECIES[sid].phase == "g" and not include_gases:
            continue
        values = heating_values(sid, T)
        candidates.append({"fuel": sid, "name": values["name"], "phase": values["phase"],
                           "calorific_value": values["calorific_value"],
                           "difference": values["calorific_value"] / measured - 1.0})
    candidates.sort(key=lambda c: abs(c["difference"]))
    return {"mass": mass, "dT": dT, "C_cal": C_cal, "corrections": corrections,
            "measured_calorific_value": measured, "include_gases": include_gases,
            "compared": len(candidates), "candidates": candidates[:limit]}
