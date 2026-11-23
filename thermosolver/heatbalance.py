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

One phase change can be switched on: the water of the outlet (class
WaterSplit). Below its dew point the outlet cannot carry all of its water as
vapour, and the part that condenses gives up its latent heat. The energy
balance then has a fourth step,

        Q = dH_R + dH298 + dH_P + dH_phase,   dH_phase = -n_liquid * dH_vap(T_out)

with dH_P taken for the products with all their water as vapour.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import math

from . import phase
from .constants import P0, R, T0
from .errors import DataUnavailableError, InputError
from .data import HIGH_T_MAX
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
        # Temperatures at which a species of the stream changes the source of
        # its heat capacity (298.15 K, and the end of the SVN range for the
        # gases that have NIST data above it).
        self.breakpoints = sorted({b for s in self.moles for b in SPECIES[s].breakpoints()})
        self._sets: Dict[int, Tuple[tuple, float, float]] = {}
        self._window: Optional[Tuple[float, float]] = None

    def _set(self, T: float) -> Tuple[tuple, float, float]:
        """(summed constants, enthalpy offset, entropy offset) that apply at T.
        Between two breakpoints they do not change, so they are kept."""
        key = sum(1 for b in self.breakpoints if T > b) if T >= T0 else -1
        if key not in self._sets:
            with_cp = [(n, SPECIES[s]) for s, n in self.moles.items() if SPECIES[s].cp is not None]
            coeffs = combine((n, sp.coeffs_at(T)) for n, sp in with_cp)
            off_H = sum(n * sp.offsets_at(T)[0] for n, sp in with_cp)
            off_S = sum(n * sp.offsets_at(T)[1] for n, sp in with_cp)
            self._sets[key] = (coeffs, off_H, off_S)
        return self._sets[key]

    def coeffs_at(self, T: float):
        """The summed constants that apply at T (see Species.coeffs_at)."""
        return self._set(T)[0]

    def _integral(self, integral, which: int, T1: float, T2: float) -> float:
        """An integral of the heat capacity from T1 to T2 (``which``: 0 for
        enthalpy, 1 for entropy). When the two temperatures use different sets
        of constants, each end is taken from 298.15 K with its own set and
        offset (see Species.offsets_at)."""
        s1, s2 = self._set(T1), self._set(T2)
        if s1 is s2:
            return integral(T1, T2, s1[0])
        return (integral(T0, T2, s2[0]) + s2[1 + which]) - (integral(T0, T1, s1[0]) + s1[1 + which])

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
        return R * self._integral(icph, 0, T1, T2)

    def H(self, T: float) -> float:
        """Enthalpy of the stream at T on the formation scale, in J."""
        return self.H298 + self.sensible(T0, T)

    def cp(self, T: float) -> float:
        """Total heat capacity sum n_i Cp_i at T, in J/K."""
        self._need_cp()
        return R * cp_over_r(self.coeffs_at(T), T)

    def entropy_change(self, T1: float, T2: float) -> float:
        """sum n_i * integral of Cp_i dT/T from T1 to T2 at constant pressure
        and composition, in J/K."""
        if abs(T1 - T2) < 1e-12:
            return 0.0
        self._need_cp()
        return R * self._integral(icps, 1, T1, T2)

    def window(self) -> Tuple[float, float]:
        """Temperature interval around 298.15 K in which the total heat
        capacity is positive, so that H(T) rises with T and the energy balance
        has one solution. A polynomial Cp can turn negative far outside the
        range it was fitted to; the outlet-temperature search never goes there."""
        if self._window is None:
            lo = hi = T0
            while lo > T_SEARCH_MIN:
                lower = max(T_SEARCH_MIN, lo - 25.0)
                if self.cp(lower) <= 0.0:
                    break
                lo = lower
            while hi < T_SEARCH_MAX:
                higher = min(T_SEARCH_MAX, hi + 50.0)
                if self.cp(higher) <= 0.0:
                    break
                hi = higher
            self._window = (lo, hi)
        return self._window

    def require(self, T: float, what: str) -> None:
        """Refuse a temperature outside the window. There the enthalpy of the
        stream does not rise with temperature, and an energy balance would
        return a second, meaningless root."""
        if abs(T - T0) < 1e-9:
            return
        lo, hi = self.window()
        if lo - 1e-9 <= T <= hi + 1e-9:
            return
        hint = " The solver works in kelvin: add 273.15 to degrees Celsius." if T < lo else ""
        raise InputError(
            f"The {what} temperature of {T:g} K is outside the range in which the heat capacities of this "
            f"stream can be used ({lo:.0f} to {hi:.0f} K).{hint}", {"limit": "below" if T < lo else "above"})


