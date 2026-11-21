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
| 1. Data integrity | Was the data typed in correctly? | `tests/test_data_integrity.py` | SVN: Cp checksum against the printed Cp298/R column; molar mass from formula against Table B.1; ΔS°f plus CODATA element entropies against CODATA/NIST absolute entropies; physical sanity of critical constants. NIST species: the Shomate equation reproduced exactly, its integrals against NIST's own H(T) and S(T) functions, every point of the acetic acid table against the fit, and a check that exactly three species use outside data and all three say so |
| 2. Textbook benchmarks | Does the solver reproduce SVN's worked examples? | `thermosolver/benchmarks.py`, `tests/test_api.py` | Values printed in the book (sensible heat, ΔH° at 800 °C, K of ethylene hydration, residual-property table for n-butane, Gibbs-minimisation example, fuel-cell section), plus one cubic-EOS result from the course slides |
| 3. Thermodynamic identities | Are the equations mutually consistent? | `thermosolver/audit.py`, used in `tests/test_reaction.py`, `tests/test_realgas.py` | Kirchhoff, van 't Hoff, Gibbs-Helmholtz, Gᴿ = Hᴿ − TSᴿ, (∂ ln φ/∂P)_T = (Z − 1)/P, all by numerical differentiation; analytical integrals against Simpson quadrature |
| 4. Independent routes | Do two different methods give the same answer? | `tests/test_equilibrium.py`, `tests/test_reaction.py` | Hess sum against direct evaluation; Gibbs minimisation against the single-reaction solver; closed-form water-gas-shift conversion; carbon activity against the Boudouard equilibrium; cubic roots substituted back into the pressure-explicit equation |
| 5. Physical behaviour | Do the trends make sense? | all test files | Le Chatelier in T and P; ideal-gas limit as P → 0; K = Psat/P° for water at 100 °C; liquid more stable than vapour at 25 °C; ammonia heat of reaction grows with pressure |
| 6. Inputs and errors | Does bad input get a clear message and never a wrong number? | `tests/test_reaction.py`, `tests/test_api.py` | Unbalanced reactions rejected with the imbalance and a suggested fix; unknown species; ambiguous isomers; non-physical T and P; 1,500 random garbage inputs must never produce an internal error |
| 7. The assignment's AI Error Challenge | The five named stress tests | `tests/test_api.py` (`TestAIErrorChallenge`), `thermosolver/literature.py` | Stoichiometry rejection; constant against temperature-dependent Cp at 1000 K; H₂O(l) against H₂O(g) in methane combustion; extrapolation warnings; comparison with published values |
| 8. Whole library | Does everything in the menus actually run? | `tests/test_api.py` | Every predefined reaction, combination, network and electrochemical example is run through its endpoint and its audit must pass |
| 9. Review regressions | Do the bugs found in review stay fixed? | `tests/test_review_regressions.py` | One test per finding of the independent code review, plus a structured fuzz: 4,000 random combinations of JSON types on every parameter of every endpoint |
| 10. Browser | Does the hosted page work? | manual, see below | Pyodide runs the same Python files, so layers 1 to 9 already cover the numbers |

In total: 175 tests in six files, about 15 seconds. Four of them guard the deployment itself: the browser worker must list every solver module, `.nojekyll` must exist, every script the page loads must exist, and no thermodynamic constant may appear in the JavaScript.

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
3. Open each of the seven tabs: no red error box, plots drawn.
4. Type `CH4 + O2 -> CO2 + H2O` on tab 1: it must be rejected and offer the balanced form.
5. Tab 7 must report every textbook benchmark as "pass".

## Bugs the tests have caught so far

See [DEBUG_LOG.md](DEBUG_LOG.md).
