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

## Change made after this review

Hydrogen peroxide gas and acetic acid (vapour, and a heat capacity for the liquid) were added from the NIST Chemistry WebBook, which needed an optional T³ term in the heat-capacity functions and a separate electron-count rule for peroxide. This code was not part of the independent review. It is covered by its own tests (`TestOtherSources`, `test_reactions_with_nist_species`, `test_electron_count_with_hydrogen_peroxide`, `test_nist_species_through_the_api`) and by the existing consistency audit, which runs on every library reaction including the new ones.
