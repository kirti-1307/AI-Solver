# Debug log

What went wrong while building the solver, how it was found, and what was done about it. Kept honest on purpose: this is the raw material for the "AI Error Challenge" part of the report.

Items 5, 11 and 13 concern the electrochemical lens, the first version of extra feature 2. It was replaced by the heat lab in Round 5 because the course had not covered electrochemistry. The items are kept as a record of what was found at the time.

## Round 1: first full run of the test-suite (8 of 137 tests failed)

### 1. Residual enthalpy and fugacity coefficient disagreed (virial model)

- **Expected:** (∂ ln φ/∂T)_P = −Hᴿ/(R·T²), the Gibbs-Helmholtz relation, to numerical precision.
- **Actual:** off by 0.03 to 0.07 % for N₂ and NH₃ with the generalized virial correlation. The cubic equations passed.
- **Root cause:** the derivative constants printed in SVN, dB⁰/dTr = 0.675/Tr^2.6 and dB¹/dTr = 0.722/Tr^5.2, are the exact derivatives 0.422 × 1.6 = 0.6752 and 0.172 × 4.2 = 0.7224 rounded to three figures. ln φ uses B⁰ and B¹ themselves, Hᴿ uses the rounded derivatives, so the two are not exactly consistent.
- **Fix:** use the unrounded products (`realgas.DB0_COEFF`, `DB1_COEFF`). Effect on Hᴿ: at most 0.06 %.
- **Prevention:** the Gibbs-Helmholtz check runs for every model in the test-suite and live in the app's audit panel.

### 2. Crash at extreme conditions (overflow)

- **Actual:** `OverflowError: math range error` from the pressure endpoint at T = 1 K, P = 5000 bar.
- **Root cause:** `exp(ln φ)` with a huge ln φ. The result is physically meaningless there anyway, but the page must not crash.
- **Fix:** `safe_exp` returns infinity, which the API turns into "–". Covered by `test_extreme_but_legal_conditions`.

### 3. 1,3-Butadiene failed the heat-capacity checksum

- **Actual:** A, B, C give Cp298/R = 9.931; the table's own Cp298/R column says 10.720.
- **Investigation:** suspected a transcription error first. The row was compared with the printed table (two editions): the transcription is correct. The book's row is internally inconsistent; the measured value is about 9.6, so the constants are the reliable part.
- **Fix:** the constants are kept, the species is listed as the single documented exception to the checksum test, and the database page says so.

### 4. Ammonia ΔG°f: edition difference

- **Found by:** comparing the data file with the printed tables.
- **Actual:** I had −16,450 J/mol (6th edition). The 8th and 9th editions print −16,400 J/mol.
- **Fix:** changed to the 8th-edition value, with a comment. It moves K of ammonia synthesis by about 2 % at 700 K.

### 5. A benchmark was attributed to the wrong case

- **Actual:** a benchmark said "SVN fuel-cell section: 1.229 V". SVN works the hydrogen cell with water *vapour* as product and gets 1.184 V; 1.229 V is the liquid-water value from the same table.
- **Fix:** the benchmark now uses the book's case (ΔG = −228,572 J, Q = −13,246 J, E = 1.184 V, and the 60 °C values −242,168 and −226,997 J). The liquid-water value is still tested, labelled as a hand calculation.

### 6. Four failures were wrong test expectations, not solver bugs

| Test | What I assumed | What is actually true |
|---|---|---|
| Critical-point root of RK and PR equals 1/3 and 0.3074 | Exact | The critical point is a triple root. The five-digit Ω and Ψ of Table 3.1 perturb it by about the cube root of the rounding, roughly 0.01. Replaced by a stronger test: every root is substituted back into the pressure-explicit equation. |
| Dry reforming at 1400 K is carbon-free | a_C < 1 | A 1:1 CH₄:CO₂ feed sits exactly on the O/C = 1 line and stays marginally carbon-forming until about 1500 K (a_C = 1.12 at 1400 K). The solver was right; the Boudouard cross-check confirms it. The test now uses excess CO₂ for the carbon-free case. |
| Real gas at 1 bar equals the standard state within 10 J/mol | Exact enough | Σν·RT·ln φ at 1 bar is 10.4 J/mol for ammonia synthesis at 700 K: real, but tiny. Tolerance widened and a P → 0 check added. |
| Water boils where ΔG° = 0 inside the valid Cp range | Root exists | The SVN data put the root at 373.2 K, just above the 373.15 K limit of the liquid Cp correlation. Replaced by K(373.15 K) = Psat/P°. |

