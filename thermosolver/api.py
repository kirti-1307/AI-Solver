"""JSON API used by the web front end (and usable from any script).

Every endpoint takes a plain dict and returns a plain dict made only of
JSON-safe values. ``call(endpoint, json_text)`` wraps them with error handling
so the browser always receives either {"ok": true, "result": ...} or
{"ok": false, "error": {...}}.

Units everywhere: T in K, P in bar, energies in J/mol, entropies in J/(mol K).
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Callable, Dict, List, Optional

from . import benchmarks, eoschoice, heatbalance, library, phase
from .audit import audit_reaction, audit_residuals
from .combine import combine_reactions, formation_decomposition, formation_reaction
from .constants import P0, R, T0
from .data import HIGH_T_MAX, LOW_T_MIN, LOW_T_NOT_COVERED, SOURCES
from .equilibrium import atom_distribution, gibbs_minimize, reaction_equilibrium
from .errors import InputError, SolverError, UnbalancedReactionError
from .heatcap import mcph, mcps
from .realgas import MODEL_NAMES, compare_models, pressure_sweep, reaction_at_pressure
from .reaction import Reaction, format_coeff, suggest_balance
from .species import SPECIES, find_species

T_ABS_MIN = 1.0
T_ABS_MAX = 6000.0
P_ABS_MIN = 1e-6
P_ABS_MAX = 5000.0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _num(payload: dict, key: str, default: Optional[float] = None, lo: Optional[float] = None,
         hi: Optional[float] = None, label: Optional[str] = None) -> Optional[float]:
    value = payload.get(key, default)
    if value is None or value == "":
        value = default
    if value is None:
        return None
    label = label or key
    if isinstance(value, bool):
        raise InputError(f"{label} must be a number.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise InputError(f"{label} must be a number.")
    except OverflowError:
        raise InputError(f"{label} must be a finite number.")
    if not math.isfinite(value):
        raise InputError(f"{label} must be a finite number.")
    if lo is not None and value < lo:
        raise InputError(f"{label} must be at least {lo:g}.")
    if hi is not None and value > hi:
        raise InputError(f"{label} must be at most {hi:g}.")
    return value


def _temperature(payload: dict, key: str = "T", default: float = T0) -> float:
    value = payload.get(key, default)
    if value is None or value == "":
        value = default
    if isinstance(value, bool):
        raise InputError("Temperature must be a number in kelvin.")
    try:
        T = float(value)
    except (TypeError, ValueError):
        raise InputError("Temperature must be a number in kelvin.")
    except OverflowError:
        raise InputError("Temperature must be a finite number.")
    if not math.isfinite(T):
        raise InputError("Temperature must be a finite number.")
    if T <= 0:
        raise InputError("Temperature must be above 0 K. The solver works in kelvin: add 273.15 to degrees Celsius.")
    if T < T_ABS_MIN:
        raise InputError(f"Temperature must be at least {T_ABS_MIN:g} K.")
    if T > T_ABS_MAX:
        raise InputError(f"Temperature must be at most {T_ABS_MAX:g} K.")
    return T


def _pressure(payload: dict, key: str = "P", default: float = P0) -> float:
    value = payload.get(key, default)
    if value is None or value == "":
        value = default
    if isinstance(value, bool):
        raise InputError("Pressure must be a number in bar.")
    try:
        P = float(value)
    except (TypeError, ValueError):
        raise InputError("Pressure must be a number in bar.")
    except OverflowError:
        raise InputError("Pressure must be an absolute pressure above 0 bar.")
    if not math.isfinite(P) or P <= 0:
        raise InputError("Pressure must be an absolute pressure above 0 bar.")
    if P < P_ABS_MIN:
        raise InputError(f"Pressure must be at least {P_ABS_MIN:g} bar.")
    if P > P_ABS_MAX:
        raise InputError(f"Pressure must be at most {P_ABS_MAX:g} bar.")
    return P


def _model(payload: dict, default: str = "pr") -> str:
    model = payload.get("model") or default
    if not isinstance(model, str) or model not in MODEL_NAMES:
        raise InputError(f"Unknown real-gas model. Choose from: {', '.join(MODEL_NAMES)}.")
    return model


def _flag(payload: dict, key: str, label: str) -> bool:
    """A yes/no setting; anything other than true or false is refused."""
    value = payload.get(key, False)
    if value is None or value == "":
        return False
    if not isinstance(value, bool):
        raise InputError(f"{label} must be true or false.")
    return value


def _points(payload: dict, default: int) -> int:
    """Number of points of a sweep, always a whole number between 2 and 401."""
    return int(_num(payload, "n_points", default, 2, 401, "Number of plot points"))


def _reaction(payload: dict, key: str = "equation") -> Reaction:
    text = payload.get(key)
    if not isinstance(text, str) or not text.strip():
        raise InputError("Please enter a reaction, for example: CO + 2 H2 -> CH3OH")
    if len(text) > 400:
        raise InputError("The reaction text is too long.")
    return Reaction.parse(text, name=str(payload.get("name") or ""))


def _grid(lo: float, hi: float, n: int) -> List[float]:
    n = max(2, min(int(n), 401))
    if hi <= lo:
        return [lo]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _safe(obj: Any) -> Any:
    """Make a structure JSON-safe: drop Reaction objects, map inf/nan to None."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): _safe(v) for k, v in obj.items() if not isinstance(v, Reaction)}
    if isinstance(obj, (list, tuple)):
        return [_safe(v) for v in obj]
    return obj


def _join_points(lo: float, hi: float, breakpoints: List[float]) -> set:
    """Two points right at every temperature inside (lo, hi) where a heat
    capacity changes its source. They let a plot show the small step in Cp
    honestly instead of smearing it over one grid spacing."""
    points = set()
    for b in breakpoints:
        if lo < b < hi:
            # the lower set applies up to and including the end of the SVN range,
            # and strictly below 298.15 K
            points |= {b - 1e-6, b} if abs(b - T0) < 1e-9 else {b, b + 1e-6}
    return points


def _hull(pieces, limits) -> Optional[tuple]:
    """The temperature range covered by the pieces of a reaction that changes
    phase: for each piece its own range (``limits`` picks which one), cut to
    the temperatures where that piece applies, and then the lowest and the
    highest of those."""
    spans = []
    for a, b, variant in pieces:
        rng = limits(variant)
        if rng is None:
            continue
        lo, hi = max(rng[0], a), min(rng[1], b)
        if lo < hi:
            spans.append((lo, hi))
    if not spans:
        return None
    return min(s[0] for s in spans), max(s[1] for s in spans)


def _sweep_range(rxn: Reaction, payload: dict, pieces=None, floor: bool = False):
    """The temperatures of the plots. With ``floor`` (tab 1) they start at
    298.15 K at the lowest, and a lower start typed by the user is refused."""
    rng = rxn.plot_range() if pieces is None else _hull(pieces, lambda v: v.plot_range())
    if rng is None:
        return None
    lo = _num(payload, "T_min", None, 1.0, T_ABS_MAX, "Minimum temperature")
    hi = _num(payload, "T_max", None, 1.0, T_ABS_MAX, "Maximum temperature")
    if floor and lo is not None and lo < T0 - 1e-9:
        raise InputError(f"The plot starts at {T0:g} K at the lowest, the reference temperature of the data.")
    lo = (max(rng[0], T0) if floor else rng[0]) if lo is None else lo
    hi = rng[1] if hi is None else hi
    if lo == 298.0 and payload.get("T_min") in (None, ""):
        lo = T0                        # SVN prints "298 K" for 298.15 K
    if hi <= lo:
        raise InputError("The maximum temperature of the plot must be above the minimum.")
    return lo, hi


