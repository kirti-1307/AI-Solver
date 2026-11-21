"""Exception types. Every error the solver raises on purpose is a SolverError,
so the web front end can show a clear message instead of a stack trace."""

from __future__ import annotations

from typing import Any, Dict, Optional


class SolverError(Exception):
    """Base class for all expected solver errors."""

    kind = "solver_error"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "message": self.message, "details": self.details}


class InputError(SolverError):
    """The user input could not be understood (bad formula, bad number...)."""

    kind = "input_error"


class UnknownSpeciesError(SolverError):
    """A species is not in the SVN-based database."""

    kind = "unknown_species"


class UnbalancedReactionError(SolverError):
    """The reaction does not conserve every element."""

    kind = "unbalanced_reaction"


class DataUnavailableError(SolverError):
    """The calculation needs data that SVN does not tabulate for a species."""

    kind = "data_unavailable"


class PhaseError(SolverError):
    """A gas-phase calculation was asked for a state where a species has no
    vapour-like state (it would be a liquid)."""

    kind = "phase_error"


class ConvergenceError(SolverError):
    """An iterative calculation did not converge."""

    kind = "convergence_error"
