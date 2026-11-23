"""Chemical equilibrium (SVN chemical-reaction-equilibria chapter).

Two calculations are provided.

1. ``reaction_equilibrium`` - one reaction, reaction-coordinate method.
   With n_i = n_i0 + nu_i * eps the equilibrium condition is

        prod_gas (y_i * phi_i)^nu_i = K * (P/P0)^(-nu_gas)

   (pure solids and liquids have unit activity). It is solved for eps by
   bisection; the left side increases monotonically with eps.

2. ``gibbs_minimize`` - any number of simultaneous reactions, by direct
   minimisation of the total Gibbs energy (SVN's Lagrange-multiplier method).
   For a gas mixture of N species made of w elements:

        G/RT = sum_i n_i [ G_i(T)/RT + ln(y_i * phi_i * P/P0) ]
        subject to  sum_i n_i a_ik = A_k     (atoms of element k are conserved)

   Stationarity gives, for every species,
        G_i/RT + ln(y_i phi_i P/P0) = sum_k pi_k a_ik
   where pi_k are the Lagrange multipliers (element potentials divided by RT).
   No list of reactions is needed: the species list alone decides what can
   form. The equations are solved by Newton's method in ln(n_i), the scheme
   used in NASA's CEA code, which keeps every mole number positive.

Fugacity coefficients phi_i are those of the pure species at T and P
(ideal-solution / Lewis-Randall assumption), or 1 for the ideal-gas model.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

from .constants import P0, R
from .errors import ConvergenceError, InputError
from .realgas import require_vapour, residual
from .species import SPECIES, find_species


# ---------------------------------------------------------------------------
# Small dense linear solver (Gaussian elimination with partial pivoting)
# ---------------------------------------------------------------------------
def solve_linear(matrix: List[List[float]], rhs: List[float]) -> List[float]:
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-300:
            raise ConvergenceError("The equilibrium calculation could not be solved for this set of species.")
        a[col], a[pivot] = a[pivot], a[col]
        pv = a[col][col]
        for r in range(col + 1, n):
            factor = a[r][col] / pv
            if factor != 0.0:
                for c in range(col, n + 1):
                    a[r][c] -= factor * a[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = a[i][n] - sum(a[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / a[i][i]
    return x


def _independent_rows(rows: List[List[float]]) -> List[int]:
    """Indices of a maximal set of linearly independent rows."""
    work = [r[:] for r in rows]
    chosen: List[int] = []
    basis: List[List[float]] = []
    for idx, row in enumerate(work):
        v = row[:]
        for b in basis:
            lead = next(i for i, x in enumerate(b) if abs(x) > 1e-12)
            if abs(v[lead]) > 1e-12:
                f = v[lead] / b[lead]
                v = [x - f * y for x, y in zip(v, b)]
        if any(abs(x) > 1e-9 for x in v):
            basis.append(v)
            chosen.append(idx)
    return chosen


MAX_FEED = 1e9      # mol; far beyond any real basis, and safe from overflow


def _clean_feed(feed: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for key, moles in feed.items():
        sp, _ = find_species(str(key))
        if not isinstance(moles, (int, float)) or isinstance(moles, bool) or not math.isfinite(moles):
            raise InputError(f"The feed amount of {sp.id} must be a number.")
        if moles < 0:
            raise InputError(f"The feed amount of {sp.id} cannot be negative.")
        if moles > MAX_FEED:
            raise InputError(f"The feed amount of {sp.id} must be at most {MAX_FEED:g} mol.")
        if moles > 0:
            out[sp.id] = out.get(sp.id, 0.0) + float(moles)
    return out


# ---------------------------------------------------------------------------
# 1. Single reaction
# ---------------------------------------------------------------------------
def reaction_equilibrium(rxn, T: float, P: float = P0,
                         feed: Optional[Dict[str, float]] = None, model: str = "ideal") -> dict:
    """Equilibrium extent of one reaction at T (K) and P (bar).

    ``feed`` maps species to moles and may contain inerts. If omitted, the
    reactants are fed in stoichiometric proportion (|nu_i| moles each).
    """
    if isinstance(P, bool) or not isinstance(P, (int, float)) or not math.isfinite(P) or P <= 0:
        raise InputError("Pressure must be above 0 bar.")
    lnK = rxn.lnK(T)
    if feed:
        n0 = _clean_feed(feed)
    else:
        n0 = {sid: -nu for sid, nu in rxn.stoich.items() if nu < 0}
    for sid in rxn.stoich:
        n0.setdefault(sid, 0.0)
    if not any(n0[s] > 0 for s in rxn.reactant_ids) and not any(n0[s] > 0 for s in rxn.product_ids):
        raise InputError("The feed contains none of the species of this reaction.")

    gas = [sid for sid in n0 if SPECIES[sid].phase == "g"]
    lnphi: Dict[str, float] = {}
    notes: List[dict] = []
    for sid in gas:
        if sid not in rxn.stoich:
            continue                     # an inert only dilutes; its fugacity coefficient is never used
        res = residual(SPECIES[sid], T, P, model)
        require_vapour(res)              # a liquid root must never enter a gas-phase equilibrium
        lnphi[sid] = res.lnphi
        for note in res.notes:
            if note not in notes:
                notes.append(note)

    # Extent bounds: every mole number must stay >= 0
    eps_hi = min(n0[s] / -nu for s, nu in rxn.stoich.items() if nu < 0)
    eps_lo = max(-n0[s] / nu for s, nu in rxn.stoich.items() if nu > 0)
    dn = rxn.delta_n_gas
    ln_p = math.log(P / P0)

    def moles(eps: float) -> Dict[str, float]:
        return {sid: n0[sid] + rxn.stoich.get(sid, 0.0) * eps for sid in n0}

    def f(eps: float) -> float:
        n = moles(eps)
        n_gas = sum(n[s] for s in gas)
        total = dn * ln_p - lnK
        for sid, nu in rxn.stoich.items():
            if sid not in lnphi:
                continue
            if n[sid] <= 0.0:
                return -math.inf if nu > 0 else math.inf
            total += nu * (math.log(n[sid] / n_gas) + lnphi[sid])
        return total

    span = eps_hi - eps_lo
    status = "equilibrium"
    if span <= 0:
        eps = eps_lo
        status = "no_reaction_possible"
    else:
        a = eps_lo + 1e-13 * span
        b = eps_hi - 1e-13 * span
        fa, fb = f(a), f(b)
        if fa >= 0:
            # Even at the lowest possible extent the products are in excess.
            # With no product in the feed that means nothing reacts; with
            # products in the feed the reaction has run fully in reverse.
            eps = eps_lo
            status = "complete_reverse" if eps_lo < 0 else "no_forward_reaction"
        elif fb <= 0:
            eps, status = eps_hi, "complete"
        else:
            for _ in range(200):
                mid = 0.5 * (a + b)
                if f(mid) < 0:
                    a = mid
                else:
                    b = mid
            eps = 0.5 * (a + b)

    n = moles(eps)
    n_gas = sum(n[s] for s in gas)
    y = {s: (n[s] / n_gas if n_gas > 0 else 0.0) for s in gas}

    limiting = None
    conversion = None
    fed_reactants = [s for s in rxn.reactant_ids if n0[s] > 0]
    if fed_reactants:
        limiting = min(fed_reactants, key=lambda s: n0[s] / -rxn.stoich[s])
        conversion = (n0[limiting] - n[limiting]) / n0[limiting]

    sum_lnphi = sum(nu * lnphi.get(sid, 0.0) for sid, nu in rxn.stoich.items())
    return {
        "T": T, "P": P, "model": model, "status": status,
        "lnK": lnK, "lnKy_required": lnK - dn * ln_p - sum_lnphi,
        "extent": eps, "extent_max": eps_hi, "extent_min": eps_lo,
        "feed": n0, "moles": n, "y": y,
        "limiting_reactant": limiting, "conversion": conversion,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# 2. Gibbs-energy minimisation
# ---------------------------------------------------------------------------
def gibbs_minimize(species_ids: Sequence[str], feed: Dict[str, float], T: float, P: float = P0,
                   model: str = "ideal", g_rt_override: Optional[Dict[str, float]] = None,
                   max_iter: int = 2000, tol: float = 1e-12) -> dict:
    """Equilibrium composition of a gas mixture by Gibbs-energy minimisation.

    species_ids : the gaseous species allowed to exist at equilibrium
    feed        : {species: moles} of the feed (fixes the element totals)
    g_rt_override : optional {species: G_i/RT} to use instead of the database
                    (used to reproduce textbook examples that quote their own
                    Gibbs energies of formation at T)
    """
    for label, value in (("Temperature", T), ("Pressure", P)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise InputError(f"{label} must be a positive number.")
    n_feed = _clean_feed(feed)
    if not n_feed:
        raise InputError("The feed is empty: give a positive amount of at least one species.")

    ids: List[str] = []
    for key in list(species_ids) + list(n_feed):
        sp, _ = find_species(key)
        if sp.id not in ids:
            ids.append(sp.id)
    for sid in ids:
        if SPECIES[sid].phase != "g":
            raise InputError(
                f"{sid} is not a gas. The product slate works with a gas mixture only; "
                f"for solid carbon it reports whether it can form."
            )
    if len(ids) < 2:
        raise InputError("Choose at least two species for an equilibrium calculation.")

    elements = sorted({el for sid in ids for el in SPECIES[sid].elements})
    b_all = {el: sum(SPECIES[s].elements.get(el, 0) * n for s, n in n_feed.items()) for el in elements}

    # Species containing an element that is absent from the feed cannot form.
    absent = [el for el in elements if b_all[el] <= 0.0]
    excluded = [sid for sid in ids if any(el in SPECIES[sid].elements for el in absent)]
    active = [sid for sid in ids if sid not in excluded]
    act_elements = [el for el in elements if el not in absent]

    rows = [[float(SPECIES[s].elements.get(el, 0)) for s in active] for el in act_elements]
    keep = _independent_rows(rows)
    el_used = [act_elements[i] for i in keep]
    a = [rows[i] for i in keep]                      # a[k][j], element k, species j
    b = [b_all[el] for el in el_used]
    m, ns = len(el_used), len(active)

    notes: List[dict] = []
    g_const = []
    ln_p = math.log(P / P0)
    for sid in active:
        sp = SPECIES[sid]
        res = residual(sp, T, P, model)
        require_vapour(res)
        for note in res.notes:
            if note not in notes:
                notes.append(note)
        if g_rt_override and sid in g_rt_override:
            g0 = g_rt_override[sid]
        else:
            g0 = sp.G(T) / (R * T)
        g_const.append(g0 + ln_p + res.lnphi)

    total_feed = sum(n_feed.values())
    ln_n = [math.log(total_feed / ns)] * ns
    ln_N = math.log(total_feed)
    converged = False
    iterations = 0
    pi = [0.0] * m

    for iterations in range(1, max_iter + 1):
        n = [math.exp(v) for v in ln_n]
        N = math.exp(ln_N)
        mu = [g_const[j] + ln_n[j] - ln_N for j in range(ns)]
        sum_n = sum(n)

        matrix = [[0.0] * (m + 1) for _ in range(m + 1)]
        rhs = [0.0] * (m + 1)
        for i in range(m):
            for k in range(m):
                matrix[i][k] = sum(a[i][j] * a[k][j] * n[j] for j in range(ns))
            bi = sum(a[i][j] * n[j] for j in range(ns))
            matrix[i][m] = bi
            matrix[m][i] = bi
            rhs[i] = b[i] - bi + sum(a[i][j] * n[j] * mu[j] for j in range(ns))
        matrix[m][m] = sum_n - N
        rhs[m] = N - sum_n + sum(n[j] * mu[j] for j in range(ns))

        sol = solve_linear(matrix, rhs)
        pi, dlnN = sol[:m], sol[m]
        dln = [sum(a[k][j] * pi[k] for k in range(m)) + dlnN - mu[j] for j in range(ns)]

        # Step-size control (keeps the Newton step inside its region of validity)
        big = 5.0 * abs(dlnN)
        lam2 = 1.0
        for j in range(ns):
            frac = ln_n[j] - ln_N
            if frac > -18.420681:               # n_j/N > 1e-8
                big = max(big, abs(dln[j]))
            elif dln[j] > 0:
                denom = dln[j] - dlnN
                if denom > 0:
                    lam2 = min(lam2, abs((-frac - 9.2103404) / denom))
        lam = min(1.0, lam2, 2.0 / big if big > 0 else 1.0)

        for j in range(ns):
            ln_n[j] = max(ln_n[j] + lam * dln[j], ln_N - 690.0)
        ln_N += lam * dlnN

        change = max(n[j] * abs(dln[j]) for j in range(ns)) / sum_n
        change = max(change, N * abs(dlnN) / sum_n)
        el_err = max(abs(b[i] - sum(a[i][j] * n[j] for j in range(ns))) for i in range(m)) / max(b)
        if change < tol and el_err < 1e-10 and lam == 1.0:
            converged = True
            break

    if not converged:
        raise ConvergenceError(
            "The search for the mixture with the lowest Gibbs energy did not settle on an answer. "
            "Try a different temperature or remove species that cannot realistically form.",
            {"iterations": iterations},
        )

    n = [math.exp(v) for v in ln_n]
    N = sum(n)
    moles = {sid: 0.0 for sid in ids}
    moles.update({sid: n[j] for j, sid in enumerate(active)})
    y = {sid: moles[sid] / N for sid in ids}
    g_total = sum(n[j] * (g_const[j] + math.log(n[j] / N)) for j in range(ns))
    kkt = max(
        abs(g_const[j] + math.log(n[j] / N) - sum(a[k][j] * pi[k] for k in range(m)))
        for j in range(ns) if n[j] / N > 1e-25
    )
    element_potentials = {el: pi[k] for k, el in enumerate(el_used)}

    # Would graphite form?  a_C = exp(pi_C - G_graphite/RT).  a_C > 1 means the
    # gas is supersaturated in carbon, i.e. coke deposition is thermodynamically
    # favoured. Only meaningful when the carbon balance is an independent constraint.
    # Skipped when the caller supplied its own G/RT values: those are on a
    # different reference scale from the database value used for graphite.
    carbon_activity = None
    if "C" in element_potentials and len(el_used) == len(act_elements) and not g_rt_override:
        graphite = SPECIES["C(s)"]
        exponent = element_potentials["C"] - graphite.G(T) / (R * T)
        carbon_activity = math.exp(exponent) if exponent < 700 else math.inf

    conversions = {}
    for sid, nf in n_feed.items():
        conversions[sid] = (nf - moles[sid]) / nf

    return {
        "T": T, "P": P, "model": model,
        "species": ids, "feed": {sid: n_feed.get(sid, 0.0) for sid in ids},
        "moles": moles, "y": y, "total_moles": N,
        "G_over_RT": g_total,
        "elements": {el: b_all[el] for el in elements},
        "element_potentials": element_potentials,
        "carbon_activity": carbon_activity,
        "conversions": conversions,
        "excluded": excluded,
        "iterations": iterations,
        "kkt_residual": kkt,
        "notes": notes,
    }


def atom_distribution(result: dict, element: str) -> Dict[str, float]:
    """Fraction of the atoms of ``element`` found in each species at equilibrium.
    For carbon this is the usual carbon-based product distribution."""
    amounts = {
        sid: SPECIES[sid].elements.get(element, 0) * n for sid, n in result["moles"].items()
    }
    total = sum(amounts.values())
    if total <= 0:
        return {}
    return {sid: v / total for sid, v in amounts.items() if SPECIES[sid].elements.get(element, 0)}