# ---------------------------------------------------------------------------
# database and library
# ---------------------------------------------------------------------------
def database(payload: Optional[dict] = None) -> dict:
    species = [sp.to_dict() for sp in SPECIES.values()]
    phases = {"g": 0, "l": 0, "s": 0}
    for sp in SPECIES.values():
        phases[sp.phase] += 1
    return {
        "species": species,
        "count": len(species),
        "svn_count": sum(1 for sp in SPECIES.values() if sp.from_svn),
        "phase_counts": phases,
        "constants": {"R": R, "T0": T0, "P0": P0},
        "sources": SOURCES,
        "models": MODEL_NAMES,
        "low_T": {
            "T_min": LOW_T_MIN, "covered": sum(1 for sp in SPECIES.values() if sp.cp_low is not None),
            "not_covered": LOW_T_NOT_COVERED,
        },
        "high_T": {
            "T_max": HIGH_T_MAX, "covered": sum(1 for sp in SPECIES.values() if sp.cp_high is not None),
        },
        "data_notes": [
            {"species": "Below 298.15 K", "reason": (
                "SVN's heat-capacity tables start at 298 K, and extrapolating them downwards is not safe "
                "(for CO2 at 200 K the SVN constants give a heat capacity 29 % too low). From 200 K to 298.15 K "
                "the heat capacities of all 40 SVN gases, of acetic acid vapour and of six solids are therefore "
                "taken from NIST: the NIST-JANAF Thermochemical Tables (Chase 1998) and the recommended "
                "ideal-gas values of the NIST Chemistry WebBook. Each is a quadratic in T fixed by the tabulated "
                "values. The formation data at 298.15 K and everything above 298.15 K are unchanged. Liquids keep "
                "the SVN range of 273.15 to 373.15 K. Not covered below 298.15 K: H2O2(g) (its NIST-JANAF table is "
                "not consistent with itself there), CaCO3(s) and CaC2(s) (not in NIST-JANAF).")},
            {"species": "Above the SVN range", "reason": (
                "SVN's formula for the gases of a flame ends at 2000 K, and a flame is hotter. Beyond its range the "
                "formula keeps rising while the real heat capacity levels off, so it must not be stretched. For "
                "N2, O2, CO2, H2O, CO, H2, SO2 and NO the heat capacity above the SVN limit, up to 6000 K, is "
                "therefore taken from the heat-capacity equations of the NIST Chemistry WebBook (fitted to the "
                "NIST-JANAF tables). The equations are used as published. Inside the SVN range nothing is changed. Every other "
                "species keeps its SVN limit, and the solver warns beyond it.")},
            {"species": "Step at 298.15 K", "reason": (
                "The SVN correlation and the NIST value do not give exactly the same heat capacity at 298.15 K. "
                "For 25 of the 47 species the two agree within 1 %. The largest differences: SVN's constants are "
                "14 % above NIST for ethanol, 7 % for styrene and calcium hydroxide, and 5 % for methanol. "
                "Neither source is altered, so "
                "plots of the heat capacity show a small step at 298.15 K. Enthalpy, entropy and Gibbs energy "
                "stay continuous because every integral starts at 298.15 K.")},
            {"species": "H2O2(g)", "reason": "Hydrogen peroxide is absent from SVN Tables B.1 and C.1 to C.4. The gas is taken from the NIST Chemistry WebBook (NIST-JANAF: ΔH°f = -136.11 kJ/mol, S° = 232.95 J/(mol·K), NIST heat-capacity equation, 298 to 1500 K). It has no critical constants in Table B.1, so it is an ideal gas in pressure calculations. Liquid H2O2 is not included."},
            {"species": "CH3COOH(g)", "reason": "Acetic acid vapour is not in SVN. NIST Chemistry WebBook: ΔH°f = -432.9 kJ/mol, S° = 282.84 J/(mol·K), heat capacity fitted to the tabulated values (largest deviation 0.21 %). The values are for single molecules; in the real vapour part of the molecules pair up."},
            {"species": "1,3-Butadiene", "reason": "The Cp298/R printed in SVN Table C.1 (10.720) does not agree with the printed A, B, C (9.931). The constants are used."},
            {"species": "NH3", "reason": "ΔG°f,298 is -16,400 J/mol in the 8th and 9th editions (used here) and -16,450 J/mol in the 6th edition."},
            {"species": "CH3COOH(l)", "reason": "SVN lists liquid acetic acid in Table C.4 (formation data used here) but gives no heat capacity. A constant 123.1 J/(mol·K) from the NIST Chemistry WebBook is used, valid from 290 to 320 K."},
            {"species": "NO2, N2O4, ethylene oxide", "reason": "Not in SVN Table B.1 (no critical constants): treated as ideal gases in pressure calculations."},
        ],
    }


def get_library(payload: Optional[dict] = None) -> dict:
    reactions = []
    for rid, name, eq, category, T, note in library.REACTIONS:
        rxn = Reaction.parse(eq, name)
        reactions.append({
            "id": rid, "name": name, "equation": eq, "display": rxn.equation,
            "category": category, "T": T, "note": note,
            "dH0": rxn.dH0, "dG0": rxn.dG0,
            "valid_range": rxn.valid_range(),
        })
    combos = []
    for c in library.COMBINATIONS:
        combos.append({
            "id": c["id"], "name": c["name"], "T": c["T"],
            "steps": [{"equation": eq, "multiplier": m} for eq, m in c["steps"]],
        })
    return _safe({
        "reactions": reactions,
        "combinations": combos,
        "networks": library.NETWORKS,
        "heat_examples": library.HEAT_EXAMPLES,
        "fuels": [{"id": sid, "name": SPECIES[sid].name, "phase": SPECIES[sid].phase}
                  for sid in heatbalance.combustible_species()],
        "calorimeter_handout": library.CALORIMETER_HANDOUT,
        "joule_per_cal": heatbalance.JOULE_PER_CAL,
    })


# ---------------------------------------------------------------------------
# 1. standard thermodynamics of one reaction
# ---------------------------------------------------------------------------
def _derivation(rxn: Reaction, ev: dict) -> List[dict]:
    """The calculation written out step by step, with numbers."""
    T = ev["T"]

    def terms(attr: str) -> str:
        parts = []
        for sid, nu in rxn.stoich.items():
            value = getattr(SPECIES[sid], attr)
            parts.append(f"({'+' if nu > 0 else '-'}{format_coeff(nu)})({value:,.0f})")
        return " + ".join(parts)

    steps = [
        {"title": "Standard heat of reaction at 298.15 K",
         "formula": "ΔH°₂₉₈ = Σ νᵢ ΔH°f,ᵢ",
         "work": terms("dHf"), "value": ev["dH0"], "unit": "J/mol"},
        {"title": "Standard Gibbs energy change at 298.15 K",
         "formula": "ΔG°₂₉₈ = Σ νᵢ ΔG°f,ᵢ",
         "work": terms("dGf"), "value": ev["dG0"], "unit": "J/mol"},
        {"title": "Standard entropy change at 298.15 K",
         "formula": "ΔS°₂₉₈ = (ΔH°₂₉₈ − ΔG°₂₉₈) / T₀",
         "work": f"({ev['dH0']:,.0f} − ({ev['dG0']:,.0f})) / 298.15",
         "value": ev["dS0"], "unit": "J/(mol·K)"},
    ]
    if ev.get("dA") is None:
        return steps
    low = bool(ev.get("low_T_species"))
    high = ev.get("high_T_species") or []
    title = "Heat-capacity change of reaction"
    if low:
        title += " (constants for 200 to 298.15 K, from NIST tables)"
    elif high:
        title += f" (above the SVN range the constants of {', '.join(high)} are NIST's)"
    # above the SVN range of a species the integral is taken in two pieces
    pieces = ",  in two pieces: SVN constants up to their limit, NIST's above it" if high else ""
    steps += [
        {"title": title,
         "formula": ("ΔCp°/R = ΔA + ΔB·T + ΔC·T² + ΔD·T⁻²"
                     + (" + ΔE·T³" if ev["dE"] else "") + ",  Δ = Σ νᵢ (…)ᵢ"),
         "work": (f"ΔA = {ev['dA']:.4g},  ΔB = {ev['dB']:.4e},  "
                  f"ΔC = {ev['dC']:.4e},  ΔD = {ev['dD']:.4e}"
                  + (f",  ΔE = {ev['dE']:.4e}" if ev["dE"] else "")),
         "value": ev["dCp"], "unit": f"J/(mol·K) at {T:g} K"},
        {"title": f"Standard heat of reaction at {T:g} K",
         "formula": "ΔH°(T) = ΔH°₂₉₈ + R ∫ (ΔCp°/R) dT" + pieces,
         "work": f"{ev['dH0']:,.0f} + 8.314 × ({ev['IDCPH']:,.3f} K)",
         "value": ev["dH"], "unit": "J/mol"},
        {"title": f"Standard entropy change at {T:g} K",
         "formula": "ΔS°(T) = ΔS°₂₉₈ + R ∫ (ΔCp°/R) dT/T" + pieces,
         "work": f"{ev['dS0']:,.3f} + 8.314 × ({ev['IDCPS']:,.5f})",
         "value": ev["dS"], "unit": "J/(mol·K)"},
        {"title": f"Standard Gibbs energy change at {T:g} K",
         "formula": "ΔG°(T) = ΔH°(T) − T·ΔS°(T)",
         "work": f"{ev['dH']:,.0f} − {T:g} × ({ev['dS']:,.3f})",
         "value": ev["dG"], "unit": "J/mol"},
        {"title": "Equilibrium constant Kp (partial pressures in bar)",
         "formula": "ln Kp = −ΔG°(T) / (R·T)",
         "work": f"−({ev['dG']:,.0f}) / (8.314 × {T:g})",
         "value": ev["lnK"], "unit": "(ln K)"},
    ]
    return steps