class SvnStream(Stream):
    """The same mixture with the main (SVN) heat-capacity formulas used at
    every temperature from 298.15 K upwards, extrapolated beyond their range.

    This is what SVN's own flame-temperature example does: it ends at 2066 K
    with formulas that are valid to 2000 K. The solver itself uses NIST data
    above the SVN range (class Stream); this class exists to reproduce the
    textbook number and to show how far the two answers are apart.
    """

    def __init__(self, moles: Dict[str, float]):
        super().__init__(moles)
        self.breakpoints = [T0] if any(SPECIES[s].cp_low is not None for s in self.moles) else []

    def _set(self, T: float) -> Tuple[tuple, float, float]:
        key = 0 if T >= T0 else -1
        if key not in self._sets:
            with_cp = [(n, SPECIES[s]) for s, n in self.moles.items() if SPECIES[s].cp is not None]
            coeffs = combine((n, sp.cp if (T >= T0 or sp.cp_low is None) else sp.cp_low) for n, sp in with_cp)
            self._sets[key] = (coeffs, 0.0, 0.0)
        return self._sets[key]


class WaterSplit:
    """The outlet with its water divided between vapour and liquid.

    A gas can carry water vapour only up to its vapour pressure: the partial
    pressure y_w * P cannot exceed P_sat(T). With n_w moles of water and
    n_other moles of other gases at the total pressure P (1 bar), the gas
    holds at most n_other * P_sat / (P - P_sat) moles of vapour. The rest is
    liquid. The temperature at which the first drop forms is the dew point,
    where P_sat(T_dew) = y_w * P with all the water as vapour.

    P_sat comes from the solver's own data for liquid water and steam (module
    ``phase``). The liquid is taken as pure water, and the other gases do not
    dissolve in it.

    The enthalpy of the outlet at T is that of the same stream with all its
    water as vapour, minus the latent heat of the part that is liquid:

        H(T) = H_all_vapour(T) - n_liquid(T) * dH_vap(T)
    """

    def __init__(self, moles: Dict[str, float], P: float = P0):
        self.water = phase.TRANSITIONS["Water"]
        gas, liquid = self.water.gas, self.water.liquid
        written = {s: float(n) for s, n in moles.items() if n > _TINY}
        self.P = P
        self.n_written_liquid = written.get(liquid, 0.0)
        self.n_water = written.get(gas, 0.0) + self.n_written_liquid
        self.dry = {s: n for s, n in written.items() if s not in (gas, liquid)}
        self.n_other_gas = sum(n for s, n in self.dry.items() if SPECIES[s].phase == "g")
        self.all_vapour = Stream({**self.dry, gas: self.n_water})
        self.total = self.all_vapour.total
        # mole fraction of water in the gas if none of it were liquid
        self.y_all_vapour = self.n_water / (self.n_water + self.n_other_gas)
        self.T_dew = phase.dew_point(self.water, self.y_all_vapour, P)

    def vapour(self, T: float) -> float:
        """Moles of water that are vapour at T."""
        if T >= self.water.T_boil:
            # At or above the boiling point at 1 bar nothing is liquid. (The
            # data for liquid water end at 373.15 K and are not used beyond.)
            return self.n_water
        return phase.vapour_moles(self.n_water, self.n_other_gas, phase.vapour_pressure(self.water, T), self.P)

    def moles_at(self, n_vapour: float) -> Dict[str, float]:
        """The outlet as {species: moles} with the given amount of water vapour."""
        out = dict(self.dry)
        if n_vapour > _TINY:
            out[self.water.gas] = n_vapour
        if self.n_water - n_vapour > _TINY:
            out[self.water.liquid] = self.n_water - n_vapour
        return out

    def latent(self, T: float) -> float:
        """dH_vap of water at T, J/mol."""
        return phase.latent_heat(self.water, T)

    def H(self, T: float, n_vapour: Optional[float] = None) -> float:
        """Enthalpy of the outlet at T on the formation scale, in J."""
        n_vapour = self.vapour(T) if n_vapour is None else n_vapour
        n_liquid = self.n_water - n_vapour
        H = self.all_vapour.H(T)
        if n_liquid > _TINY:
            H -= n_liquid * self.latent(T)
        return H

    def S(self, T: float, n_vapour: Optional[float] = None) -> float:
        """Entropy of the outlet at T and 1 bar on the formation scale, in J/K:
        every gas as part of an ideal-gas mixture (S_i - R ln y_i), the liquid
        water and any other condensed species as pure phases."""
        n_vapour = self.vapour(T) if n_vapour is None else n_vapour
        moles = self.moles_at(n_vapour)
        n_gas = sum(n for s, n in moles.items() if SPECIES[s].phase == "g")
        total = 0.0
        for sid, n in moles.items():
            sp = SPECIES[sid]
            total += n * sp.S(T)
            if sp.phase == "g":
                total -= n * R * math.log(n / n_gas * self.P / P0)
        return total

    def window(self) -> Tuple[float, float]:
        return self.all_vapour.window()

    def require(self, T: float, what: str) -> None:
        self.all_vapour.require(T, what)


