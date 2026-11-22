# Code review: Thermodynamic Reaction Energy Solver v1.0

**Scope:** the whole `thermosolver/` package, the front end (`index.html`, `web/`) and the tests, before the first release.
**How:** an independent reviewer (a separate AI agent that had not written the code) read every file, re-derived the key equations on its own, and probed the solver with its own scripts. It was asked to hunt for wrong thermodynamics first, then crashes, misleading output, front-end problems and weak tests.

## Summary

The core thermodynamics was confirmed by independent derivation. The problems were in the newest code (the phase-state logic added the same day), in one plotting loop and in input hardening. Every critical and should-fix finding below has been fixed, and each has a regression test in `tests/test_review_regressions.py`.

## Critical issues (all fixed)

| # | File | Issue | Fix |
|---|---|---|---|
| C1 | `api.py`, `pressure()` | Ideal and real conversions were appended inside one `try`. When the real-gas point was refused, the ideal value had already been appended and then a `None` was added too, so `conversion_ideal` grew longer than the pressure axis and every later point was drawn at the wrong pressure. Ten of the presets were affected at the default 200 bar. | The two calculations are now separate, each with its own `try`. Both lists always have one entry per pressure. |
| C2 | `realgas.py`, `residual()` | A single cubic root below Tc was called "liquid-like" whenever P exceeded the Lee/Kesler vapour-pressure estimate. That is a different model from the equation being solved. For van der Waals and Redlich/Kwong there is a pressure window where the only root is a vapour, and the solver refused a valid calculation there. | The root is now classified by the equation of state itself: it is liquid-like only if its molar volume is below the critical volume that the same equation predicts (Z·Tr/Pr < Zc). The Lee/Kesler estimate is used for the warning text only. |
| C3a | `api.py` | `n_points` was passed straight to `int()`: text, lists or 1e999 produced an internal error. | Read through `_points()` with a range of 2 to 401. |
| C3b | `api.py`, `_model()` | A non-text model (for example a list) raised a `TypeError`. | Type check. |
| C3c | `api.py`, `network()` | Species list items were not checked to be text. | Type check. |
| C3d | `api.py`, `heatcap.py` | No lower bound on T: 1e-200 K underflowed `D/T²` into a division by zero. | Temperatures below 1 K are rejected with a message. |
| C3e | `reaction.py` | A coefficient with 310 digits became infinity, passed the balance test and crashed the formatter. | Coefficients must be finite and between 1e-6 and 1e6. |
| C3f | `equilibrium.py` | A feed of 1e308 mol overflowed. | Feed amounts are capped at 1e9 mol. |

## Should fix (all fixed)

| # | File | Issue | Fix |
|---|---|---|---|
| S1 | `electrochem.py` | With a real-gas model the automatic temperature sweep started at 298 K, where water has no vapour state, so a perfectly valid high-temperature point failed. | The sweep leaves a gap at such temperatures instead of failing. |
| S2 | `realgas.py` | When the Soave term 1 + κ(1 − √Tr) reached zero the gas was switched to ideal, a jump in Z, φ and Hᴿ (for N₂ with SRK at 1027 K, inside the range the presets use). | α now stays at zero beyond that point, and the residual expressions use dα/d ln Tr (finite) instead of d ln α/d ln Tr (singular). All properties are continuous. |
| S3 | `equilibrium.py` | With caller-supplied Gibbs energies the carbon activity mixed two reference scales. | Not reported in that case. |
| S4 | `tab-electro.js` | For an electrolytic reaction with ΔH < 0 (ammonia synthesis at 723 K) the page printed a negative "thermoneutral voltage" and called ΔH the "energy demand". | Separate wording for each sign combination of ΔG and ΔH; the thermoneutral voltage is shown only when it exists. |
| S5 | `tab-electro.js` | In electrolyser mode the temperature coefficient and Nernst shift were printed with the fuel-cell sign, contradicting the displayed voltage. | One sign convention applied to every printed voltage, slope and shift. |
| S6 | `tab-reaction.js` | ln K for the constant-Cp comparison was computed in JavaScript with R typed in, against the rule that no thermodynamics lives in the page. | The solver returns it. |
| S7 | `__main__.py` | The command line printed sums that the API blanks when a species has only a liquid root. | Same check as the API. |
| S8 | `tab-network.js` | Refused sweep points appeared as unexplained gaps. | The gaps are counted and explained under the plots. |
| S9 | `equilibrium.py` | A reaction that ran completely in reverse was labelled "no forward reaction". | New status `complete_reverse`. |
| S10 | `audit.py` | A fixed 0.01 K step made T − h negative for tiny T and produced an untrue error message. | Covered by the 1 K floor. |
| S11 | `tests/` | No test for any of the above; the fuzz test only varied four fields. | `test_review_regressions.py`: one test per finding, plus a structured fuzz of every parameter of every endpoint (4,000 cases). |

## Minor (fixed unless noted)

