# Debug log

What went wrong while building the solver, how it was found, and what was done about it. Kept honest on purpose: this is the raw material for the "AI Error Challenge" part of the report.

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