def has_water(moles: Dict[str, float]) -> bool:
    """True when a stream contains water, as vapour or as liquid."""
    water = phase.TRANSITIONS["Water"]
    return moles.get(water.gas, 0.0) + moles.get(water.liquid, 0.0) > _TINY


def outlet_model(case: dict, condense: bool = False):
    """The object that gives the enthalpy of the outlet at any temperature:
    a WaterSplit when the water may change phase, a plain Stream otherwise."""
    if condense and has_water(case["outlet"]):
        return WaterSplit(case["outlet"])
    return Stream(case["outlet"])


# Above this temperature the products of a flame dissociate noticeably, which
# the energy balance does not include.
T_DISSOCIATION = 2000.0
T_DISSOCIATION_STRONG = 2500.0


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
        nitrogen = AIR_N2_PER_O2 * feed["O2(g)"]
        if key == "N2(g)":
            raise InputError("With air as the oxygen source the nitrogen enters with the oxygen (79 to 21), "
                             "so N2 cannot be the basis of the calculation. Choose O2 as the basis, or untick air.")
        if "N2(g)" in reactants:
            # nitrogen is itself a reactant: the air is its only source
            feed["N2(g)"] = nitrogen
            notes.append(f"Air is taken as 21 mol-% O2 and 79 mol-% N2. The nitrogen that reacts is the nitrogen "
                         f"of the air: {AIR_N2_PER_O2:.3f} mol N2 enter with every mol O2.")
        else:
            feed["N2(g)"] = feed.get("N2(g)", 0.0) + nitrogen
            notes.append(f"Air is taken as 21 mol-% O2 and 79 mol-% N2: {AIR_N2_PER_O2:.3f} mol N2 "
                         f"enter with every mol O2.")
    for sid, n in (extra or {}).items():
        if n < 0.0:
            raise InputError(f"The amount of {sid} in the feed cannot be negative.")
        if n > 0.0 and sid == key:
            raise InputError(f"{key} is the basis of the calculation, so its feed is fixed at 1 mol. "
                             f"Give the extra feed for another species.")
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
            f"correlations no longer apply. Remove less heat, convert less or preheat the feed.",
            {"limit": "below"})
    if outlet.H(hi) - target < 0.0:
        raise InputError(
            f"The energy balance has no solution below {hi:.0f} K. Complete reaction of this feed would be "
            f"hotter than the heat-capacity correlations can describe (real products break apart long before). "
            f"Add excess air or an inert, lower the conversion or remove heat.", {"limit": "above"})
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


def outlet_temperature_split(feed: Stream, split: WaterSplit, T_in: float, Q: float = 0.0) -> Tuple[float, float]:
    """T_out and the moles of water vapour from H_out(T_out) = H_in(T_in) + Q
    when the water of the outlet may condense.

    The enthalpy still rises with temperature (evaporating water takes up
    heat), so the root is found by bisection. If the outlet holds no other
    gas, the water boils at one temperature and the enthalpy jumps there; a
    target inside the jump means the outlet is at the boiling point, partly
    liquid, and the split follows from the energy balance (lever rule).
    """
    target = feed.H(T_in) + Q
    lo, hi = split.window()
    if split.H(lo) - target > 0.0:
        raise InputError(
            f"The energy balance puts the outlet below {lo:.0f} K, where the heat-capacity "
            f"correlations no longer apply. Remove less heat, convert less or preheat the feed.",
            {"limit": "below"})
    if split.H(hi) - target < 0.0:
        raise InputError(
            f"The energy balance has no solution below {hi:.0f} K. Complete reaction of this feed would be "
            f"hotter than the heat-capacity correlations can describe (real products break apart long before). "
            f"Add excess air or an inert, lower the conversion or remove heat.", {"limit": "above"})
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if split.H(mid) - target > 0.0:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-11:
            break
    T = 0.5 * (lo + hi)
    n_vapour = split.vapour(T)
    T_boil = split.water.T_boil
    if split.n_other_gas <= _TINY and abs(T - T_boil) < 1e-6:
        H_vapour = split.H(T_boil, split.n_water)
        H_liquid = split.H(T_boil, 0.0)
        if H_vapour > H_liquid:
            fraction = min(1.0, max(0.0, (target - H_liquid) / (H_vapour - H_liquid)))
            T, n_vapour = T_boil, fraction * split.n_water
    return T, n_vapour


