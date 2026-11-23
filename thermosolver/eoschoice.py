"""Which equation of state the solver uses for each gas.

The user does not pick an equation: a wrong pick would give a wrong answer
without any warning. Instead the solver compares the five equations of the
course (generalized virial correlation, van der Waals, Redlich/Kwong,
Soave/Redlich/Kwong, Peng/Robinson; SVN Chapter 3 and Sec. 6.4 and 6.7) with
measured data:

    measured   H^R(T, P) = H(T, P) - H(T, 0.01 bar)       (NIST, data.NIST_FLUID)
    error of an equation  = |H^R(equation) - H^R(measured)|

For each of the 24 gases that NIST has, the error is averaged over all its
measured points, and the gas gets the equation with the smallest average
error. A gas without measured data gets the equation with the smallest
average error over the measured points of all 24 gases together. A gas
without critical constants stays an ideal gas, as before.

The choice is made once for each gas, not for each temperature and
pressure. A gas therefore keeps one equation along a plot, so its H^R is a
smooth function of T and P, and the relations between H^R, S^R and G^R that
the test-suite checks still hold.

The comparison only uses points at which every equation describes a gas,
so that all five are judged on the same points.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Tuple

from . import data
from .species import SPECIES, Species

EQUATIONS = ("virial", "vdw", "rk", "srk", "pr")
LOW_P = 0.01          # bar, the row of each isotherm that stands for the ideal gas


@lru_cache(maxsize=None)
def measured_points(sid: str) -> Tuple[Tuple[float, float, float], ...]:
    """(T in K, P in bar, measured H^R in J/mol) of one gas, from the rows of data.NIST_FLUID."""
    _, rows = data.NIST_FLUID[sid]
    low = {T: H for T, P, H in rows if abs(P - LOW_P) < 1e-9}
    return tuple((T, P, 1000.0 * (H - low[T])) for T, P, H in rows if P > LOW_P + 1e-9 and T in low)


def _model_HR(sp: Species, T: float, P: float, model: str):
    """H^R of one equation, or None where it does not describe a gas."""
    from .realgas import residual          # imported here: realgas imports this module lazily too
    res = residual(sp, T, P, model)
    return None if res.state == "liquid_like" else res.HR


@lru_cache(maxsize=None)
def _errors(sid: str) -> Dict[str, Tuple[float, ...]]:
    """Absolute error of each equation at every measured point where all five describe a gas."""
    sp = SPECIES[sid]
    out: Dict[str, List[float]] = {m: [] for m in EQUATIONS}
    for T, P, hr in measured_points(sid):
        values = {m: _model_HR(sp, T, P, m) for m in EQUATIONS}
        if any(v is None for v in values.values()):
            continue
        for m in EQUATIONS:
            out[m].append(abs(values[m] - hr))
    return {m: tuple(v) for m, v in out.items()}


@lru_cache(maxsize=None)
def scores(sid: str) -> dict:
    """Mean and largest error of every equation for one measured gas, and the equation chosen."""
    errs = _errors(sid)
    n = len(errs["pr"])
    mean = {m: sum(e) / n for m, e in errs.items()}
    largest = {m: max(e) for m, e in errs.items()}
    best = min(EQUATIONS, key=lambda m: mean[m])
    return {"species": sid, "name": SPECIES[sid].name, "webbook_id": data.NIST_FLUID[sid][0],
            "points": n, "mean": mean, "max": largest, "best": best,
            "T_range": [min(p[0] for p in measured_points(sid)), max(p[0] for p in measured_points(sid))],
            "P_range": [min(p[1] for p in measured_points(sid)), max(p[1] for p in measured_points(sid))]}


@lru_cache(maxsize=None)
def overall() -> dict:
    """Mean error of every equation over the measured points of all gases together."""
    pooled: Dict[str, List[float]] = {m: [] for m in EQUATIONS}
    for sid in data.NIST_FLUID:
        for m, e in _errors(sid).items():
            pooled[m].extend(e)
    n = len(pooled["pr"])
    mean = {m: sum(e) / n for m, e in pooled.items()}
    return {"points": n, "gases": len(data.NIST_FLUID), "mean": mean,
            "best": min(EQUATIONS, key=lambda m: mean[m]),
            "wins": {m: sum(1 for s in data.NIST_FLUID if scores(s)["best"] == m) for m in EQUATIONS}}


def choose(sp: Species) -> Tuple[str, dict]:
    """The equation used for one species, and why.

    basis "measured": the gas has measured data; its own smallest error decides.
    basis "overall":  no measured data; the equation best over all measured gases.
    basis "no_critical": no critical constants; the gas stays ideal (as before).
    basis "condensed": a liquid or solid; no pressure correction (as before).
    """
    if sp.phase != "g":
        return "ideal", {"basis": "condensed"}
    if sp.critical is None:
        return "ideal", {"basis": "no_critical"}
    if sp.id in data.NIST_FLUID:
        s = scores(sp.id)
        ranked = sorted(EQUATIONS, key=lambda m: s["mean"][m])
        return s["best"], {"basis": "measured", "points": s["points"], "mean_error": s["mean"][s["best"]],
                           "runner_up": ranked[1], "runner_up_error": s["mean"][ranked[1]]}
    o = overall()
    return o["best"], {"basis": "overall", "points": o["points"], "gases": o["gases"],
                       "mean_error": o["mean"][o["best"]]}


def summary() -> dict:
    """Everything the Validation tab shows: each measured gas and the result over all gases."""
    rows = [scores(sid) for sid in data.NIST_FLUID]
    return {"equations": list(EQUATIONS), "rows": rows, "overall": overall(), "source": data.SOURCES["fluid_webbook"]}
