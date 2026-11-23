# Data sources

Smith, Van Ness & Abbott, *Introduction to Chemical Engineering Thermodynamics* (SVN) is the source for everything it covers: from 298.15 K upwards, 54 of the 57 species use SVN data only. Three entries that SVN does not cover come from the NIST Chemistry WebBook and are described in their own section below. SVN's heat capacities start at 298 K, so between 200 K and 298.15 K the heat capacities come from NIST tables; that also has its own section. Nothing is taken from an AI model's memory without being checked against the source itself.

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

Standard state: the pure species at 1 bar, at whatever temperature is being considered. Gases are in the ideal-gas standard state; liquids and solids are the real pure substance at 1 bar. The standard state does not fix the temperature. 298.15 K is only the reference temperature at which Table C.4 lists the formation data; ΔH°, ΔS° and ΔG° at any other temperature are standard values too, reached with the heat capacities.

Validity of the heat-capacity correlations, exactly as the tables state: gases and solids from 298 K to the listed Tmax (1000 to 3000 K depending on the species); liquids from 273.15 K to 373.15 K. Below 298.15 K the SVN constants are not used for gases and solids (next but one section).

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

## Heat capacities below 298.15 K

SVN's Tables C.1 and C.2 are valid from 298 K. Extrapolating them downwards is not safe, because the D/T² term takes over: at 200 K the SVN constants give a heat capacity 29 % too low for CO₂ and 37 % too low for SO₃, and a negative one for graphite. So from 200 K to 298.15 K the solver uses tabulated values instead.

| Source | Species | What was read |
|---|---|---|
| NIST-JANAF Thermochemical Tables, 4th edition (Chase 1998), janaf.nist.gov | 21 gases (HCN, CH₂O, CH₄, CO, CO₂, C₂H₂, C₂H₄, HCl, H₂, H₂O, H₂S, NH₃, NO, NO₂, N₂, N₂O, N₂O₄, O₂, SO₂, SO₃, Cl₂) and 6 solids (graphite, CaO, Ca(OH)₂, Fe, Fe₂O₃, Fe₃O₄) | The rows at 200 K, 250 K (where the table has one) and 298.15 K: Cp, S and H − H(298.15 K) |
| NIST Chemistry WebBook, "Constant pressure heat capacity of gas", recommended ideal-gas values | 20 organic gases: methanol, ethanol, acetaldehyde, ethylene oxide, acetic acid, ethane to n-octane, propylene, 1-butene, 1,3-butadiene, benzene, cyclohexane, toluene, ethylbenzene, styrene | Cp at 200 K, 273.15 K and 298.15 K (for ethane at 100 K, 200 K and 298.15 K, because NIST lists nothing in between) |

Both were read on 22 November 2026. The rows are stored as read in `data.py` (`JANAF_LOW_T`, `WEBBOOK_LOW_T`) with the table number or the WebBook species ID of each. No fitted constant is typed in: Cp/R = A + B·T + C·T² is computed from the rows when the package is loaded.

- **NIST-JANAF species.** The quadratic takes the tabulated Cp at 200 K and at 298.15 K, and its integral between them equals the tabulated H(200 K) − H(298.15 K). So the enthalpy at 200 K is exactly the table's.
- **WebBook species.** The quadratic passes through the three tabulated Cp values.

**How this was checked.** The NIST-JANAF entropy column and the 250 K rows were not used for the fit, so they are an independent test of both the transcription and the method. The fitted curves reproduce the 14 rows at 250 K within 0.01 J/(mol·K) in Cp, 1.4 J/mol in enthalpy and 0.004 J/(mol·K) in entropy, and the entropy at 200 K within 0.03 J/(mol·K) for every species but one (see the oddities below). For ethane, five measured heat capacities listed on the same WebBook page (209 to 292 K) are reproduced within 0.8 %.

**What is not changed.** The formation data at 298.15 K, and every heat capacity from 298.15 K upwards. Every integral the solver takes starts at 298.15 K, so a calculation above that temperature never touches the low-temperature data, and one below it never touches the SVN constants.

**The step at 298.15 K.** The SVN correlation and the NIST value do not give exactly the same Cp at 298.15 K. For 25 of the 47 species they agree within 1 %. The largest differences: SVN is 14 % above NIST for ethanol, 7 % for styrene and for calcium hydroxide, 5 % for methanol. Neither source is altered to hide this, so a plot of Cp or ΔCp shows a small step at 298.15 K. ΔH°, ΔS°, ΔG° and K stay continuous. The Species tab lists the step for every species.

**Not covered below 298.15 K.** H₂O₂(g), CaCO₃(s) and CaC₂(s) (reasons in the oddities table below and in `LOW_T_NOT_COVERED`), and the liquids, which keep the SVN range of 273.15 to 373.15 K. Below 200 K nothing is stored: hydrogen then needs its ortho and para forms treated separately, and several solids have transitions. The solver extrapolates there and warns.

**A reminder about phases.** Below its boiling point a species is not a gas at 1 bar. The ideal-gas standard state is still well defined, and that is what "(g)" means in a reaction; the solver adds a note whenever a gas is used below its normal boiling point.

