"""Physical constants and reference conditions.

Everything here follows Smith, Van Ness, Abbott & Swihart, *Introduction to
Chemical Engineering Thermodynamics* (referred to as SVN in this package).

* R is the value printed in SVN Table A.2 and used in every worked example of
  the book. Using the same rounded value is what lets the solver reproduce the
  textbook answers digit for digit.
* The standard state is the one SVN defines in Sec. 4.3: the pure species at
  the standard-state pressure of 1 bar, as an ideal gas for gases and as the
  real pure liquid or solid for condensed phases.
* The reference temperature is 298.15 K, the temperature at which SVN
  Table C.4 lists the formation properties.
"""

R = 8.314            # J mol^-1 K^-1            (SVN Table A.2)
R_CM3_BAR = 83.14    # cm^3 bar mol^-1 K^-1     (SVN Table A.2)
T0 = 298.15          # K, reference temperature of SVN Table C.4
P0 = 1.0             # bar, standard-state pressure
FARADAY = 96485.0    # C mol^-1, Faraday constant as used in the SVN fuel-cell section

# Standard atomic weights. They are used only to cross-check the chemical
# formulas against the molar masses printed in SVN Table B.1 and to report a
# molar mass for the few species that are not in Table B.1.
ATOMIC_WEIGHTS = {
    "H": 1.008,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "S": 32.065,
    "Cl": 35.453,
    "Ca": 40.078,
    "Fe": 55.845,
}
