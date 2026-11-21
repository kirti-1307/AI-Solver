"""Building a new reaction by adding and subtracting known reactions (Hess's law).

Enthalpy, entropy and Gibbs energy are state functions, so if a target
reaction is the linear combination

        target = sum_j m_j * (reaction j)        (m_j < 0 reverses reaction j)

then at any temperature

        dH = sum_j m_j dH_j     dS = sum_j m_j dS_j     dG = sum_j m_j dG_j
        ln K = sum_j m_j ln K_j        i.e.  K = product of K_j^m_j

This is the same rule that builds a heat of reaction from formation reactions
(SVN Sec. 4.4). The module computes the target both ways - by summing the
steps and directly from the net stoichiometry - and reports the difference,
which must be zero to round-off.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .errors import InputError
from .reaction import Reaction, format_coeff

_KEYS = ("dH0", "dG0", "dS0", "dH", "dS", "dG", "lnK")


def combine_reactions(steps: Sequence[Tuple[Reaction, float]], T: float, name: str = "") -> dict:
    """Combine ``steps`` = [(reaction, multiplier), ...] and evaluate at T (K)."""
    if len(steps) < 2:
        raise InputError("Give at least two reactions to combine.")
    net: Dict[str, float] = {}
    seen = set()
    step_rows: List[dict] = []
    sums = {k: 0.0 for k in _KEYS}

    for rxn, mult in steps:
        if not isinstance(mult, (int, float)) or isinstance(mult, bool) or abs(mult) < 1e-12:
            raise InputError("Each reaction needs a non-zero multiplier (use -1 to reverse it).")
        for sid, nu in rxn.stoich.items():
            net[sid] = net.get(sid, 0.0) + mult * nu
            seen.add(sid)
        values = rxn.evaluate(T)
        row = {
            "equation": rxn.equation,
            "name": rxn.name,
            "multiplier": mult,
            "applied": rxn.scaled(mult).equation,
        }
        for k in _KEYS:
            row[k] = values[k]
            row["m_" + k] = mult * values[k]
            sums[k] += mult * values[k]
        step_rows.append(row)

    net = {sid: nu for sid, nu in net.items() if abs(nu) > 1e-9}
    if not net:
        raise InputError("These reactions cancel each other completely; there is no net reaction.")
    cancelled = sorted(seen - set(net))
    target = Reaction(net, name)
    target.assert_balanced()          # always true if every step is balanced
    direct = target.evaluate(T)

    check = {k: {"hess": sums[k], "direct": direct[k], "difference": sums[k] - direct[k]} for k in _KEYS}
    return {
        "T": T,
        "steps": step_rows,
        "net_equation": target.equation,
        "net_stoich": dict(target.stoich),
        "cancelled_intermediates": cancelled,
        "hess": sums,
        "direct": direct,
        "check": check,
        "max_difference_J": max(abs(check[k]["difference"]) for k in ("dH", "dG", "dH0", "dG0")),
        "reaction": target,
    }


def formation_reaction(species) -> Reaction:
    """The formation reaction of a compound from its elements in their
    standard states, written for one mole of the compound."""
    from .data import ELEMENT_REFERENCE

    stoich = {species.id: 1.0}
    for el, count in species.elements.items():
        ref = ELEMENT_REFERENCE.get(el)
        if ref is None:
            raise InputError(
                f"SVN gives no heat capacity for the standard-state form of element {el}, "
                f"so the formation reaction of {species.id} cannot be built."
            )
        ref_id, atoms = ref
        if ref_id == species.id:
            raise InputError(f"{species.id} is an element in its standard state.")
        stoich[ref_id] = stoich.get(ref_id, 0.0) - count / atoms
    return Reaction(stoich, f"Formation of {species.name}")


def formation_decomposition(rxn: Reaction) -> List[dict]:
    """Write a reaction as a sum of formation reactions: the multipliers are
    simply the stoichiometric numbers of the compounds."""
    from .species import SPECIES

    rows = []
    for sid, nu in rxn.stoich.items():
        sp = SPECIES[sid]
        if sp.is_element:
            rows.append({"species": sid, "nu": nu, "is_element": True, "equation": None,
                         "dHf": 0.0, "dGf": 0.0})
            continue
        try:
            eq = formation_reaction(sp).equation
        except InputError:
            eq = None
        rows.append({"species": sid, "nu": nu, "is_element": False, "equation": eq,
                     "dHf": sp.dHf, "dGf": sp.dGf,
                     "term": f"{'+' if nu > 0 else '-'} {format_coeff(nu)} x"})
    return rows
