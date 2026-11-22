"""Reactions: parsing, elemental balance, and standard property changes.

Sign convention (SVN Sec. 4.6): stoichiometric numbers nu_i are positive for
products and negative for reactants, and every property change of reaction is

        delta M = sum_i nu_i * M_i        (per mole of reaction as written)

Temperature dependence (SVN Sec. 4.6 and the chemical-equilibrium chapter),
with T0 = 298.15 K and delta-Cp/R = dA + dB*T + dC*T^2 + dD/T^2 (+ dE*T^3 when
a species from the NIST WebBook takes part):

    dH(T) = dH0 + R * integral_T0^T (dCp/R) dT
    dS(T) = dS0 + R * integral_T0^T (dCp/R) dT/T,   dS0 = (dH0 - dG0)/T0
    dG(T) = dH(T) - T*dS(T)
          = dH0 - (T/T0)(dH0 - dG0) + R*IDCPH - R*T*IDCPS
    ln K  = -dG(T) / (R*T)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import data
from .constants import R, T0
from .errors import DataUnavailableError, InputError, SolverError, UnbalancedReactionError
from .heatcap import Coeffs, combine, cp_over_r, icph, icps, mcph, mcps
from .species import SPECIES, Species, find_species

_ARROW = re.compile(r"\s*(?:<=>|<->|<-->|⇌|⇄|↔|⟶|→|=>|-->|->|=)\s*")
_COEFF = re.compile(r"^\s*(\d+(?:\.\d*)?|\.\d+)\s*(?:/\s*(\d+(?:\.\d*)?))?\s*\*?\s*(.+?)\s*$")
_BALANCE_TOL = 1e-8
MAX_COEFF = 1e6          # stoichiometric coefficients beyond this are treated as typing errors


def format_coeff(x: float) -> str:
    """Readable stoichiometric coefficient: 2, 1/2, 1.25 ..."""
    x = abs(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    frac = Fraction(x).limit_denominator(24)
    if abs(float(frac) - x) < 1e-9:
        return f"{frac.numerator}/{frac.denominator}"
    return f"{x:.6g}"


def _parse_side(text: str, notes: List[str]) -> List[Tuple[float, Species]]:
    terms = []
    # A '+' separates terms. Species names in this database never contain '+'.
    for chunk in text.split("+"):
        chunk = chunk.strip()
        if not chunk:
            raise InputError("There is an empty term in the reaction (check the '+' signs).")
        coeff = 1.0
        try:
            # Whole term first, so names that begin with a digit (1-butene) work.
            sp, note = find_species(chunk)
        except SolverError:
            # Otherwise the leading number is the stoichiometric coefficient.
            m = _COEFF.match(chunk)
            if m is None:
                raise
            coeff = float(m.group(1))
            if m.group(2):
                denom = float(m.group(2))
                if denom == 0:
                    raise InputError(f"Division by zero in the coefficient of '{chunk}'.")
                coeff /= denom
            sp, note = find_species(m.group(3))
        if not math.isfinite(coeff) or coeff <= 0:
            raise InputError(f"The coefficient of '{chunk[:40]}' must be a positive number.")
        if coeff > MAX_COEFF or coeff < 1.0 / MAX_COEFF:
            raise InputError(
                f"The coefficient of {sp.id} is outside the sensible range "
                f"({1.0 / MAX_COEFF:g} to {MAX_COEFF:g}).")
        if note and note not in notes:
            notes.append(note)
        terms.append((coeff, sp))
    return terms


def element_totals(stoich: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
    """Atoms of each element on the (reactant, product) side."""
    totals: Dict[str, List[float]] = {}
    for sid, nu in stoich.items():
        for el, n in SPECIES[sid].elements.items():
            pair = totals.setdefault(el, [0.0, 0.0])
            if nu < 0:
                pair[0] += -nu * n
            else:
                pair[1] += nu * n
    return {el: (a, b) for el, (a, b) in totals.items()}


def suggest_balance(reactants: Sequence[str], products: Sequence[str]) -> Optional[Dict[str, float]]:
    """Find the unique set of smallest whole-number coefficients that balances
    the given reactants and products, if there is one.

    The element-balance equations form a homogeneous linear system. When its
    null space is one-dimensional and all coefficients come out positive, the
    balanced equation is unique. Exact rational arithmetic avoids round-off.
    """
    species = list(reactants) + list(products)
    if len(set(species)) != len(species) or not reactants or not products:
        return None
    elements = sorted({el for sid in species for el in SPECIES[sid].elements})
    rows = []
    for el in elements:
        row = []
        for sid in species:
            n = SPECIES[sid].elements.get(el, 0)
            row.append(Fraction(n if sid in reactants else -n))
        rows.append(row)

    # Reduced row echelon form
    ncols = len(species)
    pivots = []
    r = 0
    for c in range(ncols):
        pivot = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        pv = rows[r][c]
        rows[r] = [v / pv for v in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                factor = rows[i][c]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == len(rows):
            break

    free = [c for c in range(ncols) if c not in pivots]
    if len(free) != 1:
        return None
    vec = [Fraction(0)] * ncols
    vec[free[0]] = Fraction(1)
    for i, c in enumerate(pivots):
        vec[c] = -rows[i][free[0]]
    if any(v == 0 for v in vec):
        return None
    if all(v < 0 for v in vec):
        vec = [-v for v in vec]
    if not all(v > 0 for v in vec):
        return None
    lcm = 1
    for v in vec:
        lcm = lcm * v.denominator // math.gcd(lcm, v.denominator)
    ints = [int(v * lcm) for v in vec]
    g = 0
    for v in ints:
        g = math.gcd(g, v)
    ints = [v // g for v in ints]
    return {sid: float(n) for sid, n in zip(species, ints)}


def _equation_from(reactants: Sequence[Tuple[float, str]], products: Sequence[Tuple[float, str]]) -> str:
    def side(items):
        parts = []
        for coeff, sid in items:
            c = format_coeff(coeff)
            parts.append(sid if c == "1" else f"{c} {sid}")
        return " + ".join(parts)

    return f"{side(reactants)} → {side(products)}"


@dataclass
class Reaction:
    """A balanced chemical reaction.  ``stoich`` maps species id -> nu."""

    stoich: Dict[str, float]
    name: str = ""
    notes: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ build
    @classmethod
    def parse(cls, text: str, name: str = "", check_balance: bool = True) -> "Reaction":
        """Build a reaction from text such as ``CH4 + 2 O2 -> CO2 + 2 H2O(l)``."""
        if not isinstance(text, str) or not text.strip():
            raise InputError("Please enter a reaction, for example: CO + 2 H2 -> CH3OH")
        sides = _ARROW.split(text.strip())
        if len(sides) != 2 or not sides[0].strip() or not sides[1].strip():
            raise InputError(
                "A reaction needs exactly one arrow with species on both sides, "
                "for example: N2 + 3 H2 -> 2 NH3"
            )
        notes: List[str] = []
        reactants = _parse_side(sides[0], notes)
        products = _parse_side(sides[1], notes)

        stoich: Dict[str, float] = {}
        for coeff, sp in reactants:
            stoich[sp.id] = stoich.get(sp.id, 0.0) - coeff
        for coeff, sp in products:
            stoich[sp.id] = stoich.get(sp.id, 0.0) + coeff
        cancelled = [sid for sid, nu in stoich.items() if abs(nu) < 1e-12]
        for sid in cancelled:
            del stoich[sid]
            notes.append(f"{sid} appears equally on both sides and cancels out.")
        if not stoich:
            raise InputError("Everything cancels: the two sides of the reaction are identical.")

        rxn = cls(stoich, name, notes)
        if check_balance:
            rxn.assert_balanced()
        return rxn

    # ---------------------------------------------------------------- balance
    def imbalance(self) -> Dict[str, Tuple[float, float]]:
        """Elements that are not conserved: {element: (reactant atoms, product atoms)}."""
        bad = {}
        for el, (left, right) in element_totals(self.stoich).items():
            if abs(left - right) > _BALANCE_TOL * max(1.0, left, right):
                bad[el] = (left, right)
        return bad

    def is_balanced(self) -> bool:
        return not self.imbalance()

    def assert_balanced(self) -> None:
        bad = self.imbalance()
        if not bad:
            return
        parts = [
            f"{el}: {format_coeff(l)} on the left, {format_coeff(r)} on the right"
            for el, (l, r) in sorted(bad.items())
        ]
        details = {
            "equation": self.equation,
            "imbalance": {el: {"reactants": l, "products": r} for el, (l, r) in bad.items()},
        }
        message = (
            f"The reaction {self.equation} is not balanced ("
            + "; ".join(parts)
            + "). No thermodynamics was calculated."
        )
        suggestion = suggest_balance(self.reactant_ids, self.product_ids)
        if suggestion:
            fixed = _equation_from(
                [(suggestion[s], s) for s in self.reactant_ids],
                [(suggestion[s], s) for s in self.product_ids],
            )
            details["suggestion"] = fixed
            message += f" Did you mean: {fixed} ?"
        raise UnbalancedReactionError(message, details)

    # ------------------------------------------------------------ description
    @property
    def reactant_ids(self) -> List[str]:
        return [s for s, nu in self.stoich.items() if nu < 0]

    @property
    def product_ids(self) -> List[str]:
        return [s for s, nu in self.stoich.items() if nu > 0]

    @property
    def species(self) -> List[Species]:
        return [SPECIES[s] for s in self.stoich]

    @property
    def equation(self) -> str:
        return _equation_from(
            [(-self.stoich[s], s) for s in self.reactant_ids],
            [(self.stoich[s], s) for s in self.product_ids],
        )

    @property
    def delta_n_gas(self) -> float:
        """Change in the number of moles of gas, sum of nu_i over gaseous species."""
        return sum(nu for s, nu in self.stoich.items() if SPECIES[s].phase == "g")

    def scaled(self, factor: float) -> "Reaction":
        """The same reaction multiplied by ``factor`` (negative reverses it)."""
        if abs(factor) < 1e-12:
            raise InputError("A reaction cannot be multiplied by zero.")
        return Reaction({s: nu * factor for s, nu in self.stoich.items()}, self.name, list(self.notes))

    def reversed(self) -> "Reaction":
        return self.scaled(-1.0)

    # --------------------------------------------------------- 298.15 K values
    @property
    def dH0(self) -> float:
        """Standard heat of reaction at 298.15 K, J/mol."""
        return sum(nu * SPECIES[s].dHf for s, nu in self.stoich.items())

    @property
    def dG0(self) -> float:
        """Standard Gibbs energy change of reaction at 298.15 K, J/mol."""
        return sum(nu * SPECIES[s].dGf for s, nu in self.stoich.items())

    @property
    def dS0(self) -> float:
        """Standard entropy change of reaction at 298.15 K, J/(mol K)."""
        return (self.dH0 - self.dG0) / T0

    # ----------------------------------------------------------- heat capacity
    @property
    def has_cp(self) -> bool:
        return all(sp.cp is not None for sp in self.species)

    def delta_coeffs(self, T: Optional[float] = None) -> Coeffs:
        """(dA, dB, dC, dD, dE) = sum of nu_i * (A_i, B_i, C_i, D_i, E_i).
        dE is zero unless a species with a cubic heat-capacity term (NIST) takes part.

        Without T, or from 298.15 K upwards, these are the constants of the
        main correlations (SVN). Below 298.15 K each species contributes its
        low-temperature constants (NIST tables) where it has them.
        """
        if T is None:
            return combine((nu, SPECIES[s].require_cp()) for s, nu in self.stoich.items())
        return combine((nu, SPECIES[s].coeffs_at(T)) for s, nu in self.stoich.items())

    def uses_low_T_data(self, T: float) -> List[str]:
        """Species whose heat capacity at T comes from the low-temperature tables."""
        if T >= T0:
            return []
        return [sp.id for sp in self.species if sp.cp_low is not None]

    def dCp(self, T: float) -> float:
        """Heat-capacity change of reaction at T, J/(mol K)."""
        return R * cp_over_r(self.delta_coeffs(T), T)

    def valid_range(self) -> Optional[Tuple[float, float]]:
        """Temperature range in which every species' Cp correlation is valid."""
        if not self.has_cp:
            return None
        lo = max(sp.cp_Tmin for sp in self.species)
        hi = min(sp.cp_Tmax for sp in self.species)
        return (lo, hi) if lo <= hi else None

    # -------------------------------------------------------- values at any T
    def _check_T(self, T: float) -> None:
        if not isinstance(T, (int, float)) or isinstance(T, bool) or not math.isfinite(T):
            raise InputError("Temperature must be a number.")
        if T <= 0:
            raise InputError("Temperature must be above 0 K (use kelvin, not degrees Celsius).")
        if not self.has_cp and abs(T - T0) > 1e-6:
            missing = ", ".join(sp.id for sp in self.species if sp.cp is None)
            raise DataUnavailableError(
                f"SVN gives no heat capacity for {missing}, so this reaction can only "
                f"be evaluated at {T0} K.",
                {"species": missing},
            )

    def _is_T0(self, T: float) -> bool:
        return abs(T - T0) < 1e-9

    def dH(self, T: float) -> float:
        """Standard heat of reaction at T, J/mol."""
        self._check_T(T)
        if self._is_T0(T):
            return self.dH0
        return self.dH0 + R * icph(T0, T, self.delta_coeffs(T))

    def dS(self, T: float) -> float:
        """Standard entropy change of reaction at T, J/(mol K)."""
        self._check_T(T)
        if self._is_T0(T):
            return self.dS0
        return self.dS0 + R * icps(T0, T, self.delta_coeffs(T))

    def dG(self, T: float) -> float:
        """Standard Gibbs energy change of reaction at T, J/mol."""
        return self.dH(T) - T * self.dS(T)

    def lnK(self, T: float) -> float:
        """Natural log of the equilibrium constant, ln K = -dG/(RT)."""
        return -self.dG(T) / (R * T)

    def K(self, T: float) -> float:
        x = self.lnK(T)
        if x > 700:
            return math.inf
        return math.exp(x)

    # ------------------------------------------------- simplified Cp treatments
    def dH_constant_cp(self, T: float) -> float:
        """Heat of reaction if delta-Cp is frozen at its 298.15 K value."""
        return self.dH0 + self.dCp(T0) * (T - T0)

    def dS_constant_cp(self, T: float) -> float:
        return self.dS0 + self.dCp(T0) * math.log(T / T0)

    def dG_constant_cp(self, T: float) -> float:
        return self.dH_constant_cp(T) - T * self.dS_constant_cp(T)

    def dG_no_cp(self, T: float) -> float:
        """Gibbs energy change if delta-Cp is ignored altogether
        (dH and dS frozen at 298.15 K)."""
        return self.dH0 - T * self.dS0

    # --------------------------------------------------------------- utilities
    def crossover_temperatures(self, lo: Optional[float] = None, hi: Optional[float] = None) -> List[float]:
        """Temperatures where dG(T) = 0 (K = 1) inside the valid Cp range."""
        rng = self.valid_range()
        if rng is None:
            return []
        lo = max(rng[0], lo) if lo else rng[0]
        hi = min(rng[1], hi) if hi else rng[1]
        if hi <= lo:
            return []
        roots = []
        n = 400
        prev_T = lo
        prev_g = self.dG(lo)
        for i in range(1, n + 1):
            T = lo + (hi - lo) * i / n
            g = self.dG(T)
            if prev_g == 0.0:
                roots.append(prev_T)
            elif prev_g * g < 0:
                a, b, ga = prev_T, T, prev_g
                for _ in range(80):
                    mid = 0.5 * (a + b)
                    gm = self.dG(mid)
                    if ga * gm <= 0:
                        b = mid
                    else:
                        a, ga = mid, gm
                roots.append(0.5 * (a + b))
            prev_T, prev_g = T, g
        if prev_g == 0.0:                  # an exact root at the last grid point
            roots.append(prev_T)
        return roots

    def range_warnings(self, T: float) -> List[dict]:
        """Warnings about heat-capacity extrapolation and physical state at T."""
        out = []
        low = self.uses_low_T_data(T)
        if low:
            out.append({
                "level": "info", "species": ", ".join(low), "kind": "low_T_data",
                "message": (
                    f"Below {T0} K the heat capacities are not from SVN, whose tables start at 298 K. "
                    f"From {data.LOW_T_MIN:g} K to {T0} K they come from NIST tables (NIST-JANAF and the "
                    f"NIST Chemistry WebBook) for: {', '.join(low)}."
                ),
            })
        for sp in self.species:
            if sp.remark:
                out.append({"level": "info", "species": sp.id, "kind": "data_source",
                            "message": f"{sp.id}: {sp.remark}"})
            if sp.cp is None:
                if not self._is_T0(T):
                    out.append({
                        "level": "error", "species": sp.id,
                        "message": f"No heat-capacity data in SVN for {sp.id}.",
                    })
                continue
            if not sp.in_cp_range(T):
                side = "below" if T < sp.cp_Tmin else "above"
                out.append({
                    "level": "warning", "species": sp.id, "kind": "cp_extrapolation",
                    "message": (
                        f"{sp.id}: T = {T:g} K is {side} the validity range of its heat-capacity "
                        f"correlation ({sp.cp_Tmin:g} to {sp.cp_Tmax:g} K, {sp.cp_source_at(T)}). "
                        f"The polynomial is being extrapolated and the result is unreliable."
                    ),
                })
            crit = sp.critical
            if crit and crit.Tn:
                if sp.phase == "l" and T > crit.Tn + 0.5:
                    out.append({
                        "level": "info", "species": sp.id, "kind": "phase",
                        "message": (
                            f"{sp.id}: at 1 bar this liquid boils at {crit.Tn:g} K, so a liquid "
                            f"standard state at {T:g} K is hypothetical. Consider the gas species."
                        ),
                    })
                elif sp.phase == "g" and T < crit.Tn - 0.5:
                    out.append({
                        "level": "info", "species": sp.id, "kind": "phase",
                        "message": (
                            f"{sp.id}: below its normal boiling point ({crit.Tn:g} K) the stable "
                            f"phase at 1 bar is a liquid. The ideal-gas standard state is still "
                            f"well defined, but check that gas is the phase you mean."
                        ),
                    })
        return out

    def species_table(self, T: float) -> List[dict]:
        """Per-species data and individual sensible-heat effects from T0 to T."""
        rows = []
        at_T0 = self._is_T0(T)
        for sid, nu in self.stoich.items():
            sp = SPECIES[sid]
            if sp.cp is None:
                sens_H = 0.0 if at_T0 else None
                sens_S = 0.0 if at_T0 else None
                cp_T = None
                mean_cp = None
            else:
                sens_H = sp.sensible_dH(T0, T)
                sens_S = sp.sensible_dS(T0, T)
                cp_T = sp.cp_J(T)
                mean_cp = R * mcph(T0, T, sp.coeffs_at(T))
            rows.append({
                "id": sid,
                "name": sp.name,
                "phase": sp.phase,
                "nu": nu,
                "role": "product" if nu > 0 else "reactant",
                "dHf": sp.dHf,
                "dGf": sp.dGf,
                "cp_T": cp_T,
                "mean_cp_H": mean_cp,
                "sensible_dH": sens_H,
                "nu_sensible_dH": None if sens_H is None else nu * sens_H,
                "sensible_dS": sens_S,
                "H_T": None if sens_H is None else sp.dHf + sens_H,
                "in_cp_range": sp.in_cp_range(T),
                "cp_from_low_T_table": sp.cp_low is not None and T < T0,
                "cp_Tmin": sp.cp_Tmin,
                "cp_Tmax": sp.cp_Tmax,
            })
        return rows

    def evaluate(self, T: float) -> dict:
        """All standard property changes at T in one dictionary (SI, J and K)."""
        self._check_T(T)
        dH0, dG0, dS0 = self.dH0, self.dG0, self.dS0
        out = {
            "T": T,
            "dH0": dH0, "dG0": dG0, "dS0": dS0,
            "lnK0": -dG0 / (R * T0),
            "delta_n_gas": self.delta_n_gas,
        }
        if self.has_cp:
            # Below 298.15 K these are the low-temperature constants (NIST)
            d = self.delta_coeffs(T)
            idcph = 0.0 if self._is_T0(T) else icph(T0, T, d)
            idcps = 0.0 if self._is_T0(T) else icps(T0, T, d)
            out.update({
                "dA": d[0], "dB": d[1], "dC": d[2], "dD": d[3], "dE": d[4],
                "low_T_species": self.uses_low_T_data(T),
                "dCp0": R * cp_over_r(self.delta_coeffs(), T0),
                "dCp": R * cp_over_r(d, T),
                "IDCPH": idcph, "IDCPS": idcps,
                "mean_dCp_H": R * mcph(T0, T, d),
                "mean_dCp_S": R * mcps(T0, T, d),
            })
        else:
            idcph = idcps = 0.0
            out.update({k: None for k in (
                "dA", "dB", "dC", "dD", "dE", "dCp0", "dCp", "mean_dCp_H", "mean_dCp_S")})
            out.update({"IDCPH": 0.0, "IDCPS": 0.0})
        dH = dH0 + R * idcph
        dS = dS0 + R * idcps
        dG = dH - T * dS
        lnK = -dG / (R * T)
        out.update({
            "dH": dH, "dS": dS, "dG": dG, "TdS": T * dS,
            "lnK": lnK,
            "log10K": lnK / math.log(10.0),
            "K": math.exp(lnK) if abs(lnK) < 700 else None,
            "thermicity0": thermicity(dH0),
            "thermicity": thermicity(dH),
            "favourability": favourability(lnK),
        })
        # Hess-law path used for the temperature correction (SVN Fig. 4.x):
        # cool reactants T -> T0, react at T0, heat products T0 -> T.
        if self.has_cp:
            cool = sum(nu * SPECIES[s].sensible_dH(T0, T) for s, nu in self.stoich.items() if nu < 0)
            heat = sum(nu * SPECIES[s].sensible_dH(T0, T) for s, nu in self.stoich.items() if nu > 0)
            out["path"] = {"cool_reactants": cool, "react_at_T0": dH0, "heat_products": heat}
            dG_const = self.dG_constant_cp(T)
            dG_none = self.dG_no_cp(T)
            out["constant_cp"] = {
                "dH": self.dH_constant_cp(T),
                "dS": self.dS_constant_cp(T),
                "dG": dG_const,
                "lnK": -dG_const / (R * T),
            }
            out["no_cp"] = {"dH": dH0, "dS": dS0, "dG": dG_none, "lnK": -dG_none / (R * T)}
        return out


