"""thermosolver: a thermodynamic reaction-energy solver built on the data and
equations of Smith, Van Ness & Abbott, *Introduction to Chemical Engineering
Thermodynamics*.

Quick start::

    from thermosolver import Reaction
    rxn = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
    rxn.dH(1073.15)      # -103,566 J/mol, the SVN worked example
    rxn.K(523.15)        # equilibrium constant at 250 C
"""

from .constants import FARADAY, P0, R, T0
from .errors import (
    ConvergenceError,
    DataUnavailableError,
    InputError,
    SolverError,
    UnbalancedReactionError,
    UnknownSpeciesError,
)
from .reaction import Reaction
from .species import SPECIES, Species, find_species

__version__ = "1.0.0"

__all__ = [
    "Reaction", "Species", "SPECIES", "find_species",
    "R", "T0", "P0", "FARADAY",
    "SolverError", "InputError", "UnknownSpeciesError", "UnbalancedReactionError",
    "DataUnavailableError", "ConvergenceError",
]