def _T_sweep(rxn: Reaction, lo: float, hi: float, n: int, pieces=None) -> dict:
    """Property changes against temperature. ``pieces`` (from phase.segments)
    makes every species take the phase that is stable at each temperature;
    two points are then placed right at each boiling point, so that the plot
    shows the jump of dH there as a jump."""
    pieces = pieces or [(0.0, math.inf, rxn)]
    points = set(_grid(lo, hi, n))
    for a, b, variant in pieces:
        points |= {t for t in _join_points(lo, hi, variant.breakpoints()) if a <= t < b}
        if lo < a < hi:
            points |= {a - 1e-6, a}
    out: Dict[str, list] = {k: [] for k in (
        "T", "dH", "dS", "dG", "TdS", "lnK", "log10K", "dCp",
        "dH_const_cp", "dG_const_cp", "dG_no_cp", "in_range")}
    for T in sorted(points):
        variant = next(v for a, b, v in pieces if a <= T < b)
        rng = variant.valid_range()
        dH, dS = variant.dH(T), variant.dS(T)
        dG = dH - T * dS
        lnK = -dG / (R * T)
        out["T"].append(T)
        out["dH"].append(dH)
        out["dS"].append(dS)
        out["dG"].append(dG)
        out["TdS"].append(T * dS)
        out["lnK"].append(lnK)
        out["log10K"].append(lnK / math.log(10.0))
        out["dCp"].append(variant.dCp(T))
        out["dH_const_cp"].append(variant.dH_constant_cp(T))
        out["dG_const_cp"].append(variant.dG_constant_cp(T))
        out["dG_no_cp"].append(variant.dG_no_cp(T))
        out["in_range"].append(bool(rng and rng[0] - 1e-9 <= T <= rng[1] + 1e-9))
    return out


_ASSUMED = re.compile(r"^No phase was given for .+?; (\S+) was assumed")


def _untyped(typed: Reaction) -> set:
    """Species ids that the parser chose because no phase was typed (see species.find_species)."""
    return {m.group(1) for m in (_ASSUMED.match(n) for n in typed.notes) if m}


def _phase_choice(typed: Reaction, T: float, auto: bool, untyped_only: bool = False) -> dict:
    """What the choice of phase does for one reaction at T: which species can
    change phase, where they boil, what is swapped (or would be), and the
    reaction to calculate with.

    auto: every species that can change phase gets the stable phase, even a typed one.
    untyped_only (tab 1's default since 23 November 2026): only a species typed
    without a phase gets the stable phase; a phase that is typed is kept.
    """
    candidates, skipped = phase.choices(typed)
    free = _untyped(typed)
    if auto:
        used = candidates
    elif untyped_only:
        used = [t for t in candidates if (t.liquid in typed.stoich and t.liquid in free) or (t.gas in typed.stoich and t.gas in free)]
    else:
        used = []
    active = bool(used)
    stable_all, swaps_all = phase.at_temperature(typed, T, candidates)
    stable, swaps = phase.at_temperature(typed, T, used) if active else (typed, [])
    for s in swaps_all + swaps:
        s["untyped"] = s["typed"] in free
    info = {
        "auto": active,
        "equation_typed": typed.equation,
        "transitions": phase.jumps(typed, used if active else candidates),
        "skipped": skipped,
        # typed phase -> stable phase at T: what was applied (auto) or what would be (hint)
        "swaps": swaps if active else swaps_all,
        # the phase the solver uses at T for each species it chose itself, and whether it was typed
        "chosen": [{"compound": t.compound, "species": phase.stable_id(t, T),
                    "untyped": (t.liquid in free or t.gas in free)} for t in used],
        "equation_stable": stable_all.equation,
        "pieces": None,
        "audit": phase.audit(used) if active else [],
    }
    return {"info": info, "used": used, "reaction": stable if active else typed,
            "pieces": phase.segments(typed, used) if active else None}


def analyze(payload: dict) -> dict:
    """Standard heat of reaction, entropy and Gibbs energy at T, with the
    temperature sweep, warnings, written-out steps and consistency audit.

    With "auto_phase" every species that the database holds as a liquid and
    as a gas is put into the phase that is stable at T and 1 bar (see the
    module ``phase``), at the chosen temperature and along the plots.
    """
    typed = _reaction(payload)
    T = _temperature(payload)
    P = _pressure(payload)          # only for the equilibrium conversion; the standard values are at 1 bar
    # Tab 1 sends "from_reference_T": it works from 298.15 K upwards only (the user's request of
    # 23 November 2026). The NIST data below 298.15 K stay in the solver for everything else.
    floor = _flag(payload, "from_reference_T", "'from_reference_T'")
    if floor and T < T0 - 1e-9:
        raise InputError(f"This tab starts at the reference temperature of the data, {T0:g} K. Choose {T0:g} K or more.")
    choice = _phase_choice(typed, T, _flag(payload, "auto_phase", "'auto_phase'"),
                           _flag(payload, "auto_phase_untyped", "'auto_phase_untyped'"))
    rxn, pieces = choice["reaction"], choice["pieces"]
    ev = rxn.evaluate(T)
    warnings = rxn.range_warnings(T)
    if pieces is not None:
        # The solver has chosen the phase itself, so the hint to check the
        # phase is replaced by the account of the choice (result["phase"]).
        handled = {sid for t in choice["used"] for sid in (t.liquid, t.gas)}
        warnings = [w for w in warnings if not (w.get("kind") == "phase" and w.get("species") in handled)]
        crossover = sorted(x for a, b, v in pieces
                           for x in v.crossover_temperatures(a if a > 0.0 else None, b if math.isfinite(b) else None))
        valid_range = _hull(pieces, lambda v: v.valid_range())
        choice["info"]["pieces"] = [{"T_from": a if a > 0.0 else None, "T_to": b if math.isfinite(b) else None,
                                     "equation": v.equation, "valid_range": v.valid_range()} for a, b, v in pieces]
    else:
        crossover = rxn.crossover_temperatures()
        valid_range = rxn.valid_range()
    species_rows = rxn.species_table(T)
    if floor:
        # Nothing below 298.15 K: a sign change of dG below it is not reported, the valid range
        # is cut there, and a gas's Cp range is the textbook's own (from 298 K, without the NIST rows).
        crossover = [x for x in crossover if x >= T0 - 1e-9]
        if valid_range is not None:
            valid_range = (max(valid_range[0], T0), valid_range[1])
        for row in species_rows:
            sp = SPECIES[row["id"]]
            if sp.cp_low is not None:
                row["cp_Tmin"] = sp.cp_main_Tmin
    notes = rxn.notes
    if pieces is not None:
        # The solver chose the phase of these species itself, so the note that a gas was
        # assumed for a species typed without a phase would contradict what was used.
        handled = {sid.split("(")[0] for t in choice["used"] for sid in (t.liquid, t.gas)}
        notes = [n for n in notes if not (n.startswith("No phase was given for ") and
                                          n[len("No phase was given for "):].split(";")[0] in handled)]
    result = {
        "equation": rxn.equation,
        "name": rxn.name,
        "notes": notes,
        "stoich": rxn.stoich,
        "T": T,
        "P": P,
        "at_T": ev,
        "species": species_rows,
        "warnings": warnings,
        "valid_range": valid_range,
        "crossover": crossover,
        "audit": audit_reaction(rxn, T) + choice["info"]["audit"],
        "formation": formation_decomposition(rxn),
        "steps": _derivation(rxn, ev),
        "has_cp": rxn.has_cp,
        "phase": choice["info"],
        "sweep": None,
        "equilibrium": None,
    }
    rng = _sweep_range(rxn, payload, pieces, floor)
    if rng:
        result["sweep"] = _T_sweep(rxn, rng[0], rng[1], _points(payload, 81), pieces)
        if pieces is not None:
            # Stretches of the plot where a heat capacity is used outside its
            # range. Each piece has its own range, so the page cannot work
            # them out from one pair of limits.
            bands = []
            for a, b, variant in pieces:
                lo, hi = max(a, rng[0]), min(b, rng[1])
                valid = variant.valid_range()
                if lo >= hi or valid is None:
                    continue
                if lo < valid[0]:
                    bands.append([lo, min(hi, valid[0])])
                if hi > valid[1]:
                    bands.append([max(lo, valid[1]), hi])
            result["sweep"]["out_of_range"] = [band for band in bands if band[1] - band[0] > 0.1]
    # How far the reaction goes with a stoichiometric feed treated as an
    # ideal-gas mixture: at 1 bar, and at the pressure the user chose. K
    # depends on temperature only; the pressure enters through the mole
    # fractions, K = prod(y_i^nu_i) * (P/P0)^(sum of nu of the gases).
    # A species that can condense is not simply taken in its standard-state
    # phase here: in a gas mixture it stays a vapour until its partial
    # pressure reaches its vapour pressure (phase.equilibrium).
    def conversion(t: float, p: float) -> Optional[dict]:
        try:
            if pieces is not None:
                return phase.equilibrium(typed, choice["used"], t, p)
            return reaction_equilibrium(rxn, t, p, model="ideal")
        except SolverError as exc:
            return {"error": exc.message, "conversion": None, "limiting_reactant": None}

    result["equilibrium"] = conversion(T, P0)
    result["equilibrium_P"] = conversion(T, P)
    if result["sweep"]:
        Ts = result["sweep"]["T"]
        at_1 = [conversion(t, P0)["conversion"] for t in Ts]
        result["sweep"]["conversion_1bar"] = at_1
        result["sweep"]["conversion_P"] = at_1 if abs(P - P0) < 1e-12 else [conversion(t, P)["conversion"] for t in Ts]
    return _safe(result)