## Round 2: found while collecting numbers for the report

### 7. A liquid was silently used inside a gas-phase calculation

- **Actual:** CO₂ + 3 H₂ → CH₃OH + H₂O at 523 K with Peng/Robinson gave 21 % conversion at 50 bar but 48 % at 100 bar, with Σ ν Hᴿ jumping from −6 to −49 kJ/mol.
- **Root cause:** water at 523 K has a vapour pressure of about 40 bar. Up to about 80 bar the cubic equation still has a (metastable) vapour root, which is what a gas mixture needs. Above that only the liquid root is left, and the code took it without complaint: Hᴿ = −34 kJ/mol is essentially the heat of condensation, and φ was that of liquid water.
- **Fix:** every residual result now carries a state: vapour, hypothetical vapour (above the vapour pressure, vapour-like root still exists) or liquid-like. A liquid-like state is never passed into a gas-phase equilibrium (`PhaseError` with advice), the isotherm plots stop where the gas phase ends, and the summary cards show "–" instead of a number.
- **Prevention:** `test_a_liquid_root_is_never_passed_off_as_a_gas`.

### 8. A misleading sentence about favourability

- **Actual:** for ammonia synthesis at 723 K (K = 4.6 × 10⁻⁵) the explanation said "practically no reaction at equilibrium". At 200 bar the same reaction reaches 43 % conversion.
- **Root cause:** K was read as if it were a conversion. K refers to the 1-bar standard state, and for a reaction that changes the number of gas moles the conversion depends strongly on pressure.
- **Fix:** the wording now says where the equilibrium lies "with every species at 1 bar", and the Pressure tab gives a separate verdict from ΔG(T,P) at the chosen pressure, saying explicitly when pressure alone has changed the sign.

## Round 3: independent code review

The full list is in [CODE_REVIEW.md](CODE_REVIEW.md). The three that mattered most:

### 9. My own fix for item 7 was wrong for two of the four cubic equations

- **Actual:** the first version of the liquid-root check compared the pressure with the Lee/Kesler vapour-pressure estimate. For van der Waals and Redlich/Kwong the equation's own saturation pressure lies above that estimate, so there was a window (up to 14 bar wide for water) where a perfectly good vapour root was labelled "liquid" and the calculation was refused.
- **Root cause:** one model was being judged by another model.
- **Fix:** the root is classified by the equation of state itself, by comparing its molar volume with that equation's critical volume. A randomised test (4,000 states, all four equations) checks the rule.

### 10. The ideal-gas conversion curve was drawn at the wrong pressures

- **Actual:** on the Pressure tab, when the real-gas calculation stopped (item 7), the ideal-gas conversion list received an extra entry for every refused point, so the dashed "ideal gas" curve was shifted along the pressure axis: 45.8 % was plotted at 300 bar where the true value is 53.8 %.
- **Root cause:** two `append` calls inside one `try` block.
- **Fix:** separate `try` blocks, and a test that both lists have exactly one entry per pressure.

### 11. Electrolysis of an exothermic reaction was described wrongly

- **Actual:** for ammonia synthesis at 723 K (ΔG > 0 but ΔH < 0) the electrochemical tab printed a "thermoneutral voltage" of −0.184 V and called ΔH = −106.5 kJ/mol the "energy demand".
- **Fix:** the text and cards now distinguish the four sign combinations of ΔG and ΔH, and a thermoneutral voltage is shown only when ΔG and ΔH have the same sign.

## Round 4: adding species from the NIST Chemistry WebBook

### 12. NIST's own enthalpy function is not exactly zero at 298.15 K

