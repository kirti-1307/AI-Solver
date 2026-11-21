"""Species objects built from the SVN tables, and the name lookup."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import data
from .constants import R, T0
from .errors import DataUnavailableError, InputError, UnknownSpeciesError
from .formula import molar_mass, parse_formula
from .heatcap import Coeffs, cp_over_r, icph, icps, shomate_to_coeffs


@dataclass(frozen=True)
class Critical:
    """Row of SVN Table B.1."""

    molar_mass: float
    omega: float
    Tc: float          # K
    Pc: float          # bar
    Zc: float
    Vc: float          # cm^3/mol
    Tn: Optional[float]  # normal boiling point, K


@dataclass(frozen=True)
class Species:
    id: str
    name: str
    formula: str
    phase: str                      # 'g', 'l' or 's'
    dHf: float                      # J/mol, standard enthalpy of formation at 298.15 K
    dGf: float                      # J/mol, standard Gibbs energy of formation at 298.15 K
    cp: Optional[Coeffs]            # (A, B, C, D) of Cp/R, or None if SVN gives no Cp
    cp_Tmin: Optional[float]        # K
    cp_Tmax: Optional[float]        # K
    cp298_tab: Optional[float]      # Cp/R at 298.15 K as printed in SVN (checksum only)
    critical: Optional[Critical]
    cp_source: str
    elements: Dict[str, int] = field(default_factory=dict, compare=False, hash=False)
    formation_source: str = data.SOURCES["formation"]
    from_svn: bool = True           # False when any property comes from outside SVN

    @property
    def remark(self) -> Optional[str]:
        """A caution about this species' data that is shown whenever it is used."""
        return data.SPECIES_REMARKS.get(self.id)

    # --- formation properties -------------------------------------------------
    @property
    def dSf(self) -> float:
        """Standard entropy of formation at 298.15 K, J/(mol K).

        From the definition G = H - T S applied to the formation reaction:
        dSf = (dHf - dGf) / T0.  Uses SVN Table C.4 only.
        """
        return (self.dHf - self.dGf) / T0

    @property
    def S298_absolute(self) -> Optional[float]:
        """Third-law entropy at 298.15 K, J/(mol K). Display and cross-check
        only: dSf (SVN) plus the CODATA entropies of the elements."""
        total = self.dSf
        for el, n in self.elements.items():
            s_el = data.ELEMENT_ENTROPY_CODATA.get(el)
            if s_el is None:
                return None
            total += n * s_el
        return total

    @property
    def molar_mass(self) -> float:
        return self.critical.molar_mass if self.critical else molar_mass(self.formula)

    @property
    def is_element(self) -> bool:
        ref = data.ELEMENT_REFERENCE
        return len(self.elements) == 1 and ref.get(next(iter(self.elements)), ("",))[0] == self.id

    # --- heat capacity --------------------------------------------------------
    def require_cp(self) -> Coeffs:
        if self.cp is None:
            raise DataUnavailableError(
                f"SVN gives no heat-capacity correlation for {self.id} ({self.name}). "
                f"It can only be used at {T0} K.",
                {"species": self.id},
            )
        return self.cp

    def cp_R(self, T: float) -> float:
        """Cp/R at T."""
        return cp_over_r(self.require_cp(), T)

    def cp_J(self, T: float) -> float:
        """Cp in J/(mol K) at T."""
        return R * self.cp_R(T)

    def in_cp_range(self, T: float) -> bool:
        if self.cp is None:
            return abs(T - T0) < 1e-6
        return self.cp_Tmin - 1e-9 <= T <= self.cp_Tmax + 1e-9

    # --- standard-state properties at T ----------------------------------------
    def sensible_dH(self, T1: float, T2: float) -> float:
        """Sensible enthalpy change, integral of Cp dT from T1 to T2, J/mol."""
        if abs(T1 - T2) < 1e-12:
            return 0.0
        return R * icph(T1, T2, self.require_cp())

    def sensible_dS(self, T1: float, T2: float) -> float:
        """Entropy change at constant pressure, integral of Cp dT/T, J/(mol K)."""
        if abs(T1 - T2) < 1e-12:
            return 0.0
        return R * icps(T1, T2, self.require_cp())

    def H(self, T: float) -> float:
        """Standard-state enthalpy at T on the formation scale, J/mol:
        H(T) = dHf298 + integral of Cp dT from 298.15 K to T."""
        return self.dHf + self.sensible_dH(T0, T)

    def S(self, T: float) -> float:
        """Standard-state entropy at T on the formation scale, J/(mol K):
        S(T) = dSf298 + integral of Cp dT/T from 298.15 K to T."""
        return self.dSf + self.sensible_dS(T0, T)

    def G(self, T: float) -> float:
        """Standard-state Gibbs energy at T on the formation scale, J/mol.

        G(T) = H(T) - T*S(T).  At 298.15 K this equals dGf298.  At other
        temperatures it is NOT the Gibbs energy of formation (the elements are
        referenced at 298.15 K), but the stoichiometric sum over any balanced
        reaction gives exactly the standard Gibbs energy change of reaction.
        """
        return self.H(T) - T * self.S(T)

    def to_dict(self) -> dict:
        crit = self.critical
        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "phase": self.phase,
            "elements": dict(self.elements),
            "molar_mass": round(self.molar_mass, 3),
            "dHf": self.dHf,
            "dGf": self.dGf,
            "dSf": self.dSf,
            "S298_absolute": self.S298_absolute,
            "cp": list(self.cp) if self.cp else None,
            "cp_Tmin": self.cp_Tmin,
            "cp_Tmax": self.cp_Tmax,
            "cp298_R": cp_over_r(self.cp, T0) if self.cp else None,
            "cp298_R_tab": self.cp298_tab,
            "cp_source": self.cp_source,
            "formation_source": self.formation_source,
            "from_svn": self.from_svn,
            "remark": self.remark,
            "is_element": self.is_element,
            "critical": None
            if crit is None
            else {
                "omega": crit.omega,
                "Tc": crit.Tc,
                "Pc": crit.Pc,
                "Zc": crit.Zc,
                "Vc": crit.Vc,
                "Tn": crit.Tn,
            },
        }


