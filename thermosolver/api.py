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
from typing import Any, Callable, Dict, List, Optional

from . import benchmarks, library
from .audit import audit_reaction, audit_residuals
from .combine import combine_reactions, formation_decomposition, formation_reaction
from .constants import FARADAY, P0, R, T0
from .data import SOURCES
from .electrochem import electrochemistry, electrochemistry_sweep, electron_count
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


def _sweep_range(rxn: Reaction, payload: dict):
    rng = rxn.valid_range()
    if rng is None:
        return None
    lo = _num(payload, "T_min", None, 1.0, T_ABS_MAX, "Minimum temperature")
    hi = _num(payload, "T_max", None, 1.0, T_ABS_MAX, "Maximum temperature")
    lo = rng[0] if lo is None else lo
    hi = rng[1] if hi is None else hi
    if lo < 298.15 and rng[0] <= 298.15 and payload.get("T_min") in (None, ""):
        lo = 298.15
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
        "constants": {"R": R, "T0": T0, "P0": P0, "F": FARADAY},
        "sources": SOURCES,
        "models": MODEL_NAMES,
        "data_notes": [
            {"species": "H2O2(g)", "reason": "Hydrogen peroxide is absent from SVN Tables B.1 and C.1 to C.4. The gas is taken from the NIST Chemistry WebBook (NIST-JANAF: ΔH°f = -136.11 kJ/mol, S° = 232.95 J/(mol·K), Shomate heat-capacity equation, 298 to 1500 K). It has no critical constants in Table B.1, so it is an ideal gas in pressure calculations. Liquid H2O2 is not included."},
            {"species": "CH3COOH(g)", "reason": "Acetic acid vapour is not in SVN. NIST Chemistry WebBook: ΔH°f = -432.9 kJ/mol, S° = 282.84 J/(mol·K), heat capacity fitted to the tabulated values (largest deviation 0.21 %). Values are for the ideal-gas monomer; the real vapour is partly dimerised."},
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
    electro = []
    for rid, label in library.ELECTRO_EXAMPLES:
        row = library.reaction_by_id(rid)
        electro.append({"id": rid, "label": label, "equation": row[2]})
    return _safe({
        "reactions": reactions,
        "combinations": combos,
        "networks": library.NETWORKS,
        "electro_examples": electro,
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
    steps += [
        {"title": "Heat-capacity change of reaction",
         "formula": ("ΔCp°/R = ΔA + ΔB·T + ΔC·T² + ΔD·T⁻²"
                     + (" + ΔE·T³" if ev["dE"] else "") + ",  Δ = Σ νᵢ (…)ᵢ"),
         "work": (f"ΔA = {ev['dA']:.4g},  ΔB = {ev['dB']:.4e},  "
                  f"ΔC = {ev['dC']:.4e},  ΔD = {ev['dD']:.4e}"
                  + (f",  ΔE = {ev['dE']:.4e}" if ev["dE"] else "")),
         "value": ev["dCp"], "unit": f"J/(mol·K) at {T:g} K"},
        {"title": f"Standard heat of reaction at {T:g} K",
         "formula": "ΔH°(T) = ΔH°₂₉₈ + R ∫ (ΔCp°/R) dT",
         "work": f"{ev['dH0']:,.0f} + 8.314 × ({ev['IDCPH']:,.3f} K)",
         "value": ev["dH"], "unit": "J/mol"},
        {"title": f"Standard entropy change at {T:g} K",
         "formula": "ΔS°(T) = ΔS°₂₉₈ + R ∫ (ΔCp°/R) dT/T",
         "work": f"{ev['dS0']:,.3f} + 8.314 × ({ev['IDCPS']:,.5f})",
         "value": ev["dS"], "unit": "J/(mol·K)"},
        {"title": f"Standard Gibbs energy change at {T:g} K",
         "formula": "ΔG°(T) = ΔH°(T) − T·ΔS°(T)",
         "work": f"{ev['dH']:,.0f} − {T:g} × ({ev['dS']:,.3f})",
         "value": ev["dG"], "unit": "J/mol"},
        {"title": "Equilibrium constant",
         "formula": "ln K = −ΔG°(T) / (R·T)",
         "work": f"−({ev['dG']:,.0f}) / (8.314 × {T:g})",
         "value": ev["lnK"], "unit": "(ln K)"},
    ]
    return steps


def _T_sweep(rxn: Reaction, lo: float, hi: float, n: int) -> dict:
    Ts = _grid(lo, hi, n)
    rng = rxn.valid_range()
    out: Dict[str, list] = {k: [] for k in (
        "T", "dH", "dS", "dG", "TdS", "lnK", "log10K", "dCp",
        "dH_const_cp", "dG_const_cp", "dG_no_cp", "in_range")}
    for T in Ts:
        dH, dS = rxn.dH(T), rxn.dS(T)
        dG = dH - T * dS
        lnK = -dG / (R * T)
        out["T"].append(T)
        out["dH"].append(dH)
        out["dS"].append(dS)
        out["dG"].append(dG)
        out["TdS"].append(T * dS)
        out["lnK"].append(lnK)
        out["log10K"].append(lnK / math.log(10.0))
        out["dCp"].append(rxn.dCp(T))
        out["dH_const_cp"].append(rxn.dH_constant_cp(T))
        out["dG_const_cp"].append(rxn.dG_constant_cp(T))
        out["dG_no_cp"].append(rxn.dG_no_cp(T))
        out["in_range"].append(bool(rng and rng[0] - 1e-9 <= T <= rng[1] + 1e-9))
    return out


def analyze(payload: dict) -> dict:
    """Standard heat of reaction, entropy and Gibbs energy at T, with the
    temperature sweep, warnings, written-out steps and consistency audit."""
    rxn = _reaction(payload)
    T = _temperature(payload)
    ev = rxn.evaluate(T)
    result = {
        "equation": rxn.equation,
        "name": rxn.name,
        "notes": rxn.notes,
        "stoich": rxn.stoich,
        "T": T,
        "at_T": ev,
        "species": rxn.species_table(T),
        "warnings": rxn.range_warnings(T),
        "valid_range": rxn.valid_range(),
        "crossover": rxn.crossover_temperatures(),
        "audit": audit_reaction(rxn, T),
        "formation": formation_decomposition(rxn),
        "steps": _derivation(rxn, ev),
        "has_cp": rxn.has_cp,
        "sweep": None,
        "equilibrium": None,
    }
    rng = _sweep_range(rxn, payload)
    if rng:
        result["sweep"] = _T_sweep(rxn, rng[0], rng[1], _points(payload, 81))
    try:
        result["equilibrium"] = reaction_equilibrium(rxn, T, P0, model="ideal")
    except SolverError as exc:
        result["equilibrium"] = {"error": exc.message}
    return _safe(result)


# ---------------------------------------------------------------------------
# 2. pressure effect at constant temperature (residual properties)
# ---------------------------------------------------------------------------
def pressure(payload: dict) -> dict:
    rxn = _reaction(payload)
    T = _temperature(payload)
    P = _pressure(payload)
    model = _model(payload)
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
        })

    try:
        eq_real = reaction_equilibrium(rxn, T, P, model=model)
    except SolverError as exc:
        eq_real = {"conversion": None, "limiting_reactant": None, "error": exc.message}

    result = {
        "equation": rxn.equation, "T": T, "P": P, "model": model,
        "at_P": at_P,
        "sweep": sweep,
        "models": models,
        "equilibrium_ideal": reaction_equilibrium(rxn, T, P, model="ideal"),
        "equilibrium_real": eq_real,
        "audit": audit_residuals(rxn, T, P, model),
        "warnings": rxn.range_warnings(T),
    }
    return _safe(result)


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
    hi_default = min(SPECIES[s].cp_Tmax for s in ids)
    sweep = None
    if variable == "T":
        lo = _num(payload, "T_min", max(lo_default, 300.0), 1.0, T_ABS_MAX, "Minimum temperature")
        hi = _num(payload, "T_max", hi_default, 1.0, T_ABS_MAX, "Maximum temperature")
        xs = _grid(lo, hi, _points(payload, 41)) if hi > lo else []
    elif variable == "P":
        lo = _num(payload, "P_min", 1.0, P_ABS_MIN, P_ABS_MAX, "Minimum pressure")
        hi = _num(payload, "P_max", max(P, 100.0), P_ABS_MIN, P_ABS_MAX, "Maximum pressure")
        xs = _grid(lo, hi, _points(payload, 41)) if hi > lo else []
    else:
        raise InputError("The sweep variable must be 'T' or 'P'.")
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
# 5. feature: electrochemical lens
# ---------------------------------------------------------------------------
def electro(payload: dict) -> dict:
    rxn = _reaction(payload)
    T = _temperature(payload)
    P = _pressure(payload)
    model = _model(payload, "ideal")
    n = _num(payload, "n_electrons", None, 1e-6, 1e4, "Number of electrons")
    T_cold = _num(payload, "T_cold", T0, 1.0, T_ABS_MAX, "Cold-reservoir temperature")
    point = electrochemistry(rxn, T, n, P, model, T_cold)
    auto_n, basis = electron_count(rxn)
    result = {
        "equation": rxn.equation, "point": point,
        "auto_n": auto_n, "auto_basis": basis,
        "warnings": rxn.range_warnings(T),
        "sweep": None,
    }
    rng = _sweep_range(rxn, payload)
    if rng:
        Ts = _grid(rng[0], rng[1], _points(payload, 61))
        result["sweep"] = electrochemistry_sweep(rxn, Ts, n, P, model, T_cold)
    return _safe(result)


# ---------------------------------------------------------------------------
# 6. sensible heat of a single species
# ---------------------------------------------------------------------------
def sensible(payload: dict) -> dict:
    sp, note = find_species(str(payload.get("species") or ""))
    T1 = _temperature(payload, "T1")
    T2 = _temperature(payload, "T2", 1000.0)
    moles = _num(payload, "moles", 1.0, 0.0, 1e12, "Amount")
    cp = sp.require_cp()
    dH = sp.sensible_dH(T1, T2)
    dS = sp.sensible_dS(T1, T2)
    warnings = []
    for T in (T1, T2):
        if not sp.in_cp_range(T):
            warnings.append({
                "level": "warning", "species": sp.id,
                "message": (f"{T:g} K is outside the validity range of the heat-capacity "
                            f"correlation of {sp.id} ({sp.cp_Tmin:g} to {sp.cp_Tmax:g} K)."),
            })
    Ts = _grid(min(T1, T2), max(T1, T2), 61) if abs(T2 - T1) > 1e-9 else [T1]
    return _safe({
        "species": sp.to_dict(), "note": note, "T1": T1, "T2": T2, "moles": moles,
        "dH_molar": dH, "dS_molar": dS, "Q": moles * dH, "dS_total": moles * dS,
        "cp_T1": sp.cp_J(T1), "cp_T2": sp.cp_J(T2),
        "mean_cp_H": R * mcph(T1, T2, cp), "mean_cp_S": R * mcps(T1, T2, cp),
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

    # 2. Constant Cp versus temperature-dependent Cp at 1000 K
    rows = []
    for rid in ("smr", "ammonia", "methanol_synthesis", "co2_methanol", "wgs", "dry_reforming"):
        _, name, eq, *_ = library.reaction_by_id(rid)
        rxn = Reaction.parse(eq)
        T = 1000.0
        ev = rxn.evaluate(T)
        rows.append({
            "name": name, "equation": rxn.equation, "T": T,
            "dH": ev["dH"], "dH_const": ev["constant_cp"]["dH"], "dH_none": ev["dH0"],
            "dG": ev["dG"], "dG_const": ev["constant_cp"]["dG"], "dG_none": ev["no_cp"]["dG"],
            "K": ev["K"], "lnK": ev["lnK"],
            "lnK_const": -ev["constant_cp"]["dG"] / (R * T),
            "lnK_none": -ev["no_cp"]["dG"] / (R * T),
        })
    out["cp_assumption"] = rows

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
                    ("N2 + 3 H2 -> 2 NH3", 250.0)):
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
    "species_residual": species_residual,
    "combine": combine,
    "formation": formation,
    "network": network,
    "electro": electro,
    "sensible": sensible,
    "balance": balance,
    "validate": validate,
    "challenge": challenge,
    "literature": literature,
    "equilibrium": equilibrium,
}


def call(endpoint: str, payload_json: str = "{}") -> str:
    """Entry point for the browser: JSON text in, JSON text out, never raises."""
    try:
        func = ENDPOINTS.get(endpoint)
        if func is None:
            raise InputError(f"Unknown endpoint '{endpoint}'.")
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise InputError("The request must be a JSON object.")
        return json.dumps({"ok": True, "result": func(payload)}, allow_nan=False)
    except SolverError as exc:
        return json.dumps({"ok": False, "error": _safe(exc.to_dict())})
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": {"kind": "input_error",
                                                   "message": "The request was not valid JSON.", "details": {}}})
    except Exception as exc:  # an unexpected bug: report it, never crash the page
        return json.dumps({"ok": False, "error": {
            "kind": "internal_error",
            "message": f"Unexpected error in the solver ({type(exc).__name__}: {exc}). Please report this input.",
            "details": {}}})