- Unused imports and dead code removed (`ZERO`, `PHASE_NAMES`, `get_species`, `Reaction.from_stoich`, `TS.lastReaction`).
- JSON `true` was accepted as a temperature of 1 K: now rejected.
- Notes of inert feed gases were reported although their fugacity coefficient is never used: no longer evaluated.
- ln K = 0 exactly was described as "K is less than 1": now "balanced".
- `TS.chem` put subscripts into plain prose ("1e3", "dH0"): it now subscripts only after an element symbol or a closing bracket, and the benchmark names use proper symbols.
- The desired outcome "warning shown" was styled in red: now styled as a pass.
- "ΔG° is negative at every temperature" was inferred from one temperature: reworded.
- The residual audit had about one marginal false failure in 26,000 random states: tolerance widened from 2 × 10⁻⁵ to 10⁻⁴ relative, with a small absolute allowance.
- Accessibility: tabs now have `aria-controls` and `aria-selected` from the start, panels have `role="tabpanel"`, result areas are live regions, and each species tick-box has its own label.
- **Not changed:** temperature and pressure are still validated in several layers (API, reaction, real gas). The duplication is deliberate defence in depth for people who call the Python functions directly.
- **Not changed:** two tests the review called tautological (`dH(T0) == dH0`, Hess sum equals direct evaluation) are kept as cheap guards against a future refactor breaking the identity.

## What the reviewer verified as correct

By its own derivation or by running its own code:

- ∫Cp dT and ∫Cp dT/T closed forms, including the D terms, and their equality with the SVN bracketed form.
- ΔG°(T): independent Gibbs-Helmholtz integration with its own quadrature for six reactions agreed to 10⁻³ J/mol.
- The cubic equation in Z (coefficients expanded by hand), Table 3.1 constants, both κ(ω) polynomials and d ln α/d ln Tr.
- Hᴿ, Sᴿ and ln φ for all four cubic equations against numerical integration of (Z − 1)/P and (∂Z/∂T)_P/P: ln φ to six decimals, Hᴿ within 0.05 J/mol.
- The virial expressions, the cm³·bar to joule factor and the hydrogen path.
- The single-reaction equilibrium condition and its monotonicity; limestone with inert nitrogen gives y(CO₂) = K/P; water with nitrogen at 350 K gives y = Psat/P.
- The Gibbs-minimisation Newton system against the Gordon-McBride equations; 47 edge cases converged with residuals below 10⁻¹².
- Carbon activity against the methane-cracking equilibrium to 14 digits (independent of the Boudouard test in the suite).
- Electrochemical relations and the automatic electron count for 15 reactions.
- 60,000 random real-gas states produced no exception and no NaN.
- No injection path through any of the 23 `innerHTML` sinks: user text always passes through an escaping function.
- Every displayed unit and scale factor in the seven tabs against the API fields.

## Verdict

Approved after the fixes above. All 166 tests passed at that point; the suite has since grown to 175 with the NIST species added after the review.

## Changes made after this review

Hydrogen peroxide gas and acetic acid (vapour, and a heat capacity for the liquid) were added from the NIST Chemistry WebBook, which needed an optional T³ term in the heat-capacity functions. That code is covered by its own tests (`TestOtherSources`, `test_reactions_with_nist_species`, `test_nist_species_through_the_api`) and by the consistency audit, which runs on every library reaction.

The electrochemical lens (findings S1, S4 and S5 above) was later removed and replaced by the heat lab. The heat lab and the live product slate were reviewed separately; see below.

# Second review: the heat lab and the live product slate (v1.1)

**Scope:** `thermosolver/heatbalance.py`, the endpoints `heat_balance` and `calorimeter`, the new library entries and benchmarks, `web/tab-heat.js`, `web/tab-network.js`, the new helpers in `web/ui.js`, and `tests/test_heatbalance.py`.
**How:** again a separate AI agent that had not written the code. It re-derived the energy balance with its own quadrature and root finder, sharing only the tabulated data, ran about 27,000 fuzz calls, read the page code against the fields the solver returns, and planted 18 deliberate faults in a copy of the code to see which ones the tests would miss.

## Summary

The energy balance, the flame temperature, the fuel numbers and the calorimeter were confirmed by independent calculation. The problems were in the goal seek, in the state handling of the page, in a few sentences that were only true for an exothermic adiabatic case, and in the tests, which were too easy to satisfy. Every finding below is fixed, and each has a test in `tests/test_heatbalance.py` (`TestSecondReview`).

## Critical (all fixed)