# ---------------------------------------------------------------------------
# 2. pressure effect at constant temperature (residual properties)
# ---------------------------------------------------------------------------
def _percent_change(dH_ideal: float, dH_real: Optional[float]) -> Optional[float]:
    """By how many percent the size of the real-gas heat of reaction differs
    from the ideal-gas one. Positive: more heat is released (or absorbed)."""
    if dH_real is None or abs(dH_ideal) < 1e-9:
        return None
    return 100.0 * (abs(dH_real) - abs(dH_ideal)) / abs(dH_ideal)


def _effect_size(percent: Optional[float]) -> Optional[str]:
    """A word for how much the pressure changes the heat of reaction."""
    if percent is None:
        return None
    size = abs(percent)
    if size < 0.5:
        return "negligible"
    if size < 2.0:
        return "small"
    if size < 10.0:
        return "significant"
    return "large"


def _real_against_ideal(at_P: dict) -> dict:
    """The heat of reaction of the real gas next to the ideal-gas value.

    The residual enthalpy H^R is the enthalpy of the real gas minus that of
    the ideal gas at the same T and P. Enthalpy is a state function, so the
    real-gas heat of reaction can be walked in three steps (SVN Ch. 6):

        1. real reactants -> ideal-gas reactants      -sum over reactants |nu_i| H_i^R
        2. reaction in the ideal-gas state             dH0(T)
        3. ideal-gas products -> real products         +sum over products nu_i H_i^R

    and the three add up to dH(T,P) = dH0(T) + sum nu_i H_i^R.
    """
    ok = at_P["gas_phase_valid"]
    dH_ideal = at_P["dH_std"]
    rows = at_P["species"]
    step1 = sum(r["nu"] * r["HR"] for r in rows if r["nu"] < 0)      # nu < 0, so this is -|nu| H^R
    step3 = sum(r["nu"] * r["HR"] for r in rows if r["nu"] > 0)
    dH_real = at_P["dH_P"] if ok else None
    percent = _percent_change(dH_ideal, dH_real)
    if percent is None:
        effect = None
    elif dH_ideal * dH_real < 0:
        effect = "changes the sign of the heat of reaction"
    elif abs(percent) < 1e-9:
        effect = "no change"
    else:
        verb = "released" if dH_ideal < 0 else "absorbed"
        effect = f"{'more' if percent > 0 else 'less'} heat {verb}"
    real_gases = [r for r in rows if r["phase"] == "g" and not r["treated_ideal"]]
    largest = max(real_gases, key=lambda r: abs(r["nu"] * r["HR"]), default=None)
    return {
        "dH_ideal": dH_ideal,
        "residual": at_P["sum_HR"] if ok else None,
        "dH_real": dH_real,
        "percent": percent,
        "effect": effect,
        "size": _effect_size(percent),
        "path": {
            "reactants_to_ideal": step1 if ok else None,
            "ideal_reaction": dH_ideal,
            "products_to_real": step3 if ok else None,
            "total": (step1 + dH_ideal + step3) if ok else None,
        },
        "contributions": [{"species": r["species"], "nu": r["nu"], "HR": r["HR"],
                           "contribution": r["nu"] * r["HR"],
                           "role": "product" if r["nu"] > 0 else "reactant"} for r in rows],
        "largest": None if largest is None or not ok else {
            "species": largest["species"], "contribution": largest["nu"] * largest["HR"],
            "Tr": largest["Tr"], "Pr": largest["Pr"], "Z": largest["Z"]},
    }


def _residual_T_sweep(rxn: Reaction, P: float, model: str, n: int = 61) -> Optional[dict]:
    """The heat of reaction of the ideal and of the real gas along an isobar,
    to show at which temperatures the pressure effect matters."""
    rng = rxn.plot_range()
    if rng is None or rng[1] <= rng[0]:
        return None
    lo, hi = rng

    def valid(t: float) -> bool:
        return reaction_at_pressure(rxn, t, P, model)["gas_phase_valid"]

    # The curve starts where every species has a gas state at this pressure. Below that
    # there is no gas-phase value, and the plot would only show an empty stretch of axis
    # (the user's request of 23 November 2026), so the points are spent where there is data.
    gas_from = None
    if not valid(lo):
        grid = _grid(lo, hi, n)
        first = next((i for i, t in enumerate(grid) if valid(t)), None)
        if first is not None:
            a, b = grid[first - 1], grid[first]
            for _ in range(40):
                mid = 0.5 * (a + b)
                if valid(mid):
                    b = mid
                else:
                    a = mid
            lo = gas_from = b
    out: Dict[str, list] = {k: [] for k in ("T", "dH_ideal", "dH_real", "residual", "percent")}
    out["gas_from"] = gas_from
    for T in _grid(lo, hi, n):
        point = reaction_at_pressure(rxn, T, P, model)
        ok = point["gas_phase_valid"]
        out["T"].append(T)
        out["dH_ideal"].append(point["dH_std"])
        out["dH_real"].append(point["dH_P"] if ok else None)
        out["residual"].append(point["sum_HR"] if ok else None)
        out["percent"].append(_percent_change(point["dH_std"], point["dH_P"] if ok else None))
    usable = [T for T, value in zip(out["T"], out["residual"]) if value is not None]
    out["P"] = P
    out["first_valid_T"] = usable[0] if usable else None
    return out


def _gas_limit(rxn: Reaction, T: float, P: float, model: str) -> dict:
    """When a species has no vapour-like state at T and P: the highest
    pressure at this temperature at which every species still has one, and a
    round pressure a little below it to offer to the user."""
    def valid(p: float) -> bool:
        return reaction_at_pressure(rxn, T, p, model)["gas_phase_valid"]

    lo = min(1.0, P / 2.0)
    if not valid(lo):
        return {"P_max": None, "P_suggest": None}
    hi = P
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if valid(mid):
            lo = mid
        else:
            hi = mid
    suggest = float(math.floor(0.98 * lo)) if lo >= 10.0 else round(0.95 * lo, 2)
    if suggest <= 0.0 or not valid(suggest):
        suggest = None
    return {"P_max": lo, "P_suggest": suggest}


def pressure(payload: dict) -> dict:
    rxn = _reaction(payload)
    T = _temperature(payload)
    P = _pressure(payload)
    # The page sends no model: every gas gets the equation closest to measured data (eoschoice).
    # A model can still be named here, for scripts and the tests.
    model = _model(payload, "auto")
    P_max = _num(payload, "P_max", max(P, 300.0), 1e-3, P_ABS_MAX, "Maximum pressure")
    P_min = _num(payload, "P_min", min(P, 1.0), 1e-6, P_ABS_MAX, "Minimum pressure")
    if P_max <= P_min:
        raise InputError("The maximum pressure of the plot must be above the minimum.")
    n = _points(payload, 61)

    at_P = reaction_at_pressure(rxn, T, P, model)
    pressures = _grid(P_min, P_max, n)
    sweep = pressure_sweep(rxn, T, pressures, model)

    # Equilibrium conversion along the isotherm, ideal gas versus real gas.
    # The two are computed separately so that a refused real-gas point (a
    # species with no vapour state) leaves the ideal-gas point untouched and
    # both lists always have exactly one entry per pressure.
    conv_ideal, conv_real = [], []
    for p in pressures:
        try:
            conv_ideal.append(reaction_equilibrium(rxn, T, p, model="ideal")["conversion"])
        except SolverError:
            conv_ideal.append(None)
        try:
            conv_real.append(reaction_equilibrium(rxn, T, p, model=model)["conversion"])
        except SolverError:
            conv_real.append(None)
    sweep["conversion_ideal"] = conv_ideal
    sweep["conversion_real"] = conv_real

    models = []
    for key in ("ideal", "virial", "vdw", "rk", "srk", "pr"):
        point = reaction_at_pressure(rxn, T, P, key)
        ok = point["gas_phase_valid"]
        models.append({
            "model": key, "name": MODEL_NAMES[key], "gas_phase_valid": ok,
            "sum_HR": point["sum_HR"] if ok else None, "dH_P": point["dH_P"] if ok else None,
            "sum_SR": point["sum_SR"] if ok else None, "dG_P": point["dG_P"] if ok else None,
            "K_phi": point["K_phi"] if ok else None,
            "percent": _percent_change(point["dH_std"], point["dH_P"] if ok else None),
        })

    try:
        eq_real = reaction_equilibrium(rxn, T, P, model=model)
    except SolverError as exc:
        eq_real = {"conversion": None, "limiting_reactant": None, "error": exc.message}

    result = {
        "equation": rxn.equation, "T": T, "P": P, "model": model,
        "at_P": at_P,
        "comparison": _real_against_ideal(at_P),
        # only when no gas-phase value exists at this pressure: where one does
        "gas_limit": None if at_P["gas_phase_valid"] else _gas_limit(rxn, T, P, model),
        "sweep": sweep,
        "sweep_T": _residual_T_sweep(rxn, P, model),
        "models": models,
        "equilibrium_ideal": reaction_equilibrium(rxn, T, P, model="ideal"),
        "equilibrium_real": eq_real,
        "audit": audit_residuals(rxn, T, P, model),
        "warnings": rxn.range_warnings(T),
    }
    return _safe(result)