def solve(case: dict, T_in: float, mode: str = "adiabatic", T_out: Optional[float] = None,
          Q: float = 0.0, condense: bool = False) -> dict:
    """One energy balance.

    mode "adiabatic": Q is given (0 for an adiabatic reactor), T_out is found.
    mode "duty":      T_out is given, the heat duty Q is found.
    condense:         the water of the outlet takes the phase that T_out gives
                      it (class WaterSplit) instead of the phase that is written.
    All extensive results are per mole of key reactant fed.
    """
    feed, outlet = Stream(case["feed"]), Stream(case["outlet"])
    if mode not in ("adiabatic", "duty"):
        raise InputError("The mode must be 'adiabatic' or 'duty'.")
    feed.require(T_in, "inlet")
    split = WaterSplit(case["outlet"]) if has_water(case["outlet"]) else None
    use_split = condense and split is not None
    if mode == "duty":
        if T_out is None:
            raise InputError("Give the outlet temperature.")
        outlet.require(T_out, "outlet")
    if use_split:
        if mode == "adiabatic":
            T_out, n_vapour = outlet_temperature_split(feed, split, T_in, Q)
        else:
            n_vapour = split.vapour(T_out)
            Q = split.H(T_out, n_vapour) - feed.H(T_in)
        n_liquid = split.n_water - n_vapour
        out_moles = split.moles_at(n_vapour)
        # The path is walked with all the water as vapour; the phase change
        # comes last, at the outlet temperature. Water that the reaction is
        # written with as liquid is evaporated at 298.15 K, inside step 2.
        products = split.all_vapour
        dH_298 = (sum(xi * rxn.dH0 for rxn, xi in case["reactions"])
                  + split.n_written_liquid * split.latent(T0))
        dH_phase = -n_liquid * split.latent(T_out) if n_liquid > _TINY else 0.0
        H_out = split.H(T_out, n_vapour)
    else:
        if mode == "adiabatic":
            T_out = outlet_temperature(feed, outlet, T_in, Q)
        else:
            Q = outlet.H(T_out) - feed.H(T_in)
        out_moles = dict(case["outlet"])
        products = outlet
        dH_298 = sum(xi * rxn.dH0 for rxn, xi in case["reactions"])
        dH_phase = 0.0
        H_out = outlet.H(T_out)
    case_out = {**case, "outlet": out_moles}

    dH_R = feed.sensible(T_in, T0)
    dH_P = products.sensible(T0, T_out)
    mean_cp = dH_P / (T_out - T0) if abs(T_out - T0) > 1e-9 else products.cp(T0)

    n_gas_out = sum(n for s, n in out_moles.items() if SPECIES[s].phase == "g")
    rows = []
    for sid in list(case["feed"]) + [s for s in out_moles if s not in case["feed"]]:
        sp = SPECIES[sid]
        n_in = case["feed"].get(sid, 0.0)
        n_out = out_moles.get(sid, 0.0)
        if use_split:
            # mole fraction in the gas phase; the sensible heat follows the
            # path, in which all the water is heated as vapour
            y_out = (n_out / n_gas_out if n_gas_out > 0 else None) if sp.phase == "g" else None
            n_path = products.moles.get(sid, 0.0)
        else:
            y_out = n_out / outlet.total if outlet.total > 0 else None
            n_path = n_out
        rows.append({
            "id": sid, "name": sp.name, "n_in": n_in, "n_out": n_out,
            "y_out": y_out,
            "sensible_in": n_in * sp.sensible_dH(T_in, T0) if n_in > _TINY else 0.0,
            "sensible_out": n_path * sp.sensible_dH(T0, T_out) if n_path > _TINY else 0.0,
            "cp_Tmin": sp.cp_Tmin, "cp_Tmax": sp.cp_Tmax,
        })

    reacting = {sid for rxn, _ in case["reactions"] for sid in rxn.stoich}
    key = SPECIES[case["key"]]

    # Species whose heat capacity comes from the NIST equations because the
    # stream is hotter than the SVN range, and the answer the SVN formulas
    # alone would give if they were extrapolated (as the textbook example does).
    high = [sid for moles, T in ((case["feed"], T_in), (out_moles, T_out)) for sid, n in moles.items()
            if n > _TINY and SPECIES[sid].cp_high is not None and T > SPECIES[sid].cp_main_Tmax]
    high = sorted(set(high), key=high.index)
    svn_only = None
    if high:
        try:
            feed_svn, outlet_svn = SvnStream(case["feed"]), SvnStream(out_moles)
            if mode == "adiabatic":
                svn_only = {"T_out": outlet_temperature(feed_svn, outlet_svn, T_in, Q), "Q": Q}
            else:
                svn_only = {"T_out": T_out, "Q": outlet_svn.H(T_out) - feed_svn.H(T_in)}
        except InputError:
            svn_only = None

    water = water_report(case, split, use_split, mode, T_in, T_out, Q,
                         n_vapour if use_split else None, dH_phase)
    return {
        "mode": mode, "key": case["key"], "T_in": T_in, "T_out": T_out, "Q": Q,
        "high_T_species": high, "svn_only": svn_only,
        "notes": temperature_notes(high, svn_only, mode, T_in, T_out) + phase_notes(water, case_out, T_out),
        # fed species that take part in no reaction: they only carry sensible heat
        "inert": [s for s, n in case["feed"].items() if n > _TINY and s not in reacting],
        "Q_per_kg": Q / (key.molar_mass / 1000.0),
        "feed": dict(case["feed"]), "outlet": out_moles,
        "feed_total": feed.total, "outlet_total": outlet.total,
        "path": {"dH_R": dH_R, "dH_298": dH_298, "dH_P": dH_P, "dH_phase": dH_phase,
                 "total": dH_R + dH_298 + dH_P + dH_phase},
        "H_in": feed.H(T_in), "H_out": H_out,
        "mean_cp_products": mean_cp,
        "cp_feed_T_in": feed.cp(T_in), "cp_products_T_out": products.cp(T_out),
        "sum_coeffs_products": list(products.coeffs_at(T_out)),
        "species": rows,
        "water": water,
        "reactions": [{"equation": rxn.equation, "extent": xi, "dH0": rxn.dH0, "heat": xi * rxn.dH0}
                      for rxn, xi in case["reactions"]],
        "warnings": [w for w in range_warnings(case_out, T_in, T_out)
                     # liquid water at its boiling point (373.19 K from the data) is not an
                     # extrapolation worth a warning, although its Cp range is printed to 373.15 K
                     if not (use_split and w["where"] == "outlet" and w["species"] == split.water.liquid
                             and split.water.liquid in out_moles and 0.0 < T_out - w["cp_Tmax"] < 0.1)],
        "audit": audit(case, T_in, T_out, Q, split if use_split else None, n_vapour if use_split else None),
    }