def thermicity(dH: float) -> str:
    if abs(dH) < 1e-6:
        return "thermoneutral"
    return "exothermic" if dH < 0 else "endothermic"


def favourability(lnK: float) -> dict:
    """Plain-language reading of the equilibrium constant.

    dG < 0 (K > 1) means products are favoured when every species is in its
    standard state. It does not say how fast the reaction is, and the actual
    equilibrium conversion also depends on pressure and feed composition.
    """
    log10K = lnK / math.log(10.0)
    if log10K >= 3:
        label = "strongly favourable"
        text = "K is much greater than 1: with every species at 1 bar the equilibrium lies almost entirely on the product side."
    elif log10K > 0:
        label = "favourable"
        text = "K is greater than 1: products are favoured at standard conditions, with a measurable amount of reactants left."
    elif log10K == 0:
        label = "balanced"
        text = "K equals 1: neither side is favoured at standard conditions."
    elif log10K > -3:
        label = "unfavourable"
        text = "K is less than 1: reactants are favoured at standard conditions, so only partial conversion is possible."
    else:
        label = "strongly unfavourable"
        text = "K is much less than 1: with every species at 1 bar the equilibrium lies almost entirely on the reactant side."
    return {"label": label, "text": text, "spontaneous_standard": lnK > 0}