def pressure_overview(payload: Optional[dict] = None) -> dict:
    """The ideal-gas and the real-gas heat of reaction for a few industrial
    reactions at their usual conditions, largest pressure effect first. It
    shows at a glance where residual properties matter and where they do not."""
    rows = []
    for case in library.PRESSURE_CASES:
        _, name, equation, *_ = library.reaction_by_id(case["id"])
        rxn = Reaction.parse(equation)
        point = reaction_at_pressure(rxn, case["T"], case["P"], "auto")
        cmp_ = _real_against_ideal(point)
        rows.append({
            "id": case["id"], "name": name, "equation": rxn.equation,
            "T": case["T"], "P": case["P"], "model": "auto", "model_name": MODEL_NAMES["auto"],
            "gas_phase_valid": point["gas_phase_valid"],
            "dH_ideal": cmp_["dH_ideal"], "residual": cmp_["residual"], "dH_real": cmp_["dH_real"],
            "percent": cmp_["percent"], "effect": cmp_["effect"], "size": cmp_["size"],
            "largest": cmp_["largest"]["species"] if cmp_["largest"] else None,
        })
    rows.sort(key=lambda r: -abs(r["percent"] or 0.0))
    return _safe({"rows": rows})


def eos_check(payload: Optional[dict] = None) -> dict:
    """The five equations of state against measured residual enthalpies (NIST), gas by gas,
    and the equation the solver therefore uses for each gas (module eoschoice)."""
    out = eoschoice.summary()
    out["names"] = {m: MODEL_NAMES[m] for m in out["equations"]}
    out["choices"] = []
    for sid, sp in SPECIES.items():
        if sp.phase != "g":
            continue
        model, why = eoschoice.choose(sp)
        out["choices"].append({"species": sid, "name": sp.name, "model": model, "model_name": MODEL_NAMES[model],
                               "basis": why["basis"]})
    return _safe(out)


def species_residual(payload: dict) -> dict:
    """Residual properties of one pure species from every model."""
    sp, _ = find_species(str(payload.get("species") or ""))
    T = _temperature(payload)
    P = _pressure(payload)
    return _safe({"species": sp.to_dict(), "T": T, "P": P, "models": compare_models(sp, T, P)})


# ---------------------------------------------------------------------------
# 3. combining reactions (Hess's law)
# ---------------------------------------------------------------------------
def combine(payload: dict) -> dict:
    raw = payload.get("steps")
    if not isinstance(raw, list) or len(raw) < 2:
        raise InputError("Give at least two reactions to combine.")
    if len(raw) > 8:
        raise InputError("At most eight reactions can be combined at once.")
    T = _temperature(payload)
    steps = []
    for i, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise InputError(f"Step {i} is not valid.")
        mult = _num(item, "multiplier", 1.0, -1000.0, 1000.0, f"Multiplier of step {i}")
        if abs(mult) < 1e-12:
            raise InputError(f"The multiplier of step {i} cannot be zero.")
        try:
            rxn = _reaction(item)
        except SolverError as exc:
            raise type(exc)(f"Step {i}: {exc.message}", exc.details)
        steps.append((rxn, mult))

    res = combine_reactions(steps, T)
    target: Reaction = res["reaction"]
    out = {k: v for k, v in res.items() if k != "reaction"}
    out["warnings"] = target.range_warnings(T)
    out["valid_range"] = target.valid_range()
    out["species"] = target.species_table(T)

    # dG(T) of each step (already multiplied) and of the net reaction
    out["sweep"] = None
    ranges = [r.valid_range() for r, _ in steps] + [target.valid_range()]
    if all(ranges):
        lo = max(r[0] for r in ranges)
        hi = min(r[1] for r in ranges)
        if hi > lo:
            Ts = _grid(max(lo, 298.15), hi, 61)
            out["sweep"] = {
                "T": Ts,
                "steps": [[m * r.dG(t) for t in Ts] for r, m in steps],
                "steps_dH": [[m * r.dH(t) for t in Ts] for r, m in steps],
                "net_dG": [target.dG(t) for t in Ts],
                "net_dH": [target.dH(t) for t in Ts],
                "net_log10K": [target.lnK(t) / math.log(10.0) for t in Ts],
            }
    return _safe(out)


def formation(payload: dict) -> dict:
    """Formation reaction of a species and its properties at T."""
    sp, _ = find_species(str(payload.get("species") or ""))
    T = _temperature(payload)
    rxn = formation_reaction(sp)
    return _safe({"species": sp.id, "equation": rxn.equation, "at_T": rxn.evaluate(T),
                  "warnings": rxn.range_warnings(T)})


# ---------------------------------------------------------------------------
# 4. feature: competing-reaction equilibrium by Gibbs minimisation
# ---------------------------------------------------------------------------
# A mole fraction or an atom share has to move by more than this (0.05
# percentage points) before a product switch counts as changing the result.
SWITCH_TOLERANCE = 5e-4


def _switch_effects(point: dict, candidates: List[str], feed: Dict[str, float], T: float, P: float,
                    model: str, key_el: str) -> List[dict]:
    """What each product switch of the product slate would change right now.

    A switch removes one species from those allowed to form (or allows it
    again). Whether that matters depends on the conditions: a species that
    holds none of the atoms can be removed without any effect. For every
    species the equilibrium is therefore solved once more with that one switch
    flipped, and the two mixtures are compared.

    effect: "feed"        fed to the reactor, not a product
            "needed"      without it nothing can react (the atoms have nowhere else to go)
            "none"        flipping the switch changes nothing at these conditions
            "changes"     flipping the switch changes the mixture
            "cannot_form" the feed has none of an element it contains
    """
    ids = list(point["species"])
    fed = [s for s in ids if point["feed"].get(s, 0.0) > 0.0]
    with_key = [s for s in fed if SPECIES[s].elements.get(key_el, 0)]
    primary = max(with_key or fed, key=lambda s: point["feed"][s])
    dist = point["atom_distribution"]

    def solve(species: List[str]) -> Optional[dict]:
        try:
            alt = gibbs_minimize(species, feed, T, P, model)
        except SolverError:
            return None
        alt["atom_distribution"] = atom_distribution(alt, key_el)
        return alt

    def moved(alt: dict) -> float:
        """Largest change of a mole fraction or of an atom share."""
        dy = max(abs(point["y"].get(k, 0.0) - alt["y"].get(k, 0.0)) for k in set(point["y"]) | set(alt["y"]))
        other = alt["atom_distribution"]
        ds = max((abs(dist.get(k, 0.0) - other.get(k, 0.0)) for k in set(dist) | set(other)), default=0.0)
        return max(dy, ds)

    def row(sid: str, state: str) -> dict:
        return {"species": sid, "name": SPECIES[sid].name, "state": state, "effect": None, "clickable": False,
                "y": point["y"].get(sid), "share": dist.get(sid),
                "y_if_flipped": None, "share_if_flipped": None, "largest_change": None,
                "primary": primary, "conversion_now": point["conversions"][primary],
                "conversion_if_flipped": None}

    reacting = any(abs(v) > 1e-6 for v in point["conversions"].values())
    rows = []
    for sid in ids:
        r = row(sid, "feed" if sid in fed else "on")
        if sid in fed:
            r["effect"] = "feed"
        elif sid in point["excluded"]:
            r["effect"] = "cannot_form"
        else:
            alt = solve([s for s in ids if s != sid])
            if alt is None or (reacting and all(abs(v) < 1e-9 for v in alt["conversions"].values())):
                r["effect"] = "needed"
            else:
                change = moved(alt)
                r.update(largest_change=change, conversion_if_flipped=alt["conversions"][primary],
                         effect="changes" if change >= SWITCH_TOLERANCE else "none")
                r["clickable"] = r["effect"] == "changes"
        rows.append(r)

    for sid in candidates:
        r = row(sid, "off")
        r["clickable"] = True                       # a blocked product can always be allowed again
        alt = solve(ids + [sid])
        if alt is None:
            r["effect"] = "changes"
        elif sid in alt["excluded"]:
            r["effect"] = "cannot_form"
        else:
            change = moved(alt)
            r.update(largest_change=change, conversion_if_flipped=alt["conversions"][primary],
                     y_if_flipped=alt["y"][sid], share_if_flipped=alt["atom_distribution"].get(sid),
                     effect="changes" if change >= SWITCH_TOLERANCE else "none")
        rows.append(r)
    return rows


