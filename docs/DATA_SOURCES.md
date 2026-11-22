# Data sources

Smith, Van Ness & Abbott, *Introduction to Chemical Engineering Thermodynamics* (SVN) is the source for everything it covers: 54 of the 57 species use SVN data only. Three entries that SVN does not cover come from the NIST Chemistry WebBook and are described in their own section below. Nothing is taken from an AI model's memory without being checked against the source itself.

The data lives in one file, [`thermosolver/data.py`](../thermosolver/data.py). The SVN tables are in the same column layout as the book so they can be compared row by row, and the NIST entries are kept in separate tables so that the two sources are never mixed silently.

## What comes from where

| Property | Symbol | Units | SVN table |
|---|---|---|---|
| Ideal-gas heat capacity constants | A, B, C, D in Cp/R = A + BT + CT² + DT⁻² | dimensionless, T in K | C.1 |
| Solid heat capacity constants | A, B, D | dimensionless | C.2 |
| Liquid heat capacity constants | A, B, C | dimensionless | C.3 |
| Standard enthalpy of formation | ΔH°f,298 | J/mol | C.4 |
| Standard Gibbs energy of formation | ΔG°f,298 | J/mol | C.4 |
| Molar mass, acentric factor, critical constants, normal boiling point | M, ω, Tc, Pc, Zc, Vc, Tn | g/mol, –, K, bar, –, cm³/mol, K | B.1 |
| Gas constant | R = 8.314 J/(mol·K) | | A.2 |

Reference conditions: 298.15 K and a standard-state pressure of 1 bar. Gases are in the ideal-gas standard state; liquids and solids are the real pure substance at 1 bar.

Validity of the heat-capacity correlations, exactly as the tables state: gases and solids from 298 K to the listed Tmax (1000 to 3000 K depending on the species); liquids from 273.15 K to 373.15 K.

## The database

57 species: 42 gases, 7 liquids, 8 solids. Water, methanol, ethanol, benzene, cyclohexane, toluene and acetic acid are present as both gas and liquid, so the physical state of a product can be chosen explicitly. All 26 species suggested in the assignment are included.

**Standard molar entropy.** SVN does not tabulate absolute entropies. What a reaction calculation needs is the entropy *change*, and that follows from SVN alone:

    ΔS°f,298 = (ΔH°f,298 − ΔG°f,298) / 298.15

The database page also shows the familiar absolute entropy S°₂₉₈ = ΔS°f,298 + Σ S°(elements), using the CODATA Key Values for the elements (H₂ 130.680, O₂ 205.152, N₂ 191.609, Cl₂ 223.081, graphite 5.74, Ca 41.59 J/(mol·K); iron 27.32 from NIST-JANAF). For the SVN species these element entropies are for display and cross-checking only, and they cancel exactly in any balanced reaction.

## Data from the NIST Chemistry WebBook

Two species in the assignment's suggested list are not fully covered by SVN. For these, data were read from the species pages of the NIST Chemistry WebBook (NIST Standard Reference Database 69, webbook.nist.gov).

| Species | What NIST gives | How it is used |
|---|---|---|
| H₂O₂(g) | ΔH°f,298 = −136.11 kJ/mol and S°₂₉₈ = 232.95 J/(mol·K), both from the NIST-JANAF tables (Chase 1998). Shomate equation for Cp, 298 to 1500 K: A = 34.25667, B = 55.18445, C = −35.15443, D = 9.087440, E = −0.422157 | Used exactly as published. The Shomate equation Cp = A + Bt + Ct² + Dt³ + E/t² (t = T/1000) is converted term by term into the solver's form; nothing is refitted. |
| CH₃COOH(g) | ΔH°f,298 = −432.9 kJ/mol (the liquid value of Lebedeva 1964, −484.5, plus the enthalpy of vaporisation to the monomer, 51.6 kJ/mol, Konicek & Wadsö 1970). S°₂₉₈ = 282.84 J/(mol·K) (Weltner 1955). Cp tabulated at 14 temperatures from 298.15 to 1500 K (Chao 1986) | The liquid value of Lebedeva is the same −484.5 kJ/mol that SVN prints in Table C.4, so the gas and the SVN liquid are consistent. NIST gives no equation for Cp, so the table was fitted by least squares with Cp/R = A + BT + CT² + ET³; the largest deviation from the table is 0.21 %. The table itself is stored in `data.py` and a test checks every point. |
| CH₃COOH(l) | Cp = 123.1 J/(mol·K) at 298.15 K (Martin & Andon 1982) | ΔH°f and ΔG°f stay the SVN Table C.4 values. The heat capacity is taken as constant and is declared valid from 290 to 320 K only, because the heat capacity of the liquid rises noticeably with temperature. |

Three points follow from using a second source:

- **Gibbs energy of formation.** NIST gives the absolute entropy, not ΔG°f. It is obtained from ΔG°f = ΔH°f − 298.15·[S° − Σ S°(elements)] with the CODATA element entropies above. This gives −105.4 kJ/mol for H₂O₂(g) and −374.7 kJ/mol for CH₃COOH(g), in line with handbook values (−105.6 and −374.5).
- **A fifth heat-capacity term.** The Shomate equation has a T³ term, which the SVN form does not. The solver's heat-capacity function therefore has an optional fifth coefficient, Cp/R = A + BT + CT² + DT⁻² + ET³, which is zero for every SVN species.
- **Labelling.** Each of the three species is marked "NIST" in the database table, and any reaction that uses one shows a note saying so.

