"""Thermodynamic consistency audit.

Every result the solver reports is re-derived here by an independent route,
using exact relations between thermodynamic properties. If a formula, a sign
or a unit were wrong somewhere, at least one of these identities would fail.

Standard-state checks for a reaction at T
    1. Elemental balance.
    2. dG from the closed-form expression  ==  sum of nu_i G_i(T) over species.
    3. Kirchhoff:        d(dH)/dT     ==  dCp
    4. van 't Hoff:      d(ln K)/dT   ==  dH / (R T^2)
    5. Gibbs-Helmholtz:  d(dG)/dT     ==  -dS
    6. Analytical Cp integrals == Simpson numerical quadrature.

Real-gas checks for each gaseous species at T, P
    7. G^R = H^R - T S^R            ==  R T ln(phi)
    8. d(ln phi)/dT at constant P   ==  -H^R / (R T^2)
    9. d(ln phi)/dP at constant T   ==  (Z - 1) / P

The derivatives are taken numerically (central differences), so they do not
share any code with the analytical formulas they are testing.
"""

from __future__ import annotations

from typing import List

from .constants import R, T0
from .heatcap import cp_over_r, icph, icps, simpson
from .realgas import residual
from .species import SPECIES


def _check(name: str, relation: str, lhs: float, rhs: float, rel_tol: float, abs_tol: float) -> dict:
    err = abs(lhs - rhs)
    scale = max(abs(lhs), abs(rhs))
    passed = err <= abs_tol + rel_tol * scale
    return {
        "name": name, "relation": relation, "lhs": lhs, "rhs": rhs,
        "abs_error": err, "rel_error": err / scale if scale > 0 else 0.0, "passed": passed,
    }


def audit_reaction(rxn, T: float) -> List[dict]:
    """Consistency checks on the standard property changes at T."""
    checks: List[dict] = []

    worst = max((abs(left - right) for left, right in rxn.imbalance().values()), default=0.0)
    checks.append(_check("Elemental balance", "atoms in = atoms out, every element",
                         worst, 0.0, 0.0, 1e-8))

    if not rxn.has_cp or abs(T - T0) < 1e-6:
        checks.append(_check("G = H - T S at 298.15 K", "dG0 = dH0 - T0 dS0",
                             rxn.dG0, rxn.dH0 - T0 * rxn.dS0, 1e-12, 1e-6))
        return checks

    # The constants that apply at T: SVN from 298.15 K upwards, the NIST
    # low-temperature set below it.
    d = rxn.delta_coeffs(T)
    off_H, off_S = rxn.delta_offsets(T)
    closed = (rxn.dH0 - (T / T0) * (rxn.dH0 - rxn.dG0)
              + R * (icph(T0, T, d) + off_H) - R * T * (icps(T0, T, d) + off_S))
    by_species = sum(nu * SPECIES[s].G(T) for s, nu in rxn.stoich.items())
    checks.append(_check("Two routes to dG(T)",
                         "from dH0, dG0 and the heat-capacity integrals = sum nu_i G_i(T)",
                         closed, by_species, 1e-10, 1e-6))

    # The heat capacity changes its source at 298.15 K, and for some species
    # again at the end of the SVN range, so the step of the numerical
    # derivatives must not reach across such a temperature.
    gap = min(abs(T - b) for b in [T0] + rxn.breakpoints())
    if gap < 1e-6:
        return checks
    h = min(0.01, gap)
    dH_slope = (rxn.dH(T + h) - rxn.dH(T - h)) / (2 * h)
    checks.append(_check("Slope of ΔH° with temperature", "d(dH)/dT = dCp",
                         dH_slope, rxn.dCp(T), 1e-6, 1e-6))

    lnK_slope = (rxn.lnK(T + h) - rxn.lnK(T - h)) / (2 * h)
    checks.append(_check("van 't Hoff equation", "d(ln K)/dT = dH/(R T^2)",
                         lnK_slope, rxn.dH(T) / (R * T * T), 1e-6, 1e-10))

    dG_slope = (rxn.dG(T + h) - rxn.dG(T - h)) / (2 * h)
    checks.append(_check("Slope of ΔG° with temperature", "d(dG)/dT = -dS",
                         dG_slope, -rxn.dS(T), 1e-6, 1e-6))

    # Numerical integration, piece by piece between the temperatures where a
    # species changes its set of constants.
    lo, hi = min(T0, T), max(T0, T)
    cuts = [lo] + [b for b in rxn.breakpoints() if lo < b < hi] + [hi]
    num_H = num_S = 0.0
    for a, b in zip(cuts, cuts[1:]):
        piece = rxn.delta_coeffs(0.5 * (a + b))
        num_H += R * simpson(lambda t: cp_over_r(piece, t), a, b)
        num_S += R * simpson(lambda t: cp_over_r(piece, t) / t, a, b)
    sign = 1.0 if T >= T0 else -1.0
    checks.append(_check("Enthalpy integral", "integral of dCp dT from the formula = numerical integration",
                         R * rxn.idcph(T), sign * num_H, 1e-8, 1e-6))
    checks.append(_check("Entropy integral", "integral of dCp dT/T from the formula = numerical integration",
                         R * rxn.idcps(T), sign * num_S, 1e-8, 1e-8))
    return checks


def audit_residuals(rxn, T: float, P: float, model: str) -> List[dict]:
    """Consistency checks on the residual properties of each gaseous species."""
    checks: List[dict] = []
    if model == "ideal":
        return checks
    for sid in rxn.stoich:
        sp = SPECIES[sid]
        res = residual(sp, T, P, model)
        if res.treated_ideal:
            continue
        # The finite differences below need the same kind of root on both
        # sides of the point; at a liquid-like state there is nothing to audit
        # for a gas-phase calculation.
        if res.state == "liquid_like":
            continue
        # res.lnphi is G^R/(R T), obtained from the equation of state by its own formula
        checks.append(_check(f"{sid}: residual enthalpy, entropy and Gibbs energy fit together",
                             "H^R - T S^R = G^R from the equation of state",
                             res.HR - T * res.SR, R * T * res.lnphi, 1e-9, 1e-6))
        hT = 1e-4 * T
        slope_T = (residual(sp, T + hT, P, model).lnphi - residual(sp, T - hT, P, model).lnphi) / (2 * hT)
        # Tolerances: the finite difference itself is only good to about 1e-5
        # relative, and near a sign change of H^R the slope is close to zero,
        # hence the small absolute allowance.
        checks.append(_check(f"{sid}: residual enthalpy from the temperature slope",
                             "d(G^R/RT)/dT at constant P = -H^R/(R T^2)",
                             slope_T, -res.HR / (R * T * T), 1e-4, 1e-10))
        hP = 1e-4 * P
        slope_P = (residual(sp, T, P + hP, model).lnphi - residual(sp, T, P - hP, model).lnphi) / (2 * hP)
        checks.append(_check(f"{sid}: compressibility factor from the pressure slope",
                             "d(G^R/RT)/dP at constant T = (Z - 1)/P",
                             slope_P, (res.Z - 1.0) / P, 1e-4, 1e-10))
    return checks


def all_passed(checks: List[dict]) -> bool:
    return all(c["passed"] for c in checks)