def network(payload: dict) -> dict:
    species = payload.get("species")
    feed = payload.get("feed")
    if not isinstance(species, list) or not species:
        raise InputError("Choose the species that are allowed to form.")
    if len(species) > 20:
        raise InputError("At most 20 species can be included.")
    if not all(isinstance(s, str) for s in species):
        raise InputError("Every species must be given by its name or formula.")
    if not isinstance(feed, dict) or not feed:
        raise InputError("Give the feed composition in moles.")
    want_switches = payload.get("switches", False)
    if not isinstance(want_switches, bool):
        raise InputError("'switches' must be true or false.")
    blocked_names = payload.get("candidates") or []
    if (not isinstance(blocked_names, list) or len(blocked_names) > 20
            or not all(isinstance(s, str) for s in blocked_names)):
        raise InputError("The blocked products must be given as a list of at most 20 names or formulas.")
    T = _temperature(payload)
    P = _pressure(payload)
    model = _model(payload, "ideal")
    clean_feed = {str(k): _num(feed, k, 0.0, 0.0, 1e9, f"Feed of {k}") for k in feed}

    point = gibbs_minimize(species, clean_feed, T, P, model)
    ids = point["species"]
    elements = sorted(point["elements"])
    key_el = payload.get("key_element") or ("C" if "C" in elements else None)
    if key_el is None:
        candidates = [el for el in elements if el not in ("H", "O")]
        key_el = candidates[0] if candidates else elements[0]
    if key_el not in elements:
        raise InputError(f"Element {key_el} is not present in this system.")
    point["key_element"] = key_el
    point["atom_distribution"] = atom_distribution(point, key_el)

    point["switches"] = None
    if want_switches:
        blocked = []
        for name in blocked_names:
            sid = find_species(name)[0].id
            if sid not in ids and sid not in blocked:
                blocked.append(sid)
        point["switches"] = _switch_effects(point, blocked, clean_feed, T, P, model, key_el)

    warnings = []
    for sid in ids:
        sp = SPECIES[sid]
        if not sp.in_cp_range(T):
            warnings.append({
                "level": "warning", "species": sid,
                "message": (f"{sid}: {T:g} K is outside its heat-capacity range "
                            f"({sp.cp_Tmin:g} to {sp.cp_Tmax:g} K); extrapolated."),
            })
    point["warnings"] = warnings

    # Sweep along temperature (default) or pressure
    variable = payload.get("sweep") or "T"
    lo_default = max(SPECIES[s].cp_Tmin for s in ids)
    hi_default = min(SPECIES[s].cp_main_Tmax for s in ids)      # a plot stops where the SVN formulas stop
    sweep = None
    if variable == "none":
        xs = []
    elif variable == "T":
        lo = _num(payload, "T_min", max(lo_default, 300.0), 1.0, T_ABS_MAX, "Minimum temperature")
        hi = _num(payload, "T_max", hi_default, 1.0, T_ABS_MAX, "Maximum temperature")
        xs = _grid(lo, hi, _points(payload, 41)) if hi > lo else []
    elif variable == "P":
        lo = _num(payload, "P_min", 1.0, P_ABS_MIN, P_ABS_MAX, "Minimum pressure")
        hi = _num(payload, "P_max", max(P, 100.0), P_ABS_MIN, P_ABS_MAX, "Maximum pressure")
        xs = _grid(lo, hi, _points(payload, 41)) if hi > lo else []
    else:
        raise InputError("The sweep variable must be 'T', 'P' or 'none'.")
    if xs:
        sweep = {"variable": variable, "x": xs, "y": {s: [] for s in ids},
                 "distribution": {s: [] for s in point["atom_distribution"]},
                 "conversion": {s: [] for s in point["conversions"]},
                 "carbon_activity": [], "total_moles": [],
                 # points where the real-gas model has no vapour state for a species
                 "skipped": [], "skipped_reason": None}
        for x in xs:
            try:
                r = gibbs_minimize(species, clean_feed, x if variable == "T" else T,
                                   x if variable == "P" else P, model)
                dist = atom_distribution(r, key_el)
            except SolverError as exc:
                r, dist = None, {}
                sweep["skipped"].append(x)
                sweep["skipped_reason"] = sweep["skipped_reason"] or exc.message
            for s in ids:
                sweep["y"][s].append(r["y"][s] if r else None)
            for s in sweep["distribution"]:
                sweep["distribution"][s].append(dist.get(s) if r else None)
            for s in sweep["conversion"]:
                sweep["conversion"][s].append(r["conversions"][s] if r else None)
            sweep["carbon_activity"].append(r["carbon_activity"] if r else None)
            sweep["total_moles"].append(r["total_moles"] if r else None)
    point["sweep"] = sweep
    return _safe(point)