## Heat capacities above the SVN range

Table C.1 ends at 2000 K for N₂, O₂, CO₂, H₂O, SO₂ and NO, at 2500 K for CO and at 3000 K for H₂. An adiabatic flame is hotter. Beyond its last temperature the SVN formula (a straight line in T plus a D/T² term) keeps rising while the real heat capacity levels off: stretched to 3000 K it is 7 % too high for CO₂.

For these eight gases the solver therefore uses, from the SVN limit up to 6000 K, the Shomate equations of the NIST Chemistry WebBook (fits of the NIST-JANAF tables, Chase 1998), read on 22 November 2026. The constants A to E are stored as published in `data.py` (`NIST_HIGH_T`) with the WebBook species ID, and converted term by term into the solver's form. Nothing is refitted.

**How this was checked.** NIST publishes with each equation the constants F, G and H of its enthalpy and entropy functions. The solver does not use them; the tests do: the solver's integrals between two temperatures reproduce NIST's own H(T) and S(T) differences to one part in a million. As an outside check, rows of the NIST-JANAF tables themselves (2500 to 6000 K) are reproduced within 0.4 % in Cp and 0.2 % in the enthalpy and entropy gained above the join.

**What is not changed.** Everything inside the SVN range. The SVN formula is used up to the last temperature the book states for it, and the NIST equation only beyond.

**A consequence.** SVN's worked flame-temperature example (methane, 20 % excess air) ends at 2066 K, 66 K above the limit of the formulas it uses. With the SVN formulas stretched in the same way the solver gives 2066.4 K; with NIST data above 2000 K it gives 2068.8 K, and that is what the page shows, with a note that names both. The reference value on the Validation tab is the textbook's, computed the textbook's way.

**Dissociation.** Having data up to 6000 K does not make a 4000 K flame real. Above about 2000 K the products of combustion partly dissociate, which the energy balance does not include. The page says so in a note, and as a warning above 2500 K.

## Measured enthalpies of real gases (choice of the equation of state)

The solver chooses the equation of state for each gas from measured data (THEORY.md, Section 5.5). The data are `data.NIST_FLUID`: isotherms of the NIST Chemistry WebBook, "Thermophysical Properties of Fluid Systems", read on 23 November 2026 from `webbook.nist.gov/cgi/fluid.cgi` (enthalpy in kJ/mol, default reference state, which cancels in the differences used).

| Item | Value |
|---|---|
| Gases | the 24 gases of the database that the WebBook has in this section: CH₄, C₂H₆, C₃H₈, n-butane to n-octane, C₂H₄, C₃H₆, benzene, cyclohexane, toluene, CH₃OH, NH₃, CO, CO₂, H₂, H₂S, N₂, N₂O, O₂, SO₂, H₂O. Not covered: ethanol, acetic acid, acetylene, 1-butene, 1,3-butadiene, styrene, ethylbenzene, formaldehyde, acetaldehyde, Cl₂, HCl, HCN, NO, SO₃ |
| Temperatures | 300, 400, 500, 600, 700, 800 and 1000 K, as far as NIST's equation for each fluid reaches (for many fluids up to 600 or 700 K) |
| Pressures | 0.01 bar (the ideal-gas reference of each isotherm), 10, 50, 100, 200 and 300 bar (read as 10.01 to 300.01 bar, the grid of the WebBook query) |
| Points kept | only those NIST marks as vapour or supercritical; rows that NIST lists twice at the same pressure appear once; 380 points in all |

How this was checked: the rows were read in the browser and the exported text was compared with the saved copy by a checksum before it went into `data.py`. Two rows are spot-checked in `tests/test_eos_choice.py` (CO₂ at 400 K and 300 bar, methanol at 600 K and 300 bar). The test-suite also recomputes the choice for every gas straight from these rows.

## Cross-check of the SVN tables against NIST-JANAF

The heat-capacity checksum of the next section tests the SVN constants at 298.15 K only. As a second, independent check the formation data and the heat capacities over the whole SVN range were compared with rows of the NIST-JANAF tables for 21 gases and 6 solids (`tests/janaf_reference.py`, `tests/test_cross_check_janaf.py`). The two sources are not identical, so this is a search for typing errors, not a claim that they agree to the last digit.

| Quantity | Result |
|---|---|
| ΔH°f and ΔG°f at 298.15 K | within 1 kJ/mol for 19 of 22 species. The three exceptions are source differences: formaldehyde (SVN −108.57, JANAF −115.90 kJ/mol; the JANAF table dates from 1961 and SVN has the modern value), Fe₂O₃ (1.3 kJ/mol) and Fe₃O₄ (2.5 kJ/mol) |
| ΔG°f of ammonia | JANAF −16.367 kJ/mol, which supports the −16,400 J/mol of the 8th edition over the −16,450 of the 6th |
| Cp of the SVN formula, 500 to 1500 K | within 5 % of JANAF for every gas |
| H(T) − H(298.15 K) of the SVN formula | within 3.5 % for every gas, and within 0.3 % at 2000 K for N₂, O₂, CO₂, H₂O, SO₂ and SO₃ |

