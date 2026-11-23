# Testing strategy

The grading question for this project is "are the numbers right?", so the tests are built around that, in layers. Each layer catches a different kind of mistake.

## Run the tests

No installation is needed; the tests use only the Python standard library.

```
python -m unittest discover -s tests -t .
```

The same benchmarks can be printed as a table with `python -m thermosolver --validate`, and they run live in the browser on the Validation tab. Continuous integration (`.github/workflows/tests.yml`) runs the whole suite on every push for Python 3.10 to 3.13.

## The layers

| Layer | Question it answers | Where | How |
|---|---|---|---|
| 1. Data integrity | Was the data typed in correctly? | `tests/test_data_integrity.py` | SVN: Cp checksum against the printed Cp298/R column; molar mass from formula against Table B.1; ΔS°f plus CODATA element entropies against CODATA/NIST absolute entropies; physical sanity of critical constants. NIST species: the Shomate equation reproduced exactly, its integrals against NIST's own H(T) and S(T) functions, every point of the acetic acid table against the fit, and a check that exactly three species use outside data and all three say so. Outside cross-check (`tests/test_cross_check_janaf.py`): SVN formation data and SVN heat capacities over their whole range against rows of the NIST-JANAF tables, which a single mistyped constant would fail. High-temperature equations (`tests/test_high_temperature.py`): the NIST Shomate equations against NIST's own enthalpy and entropy functions and against JANAF rows up to 6000 K. Low-temperature rows (`tests/test_low_temperature.py`): every tabulated Cp reproduced, the enthalpy at 200 K carried exactly, and the 250 K rows and the entropy column, which were not used for the fit, reproduced within 0.01 J/(mol·K), 1.5 J/mol and 0.03 J/(mol·K) |
| 2. Reference values | Does the solver reproduce worked examples? | `thermosolver/benchmarks.py`, `tests/test_api.py`, `tests/test_heatbalance.py` | Values from SVN (sensible heat, ΔH° at 800 °C, K of ethylene hydration, residual-property table for n-butane, Gibbs-minimisation example, flame temperature and reformer heat requirement of Chapter 4), a cubic-EOS result from the course slides, the calibration of the bomb-calorimeter handout, six values from NIST tables below 298.15 K, and ten values on phase change: six boiling points of SVN Table B.1 and four values from the NIST saturation data of water, none of which the solver uses as data |
| 3. Thermodynamic identities | Are the equations mutually consistent? | `thermosolver/audit.py`, used in `tests/test_reaction.py`, `tests/test_realgas.py` | Kirchhoff, van 't Hoff, Gibbs-Helmholtz, Gᴿ = Hᴿ − TSᴿ, (∂ ln φ/∂P)_T = (Z − 1)/P, all by numerical differentiation; analytical integrals against Simpson quadrature |
| 4. Independent routes | Do two different methods give the same answer? | `tests/test_equilibrium.py`, `tests/test_reaction.py`, `tests/test_heatbalance.py` | Hess sum against direct evaluation; Gibbs minimisation against the single-reaction solver; closed-form water-gas-shift conversion; carbon activity against the Boudouard equilibrium; cubic roots substituted back into the pressure-explicit equation; the three-step heat path against the species-by-species enthalpy balance; an isothermal heat duty against ΔH°(T); heat duty and outlet temperature as inverses of each other for every library reaction; ideal work against numerical integration of (1 − T_σ/T)·Cp |
| 5. Physical behaviour | Do the trends make sense? | all test files | Le Chatelier in T and P; ideal-gas limit as P → 0; K = Psat/P° for water at 100 °C; liquid more stable than vapour at 25 °C; ammonia heat of reaction grows with pressure; excess air cools a flame, preheat and oxygen enrichment heat it; an endothermic reaction cools an adiabatic reactor; HHV − LHV equals the latent heat of the water formed; a flue gas cooled to 25 °C gives up more than the LHV and less than the HHV; ΔG° has no jump at a boiling point while ΔH° jumps by the latent heat; the equilibrium conversion has no jump where a product starts to condense |
| 6. Inputs and errors | Does bad input get a clear message and never a wrong number? | `tests/test_reaction.py`, `tests/test_api.py` | Unbalanced reactions rejected with the imbalance and a suggested fix; unknown species; ambiguous isomers; non-physical T and P; 1,500 random garbage inputs must never produce an internal error |
| 7. The assignment's AI Error Challenge | The five named stress tests | `tests/test_api.py` (`TestAIErrorChallenge`), `thermosolver/literature.py` | Stoichiometry rejection; constant against temperature-dependent Cp at 1000 K; H₂O(l) against H₂O(g) in methane combustion; extrapolation warnings; comparison with published values |
| 8. Whole library | Does everything in the menus actually run? | `tests/test_api.py` | Every predefined reaction, combination, network and heat-lab example is run through its endpoint and its audit must pass |
| 9. Review regressions | Do the bugs found in review stay fixed? | `tests/test_review_regressions.py`, `tests/test_heatbalance.py` | One test per finding of the independent code reviews, plus a structured fuzz: 6,000 random combinations of JSON types on every parameter of every endpoint |
| 10. The assignment brief | Is every requirement met? | `tests/test_assignment_brief.py` | One test per requirement of the brief: species and their data, predefined and own reactions, balance check, each calculation, plots, favourability at a temperature and at a pressure, the five stress tests, the deliverables |
| 11. Phase change | Does the solver find the right phase? | `tests/test_phase_change.py` | Boiling points against SVN Table B.1, vapour pressure of water against the NIST saturation table, the Clausius/Clapeyron slope, the jumps of ΔH° and ΔS° at a boiling point, continuity of ΔG° and of the conversion, the saturation of the outlet gas, heat duty and outlet temperature as inverses of each other with condensation, the lever rule for an outlet of pure water, and dH = T dS along the condensation |
| 12. Browser | Does the hosted page work? | manual, see below | Pyodide runs the same Python files, so layers 1 to 11 already cover the numbers |