# ---------------------------------------------------------------------------
# 5. feature: reactor heat balance (adiabatic temperature and heat duty)
# ---------------------------------------------------------------------------
def _species_id(text: Any, label: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise InputError(f"{label} must be a species name or formula.")
    return find_species(text)[0].id


def _heat_settings(payload: dict, rxn: Reaction) -> dict:
    """Feed and reaction settings of the heat balance, validated."""
    key = payload.get("key")
    key = heatbalance.default_key(rxn) if key in (None, "") else _species_id(key, "The key reactant")
    in_excess = payload.get("excess_species")
    in_excess = (heatbalance.default_excess_species(rxn, key) if in_excess in (None, "")
                 else _species_id(in_excess, "The reactant in excess"))
    excess = _num(payload, "excess", 0.0, None, None, "The excess")
    if not -0.99 <= excess <= heatbalance.MAX_EXCESS:
        raise InputError(f"The excess must be between -99 % and {100 * heatbalance.MAX_EXCESS:,.0f} % "
                         f"(as a fraction: -0.99 to {heatbalance.MAX_EXCESS:g}).")
    conversion = _num(payload, "conversion", 1.0, None, None, "The conversion")
    if not 0.0 <= conversion <= 1.0:
        raise InputError("The conversion must be between 0 and 100 % (as a fraction: 0 to 1).")
    if in_excess is None:
        excess = 0.0                      # a single reactant: nothing can be in excess

    raw_extra = payload.get("extra") or {}
    if not isinstance(raw_extra, dict):
        raise InputError("The extra feed must map species to moles.")
    if len(raw_extra) > 10:
        raise InputError("At most ten extra feed species can be given.")
    extra: Dict[str, float] = {}
    for name in raw_extra:
        sid = _species_id(name, "An extra feed species")
        extra[sid] = extra.get(sid, 0.0) + _num(raw_extra, name, 0.0, 0.0, 1e6, f"Feed of {name}")

    raw_side = payload.get("side") or []
    if not isinstance(raw_side, list):
        raise InputError("The side reactions must be a list.")
    if len(raw_side) > 4:
        raise InputError("At most four side reactions can be given.")
    side = []
    for i, item in enumerate(raw_side, 1):
        if not isinstance(item, dict):
            raise InputError(f"Side reaction {i} is not valid.")
        try:
            other = _reaction(item)
        except SolverError as exc:
            raise type(exc)(f"Side reaction {i}: {exc.message}", exc.details)
        side.append((other, _num(item, "extent", 0.0, 0.0, 1e6, f"Extent of side reaction {i}")))

    air = payload.get("air", False)
    if not isinstance(air, bool):
        raise InputError("'air' must be true or false.")
    return {"key": key, "conversion": conversion,
            "excess_species": in_excess, "excess": excess, "air": air, "extra": extra, "side": side}


def heat_balance(payload: dict) -> dict:
    """Energy balance on a reactor, per mole of key reactant fed.

    mode "adiabatic": the outlet temperature for a given heat input Q (0 by default).
    mode "duty":      the heat duty for a given outlet temperature.
    "condense":       the water of the outlet takes the phase its temperature gives it
                      (vapour, liquid or both) instead of the phase that is written.
    """
    rxn = _reaction(payload)
    settings = _heat_settings(payload, rxn)
    condense = _flag(payload, "condense", "'condense'")
    T_in = _temperature(payload, "T_in", T0)
    mode = payload.get("mode") or "adiabatic"
    if mode not in ("adiabatic", "duty"):
        raise InputError("The mode must be 'adiabatic' or 'duty'.")
    Q = _num(payload, "Q", 0.0, -1e10, 1e10, "Heat added") if mode == "adiabatic" else 0.0
    T_out = _temperature(payload, "T_out", T0) if mode == "duty" else None

    def run(T_in_: float, T_out_: Optional[float], **change):
        case_ = heatbalance.build_case(rxn, **{**settings, **change})
        return case_, heatbalance.solve(case_, T_in_, mode, T_out_, Q, condense)

    case, point = run(T_in, T_out)
    feed, outlet = heatbalance.Stream(case["feed"]), heatbalance.outlet_model(case, condense)

    # Enthalpy-temperature lines of the feed and of the outlet mixture
    lo = min(T0, T_in, point["T_out"])
    hi = max(T0, T_in, point["T_out"])
    pad = max(25.0, 0.06 * (hi - lo))
    Ts = _grid(max(1.0, lo - pad), min(T_ABS_MAX, hi + pad), 61)
    water = point["water"]
    if water and water["applied"] and water["T_dew"] and Ts[0] < water["T_dew"] < Ts[-1]:
        Ts = sorted(set(Ts) | {water["T_dew"]})      # the enthalpy line of the products bends at the dew point
    curves = {"T": Ts, "H_feed": [feed.H(t) for t in Ts], "H_out": [outlet.H(t) for t in Ts]}

    # Sweep of one setting
    default_sweep = "T_out" if mode == "duty" else ("excess" if case["excess_species"] else "T_in")
    variable = payload.get("sweep") or default_sweep
    sweep = None
    if variable != "none":
        if variable == "excess":
            if case["excess_species"] is None:
                raise InputError("This reaction has a single reactant, so there is no excess to vary.")
            limits = (0.0, min(heatbalance.MAX_EXCESS, max(3.0, 2.0 * settings["excess"])),
                      0.0, heatbalance.MAX_EXCESS)
        elif variable == "T_in":
            limits = (T0, max(1200.0, T_in), T_ABS_MIN, T_ABS_MAX)
        elif variable == "conversion":
            limits = (0.0, 1.0, 0.0, 1.0)
        elif variable == "T_out" and mode == "duty":
            # a cool outlet gets a short axis, so that the bend at the dew point can be seen
            limits = (T0, max(2000.0, point["T_out"]) if point["T_out"] >= 600.0 else 600.0, T_ABS_MIN, T_ABS_MAX)
        else:
            raise InputError("The sweep variable must be 'excess', 'T_in', 'conversion', "
                             "'T_out' (only when the heat is asked for) or 'none'.")
        x_lo = _num(payload, "sweep_min", limits[0], limits[2], limits[3], "Start of the plot")
        x_hi = _num(payload, "sweep_max", limits[1], limits[2], limits[3], "End of the plot")
        if x_hi <= x_lo:
            raise InputError("The end of the plot must be above its start.")
        xs = _grid(x_lo, x_hi, _points(payload, 41))
        sweep = {"variable": variable, "x": xs, "T_out": [], "Q": [], "water_liquid": []}
        for x in xs:
            try:
                if variable == "T_in":
                    _, r = run(x, T_out)
                elif variable == "T_out":
                    _, r = run(T_in, x)
                else:
                    _, r = run(T_in, T_out, **{variable: x})
                sweep["T_out"].append(r["T_out"])
                sweep["Q"].append(r["Q"])
                sweep["water_liquid"].append(r["water"]["n_liquid"] if r["water"] and r["water"]["applied"] else None)
            except SolverError:
                sweep["T_out"].append(None)
                sweep["Q"].append(None)
                sweep["water_liquid"].append(None)

    # Goal seek: the excess that holds the adiabatic outlet at a chosen temperature
    target = None
    if mode == "adiabatic" and payload.get("target_T") not in (None, "") and case["excess_species"]:
        target = heatbalance.excess_for_outlet_temperature(
            rxn, _temperature(payload, "target_T"), T_in, Q=Q, condense=condense,
            **{k: v for k, v in settings.items() if k != "excess"})

    return _safe({
        "equation": rxn.equation, "notes": list(rxn.notes) + case["notes"],
        "reactants": rxn.reactant_ids, "key": case["key"], "excess_species": case["excess_species"],
        "has_o2": "O2(g)" in case["feed"],
        "settings": {"conversion": settings["conversion"], "excess": settings["excess"], "air": settings["air"],
                     "extra": settings["extra"], "condense": condense,
                     "side": [{"equation": r.equation, "extent": xi} for r, xi in settings["side"]]},
        "dH0": rxn.dH0, "mode": mode, "point": point,
        "work": heatbalance.work_potential(case, point["T_out"], condense=condense),
        "fuel": heatbalance.fuel_facts(rxn, case["key"]),
        "curves": curves, "sweep": sweep, "target": target,
    })


def calorimeter(payload: dict) -> dict:
    """Virtual bomb calorimeter (constant-volume combustion, water as liquid).

    The calorimeter constant is either given directly ("C_cal", J/K) or found
    from a calibration run with a standard of known calorific value.

    mode "predict":  fuel and sample mass -> temperature rise
    mode "identify": sample mass and measured rise -> calorific value and the
                     closest fuels of the database
    """
    cal = heatbalance.JOULE_PER_CAL
    calibration = None
    raw = payload.get("calibration")
    if raw not in (None, ""):
        if not isinstance(raw, dict):
            raise InputError("The calibration must be an object.")
        mass_std = _num(raw, "mass", None, 1e-6, 1e6, "Mass of the standard")
        dT_std = _num(raw, "dT", None, 1e-6, 1e4, "Temperature rise of the calibration run")
        cv_std = _num(raw, "calorific_value", None, 1e-3, 1e9, "Calorific value of the standard")
        if mass_std is None or dT_std is None or cv_std is None:
            raise InputError("The calibration needs the mass of the standard, its calorific value "
                             "and the temperature rise.")
        corr_std = _num(raw, "corrections", 0.0, 0.0, 1e9, "Ignition corrections of the calibration run")
        C_cal = heatbalance.calorimeter_constant(mass_std, dT_std, cv_std, corr_std)
        calibration = {"mass": mass_std, "dT": dT_std, "calorific_value": cv_std, "corrections": corr_std,
                       "heat": mass_std * cv_std + corr_std, "C_cal": C_cal}
    else:
        C_cal = _num(payload, "C_cal", None, 1e-6, 1e12, "Calorimeter constant")
        if C_cal is None:
            raise InputError("Give the calorimeter constant or a calibration run.")

    mass = _num(payload, "mass", None, 1e-9, 1e6, "Sample mass")
    if mass is None:
        raise InputError("Give the sample mass in grams.")
    corrections = _num(payload, "corrections", 0.0, 0.0, 1e9, "Ignition corrections")
    mode = payload.get("mode") or "predict"

    result: Dict[str, Any] = {"mode": mode, "C_cal": C_cal, "C_cal_cal": C_cal / cal,
                              "calibration": calibration, "joule_per_cal": cal, "T": T0}
    if mode == "predict":
        fuel = _species_id(payload.get("fuel"), "The fuel")
        run = heatbalance.calorimeter_run(fuel, mass, C_cal, corrections)
        result["run"] = run
        result["warnings"] = ([{"level": "info", "message": SPECIES[fuel].remark}]
                              if SPECIES[fuel].remark else [])
    elif mode == "identify":
        dT = _num(payload, "dT", None, 1e-9, 1e4, "Measured temperature rise")
        if dT is None:
            raise InputError("Give the measured temperature rise.")
        gases = payload.get("include_gases", False)
        if not isinstance(gases, bool):
            raise InputError("'include_gases' must be true or false.")
        result["identify"] = heatbalance.identify_fuel(mass, dT, C_cal, corrections, include_gases=gases)
        best = result["identify"]["candidates"][0]["fuel"]
        result["run"] = heatbalance.calorimeter_run(best, mass, C_cal, corrections)
        result["warnings"] = []
    else:
        raise InputError("The mode must be 'predict' or 'identify'.")
    return _safe(result)


# ---------------------------------------------------------------------------
# 6. sensible heat of a single species
# ---------------------------------------------------------------------------
def sensible(payload: dict) -> dict:
    sp, note = find_species(str(payload.get("species") or ""))
    T1 = _temperature(payload, "T1")
    T2 = _temperature(payload, "T2", 1000.0)
    moles = _num(payload, "moles", 1.0, 0.0, 1e12, "Amount")
    sp.require_cp()
    dH = sp.sensible_dH(T1, T2)
    dS = sp.sensible_dS(T1, T2)
    same = abs(T2 - T1) < 1e-9
    warnings = []
    if sp.cp_low is not None and min(T1, T2) < T0:
        warnings.append({
            "level": "info", "species": sp.id, "kind": "low_T_data",
            "message": (f"Below {T0} K the heat capacity of {sp.id} is not from SVN, whose tables start at 298 K. "
                        f"{sp.cp_low_source}."),
        })
    if sp.cp_high is not None and max(T1, T2) > sp.cp_main_Tmax:
        warnings.append({
            "level": "info", "species": sp.id, "kind": "high_T_data",
            "message": (f"Above {sp.cp_main_Tmax:g} K the heat capacity of {sp.id} is not from SVN, whose formula ends there. "
                        f"{sp.cp_high_source}."),
        })
    for T in (T1, T2):
        if not sp.in_cp_range(T):
            warnings.append({
                "level": "warning", "species": sp.id,
                "message": (f"{T:g} K is outside the validity range of the heat-capacity "
                            f"correlation of {sp.id} ({sp.cp_Tmin:g} to {sp.cp_Tmax:g} K)."),
            })
    Ts = _grid(min(T1, T2), max(T1, T2), 61) if not same else [T1]
    Ts = sorted(set(Ts) | _join_points(min(T1, T2), max(T1, T2), sp.breakpoints()))
    return _safe({
        "species": sp.to_dict(), "note": note, "T1": T1, "T2": T2, "moles": moles,
        "dH_molar": dH, "dS_molar": dS, "Q": moles * dH, "dS_total": moles * dS,
        "cp_T1": sp.cp_J(T1), "cp_T2": sp.cp_J(T2),
        # mean heat capacities by their definitions, so that an interval that
        # crosses 298.15 K (two sets of constants) is handled as well
        "mean_cp_H": sp.cp_J(T1) if same else dH / (T2 - T1),
        "mean_cp_S": sp.cp_J(T1) if same else dS / math.log(T2 / T1),
        "dH_constant_cp": sp.cp_J(T1) * (T2 - T1),
        "curve": {"T": Ts, "cp": [sp.cp_J(t) for t in Ts], "H": [sp.sensible_dH(T1, t) for t in Ts]},
        "warnings": warnings,
    })


# ---------------------------------------------------------------------------
# 7. balance check, validation, AI error challenge
# ---------------------------------------------------------------------------
def balance(payload: dict) -> dict:
    text = payload.get("equation")
    if not isinstance(text, str) or not text.strip():
        raise InputError("Please enter a reaction.")
    rxn = Reaction.parse(text, check_balance=False)
    bad = rxn.imbalance()
    out = {"equation": rxn.equation, "balanced": not bad, "notes": rxn.notes,
           "imbalance": {el: {"reactants": l, "products": r} for el, (l, r) in bad.items()},
           "suggestion": None}
    if bad:
        fix = suggest_balance(rxn.reactant_ids, rxn.product_ids)
        if fix:
            fixed = Reaction({s: (-fix[s] if s in rxn.reactant_ids else fix[s]) for s in fix})
            out["suggestion"] = fixed.equation
    return _safe(out)


def validate(payload: Optional[dict] = None) -> dict:
    rows = benchmarks.build()
    return _safe({"rows": rows, "summary": benchmarks.summary(rows)})


def literature(payload: Optional[dict] = None) -> dict:
    """Solver values next to published research values."""
    from . import literature as lit

    return _safe(lit.build())


def challenge(payload: Optional[dict] = None) -> dict:
    """The five stress tests of the assignment's AI Error Challenge, run live."""
    out: Dict[str, Any] = {}

    # 1. Stoichiometry: an unbalanced reaction must be rejected
    cases = []
    for text in ("CH4 + O2 -> CO2 + H2O", "N2 + H2 -> NH3", "CO2 + H2 -> CH3OH + H2O",
                 "CO + 2 H2 -> CH3OH"):
        try:
            Reaction.parse(text)
            cases.append({"input": text, "accepted": True, "message": "Balanced: accepted.",
                          "suggestion": None})
        except UnbalancedReactionError as exc:
            cases.append({"input": text, "accepted": False, "message": exc.message,
                          "suggestion": exc.details.get("suggestion")})
    out["stoichiometry"] = cases

    # 2. Constant Cp versus temperature-dependent Cp at 1000 K, for every predefined reaction.
    # A reaction whose heat-capacity data stop below 1000 K (a liquid, or a solid) gets no
    # numbers: comparing two shortcuts of a formula that does not hold there would mean nothing.
    T = 1000.0
    rows = []
    for rid, name, eq, *_ in library.REACTIONS:
        rxn = Reaction.parse(eq)
        vr = rxn.valid_range()
        row: Dict[str, Any] = {"id": rid, "name": name, "equation": rxn.equation, "T": T, "valid_range": vr,
                               "in_range": vr is not None and vr[0] - 1e-9 <= T <= vr[1] + 1e-9}
        if row["in_range"]:
            ev = rxn.evaluate(T)
            row.update({
                "dH": ev["dH"], "dH_const": ev["constant_cp"]["dH"], "dH_none": ev["dH0"],
                "dG": ev["dG"], "dG_const": ev["constant_cp"]["dG"], "dG_none": ev["no_cp"]["dG"],
                "K": ev["K"], "lnK": ev["lnK"],
                "lnK_const": -ev["constant_cp"]["dG"] / (R * T),
                "lnK_none": -ev["no_cp"]["dG"] / (R * T),
            })
        rows.append(row)
    out["cp_assumption"] = rows
    inside = [r for r in rows if r["in_range"]]

    def errors(key: str) -> Dict[str, Any]:
        errs = [abs(r[key] - r["dH"]) for r in inside]
        worst = max(inside, key=lambda r: abs(r[key] - r["dH"]))
        return {"mean": sum(errs) / len(errs), "max": max(errs), "worst": worst["name"],
                "worst_error": worst[key] - worst["dH"]}

    out["cp_summary"] = {"T": T, "total": len(rows), "in_range": len(inside),
                         "constant": errors("dH_const"), "ignored": errors("dH_none")}

    # 3. Physical state: methane combustion with liquid water versus vapour
    liq = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)")
    gas = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
    vap = Reaction.parse("H2O(l) -> H2O(g)")
    out["physical_state"] = {
        "liquid": {"equation": liq.equation, "dH0": liq.dH0, "dG0": liq.dG0, "dS0": liq.dS0},
        "vapour": {"equation": gas.equation, "dH0": gas.dH0, "dG0": gas.dG0, "dS0": gas.dS0},
        "difference_dH": gas.dH0 - liq.dH0,
        "vaporisation_dH0": vap.dH0,
        "explained": 2 * vap.dH0,
    }

    # 4. Correlation validity: extrapolation must produce a warning
    ext = []
    for text, T in (("CH4 + H2O(g) -> CO + 3 H2", 1400.0), ("CH4 + H2O(g) -> CO + 3 H2", 2200.0),
                    ("H2 + 1/2 O2 -> H2O(l)", 450.0), ("CaCO3 -> CaO + CO2", 1500.0),
                    ("N2 + 3 H2 -> 2 NH3", 150.0)):
        rxn = Reaction.parse(text)
        w = [x for x in rxn.range_warnings(T) if x.get("kind") == "cp_extrapolation"]
        ext.append({"equation": rxn.equation, "T": T, "valid_range": rxn.valid_range(),
                    "warned": bool(w), "warnings": [x["message"] for x in w]})
    out["extrapolation"] = ext
    return _safe(out)