def water_report(case: dict, split: Optional[WaterSplit], applied: bool, mode: str, T_in: float,
                 T_out: float, Q: float, n_vapour: Optional[float], dH_phase: float) -> Optional[dict]:
    """What the water of the outlet does: its dew point, how much is vapour
    and how much liquid, the heat of the phase change, and the answer that
    the phases as written would give. None when the outlet holds no water."""
    if split is None:
        return None
    water = split.water
    written_vapour = split.n_water - split.n_written_liquid
    possible = split.vapour(T_out)                    # what the temperature allows
    if n_vapour is None:
        n_vapour = written_vapour                     # not applied: as written
    below_boiling = T_out <= water.T_boil + 1e-9       # liquid water can exist at T_out
    out = {
        "applied": applied,
        "n_total": split.n_water, "n_vapour": n_vapour, "n_liquid": split.n_water - n_vapour,
        "n_written_liquid": split.n_written_liquid,
        "n_vapour_possible": possible,
        "n_other_gas": split.n_other_gas,
        "y_all_vapour": split.y_all_vapour,
        "T_dew": split.T_dew, "T_boil": water.T_boil, "P": split.P,
        "P_sat": phase.vapour_pressure(water, T_out) if below_boiling else None,
        "dH_vap": split.latent(T_out) if below_boiling else None,
        "dH_vap_298": split.latent(T0),
        "dH_phase": dH_phase,
        "as_written": None,
    }
    if applied:
        # the same balance with every species kept in the phase that is written
        try:
            feed, written = Stream(case["feed"]), Stream(case["outlet"])
            if mode == "adiabatic":
                out["as_written"] = {"T_out": outlet_temperature(feed, written, T_in, Q), "Q": Q}
            else:
                out["as_written"] = {"T_out": T_out, "Q": written.H(T_out) - feed.H(T_in)}
        except InputError:
            out["as_written"] = None
    return out


def _kelvin(T: float) -> str:
    """A temperature for a sentence: 313.15, 310, 309.98."""
    return f"{T:.2f}".rstrip("0").rstrip(".")