# ---------------------------------------------------------------------------
# Build the database
# ---------------------------------------------------------------------------
def _critical(name: str) -> Optional[Critical]:
    row = data.CRITICAL.get(name)
    return Critical(*row) if row else None


def gibbs_of_formation_from_entropy(dHf: float, S298: float, elements: Dict[str, int]) -> float:
    """dGf298 = dHf298 - T0 * (S298 - sum of element entropies), in J/mol.

    Used for species whose source (NIST) gives the absolute entropy instead
    of the Gibbs energy of formation.
    """
    s_elements = sum(n * data.ELEMENT_ENTROPY_CODATA[el] for el, n in elements.items())
    return dHf - T0 * (S298 - s_elements)


def _build() -> Dict[str, Species]:
    db: Dict[str, Species] = {}

    # ---- SVN species -----------------------------------------------------------
    for sid, name, formula, tmax, cp298, A, B3, C6, D5, dHf, dGf in data.GASES:
        db[sid] = Species(
            sid, name, formula, "g", float(dHf), float(dGf),
            (A, B3 * 1e-3, C6 * 1e-6, D5 * 1e5, 0.0), 298.0, float(tmax), cp298,
            _critical(name), data.SOURCES["cp_gas"], parse_formula(formula),
        )
    for sid, name, formula, cp298, A, B3, C6, dHf, dGf in data.LIQUIDS:
        db[sid] = Species(
            sid, name, formula, "l", float(dHf), float(dGf),
            (A, B3 * 1e-3, C6 * 1e-6, 0.0, 0.0), 273.15, 373.15, cp298,
            _critical(name), data.SOURCES["cp_liquid"], parse_formula(formula),
        )
    for sid, name, formula, dHf, dGf in data.LIQUIDS_298_ONLY:
        extra = data.NIST_LIQUID_CONSTANT_CP.get(sid)
        if extra:
            # Formation data from SVN Table C.4, constant heat capacity from NIST
            cp_J, tmin, tmax = extra
            db[sid] = Species(
                sid, name, formula, "l", float(dHf), float(dGf),
                (cp_J / R, 0.0, 0.0, 0.0, 0.0), tmin, tmax, None,
                _critical(name), data.SOURCES["nist_acetic_liquid"], parse_formula(formula),
                from_svn=False,
            )
        else:
            db[sid] = Species(
                sid, name, formula, "l", float(dHf), float(dGf),
                None, None, None, None,
                _critical(name), "not tabulated in SVN", parse_formula(formula),
            )
    for sid, name, formula, tmax, cp298, A, B3, D5, dHf, dGf in data.SOLIDS:
        db[sid] = Species(
            sid, name, formula, "s", float(dHf), float(dGf),
            (A, B3 * 1e-3, 0.0, D5 * 1e5, 0.0), 298.0, float(tmax), cp298,
            None, data.SOURCES["cp_solid"], parse_formula(formula),
        )

    # ---- species from the NIST Chemistry WebBook ---------------------------------
    for sid, name, formula, dHf, S298, shomate, tmin, tmax in data.NIST_GASES_SHOMATE:
        elements = parse_formula(formula)
        db[sid] = Species(
            sid, name, formula, "g", float(dHf), gibbs_of_formation_from_entropy(dHf, S298, elements),
            shomate_to_coeffs(*shomate, R=R), tmin, tmax, None,
            _critical(name) if name in data.NIST_USE_SVN_CRITICAL else None,
            data.SOURCES["nist_h2o2"], elements,
            formation_source=data.SOURCES["nist_h2o2"], from_svn=False,
        )
    for sid, name, formula, dHf, S298, (A, B3, C6, D5, E9), tmin, tmax in data.NIST_GASES_FITTED:
        elements = parse_formula(formula)
        db[sid] = Species(
            sid, name, formula, "g", float(dHf), gibbs_of_formation_from_entropy(dHf, S298, elements),
            (A, B3 * 1e-3, C6 * 1e-6, D5 * 1e5, E9 * 1e-9), tmin, tmax, None,
            _critical(name) if name in data.NIST_USE_SVN_CRITICAL else None,
            data.SOURCES["nist_acetic_gas"], elements,
            formation_source=data.SOURCES["nist_acetic_gas"], from_svn=False,
        )
    return db


