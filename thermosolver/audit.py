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

    if not rxn.has_cp or abs(T - T0) < 1e-9:
        checks.append(_check("G = H - T S at 298.15 K", "dG0 = dH0 - T0 dS0",
                             rxn.dG0, rxn.dH0 - T0 * rxn.dS0, 1e-12, 1e-6))
        return checks

    d = rxn.delta_coeffs()
    closed = (rxn.dH0 - (T / T0) * (rxn.dH0 - rxn.dG0)
              + R * icph(T0, T, d) - R * T * icps(T0, T, d))
    by_species = sum(nu * SPECIES[s].G(T) for s, nu in rxn.stoich.items())
    checks.append(_check("Two routes to dG(T)",
                         "closed form (dH0, dG0, IDCPH, IDCPS) = sum nu_i G_i(T)",
                         closed, by_species, 1e-10, 1e-6))

    h = 0.01
    dH_slope = (rxn.dH(T + h) - rxn.dH(T - h)) / (2 * h)
    checks.append(_check("Kirchhoff's law", "d(dH)/dT = dCp",
                         dH_slope, rxn.dCp(T), 1e-6, 1e-6))

    lnK_slope = (rxn.lnK(T + h) - rxn.lnK(T - h)) / (2 * h)
    checks.append(_check("van 't Hoff equation", "d(ln K)/dT = dH/(R T^2)",
                         lnK_slope, rxn.dH(T) / (R * T * T), 1e-6, 1e-10))

    dG_slope = (rxn.dG(T + h) - rxn.dG(T - h)) / (2 * h)
    checks.append(_check("Gibbs-Helmholtz relation", "d(dG)/dT = -dS",
                         dG_slope, -rxn.dS(T), 1e-6, 1e-6))

    num_H = R * simpson(lambda t: cp_over_r(d, t), T0, T)
    checks.append(_check("Enthalpy integral", "analytical integral of dCp dT = Simpson quadrature",
                         R * icph(T0, T, d), num_H, 1e-8, 1e-6))
    num_S = R * simpson(lambda t: cp_over_r(d, t) / t, T0, T)
    checks.append(_check("Entropy integral", "analytical integral of dCp dT/T = Simpson quadrature",
                         R * icps(T0, T, d), num_S, 1e-8, 1e-8))
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
        checks.append(_check(f"{sid}: G^R identity", "H^R - T S^R = R T ln(phi)",
                             res.HR - T * res.SR, R * T * res.lnphi, 1e-9, 1e-6))
        hT = 1e-4 * T
        slope_T = (residual(sp, T + hT, P, model).lnphi - residual(sp, T - hT, P, model).lnphi) / (2 * hT)
        # Tolerances: the finite difference itself is only good to about 1e-5
        # relative, and near a sign change of H^R the slope is close to zero,
        # hence the small absolute allowance.
        checks.append(_check(f"{sid}: Gibbs-Helmholtz", "d(ln phi)/dT at constant P = -H^R/(R T^2)",
                             slope_T, -res.HR / (R * T * T), 1e-4, 1e-10))
        hP = 1e-4 * P
        slope_P = (residual(sp, T, P + hP, model).lnphi - residual(sp, T, P - hP, model).lnphi) / (2 * hP)
        checks.append(_check(f"{sid}: volume relation", "d(ln phi)/dP at constant T = (Z - 1)/P",
                             slope_P, (res.Z - 1.0) / P, 1e-4, 1e-10))
    return checks


def all_passed(checks: List[dict]) -> bool:
    return all(c["passed"] for c in checks)