What is still not available: liquid hydrogen peroxide (NIST's WebBook has no condensed-phase data for it), and critical constants for H₂O₂, so the gas is ideal in pressure calculations.

## Species that SVN covers only in part

| Species | Situation | What the solver does |
|---|---|---|
| NO₂, N₂O₄, ethylene oxide | In C.1 and C.4 but not in B.1 (no critical constants) | Full temperature dependence; treated as ideal gases in pressure calculations, with a warning. |
| Sulfur (element) | Table C.2 gives rhombic sulfur only up to 368.3 K | H₂S, SO₂ and SO₃ work normally in reactions; only their formation-from-elements reaction is not offered. |

## How the transcription was verified

1. **Against the printed tables.** Every number in `data.py` was compared with the 8th-edition appendices and cross-checked against page scans of the 6th edition. One value differs between editions (below); everything else agrees.
2. **Heat-capacity checksum.** Tables C.1 to C.3 print Cp/R at 298.15 K next to the constants. The test-suite recomputes it from A, B, C, D for every species and requires agreement to the printed precision (±0.0025). A single mistyped constant fails this test.
3. **Formula check.** The molar mass computed from each chemical formula must match the molar mass printed in Table B.1 to 0.02 g/mol.
4. **Third-law cross-check.** ΔS°f from Table C.4 plus the CODATA element entropies must reproduce the absolute entropies tabulated by CODATA / NIST for 15 common species to within 1 J/(mol·K). This catches an error in ΔH°f or ΔG°f of about 300 J/mol.
5. **NIST entries.** The NIST numbers were read from the species pages themselves. For hydrogen peroxide the solver's enthalpy and entropy integrals reproduce NIST's own H°(T) − H°(298.15) and S°(T) functions to nine decimal places; for acetic acid vapour every point of the NIST heat-capacity table is compared with the fitted polynomial.
6. **Worked examples.** The solver reproduces 51 reference values: 44 from SVN's worked examples, four from course material (two cubic-equation roots from the slides and two results of the bomb-calorimeter handout), one hand calculation from Table C.4 and two steam-table checks. See [TESTING.md](TESTING.md) and the Validation tab of the web app.

   **Not yet confirmed against a printed copy:** five of the 44 SVN values belong to the two heat-balance examples of Chapter 4 (flame temperature of methane with 20 % excess air, 2066 K; heat requirement of the steam reformer, −34,390 + 200,460 + 161,940 = 328,010 J). They were added together with the heat lab, when no copy of the book could be opened, and are quoted as remembered from the 7th and 8th editions. The solver reproduces all five to four significant figures without having been given them, which makes a wrong recollection unlikely, but they should be compared with the book before they are relied on.

## Constants of the heat lab

| Item | Value | Source |
|---|---|---|
| Composition of air | 21 mol-% O₂, 79 mol-% N₂, so 79/21 = 3.762 mol N₂ per mol O₂ | as used in the combustion examples of SVN Chapter 4 |
| Thermochemical calorie | 4.184 J | course bomb-calorimeter handout |
| Calorific value of benzoic acid | 6319 cal/g at 25 °C | course bomb-calorimeter handout |
| Calibration run | 1.1942 g of benzoic acid, rise 2.48 °C, thread and wire 41.0 cal, giving 3059.33 cal/°C | course bomb-calorimeter handout |

Benzoic acid is not a species of the database. Its calorific value is only the default of the calibration input of the virtual calorimeter, and it can be overwritten there. Heating values of the fuels themselves come from the formation data of Table C.4.

## Oddities found in the book itself

These are not transcription errors; the printed tables contain them.

| Item | What the table prints | What it implies | Handling |
|---|---|---|---|
| 1,3-Butadiene, Table C.1 | Cp298/R = 10.720 with A = 2.734, 10³B = 26.786, 10⁶C = −8.882 | The constants give 9.931, not 10.720. The measured value is about 9.6. | The constants are used. The checksum test lists this species as its only exception. |
| Chlorine, Table B.1 | Zc = 0.265 | Pc·Vc/(R·Tc) = 0.276 | Zc is displayed only; it is never used in a calculation. |
| Carbon monoxide, Table B.1 | Zc = 0.299 | Pc·Vc/(R·Tc) = 0.296 | Same. |
| Ammonia, Table C.4 | ΔG°f,298 = −16,400 J/mol (8th, 9th ed.) | The 6th edition printed −16,450 J/mol. | The 8th-edition value is used. The 50 J/mol difference changes K of ammonia synthesis by about 2 % at 700 K. |
| Virial derivative constants | dB⁰/dTr = 0.675/Tr^2.6, dB¹/dTr = 0.722/Tr^5.2 | Exact derivatives are 0.6752 and 0.7224 | The unrounded values are used so that Hᴿ, Sᴿ and φ stay mutually consistent (see THEORY.md, Section 5.1). |