SPECIES: Dict[str, Species] = _build()

_PHASE_SUFFIX = re.compile(r"\((g|l|s|gas|liq|liquid|sol|solid|v|vap)\)$", re.IGNORECASE)
_PHASE_MAP = {"g": "g", "gas": "g", "v": "g", "vap": "g", "l": "l", "liq": "l",
              "liquid": "l", "s": "s", "sol": "s", "solid": "s"}
_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _build_lookup() -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    exact: Dict[str, List[str]] = {}   # case-sensitive formula-like keys
    loose: Dict[str, List[str]] = {}   # case-insensitive names

    def add(table, key, sid):
        bucket = table.setdefault(key, [])
        if sid not in bucket:
            bucket.append(sid)

    for sid, sp in SPECIES.items():
        base = sid[: sid.rindex("(")]
        add(exact, base, sid)
        add(exact, sp.formula, sid)
        add(loose, sp.name.lower(), sid)
        for alias in data.ALIASES.get(sid, []):
            add(exact, alias, sid)
            add(loose, alias.lower(), sid)
    return exact, loose


_EXACT, _LOOSE = _build_lookup()
_PHASE_PRIORITY = {"g": 0, "l": 1, "s": 2}


def find_species(text: str) -> Tuple[Species, Optional[str]]:
    """Resolve what the user typed to a Species.

    Returns ``(species, note)`` where ``note`` explains an assumption that was
    made (for example the phase when none was given) or is None.
    """
    raw = text.strip().translate(_SUBSCRIPTS)
    if not raw:
        raise InputError("A species name is missing in the reaction.")

    if raw in SPECIES:
        return SPECIES[raw], None

    phase = None
    base = raw
    m = _PHASE_SUFFIX.search(raw)
    if m:
        phase = _PHASE_MAP[m.group(1).lower()]
        base = raw[: m.start()].strip()

    candidates = _EXACT.get(base) or _EXACT.get(base.replace(" ", ""))
    if not candidates:
        candidates = _LOOSE.get(base.lower())
    if not candidates:
        raise UnknownSpeciesError(
            f"'{text.strip()}' is not in the SVN-based species database.",
            {"input": text.strip(), "suggestions": suggest_species(base)},
        )

    if phase is not None:
        matching = [c for c in candidates if SPECIES[c].phase == phase]
        if not matching:
            available = ", ".join(sorted(candidates))
            raise UnknownSpeciesError(
                f"SVN has no data for '{base}' in phase ({phase}). Available: {available}.",
                {"input": text.strip(), "suggestions": sorted(candidates)},
            )
        candidates = matching

    # Different compounds sharing one formula (e.g. C2H4O) cannot be guessed.
    names = {SPECIES[c].name for c in candidates}
    if len(names) > 1:
        options = ", ".join(f"{c} = {SPECIES[c].name}" for c in sorted(candidates))
        raise InputError(
            f"'{base}' is ambiguous. Please use one of: {options}.",
            {"input": text.strip(), "suggestions": sorted(candidates)},
        )

    candidates = sorted(candidates, key=lambda c: _PHASE_PRIORITY[SPECIES[c].phase])
    chosen = SPECIES[candidates[0]]
    note = None
    if phase is None and len(candidates) > 1:
        others = ", ".join(candidates[1:])
        note = (
            f"No phase was given for {base}; {chosen.id} was assumed "
            f"(also available: {others})."
        )
    return chosen, note


def suggest_species(text: str, limit: int = 5) -> List[str]:
    """Species ids whose id, formula or name resembles ``text``."""
    key = text.lower().replace(" ", "")
    scored = []
    for sid, sp in SPECIES.items():
        hay = [sid.lower(), sp.formula.lower(), sp.name.lower().replace(" ", "")]
        if any(key and (key in h or h in key) for h in hay):
            scored.append(sid)
    return sorted(scored)[:limit]