| # | Where | Issue | Fix |
|---|---|---|---|
| R1 | `heatbalance.excess_for_outlet_temperature` | The search for the excess that holds a temperature limit treated every failed calculation as "too hot". For an endothermic reactor fed at 1100 K and a limit of 1200 K it reported "134 % excess", where the outlet is in fact far below 1100 K. With a side reaction that needs oxygen it reported the smallest feasible excess (5 %) as the answer. | The outlet is evaluated on a grid of excess values, a setting that cannot be calculated is not a candidate, bisection runs only between two neighbouring points that enclose the target, and the answer is solved once more and returned only if it reproduces the target. Otherwise the reason says which range of outlet temperatures can be reached. |
| R2 | `web/tab-heat.js` | The excess and the air box were sent as "0" and "off" whenever they were hidden, and whether they were hidden depended on the previous reaction. After a single-reactant reaction, a hydrogen flame was calculated without air (4485 K) while the page showed 20 % excess air (2252 K). | The controls are always sent as they stand; the solver ignores what cannot apply. After an error every control is shown again. |
| R3 | `web/tab-heat.js` | "More inert means a cooler outlet" was printed for every case. For an endothermic adiabatic reactor more inert gives a warmer outlet, and with a fixed outlet temperature the sentence means nothing. | The sentence now says that an inert pulls the outlet towards the inlet temperature, and states the direction for the case at hand. In heat-duty mode it says that the inert adds to the duty. |
| R4 | `web/tab-heat.js` | With zero conversion the heat of reaction (0 kJ) was labelled "endothermic". | A third state, "nothing reacts". |

## Should fix (all fixed)

| # | Where | Issue | Fix |
|---|---|---|---|
| R5 | `web/tab-heat.js` | Choosing another basis always failed for a reaction with two reactants, because the old "reactant in excess" was sent along and was now the basis itself. | A new basis clears the reactant in excess, and the solver picks the default. |
| R6 | `api.py` | A whole number with more than 308 digits in a numeric field, more than 4300 digits anywhere, or 100,000 nested brackets gave an internal error instead of an input error. | `OverflowError` is handled where numbers are read, and `ValueError` and `RecursionError` where the JSON is parsed. Species names are limited to 200 characters. |
| R7 | `heatbalance.solve` | Only the search for the outlet temperature was kept inside the range where the summed heat capacity is positive. An inlet temperature, or a given outlet temperature, outside it was accepted, and the balance then returned a second root: with nothing reacting and pure oxygen at 5900 K the outlet came out at 4931 K. An inlet of "25" (meant as °C) gave 1891 K. | Both temperatures must lie inside the usable range of their stream (at least 200 K). The message reminds the user that the solver works in kelvin. |
| R8 | `api.py` | Limits were reported as fractions ("must be at most 1") although the page shows percent, and an excess above 5000 % failed on the default plot range. | Messages in percent, and the default plot range is clamped. |
| R9 | `heatbalance.build_case` | When the basis was also fed another way (nitrogen as the basis of N₂ + O₂ → 2 NO with air, or extra feed of the basis), "1 mol fed" and "100 % conversion" no longer meant what they said. | With air, nitrogen cannot be the basis; if nitrogen is another reactant, the air is its only source. Extra feed of the basis is refused. |

## Minor (fixed)

- Two values were computed in JavaScript (the heat taken up by the calorimeter and the bomb value per kilogram). Both now come from the solver.
- Double negatives in two sentences ("the remaining −x kJ is taken from", "needs −x kJ").
- Every slider step ran the 41-point plot and, with a temperature limit, the goal seek. While a slider moves only the point is calculated; the plot is greyed and redrawn on release.
- The key and excess selections were attributed to the text in the box at the time of the answer, not to the text that had been sent.
- The settings summary said "heat removed" for a field named "heat added".
- On the product slate a reversed plot range silently cleared the plots; it now says why.

## Tests

The reviewer planted 18 faults that the suite did not notice, among them heating values off by a factor of 1000, the air-fuel ratio without nitrogen, a calorimeter that ignores the sample mass, the goal seek ignoring the heat removed, the two enthalpy lines swapped, and the reformer example with a wrong extent. Two tests were pure arithmetic with no solver code in them. `TestSecondReview` now holds a test for each of these, and the handout check calls the solver's own function.

## What the reviewer verified as correct

With its own Gauss-Legendre quadrature and bisection, sharing only the tabulated constants:

- Flame temperature of methane with 20 % excess air: 2066.425 K, identical to the solver.
- Four further cases, all identical: propane with 50 % excess air and a 500 K feed (1985.72 K), the SO₂ bed (1026.90 K), the ethane cracker (110,844 J) and the lime kiln (265,804 J). The reformer example gives 328,012 J.
- Reactants with a coefficient other than 1 as the basis (hydrogen in ammonia synthesis, ammonia oxidation), side reactions, extra feed of a product, preheat and Q ≠ 0: the three steps of the path match and add up to Q.
- 3,000 random streams with solids, liquids and hydrocarbons: every temperature returned was the correct root, and every refusal was justified.
- Ideal work against its own integration of (1 − T_σ/T)·Cp.
- Combustion stoichiometry, Δn_gas, ΔU, heating values, air-fuel ratio and CO₂ per MJ for eight fuels including NH₃, HCN, H₂S and graphite, and Δn_gas for all 36 fuels.
- The calibration and the ΔU to ΔH conversion of the lab handout.
- Units and scale factors of every value the two tabs display, and that all user text is escaped.

## Verdict

Approved after the fixes above. The suite has 214 tests.