# ---------------------------------------------------------------------------
# single-reaction equilibrium with any feed (for scripts; the page uses the
# stoichiometric-feed result that analyze() and pressure() already return)
# ---------------------------------------------------------------------------
def equilibrium(payload: dict) -> dict:
    rxn = _reaction(payload)
    T = _temperature(payload)
    P = _pressure(payload)
    model = _model(payload, "ideal")
    feed = payload.get("feed") or None
    if feed is not None and not isinstance(feed, dict):
        raise InputError("The feed must map species to moles.")
    return _safe(reaction_equilibrium(rxn, T, P, feed, model))


ENDPOINTS: Dict[str, Callable[[dict], dict]] = {
    "database": database,
    "library": get_library,
    "analyze": analyze,
    "pressure": pressure,
    "pressure_overview": pressure_overview,
    "species_residual": species_residual,
    "eos_check": eos_check,
    "combine": combine,
    "formation": formation,
    "network": network,
    "heat_balance": heat_balance,
    "calorimeter": calorimeter,
    "sensible": sensible,
    "balance": balance,
    "validate": validate,
    "challenge": challenge,
    "literature": literature,
    "equilibrium": equilibrium,
}


def call(endpoint: str, payload_json: str = "{}") -> str:
    """Entry point for the browser: JSON text in, JSON text out, never raises."""
    not_json = json.dumps({"ok": False, "error": {"kind": "input_error",
                                                    "message": "The request was not valid JSON.", "details": {}}})
    try:
        # Besides malformed text, Python refuses whole numbers of more than 4300
        # digits (ValueError) and extremely deep nesting (RecursionError).
        payload = json.loads(payload_json) if payload_json else {}
    except (ValueError, RecursionError):
        return not_json
    try:
        func = ENDPOINTS.get(endpoint)
        if func is None:
            raise InputError(f"Unknown endpoint '{endpoint}'.")
        if not isinstance(payload, dict):
            raise InputError("The request must be a JSON object.")
        return json.dumps({"ok": True, "result": func(payload)}, allow_nan=False)
    except SolverError as exc:
        return json.dumps({"ok": False, "error": _safe(exc.to_dict())})
    except Exception as exc:  # an unexpected bug: report it, never crash the page
        return json.dumps({"ok": False, "error": {
            "kind": "internal_error",
            "message": f"Unexpected error in the solver ({type(exc).__name__}: {exc}). Please report this input.",
            "details": {}}})