In total: 420 tests in fifteen files, about 70 seconds. Five of them guard the deployment itself: the browser worker must list every solver module, `.nojekyll` must exist, every script the page loads must exist and carry the same version tag, the guide page must match its Markdown source, and no thermodynamic constant may appear in the JavaScript.

## What is deliberately not tested

- Plot appearance. Plots only draw arrays that the tested Python code returns.
- Kinetics, transport, or anything else the solver does not claim to calculate.

## Tolerances

- Table data and sums of table data: exact (1e-6 J/mol).
- Benchmarks against printed values: the last printed digit, typically 1e-3 to 1e-4 relative. SVN's worked solutions round intermediate values (for example Tr = 1.176), which gives differences of a few hundredths of a percent in the residual-property table.
- Numerical-derivative identities: 1e-6 relative for standard-state properties, 2e-5 for residual properties.
- Published research values: not asserted to a tight tolerance, because the sources use slightly different formation data. They are reported side by side with the difference (see the Validation tab).

## Browser check before a release

1. `python serve.py` and open http://localhost:8000.
2. The status pill turns green ("Solver ready") within about ten seconds on a first visit.
3. The start page shows eight question cards; each opens its tab with a result. Then open each of the seven tabs: no red error box, plots drawn.
4. Type `CH4 + O2 -> CO2 + H2O` on tab 1: it must be rejected and offer the balanced form.
5. On tab 4, the bars must be filled in colour, and when you drag the temperature slider they must follow. With everything allowed, the methanol and CO switches must be faded and only methane clickable; after "Methane off" they must show their shares.
6. On tab 2, ammonia at 200 bar must show the ideal gas (−106.50 kJ/mol) next to the real gas (−111.66 kJ/mol), and the word "fugacity" must not appear. Picking CO₂ hydrogenation must open at 50 bar with no red box; at 200 bar a blue box must offer "Use 88 bar".
7. On tab 5 (bomb calorimeter), "Ignite" with 1 g of ethanol must give a rise of 2.31 °C and draw the temperature curve; "Identify" with 1.00 g and 2.30 °C must name ethanol first.
8. On tab 1, type `H2 + 1/2 O2 -> H2O(l)` at 500 K: a blue box must say that this is not the stable phase and offer "Pick the stable phase"; after a click the reaction must read H2O(g) and the energy plot must show a step at 373.2 K.
9. Tab 1 shows no equilibrium constant, no conversion and no pressure box, and has three graphs. The four graphs of tab 2 cover the same range of values, and the text writes steps 1 and 3 out as sums of ν·Hᴿ. Tab 4 shows no method line, no table of numbers and no soot graph, but keeps the solid-carbon card.
10. Tab 7 must report every reference value as "pass".

## Bugs the tests have caught so far

See [DEBUG_LOG.md](DEBUG_LOG.md).
