"""Chemical-formula parsing: 'Ca(OH)2' -> {'Ca': 1, 'O': 2, 'H': 2}.

The element counts are what the solver uses to verify that a reaction is
balanced before any thermodynamics is done.
"""

from __future__ import annotations

import re
from typing import Dict

from .constants import ATOMIC_WEIGHTS
from .errors import InputError

_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)|(\()|\)(\d*)")
_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def parse_formula(formula: str) -> Dict[str, int]:
    """Return the number of atoms of each element in ``formula``.

    Supports nested parentheses, e.g. ``(CH2)2O`` or ``Ca(OH)2``.
    """
    text = formula.translate(_SUBSCRIPTS).replace(" ", "")
    if not text:
        raise InputError("Empty chemical formula.")

    stack = [{}]
    pos = 0
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if match is None:
            raise InputError(
                f"Cannot read the chemical formula '{formula}' "
                f"(problem at '{text[pos:]}')."
            )
        element, count, open_paren = match.group(1), match.group(2), match.group(3)
        if element:
            if element not in ATOMIC_WEIGHTS:
                raise InputError(
                    f"Element '{element}' in '{formula}' is not in the solver's element list "
                    f"({', '.join(sorted(ATOMIC_WEIGHTS))})."
                )
            n = int(count) if count else 1
            stack[-1][element] = stack[-1].get(element, 0) + n
        elif open_paren:
            stack.append({})
        else:  # closing parenthesis, group(4) is the multiplier
            if len(stack) == 1:
                raise InputError(f"Unmatched ')' in the chemical formula '{formula}'.")
            mult = int(match.group(4)) if match.group(4) else 1
            group = stack.pop()
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * mult
        pos = match.end()

    if len(stack) != 1:
        raise InputError(f"Unmatched '(' in the chemical formula '{formula}'.")
    return stack[0]


def molar_mass(formula: str) -> float:
    """Molar mass in g/mol from standard atomic weights."""
    return sum(ATOMIC_WEIGHTS[el] * n for el, n in parse_formula(formula).items())
