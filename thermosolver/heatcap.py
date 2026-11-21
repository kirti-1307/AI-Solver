"""Heat-capacity polynomial and its two integrals (SVN Chapter 4 and 5).

The heat capacity of every species, and the heat-capacity change of every
reaction, is written as

        Cp/R = A + B*T + C*T^2 + D*T^-2  (+ E*T^3)

The first four terms are exactly the form of SVN Tables C.1 to C.3. The
optional T^3 term is zero for every SVN species. It exists so that
correlations from other sources can be used without refitting them, in
particular the Shomate equation of the NIST Chemistry WebBook, which has a
cubic term.

The same functions serve a single species (A..E from the tables) and a whole
reaction (delta-A..delta-E). They are named after the functions SVN defines
for the same purpose:

    ICPH  = integral of (Cp/R) dT        from T0 to T      [K]
    ICPS  = integral of (Cp/R) dT/T      from T0 to T      [dimensionless]
    MCPH  = <Cp>_H / R   mean heat capacity for enthalpy
    MCPS  = <Cp>_S / R   mean heat capacity for entropy
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

Coeffs = Tuple[float, float, float, float, float]


def unpack(c: Sequence[float]) -> Coeffs:
    """(A, B, C, D, E). A four-term set (the SVN form) gets E = 0."""
    if len(c) == 5:
        return (c[0], c[1], c[2], c[3], c[4])
    if len(c) == 4:
        return (c[0], c[1], c[2], c[3], 0.0)
    raise ValueError("A heat-capacity coefficient set has four or five terms.")


def shomate_to_coeffs(a: float, b: float, c: float, d: float, e: float, R: float) -> Coeffs:
    """Convert a NIST Shomate equation to this module's form, exactly.

    Shomate:  Cp [J/(mol K)] = a + b*t + c*t^2 + d*t^3 + e/t^2,   t = T/1000
    Here:     Cp/R = A + B*T + C*T^2 + D/T^2 + E*T^3
    """
    return (a / R, b / (1e3 * R), c / (1e6 * R), e * 1e6 / R, d / (1e9 * R))


def cp_over_r(c: Sequence[float], T: float) -> float:
    """Cp/R = A + B*T + C*T^2 + D/T^2 + E*T^3."""
    A, B, C, D, E = unpack(c)
    return A + B * T + C * T * T + D / (T * T) + E * T ** 3


def icph(T0: float, T: float, c: Sequence[float]) -> float:
    """Integral of (Cp/R) dT from T0 to T, in kelvin.

    A(T-T0) + B/2 (T^2-T0^2) + C/3 (T^3-T0^3) + D (T-T0)/(T*T0) + E/4 (T^4-T0^4)
    """
    A, B, C, D, E = unpack(c)
    return (
        A * (T - T0)
        + B / 2.0 * (T * T - T0 * T0)
        + C / 3.0 * (T ** 3 - T0 ** 3)
        + D * (T - T0) / (T * T0)
        + E / 4.0 * (T ** 4 - T0 ** 4)
    )


def icps(T0: float, T: float, c: Sequence[float]) -> float:
    """Integral of (Cp/R) dT/T from T0 to T, dimensionless.

    A ln(T/T0) + B (T-T0) + C/2 (T^2-T0^2) + D/2 (1/T0^2 - 1/T^2) + E/3 (T^3-T0^3)

    Without the E term this is the expression SVN writes as
    A ln(T/T0) + [B + (C + D/(T0^2 T^2)) (T+T0)/2] (T-T0).
    """
    A, B, C, D, E = unpack(c)
    return (
        A * math.log(T / T0)
        + B * (T - T0)
        + C / 2.0 * (T * T - T0 * T0)
        + D / 2.0 * (1.0 / (T0 * T0) - 1.0 / (T * T))
        + E / 3.0 * (T ** 3 - T0 ** 3)
    )


def mcph(T0: float, T: float, c: Sequence[float]) -> float:
    """Mean heat capacity for enthalpy calculations, <Cp>_H / R.

    A + B/2 (T+T0) + C/3 (T^2 + T0^2 + T*T0) + D/(T*T0)
      + E/4 (T^3 + T^2*T0 + T*T0^2 + T0^3)
    """
    A, B, C, D, E = unpack(c)
    return (A + B / 2.0 * (T + T0) + C / 3.0 * (T * T + T0 * T0 + T * T0) + D / (T * T0)
            + E / 4.0 * (T ** 3 + T * T * T0 + T * T0 * T0 + T0 ** 3))


def mcps(T0: float, T: float, c: Sequence[float]) -> float:
    """Mean heat capacity for entropy calculations, <Cp>_S / R.

    Defined by  integral (Cp/R) dT/T = <Cp>_S/R * ln(T/T0).  At T = T0 the
    limit is simply Cp/R at T0.
    """
    if abs(T - T0) < 1e-9:
        return cp_over_r(c, T0)
    return icps(T0, T, c) / math.log(T / T0)


def combine(terms) -> Coeffs:
    """Stoichiometric sum of coefficient sets: sum(nu_i * (A_i, ..., E_i))."""
    total = [0.0] * 5
    for nu, c in terms:
        for k, value in enumerate(unpack(c)):
            total[k] += nu * value
    return (total[0], total[1], total[2], total[3], total[4])


def simpson(f, a: float, b: float, n: int = 2000) -> float:
    """Composite Simpson quadrature. Used only by the consistency audit to
    check the analytical integrals above by an independent numerical route."""
    if a == b:
        return 0.0
    if n % 2:
        n += 1
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        total += f(a + i * h) * (4 if i % 2 else 2)
    return total * h / 3.0