- **Actual:** a test comparing the solver's sensible heat of H₂O₂ with NIST's Shomate enthalpy function H°(T) − H°(298.15) was off by a constant 0.0137 kJ/mol at every temperature.
- **Root cause:** not a solver error. NIST's rounded constants F and H leave the published function at −0.0137 kJ/mol at 298.15 K instead of zero (and the entropy function 0.01 J/(mol·K) off the tabulated S°).
- **Fix:** the test compares differences between two temperatures, where the offset cancels; the agreement is then exact to nine decimals. The solver itself integrates the heat-capacity equation and never uses F, G or H.

### 13. The electron count was wrong for hydrogen peroxide

- **Actual:** with the rule "4 electrons per O₂", H₂ + O₂ → H₂O₂ would have been given n = 4 and a voltage half the true one.
- **Root cause:** the rule assumes oxygen ends at oxidation state −2. In a peroxide it is −1.
- **Fix:** when H₂O₂ takes part, n is 2 per H₂, or 2 per O₂ if there is no H₂. Found before release, while adding the species.

## Round 5: replacing the electrochemical lens by the heat lab

Extra feature 2 was rebuilt on course material only: an energy balance on a reactor (flame temperature and heat duty, SVN Chapter 4) and a virtual bomb calorimeter that follows the lab handout. The product slate became a live reactor with sliders.

### 14. A heat capacity that turns negative could have produced a meaningless flame temperature

- **Risk found while designing the solver:** the outlet temperature is the root of H_out(T) = H_in + Q. The Cp polynomial of methane becomes negative above about 4400 K and that of graphite below about 210 K, both far outside their fitted ranges. There the enthalpy falls with temperature, so a plain root search can land on a second, meaningless root or report an outlet of several thousand kelvin.
- **Fix:** the search is confined to the interval around 298.15 K in which the summed heat capacity of the outlet stream is positive. If the balance has no solution there, the solver says so and suggests what to change (excess air, less conversion, heat removal).
- **Prevention:** `test_search_stays_where_the_heat_capacity_is_positive` and `test_flames_hotter_than_the_correlations_are_refused_with_advice`.

### 15. A test expected the impossible

- **Actual:** my own test asked for the adiabatic outlet temperature when half of an ethane feed at 1000 K is cracked to ethylene, and expected a number below 1000 K. The solver returned an error instead.
- **Investigation:** the feed carries 64.4 kJ/mol of sensible heat above 298.15 K, and cracking half of it absorbs 68.2 kJ/mol. The energy balance would put the outlet near 235 K, below anything the correlations describe. The solver was right to refuse.
- **Fix:** the test now uses a conversion of 20 % for the number, and separately checks that the 50 % case is refused with advice to preheat.

### 16. The calorimeter identified a gas as the unknown sample

- **Actual:** in "identify" mode a temperature rise of 2.31 °C for 1 g of sample returned ethylene oxide gas (29.56 MJ/kg) ahead of liquid ethanol (29.62 MJ/kg), the fuel the rise had been calculated from.
- **Root cause:** two things. The rise had been rounded to two decimals, which is honest, since a thermometer does no better. And the comparison ran over every combustible species, although a sample weighed into a crucible cannot be a gas.
- **Fix:** only liquids and solids are compared unless the user ticks "also compare with gases". The page also states that fuels with nearly equal calorific values cannot be told apart by this measurement.

### 17. Small display faults found in the browser

| What was seen | Cause | Fix |
|---|---|---|
| "CO 2 (g)" with gaps inside the product switches and in "79 % N 2" | The label was a flex container, so the text and each subscript became separate flex items with a gap between them | The label text is wrapped in one element |
| Four separate warnings for one flame (O₂, N₂, CO₂ and H₂O each above 2000 K) | One warning per species | Merged into one sentence on the page; the solver still returns them one by one |
| "feed, 298 K → 298.15 K" in the path | The inlet temperature was rounded to whole kelvin | Temperatures the user sets are shown with their decimals |
| A hidden checkbox stayed visible | `.form label { display: flex }` overrode the `hidden` attribute | `[hidden] { display: none !important }` |
| "Coke risk: yes" with a carbon activity of 10⁷ when methane is switched off at 523 K | Correct thermodynamics for a gas held away from full equilibrium, but alarming without context | The card now reads "can form", and the explanation says why the value is so large and that carbon, like methane, is a product a selective catalyst has to avoid |