The last line is worth a remark. At 2000 K the SVN heat capacity itself is 2 to 4 % above JANAF for these gases, and yet the enthalpy agrees to 0.3 %. The three-constant SVN formula was evidently fitted to reproduce enthalpy changes over its whole range, at the price of the heat capacity at its two ends. This is why the heat capacity shows a small step where a NIST set takes over (at 298.15 K and at the upper SVN limit) while the enthalpy does not. No transcription error was found.

## Species that SVN covers only in part

| Species | Situation | What the solver does |
|---|---|---|
| NO₂, N₂O₄, ethylene oxide (and H₂O₂ from NIST) | In C.1 and C.4 but not in B.1 (no critical constants) | Full temperature dependence; treated as ideal gases in pressure calculations, with a warning. |
| Sulfur (element) | Table C.2 gives rhombic sulfur only up to 368.3 K | H₂S, SO₂ and SO₃ work normally in reactions; only their formation-from-elements reaction is not offered. |

## How the transcription was verified

1. **Against the printed tables.** Every number in `data.py` was compared with the 8th-edition appendices and cross-checked against page scans of the 6th edition. One value differs between editions (below); everything else agrees.
2. **Heat-capacity checksum.** Tables C.1 to C.3 print Cp/R at 298.15 K next to the constants. The test-suite recomputes it from A, B, C, D for every species and requires agreement to the printed precision (±0.0025). A single mistyped constant fails this test.
3. **Formula check.** The molar mass computed from each chemical formula must match the molar mass printed in Table B.1 to 0.02 g/mol.
4. **Third-law cross-check.** ΔS°f from Table C.4 plus the CODATA element entropies must reproduce the absolute entropies tabulated by CODATA / NIST for 15 common species to within 1 J/(mol·K). This catches an error in ΔH°f or ΔG°f of about 300 J/mol.
5. **NIST entries.** The NIST numbers were read from the species pages themselves. For hydrogen peroxide the solver's enthalpy and entropy integrals reproduce NIST's own H°(T) − H°(298.15) and S°(T) functions to nine decimal places; for acetic acid vapour every point of the NIST heat-capacity table is compared with the fitted polynomial.
6. **Low-temperature rows.** See "How this was checked" in the section on heat capacities below 298.15 K.
7. **Worked examples.** The solver reproduces 67 reference values: 44 from SVN's worked examples, four from course material (two cubic-equation roots from the slides and two results of the bomb-calorimeter handout), one hand calculation from Table C.4, two steam-table checks, six from NIST tables below 298.15 K (rows and columns that were not used for the fit) and ten on phase change (next item).
8. **Phase change.** The boiling point of each liquid follows from the SVN formation data and heat capacities of its liquid and its gas (THEORY.md, Section 10). The six normal boiling points of SVN Table B.1 are compared with it and are not used in the calculation. Four more reference values come from the NIST Chemistry WebBook, "Saturation properties for water" (read on 23 November 2026): vapour pressure 0.031699 bar at 25 °C and 0.19946 bar at 60 °C, enthalpy of vaporisation 45.876 − 1.8885 kJ/mol at 25 °C, and saturation temperature 328.58 K at 0.16092 bar. They are reference values only; no number of that table is used by the solver. See [TESTING.md](TESTING.md) and the Validation tab of the web app.

   **Not yet confirmed against a printed copy:** five of the 44 SVN values belong to the two heat-balance examples of Chapter 4 (flame temperature of methane with 20 % excess air, 2066 K, computed with the SVN formulas only, as in the book; heat requirement of the steam reformer, −34,390 + 200,460 + 161,940 = 328,010 J). They were added together with the heat lab, when no copy of the book could be opened, and are quoted as remembered from the 7th and 8th editions. The solver reproduces all five to four significant figures without having been given them, which makes a wrong recollection unlikely, but they should be compared with the book before they are relied on.

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
| Ethanol, Table C.1 | A = 3.518, 10³B = 20.001, 10⁶C = −6.002, so Cp298 = 74.4 J/(mol·K) | NIST recommends 65.21 J/(mol·K) at 298.15 K: SVN is 14 % higher at its lower limit | SVN is used from 298.15 K upwards, as everywhere. The difference is shown, not smoothed. |

## Oddities found in the NIST-JANAF tables

| Item | What the table prints | What it implies | Handling |
|---|---|---|---|
| H₂O₂(g), table H-070 | Cp = 36.874 and 43.116 J/(mol·K) at 200 K and 298.15 K; S = 210.632 and 232.991 | The entropy column rises by 22.4 J/(mol·K), but no heat capacity between 36.9 and 43.1 can give more than about 17 over that interval. The enthalpy column disagrees with the heat capacities as well. | Not used. Hydrogen peroxide keeps its range of 298 to 1500 K. |
| H₂S(g), table H-080 | S(200 K) = 192.038 J/(mol·K) | The table's own heat capacities and enthalpy give 192.30 from its entropy at 298.15 K, 0.26 higher | Only Cp and the enthalpy are used, and they agree with each other to 1 J/mol. The entropy check lists this species as its only exception. |