def phase_notes(water: Optional[dict], case: dict, T_out: float) -> List[dict]:
    """Plain-language notes about the phase of the water in the outlet, and
    about other vapours that would condense there."""
    notes: List[dict] = []
    if water is None:
        pass
    elif water["applied"]:
        T_dew, n_w = water["T_dew"], water["n_total"]
        n_l, n_v = water["n_liquid"], water["n_vapour"]
        if n_l > 1e-9:
            dew = (f"is below {T_dew:.1f} K ({T_dew - 273.15:.1f} °C), the temperature at which its water vapour "
                   f"becomes saturated" if water["n_other_gas"] > _TINY
                   else f"is at or below the boiling point of water ({water['T_boil']:.1f} K)")
            text = (f"The outlet {dew}, so it cannot carry all of its water as vapour: {n_l:.3g} of the {n_w:.3g} mol "
                    f"of water leave as liquid, and condensing gives up {-water['dH_phase'] / 1000.0:,.1f} kJ "
                    f"(latent heat {water['dH_vap'] / 1000.0:.2f} kJ/mol at {_kelvin(T_out)} K).")
            if n_v > 1e-9 and water["n_other_gas"] > _TINY:
                text += (f" The gas stays saturated and keeps {n_v:.3g} mol of water vapour "
                         f"(vapour pressure {water['P_sat']:.4f} bar, total pressure 1 bar).")
            elif n_v > 1e-9:
                text += (f" The outlet is at the boiling point, part liquid and part vapour: "
                         f"{n_v:.3g} mol are still vapour.")
            notes.append({"level": "info", "kind": "condensation", "message": text})
            if T_out < 273.15:
                notes.append({"level": "warning", "kind": "freezing", "message": (
                    "Below 273.15 K water freezes. Ice is not in the database, so the liquid data are "
                    "stretched below their range here.")})
        elif water["n_written_liquid"] > 1e-9:
            notes.append({"level": "info", "kind": "evaporation", "message": (
                f"The reaction is written with liquid water, but at {T_out:,.0f} K the outlet carries all of its "
                f"water as vapour. Evaporating the {water['n_written_liquid']:.3g} mol takes "
                f"{water['n_written_liquid'] * water['dH_vap_298'] / 1000.0:,.1f} kJ, which is counted in step 2.")})
    elif water["n_vapour"] - water["n_vapour_possible"] > 1e-9:
        notes.append({"level": "warning", "kind": "would_condense", "message": (
            f"At {_kelvin(T_out)} K the outlet is colder than {water['T_dew']:.1f} K, the temperature at which its "
            f"water vapour becomes saturated: {water['n_vapour'] - water['n_vapour_possible']:.3g} "
            f"of the {water['n_total']:.3g} mol of water would condense and give up more heat. This is left out because the water is "
            f"kept in the phase that is written. Tick \"Let the water change phase\" to include it.")})
    elif water["n_written_liquid"] - (water["n_total"] - water["n_vapour_possible"]) > 1e-9:
        notes.append({"level": "warning", "kind": "would_evaporate", "message": (
            f"At {T_out:,.0f} K the liquid water that is written would be partly or fully vapour. This is left out "
            f"because the water is kept in the phase that is written. Tick \"Let the water change phase\" to include it.")})
    # other vapours that would condense: only water can change phase here
    n_gas = sum(n for s, n in case["outlet"].items() if SPECIES[s].phase == "g")
    for sid, n in case["outlet"].items():
        t = phase.transition_of(sid)
        if t is None or t is phase.TRANSITIONS["Water"] or not t.trusted or sid != t.gas or n <= _TINY:
            continue
        P_sat = phase.vapour_pressure(t, T_out)
        if T_out < t.T_boil and n / n_gas * P0 > P_sat:
            notes.append({"level": "warning", "kind": "other_condensable", "species": sid, "message": (
                f"{sid} would partly condense at {_kelvin(T_out)} K: its partial pressure in the outlet would be "
                f"{n / n_gas * P0:.3f} bar, above its vapour pressure of {P_sat:.3f} bar. In the heat lab only water "
                f"can change phase, so {sid} is kept as a vapour and its latent heat is not counted.")})
    return notes


def temperature_notes(high: List[str], svn_only: Optional[dict], mode: str, T_in: float, T_out: float) -> List[dict]:
    """Notes for a hot stream: where the heat capacities come from above the
    SVN range, and that dissociation is not part of the energy balance."""
    notes: List[dict] = []
    if high:
        text = (f"Above the range of SVN's formula the heat capacities of {', '.join(high)} are taken from "
                f"NIST equations (valid to {HIGH_T_MAX:,.0f} K), so nothing is extrapolated.")
        if svn_only is not None and mode == "adiabatic":
            text += (f" With SVN's formula stretched beyond its range, as the textbook's own flame example does, "
                     f"the outlet would be {svn_only['T_out']:,.0f} K instead of {T_out:,.0f} K.")
        elif svn_only is not None:
            text += (f" With SVN's formula stretched beyond its range the heat Q would be "
                     f"{svn_only['Q'] / 1000.0:,.1f} kJ.")
        notes.append({"level": "info", "kind": "high_T_data", "species": ", ".join(high), "message": text})
    hottest = max(T_in, T_out)
    if hottest > T_DISSOCIATION:
        strong = hottest > T_DISSOCIATION_STRONG
        notes.append({
            "level": "warning" if strong else "info", "kind": "dissociation",
            "message": (
                f"Above about {T_DISSOCIATION:,.0f} K the hot products of a real flame partly break apart "
                f"(CO2 into CO and O2, H2O into H2 and O2), and that takes up heat. This energy balance does not "
                f"include it, so a real flame is {'much ' if strong else 'somewhat '}cooler than {hottest:,.0f} K."),
        })
    return notes


def svn_outlet_temperature(case: dict, T_in: float, Q: float = 0.0) -> float:
    """The adiabatic outlet temperature with the SVN formulas only,
    extrapolated beyond their range: the number a textbook example gives."""
    return outlet_temperature(SvnStream(case["feed"]), SvnStream(case["outlet"]), T_in, Q)


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


