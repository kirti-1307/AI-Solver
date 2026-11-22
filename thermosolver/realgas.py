"""Real-gas behaviour and residual properties (SVN Chapters 3 and 6).

A residual property is the difference between the real-gas value and the
ideal-gas value at the same temperature and pressure:

        M^R = M - M^ig        (M = V, H, S, G)

For an ideal gas the enthalpy does not depend on pressure, so at constant
temperature the residual enthalpy IS the whole effect of pressure on H.

Two families of models from SVN are implemented.

1. Generalized second-virial-coefficient correlation (Pitzer/Abbott):

        B0 = 0.083 - 0.422/Tr^1.6        dB0/dTr = 0.675/Tr^2.6   (exactly 0.6752)
        B1 = 0.139 - 0.172/Tr^4.2        dB1/dTr = 0.722/Tr^5.2   (exactly 0.7224)
        Z      = 1 + (B0 + w*B1) Pr/Tr
        H^R/(R*Tc) = Pr [B0 - Tr dB0/dTr + w (B1 - Tr dB1/dTr)]
        S^R/R      = -Pr (dB0/dTr + w dB1/dTr)
        ln(phi)    = (Pr/Tr)(B0 + w*B1)

2. Generic cubic equation of state  P = RT/(V-b) - a(T)/((V+eps*b)(V+sigma*b))
   with the parameter assignments of SVN Table 3.1 (van der Waals,
   Redlich/Kwong, Soave/Redlich/Kwong, Peng/Robinson):

        beta = Omega*Pr/Tr           q = Psi*alpha(Tr)/(Omega*Tr)
        Z    = 1 + beta - q*beta*(Z - beta)/((Z + eps*beta)(Z + sigma*beta))
        I    = 1/(sigma-eps) * ln[(Z + sigma*beta)/(Z + eps*beta)]
        H^R/(R*T) = Z - 1 + [dln(alpha)/dln(Tr) - 1] q I
        S^R/R     = ln(Z - beta) + dln(alpha)/dln(Tr) q I
        ln(phi)   = Z - 1 - ln(Z - beta) - q I

Both satisfy G^R/(RT) = H^R/(RT) - S^R/R = ln(phi), which the test-suite checks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .constants import P0, R, R_CM3_BAR
from .errors import InputError, PhaseError
from .species import SPECIES, Species

SQRT2 = math.sqrt(2.0)

MODEL_NAMES = {
    "ideal": "Ideal gas",
    "virial": "Generalized virial (Pitzer/Abbott)",
    "vdw": "van der Waals",
    "rk": "Redlich/Kwong",
    "srk": "Soave/Redlich/Kwong",
    "pr": "Peng/Robinson",
}


# ---------------------------------------------------------------------------
# Cubic equations of state: SVN Table 3.1
# ---------------------------------------------------------------------------
def _kappa_srk(w: float) -> float:
    return 0.480 + 1.574 * w - 0.176 * w * w


def _kappa_pr(w: float) -> float:
    return 0.37464 + 1.54226 * w - 0.26992 * w * w


@dataclass(frozen=True)
class CubicEOS:
    key: str
    sigma: float
    epsilon: float
    Omega: float
    Psi: float
    Zc: float          # critical compressibility the equation itself predicts (SVN Table 3.1)

    def _m(self, Tr: float, w: float) -> float:
        """The Soave term 1 + kappa (1 - sqrt(Tr)); alpha = m^2."""
        kappa = _kappa_srk(w) if self.key == "srk" else _kappa_pr(w)
        return 1.0 + kappa * (1.0 - math.sqrt(Tr))

    def alpha(self, Tr: float, w: float) -> float:
        if self.key == "vdw":
            return 1.0
        if self.key == "rk":
            return Tr ** -0.5
        # Far above the critical temperature m reaches zero. Past that point
        # m^2 would rise again, which is unphysical, so alpha stays at zero
        # (attraction has faded out). This keeps every property continuous.
        m = max(self._m(Tr, w), 0.0)
        return m * m

    def dalpha_dlnTr(self, Tr: float, w: float) -> float:
        """d(alpha)/d ln(Tr) = alpha * d ln(alpha)/d ln(Tr).

        van der Waals: 0.  Redlich/Kwong: -alpha/2.  Soave-type alpha = m^2:
        -kappa sqrt(Tr) m.  Written this way (rather than as d ln alpha /
        d ln Tr) it stays finite when alpha goes to zero.
        """
        if self.key == "vdw":
            return 0.0
        if self.key == "rk":
            return -0.5 * Tr ** -0.5
        kappa = _kappa_srk(w) if self.key == "srk" else _kappa_pr(w)
        m = max(self._m(Tr, w), 0.0)
        return -kappa * math.sqrt(Tr) * m

    def alpha_faded(self, Tr: float, w: float) -> bool:
        return self.key in ("srk", "pr") and self._m(Tr, w) <= 0.0


CUBIC: Dict[str, CubicEOS] = {
    "vdw": CubicEOS("vdw", 0.0, 0.0, 1.0 / 8.0, 27.0 / 64.0, 3.0 / 8.0),
    "rk": CubicEOS("rk", 1.0, 0.0, 0.08664, 0.42748, 1.0 / 3.0),
    "srk": CubicEOS("srk", 1.0, 0.0, 0.08664, 0.42748, 1.0 / 3.0),
    "pr": CubicEOS("pr", 1.0 + SQRT2, 1.0 - SQRT2, 0.07780, 0.45724, 0.30740),
}


def _real_cubic_roots(c2: float, c1: float, c0: float) -> List[float]:
    """Real roots of z^3 + c2 z^2 + c1 z + c0 = 0, ascending, Newton-polished."""
    shift = c2 / 3.0
    p = c1 - c2 * c2 / 3.0
    q = 2.0 * c2 ** 3 / 27.0 - c2 * c1 / 3.0 + c0
    disc = q * q / 4.0 + p ** 3 / 27.0
    if disc > 1e-14:
        s = math.sqrt(disc)
        u = math.copysign(abs(-q / 2.0 + s) ** (1.0 / 3.0), -q / 2.0 + s)
        v = math.copysign(abs(-q / 2.0 - s) ** (1.0 / 3.0), -q / 2.0 - s)
        roots = [u + v - shift]
    elif p >= 0:  # triple root
        roots = [-shift]
    else:
        r = math.sqrt(-p / 3.0)
        arg = max(-1.0, min(1.0, 3.0 * q / (2.0 * p * r)))
        phi = math.acos(arg)
        roots = [2.0 * r * math.cos((phi - 2.0 * math.pi * k) / 3.0) - shift for k in range(3)]

    polished = []
    for z in roots:
        for _ in range(60):
            f = ((z + c2) * z + c1) * z + c0
            df = (3.0 * z + 2.0 * c2) * z + c1
            if df == 0:
                break
            step = f / df
            z -= step
            if abs(step) < 1e-15 * max(1.0, abs(z)):
                break
        polished.append(z)
    polished.sort()
    unique = []
    for z in polished:
        if not unique or abs(z - unique[-1]) > 1e-9:
            unique.append(z)
    return unique


def cubic_Z_roots(model: str, Tr: float, Pr: float, w: float) -> List[float]:
    """Physically meaningful compressibility-factor roots (Z > beta), ascending.

    The smallest is the liquid-like root and the largest the vapour-like root.
    """
    eos = CUBIC[model]
    beta = eos.Omega * Pr / Tr
    q = eos.Psi * eos.alpha(Tr, w) / (eos.Omega * Tr)
    e, s = eos.epsilon, eos.sigma
    # (Z - 1 - beta)(Z + e*beta)(Z + s*beta) + q*beta*(Z - beta) = 0
    c2 = (e + s) * beta - 1.0 - beta
    c1 = e * s * beta * beta - (1.0 + beta) * (e + s) * beta + q * beta
    c0 = -(1.0 + beta) * e * s * beta * beta - q * beta * beta
    return [z for z in _real_cubic_roots(c2, c1, c0) if z > beta + 1e-12]


def _cubic_properties(model: str, Z: float, Tr: float, Pr: float, w: float):
    """(H^R/RT, S^R/R, ln phi) for a given root Z of a cubic EOS."""
    eos = CUBIC[model]
    beta = eos.Omega * Pr / Tr
    q = eos.Psi * eos.alpha(Tr, w) / (eos.Omega * Tr)
    # q * d ln(alpha)/d ln(Tr), formed from d(alpha)/d ln(Tr) so it is finite at alpha = 0
    q_slope = eos.Psi * eos.dalpha_dlnTr(Tr, w) / (eos.Omega * Tr)
    e, s = eos.epsilon, eos.sigma
    if abs(s - e) < 1e-12:
        I = beta / (Z + e * beta)
    else:
        I = math.log((Z + s * beta) / (Z + e * beta)) / (s - e)
    hr_rt = Z - 1.0 + (q_slope - q) * I
    sr_r = math.log(Z - beta) + q_slope * I
    lnphi = Z - 1.0 - math.log(Z - beta) - q * I
    return hr_rt, sr_r, lnphi


# ---------------------------------------------------------------------------
# Generalized virial-coefficient correlation
# ---------------------------------------------------------------------------
def quantum_effective_critical(T: float, molar_mass: float):
    """Temperature-dependent effective critical constants for hydrogen
    (SVN Sec. 3.7, generalized correlations for quantum gases).
    To be used with an acentric factor of zero."""
    Tc = 43.6 / (1.0 + 21.8 / (molar_mass * T))
    Pc = 20.5 / (1.0 + 44.2 / (molar_mass * T))
    return Tc, Pc


def virial_B(T: float, Tc: float, Pc: float, w: float) -> float:
    """Second virial coefficient B in cm^3/mol from the Pitzer correlation."""
    Tr = T / Tc
    B0 = 0.083 - 0.422 / Tr ** 1.6
    B1 = 0.139 - 0.172 / Tr ** 4.2
    return R_CM3_BAR * Tc / Pc * (B0 + w * B1)


# Derivatives of B0 and B1.  SVN prints them as 0.675/Tr^2.6 and 0.722/Tr^5.2,
# which are the exact derivatives 0.422*1.6 = 0.6752 and 0.172*4.2 = 0.7224
# rounded to three figures. With the rounded constants H^R and S^R disagree
# with ln(phi) by up to 0.06 % (the Gibbs-Helmholtz check in audit.py detects
# it), so the unrounded values are used here.
DB0_COEFF = 0.422 * 1.6
DB1_COEFF = 0.172 * 4.2


def safe_exp(x: float) -> float:
    """exp(x) that returns infinity instead of raising for very large x."""
    return math.exp(x) if x < 700.0 else math.inf


def _virial_B_and_slope(sp: Species, T: float):
    """B (cm^3/mol) and dB/dT (cm^3/mol/K) for a species."""
    crit = sp.critical
    if sp.id == "H2(g)":
        def B_of(t):
            tc, pc = quantum_effective_critical(t, crit.molar_mass)
            return virial_B(t, tc, pc, 0.0)
        h = 1e-4 * T
        return B_of(T), (B_of(T + h) - B_of(T - h)) / (2.0 * h)
    Tr = T / crit.Tc
    dB0 = DB0_COEFF / Tr ** 2.6
    dB1 = DB1_COEFF / Tr ** 5.2
    B = virial_B(T, crit.Tc, crit.Pc, crit.omega)
    dBdT = R_CM3_BAR / crit.Pc * (dB0 + crit.omega * dB1)
    return B, dBdT


# ---------------------------------------------------------------------------
# Vapour pressure estimate (used only to warn about condensation)
# ---------------------------------------------------------------------------
def psat_estimate(sp: Species, T: float) -> Optional[float]:
    """Saturation pressure in bar from the Lee/Kesler vapour-pressure
    correlation (SVN Sec. 6.5), or None above the critical temperature.

    It is a corresponding-states estimate (good for non-polar fluids, within
    roughly 10 % for water), so it is used for warnings and never inside a
    property calculation.
    """
    crit = sp.critical
    if crit is None or T >= crit.Tc:
        return None
    Tr = T / crit.Tc
    ln_pr0 = 5.92714 - 6.09648 / Tr - 1.28862 * math.log(Tr) + 0.169347 * Tr ** 6
    ln_pr1 = 15.2518 - 15.6875 / Tr - 13.4721 * math.log(Tr) + 0.43577 * Tr ** 6
    return crit.Pc * math.exp(ln_pr0 + crit.omega * ln_pr1)


# ---------------------------------------------------------------------------
# Residual properties of one pure species
# ---------------------------------------------------------------------------
@dataclass
class Residual:
    species: str
    model: str
    T: float
    P: float
    Tr: Optional[float] = None
    Pr: Optional[float] = None
    Z: float = 1.0
    HR: float = 0.0        # J/mol
    SR: float = 0.0        # J/(mol K)
    lnphi: float = 0.0
    treated_ideal: bool = False
    # "vapour": an ordinary gas state.
    # "hypothetical_vapour": above the vapour pressure, but the model still has
    #     a vapour-like state (the metastable root of a cubic, or the virial
    #     extrapolation). This is the state the ideal-solution rule needs for
    #     a species that is dilute in a gas mixture.
    # "liquid_like": the cubic equation has only a liquid root here, so there
    #     is no gas-phase value at all.
    state: str = "vapour"
    notes: List[dict] = field(default_factory=list)

    @property
    def phi(self) -> float:
        return safe_exp(self.lnphi)

    @property
    def GR(self) -> float:
        return R * self.T * self.lnphi

    def to_dict(self) -> dict:
        return {
            "species": self.species, "model": self.model, "T": self.T, "P": self.P,
            "Tr": self.Tr, "Pr": self.Pr, "Z": self.Z, "HR": self.HR, "SR": self.SR,
            "GR": self.GR, "lnphi": self.lnphi, "phi": self.phi,
            "treated_ideal": self.treated_ideal, "state": self.state, "notes": self.notes,
        }


def _check_TP(T: float, P: float) -> None:
    for label, value in (("Temperature", T), ("Pressure", P)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise InputError(f"{label} must be a number.")
    if T <= 0:
        raise InputError("Temperature must be above 0 K.")
    if P <= 0:
        raise InputError("Pressure must be above 0 bar (absolute pressure).")


def residual(sp: Species, T: float, P: float, model: str = "pr") -> Residual:
    """Residual properties of the pure species at T (K) and P (bar).

    Condensed phases and gases without critical constants in SVN Table B.1 are
    returned with zero residuals and an explanatory note.
    """
    _check_TP(T, P)
    if model not in MODEL_NAMES:
        raise InputError(f"Unknown real-gas model '{model}'. Choose from: {', '.join(MODEL_NAMES)}.")
    res = Residual(sp.id, model, T, P)

    if sp.phase != "g":
        res.treated_ideal = True
        res.notes.append({
            "level": "info", "species": sp.id, "kind": "condensed",
            "message": (
                f"{sp.id} is a condensed phase. Its enthalpy and entropy change very little "
                f"with pressure, so no pressure correction is applied (activity = 1)."
            ),
        })
        return res
    if model == "ideal":
        res.treated_ideal = True
        return res
    crit = sp.critical
    if crit is None:
        res.treated_ideal = True
        res.notes.append({
            "level": "warning", "species": sp.id, "kind": "no_critical_data",
            "message": (
                f"{sp.id} has no critical constants in SVN Table B.1, so it is treated as an "
                f"ideal gas (zero residual properties)."
            ),
        })
        return res

    res.Tr = T / crit.Tc
    res.Pr = P / crit.Pc

    if model == "virial":
        B, dBdT = _virial_B_and_slope(sp, T)
        res.Z = 1.0 + B * P / (R_CM3_BAR * T)
        res.lnphi = B * P / (R_CM3_BAR * T)
        # H^R = P (B - T dB/dT),  S^R = -P dB/dT ; cm^3 bar -> J is a factor 0.1
        res.HR = 0.1 * P * (B - T * dBdT)
        res.SR = -0.1 * P * dBdT
        Vr = res.Z * R_CM3_BAR * T / (P * crit.Vc) if res.Z > 0 else 0.0
        if Vr < 2.0:
            res.notes.append({
                "level": "warning", "species": sp.id, "kind": "virial_range",
                "message": (
                    f"{sp.id}: reduced volume V/Vc = {Vr:.2f} is below 2. The virial equation "
                    f"truncated after B is only reliable at low to moderate pressure; use a "
                    f"cubic equation of state here."
                ),
            })
        if sp.id == "H2(g)":
            res.notes.append({
                "level": "info", "species": sp.id, "kind": "quantum_gas",
                "message": (
                    "H2 is a quantum gas: the virial correlation uses the temperature-dependent "
                    "effective critical constants of SVN Sec. 3.7 with omega = 0."
                ),
            })
    else:
        eos = CUBIC[model]
        if eos.alpha_faded(res.Tr, crit.omega):
            res.notes.append({
                "level": "info", "species": sp.id, "kind": "alpha_range",
                "message": (
                    f"{sp.id}: at Tr = {res.Tr:.1f} the alpha function of the {MODEL_NAMES[model]} "
                    f"equation has fallen to zero, so only the repulsive (co-volume) term is left."
                ),
            })
        roots = cubic_Z_roots(model, res.Tr, res.Pr, crit.omega)
        if not roots:
            raise InputError(f"The {MODEL_NAMES[model]} equation has no physical root for {sp.id}.")
        Z = roots[-1]  # vapour-like root
        hr_rt, sr_r, lnphi = _cubic_properties(model, Z, res.Tr, res.Pr, crit.omega)
        res.Z, res.HR, res.SR, res.lnphi = Z, R * T * hr_rt, R * sr_r, lnphi
        if len(roots) > 1:
            _, _, lnphi_liq = _cubic_properties(model, roots[0], res.Tr, res.Pr, crit.omega)
            if lnphi_liq < lnphi:
                res.state = "hypothetical_vapour"
                res.notes.append({
                    "level": "info", "species": sp.id, "kind": "condensation",
                    "message": (
                        f"{sp.id}: on its own this species would be a liquid at {T:g} K and {P:g} bar "
                        f"(the {MODEL_NAMES[model]} equation gives its liquid the lower Gibbs energy). "
                        f"In a reactor it is diluted by the other gases and stays a vapour, so the "
                        f"values shown are for the vapour-like state of the equation."
                    ),
                })
        elif T < crit.Tc and Z * res.Tr / res.Pr < eos.Zc:
            # Below Tc with a single root, the equation itself decides what the
            # root is: its molar volume V*Pc/(R*Tc) = Z*Tr/Pr is compared with
            # the critical volume the same equation predicts (Zc). Smaller
            # means the dense, liquid branch. No outside correlation is used.
            res.state = "liquid_like"
            res.notes.append({
                "level": "error", "species": sp.id, "kind": "no_vapour_root",
                "message": (
                    f"{sp.id}: at {T:g} K and {P:g} bar the {MODEL_NAMES[model]} equation has only "
                    f"a liquid root (Z = {Z:.3f}). The number shown belongs to a liquid, so it "
                    f"must not be used for a gas-phase reaction."
                ),
            })

    psat = psat_estimate(sp, T)
    already = any(n["kind"] in ("condensation", "no_vapour_root") for n in res.notes)
    if psat is not None and P > psat and not already:
        res.state = "hypothetical_vapour"
        res.notes.append({
            "level": "info", "species": sp.id, "kind": "condensation",
            "message": (
                f"{sp.id}: {P:g} bar is above its estimated vapour pressure at {T:g} K "
                f"(about {psat:.3g} bar, Lee/Kesler correlation), so on its own it would be a liquid. "
                f"In a reactor it is diluted by the other gases and stays a vapour, so the values "
                f"shown are for that vapour-like state."
            ),
        })
    return res


def require_vapour(res: Residual) -> None:
    """Raise if a residual result is not usable for a gas-phase calculation."""
    if res.state == "liquid_like":
        raise PhaseError(
            f"{res.species} has no vapour-like state at {res.T:g} K and {res.P:g} bar with the "
            f"{MODEL_NAMES[res.model]} equation (the pure species is a liquid there), so a "
            f"gas-phase equilibrium cannot be calculated. Lower the pressure, raise the "
            f"temperature, or use the ideal-gas or virial model.",
            {"species": res.species},
        )


def compare_models(sp: Species, T: float, P: float) -> List[dict]:
    """Residual properties of one species from every model, for side-by-side display."""
    return [residual(sp, T, P, m).to_dict() for m in ("virial", "vdw", "rk", "srk", "pr")]


# ---------------------------------------------------------------------------
# Effect of pressure on a reaction at constant temperature
# ---------------------------------------------------------------------------
def reaction_at_pressure(rxn, T: float, P: float, model: str = "pr") -> dict:
    """Property changes of reaction when every reactant and product is the
    pure species at T and P (real gas), instead of the 1-bar standard state.

        dH(T,P) = dH0(T) + sum nu_i H_i^R(T,P)
        dS(T,P) = dS0(T) - R * dn_gas * ln(P/P0) + sum nu_i S_i^R(T,P)
        dG(T,P) = dH(T,P) - T dS(T,P) = dG0(T) + R T sum_gas nu_i ln(phi_i P/P0)

    Sums run over the gaseous species; condensed phases are taken as
    incompressible with negligible pressure dependence.
    """
    _check_TP(T, P)
    std = rxn.evaluate(T)
    rows = []
    notes: List[dict] = []
    no_vapour: List[str] = []
    sum_HR = sum_SR = sum_lnphi = 0.0
    for sid, nu in rxn.stoich.items():
        sp = SPECIES[sid]
        res = residual(sp, T, P, model)
        if res.state == "liquid_like":
            no_vapour.append(sid)
        sum_HR += nu * res.HR
        sum_SR += nu * res.SR
        sum_lnphi += nu * res.lnphi
        row = res.to_dict()
        row.update({"nu": nu, "name": sp.name, "phase": sp.phase})
        rows.append(row)
        for n in res.notes:
            if n not in notes:
                notes.append(n)

    dn = rxn.delta_n_gas
    ln_p = math.log(P / P0)
    dH_P = std["dH"] + sum_HR
    dS_ig = std["dS"] - R * dn * ln_p
    dS_P = dS_ig + sum_SR
    dG_ig = std["dG"] + R * T * dn * ln_p
    dG_P = dH_P - T * dS_P
    lnK = std["lnK"]
    # Equilibrium in mole fractions:  prod(y_i^nu_i) = K * (P/P0)^(-dn) / prod(phi_i^nu_i)
    lnKy = lnK - dn * ln_p - sum_lnphi
    return {
        "T": T, "P": P, "model": model, "model_name": MODEL_NAMES[model],
        "species": rows, "notes": notes,
        # False when some species has only a liquid root: the sums below then
        # mix a liquid into a gas-phase calculation and must not be trusted.
        "gas_phase_valid": not no_vapour,
        "no_vapour_species": no_vapour,
        "delta_n_gas": dn,
        "dH_std": std["dH"], "dS_std": std["dS"], "dG_std": std["dG"], "lnK": lnK,
        "sum_HR": sum_HR, "sum_SR": sum_SR, "sum_lnphi": sum_lnphi,
        "K_phi": safe_exp(sum_lnphi),
        "dH_P": dH_P,
        "dS_ig_P": dS_ig, "dS_P": dS_P,
        "dG_ig_P": dG_ig, "dG_P": dG_P,
        "lnKy": lnKy,
        "log10Ky": lnKy / math.log(10.0),
    }


def pressure_sweep(rxn, T: float, pressures: Sequence[float], model: str = "pr") -> dict:
    """dH(T,P), dS(T,P), dG(T,P) along an isotherm."""
    keys = ("dH_P", "sum_HR", "dS_P", "sum_SR", "dG_P", "dG_ig_P", "lnKy", "K_phi")
    out = {"T": T, "model": model, "P": list(pressures), "gas_phase_valid": []}
    out.update({k: [] for k in keys})
    species_HR: Dict[str, List[Optional[float]]] = {sid: [] for sid in rxn.stoich}
    species_Z: Dict[str, List[Optional[float]]] = {sid: [] for sid in rxn.stoich}
    first_invalid = None
    for P in pressures:
        point = reaction_at_pressure(rxn, T, P, model)
        valid = point["gas_phase_valid"]
        out["gas_phase_valid"].append(valid)
        if not valid and first_invalid is None:
            first_invalid = P
        for k in keys:
            # No gas-phase value exists once a species has only a liquid root.
            out[k].append(point[k] if valid else None)
        for row in point["species"]:
            usable = row["state"] != "liquid_like"
            species_HR[row["species"]].append(row["HR"] if usable else None)
            species_Z[row["species"]].append(row["Z"] if usable else None)
    out["species_HR"] = species_HR
    out["species_Z"] = species_Z
    out["dH_std"] = rxn.dH(T)
    out["first_invalid_P"] = first_invalid
    return out