def audit(case: dict, T_in: float, T_out: float, Q: float, split: Optional[WaterSplit] = None,
          n_vapour: Optional[float] = None) -> List[dict]:
    """Independent checks of one energy balance. With ``split`` the water of
    the outlet is divided between vapour and liquid (n_vapour moles of vapour)."""
    from .audit import _check

    feed = Stream(case["feed"])
    out_moles = dict(case["outlet"]) if split is None else split.moles_at(n_vapour)
    outlet = Stream(case["outlet"]) if split is None else split.all_vapour
    checks: List[dict] = []

    atoms_in: Dict[str, float] = {}
    atoms_out: Dict[str, float] = {}
    for moles, atoms in ((case["feed"], atoms_in), (out_moles, atoms_out)):
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
    relation = "dH_R + dH298 + dH_P = sum n_out H_i(T_out) - sum n_in H_i(T_in)"
    if split is not None:
        n_liquid = split.n_water - n_vapour
        path += split.n_written_liquid * split.latent(T0)
        if n_liquid > _TINY:
            path -= n_liquid * split.latent(T_out)
        relation = "dH_R + dH298 + dH_P + dH_phase = sum n_out H_i(T_out) - sum n_in H_i(T_in)"
    h_out = [n * SPECIES[s].H(T_out) for s, n in out_moles.items() if n > _TINY]
    h_in = [n * SPECIES[s].H(T_in) for s, n in case["feed"].items() if n > _TINY]
    direct = sum(h_out) - sum(h_in)
    # The heat duty is a small difference of large enthalpies when the streams
    # are large (for example a great excess of inert), so the round-off that
    # can be expected scales with the terms that are added, not with their sum.
    slack = 1e-11 * (sum(abs(h) for h in h_out) + sum(abs(h) for h in h_in))
    checks.append(_check("Two routes to the heat Q", relation,
                         path, direct, 1e-10, 1e-6 + slack))
    # ... plus, for a solved outlet temperature, the tolerance of the root (1e-9 K)
    checks.append(_check("Energy balance closes", "H_out(T_out) - H_in(T_in) = Q",
                         direct, Q, 1e-9, 1e-5 + 10.0 * slack + 1e-9 * abs(outlet.cp(T_out))))

    # Near absolute zero the D/T^2 term makes the integrand too steep for a
    # fixed-step quadrature, so the numerical cross-check stops at 50 K.
    if abs(T_out - T0) > 1e-9 and T_out >= 50.0:
        # piece by piece between the temperatures where a species changes its constants
        lo, hi = min(T0, T_out), max(T0, T_out)
        cuts = [lo] + [b for b in outlet.breakpoints if lo < b < hi] + [hi]
        numeric = 0.0
        for a, b in zip(cuts, cuts[1:]):
            piece = outlet.coeffs_at(0.5 * (a + b))
            numeric += R * simpson(lambda t: cp_over_r(piece, t), a, b)
        if T_out < T0:
            numeric = -numeric
        checks.append(_check("Sensible heat of the products",
                             "integral of sum n_i Cp_i dT from the formula = numerical integration",
                             outlet.sensible(T0, T_out), numeric, 1e-8, 1e-6))

    if split is not None and split.n_water - n_vapour > 1e-9:
        water = split.water
        P_sat = phase.vapour_pressure(water, T_out)
        if split.n_other_gas > _TINY and n_vapour > _TINY:
            checks.append(_check("The gas is saturated with water",
                                 "partial pressure of the water vapour = vapour pressure at T_out",
                                 n_vapour / (n_vapour + split.n_other_gas) * split.P, P_sat, 1e-9, 1e-12))
        h = 0.01
        slope = (math.log(phase.vapour_pressure(water, T_out + h))
                 - math.log(phase.vapour_pressure(water, T_out - h))) / (2 * h)
        checks.append(_check("Clausius/Clapeyron equation for water",
                             "d(ln P_sat)/dT = dH_vap / (R T^2)",
                             slope, split.latent(T_out) / (R * T_out * T_out), 1e-6, 1e-10))
        # While liquid is present on both sides of T_out, the stream moves
        # along its saturation line at constant pressure, where dH = T dS.
        if split.n_other_gas > _TINY and split.n_water - split.vapour(T_out + h) > 1e-9:
            dH = split.H(T_out + h) - split.H(T_out - h)
            dS = split.S(T_out + h) - split.S(T_out - h)
            checks.append(_check("Enthalpy and entropy of the outlet agree while water condenses",
                                 "dH = T dS at constant pressure (enthalpy and entropy of the outlet)",
                                 dH, T_out * dS, 1e-6, 1e-9))
    return checks


def work_potential(case: dict, T_out: float, T_surroundings: float = T0,
                   condense: bool = False) -> Optional[dict]:
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
    condensed = 0.0
    if condense and has_water(case["outlet"]):
        # with the water free to condense on the way down
        split = WaterSplit(case["outlet"])
        dH = split.H(T_surroundings) - split.H(T_out)
        dS = split.S(T_surroundings) - split.S(T_out)
        condensed = split.vapour(T_out) - split.vapour(T_surroundings)
    else:
        outlet = Stream(case["outlet"])
        dH = outlet.sensible(T_out, T_surroundings)
        dS = outlet.entropy_change(T_out, T_surroundings)
    W = dH - T_surroundings * dS
    return {"T_surroundings": T_surroundings, "dH": dH, "dS": dS, "W_ideal": W,
            "fraction": W / dH if dH else None,
            "water_condensed": condensed,
            "carnot_at_T_out": 1.0 - T_surroundings / T_out}


# ---------------------------------------------------------------------------
# sweeps and goal seeking
# ---------------------------------------------------------------------------
_EXCESS_GRID = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5,
                10.0, 15.0, 20.0, 30.0, 50.0, 75.0, MAX_EXCESS)


def excess_for_outlet_temperature(rxn: Reaction, target_T: float, T_in: float, **settings) -> dict:
    """Excess of the chosen reactant at which the adiabatic outlet reaches ``target_T``.

    More excess only adds material that enters at T_in, so the outlet moves
    steadily from its value at the smallest feasible excess towards T_in. The
    target can be met only if it lies between those two. The outlet is first
    evaluated on a grid of excess values; a setting that cannot be calculated
    (not enough of a reactant, outlet outside the usable range) is simply not
    a candidate. The answer is found by bisection between two neighbouring
    grid points that enclose the target, and is checked before it is returned.
    """
    settings = dict(settings)
    settings.pop("excess", None)
    Q = settings.pop("Q", 0.0)
    condense = settings.pop("condense", False)

    def T_out(excess: float) -> Optional[float]:
        try:
            return solve(build_case(rxn, excess=excess, **settings), T_in, "adiabatic", Q=Q,
                         condense=condense)["T_out"]
        except InputError:
            return None

    def answer(excess: Optional[float], reason: Optional[str], found: Optional[float] = None) -> dict:
        return {"target_T": target_T, "excess": excess, "T_out": found, "reason": reason}

    points = [(e, T_out(e)) for e in _EXCESS_GRID]
    solved = [(e, t) for e, t in points if t is not None]
    if not solved:
        return answer(None, "The energy balance has no solution for any excess between 0 and "
                            f"{100 * MAX_EXCESS:,.0f} %.")

    for (e1, t1), (e2, t2) in zip(points, points[1:]):
        if t1 is None or t2 is None or (t1 - target_T) * (t2 - target_T) > 0.0:
            continue
        lo, hi, t_lo = e1, e2, t1
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            t_mid = T_out(mid)
            if t_mid is None:
                return answer(None, "The energy balance cannot be solved everywhere between "
                                    f"{100 * e1:,.0f} and {100 * e2:,.0f} % excess, so no value is reported.")
            if (t_lo - target_T) * (t_mid - target_T) <= 0.0:
                hi = mid
            else:
                lo, t_lo = mid, t_mid
            if hi - lo < 1e-10:
                break
        best = 0.5 * (lo + hi)
        check = T_out(best)
        if check is None or abs(check - target_T) > 1e-3:
            return answer(None, "The search did not reproduce the target temperature, so no value is reported.")
        return answer(best, None, check)

    (e_first, t_first), (e_last, t_last) = solved[0], solved[-1]
    return answer(None, f"Between {100 * e_first:,.0f} and {100 * e_last:,.0f} % excess the outlet goes from "
                        f"{t_first:,.0f} K to {t_last:,.0f} K. More excess only moves it towards the feed "
                        f"temperature of {T_in:,.0f} K, so {target_T:,.0f} K is not reached.")


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
        "bomb_value_mass": -(liquid.dH0 - dn_gas * R * T0) / M / 1000.0,   # MJ per kg of fuel
    }


# ---------------------------------------------------------------------------
# bomb calorimeter (constant-volume combustion)
# ---------------------------------------------------------------------------
JOULE_PER_CAL = 4.184            # thermochemical calorie, as in the course lab handout
_FUEL_ELEMENTS = {"C", "H", "O", "N", "S"}


def enthalpy_from_internal_energy(dU: float, dn_gas: float, T: float) -> float:
    """dH = dU + dn_gas * R * T: from the heat measured at constant volume to
    the heat of reaction at constant pressure (gases ideal, condensed phases
    neglected). Any energy unit per mole, as long as it is joules for R."""
    return dU + dn_gas * R * T


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
    dU = dH - dn_gas * R * T                      # the inverse of enthalpy_from_internal_energy
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
            "heat_measured": C_cal * dT,                          # J taken up by the calorimeter
            "measured_calorific_value": measured, "include_gases": include_gases,
            "compared": len(candidates), "candidates": candidates[:limit]}
