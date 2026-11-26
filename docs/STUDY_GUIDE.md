# Study guide for the presentation and the viva

This guide has everything needed to present the Thermodynamic Reaction Energy Solver and to answer questions on it. Every number in it is what the solver gives, so it matches the screen and the report. Read sections 1 to 3 the day before, skim sections 4 to 9, and go through the questions in section 10 out loud.

## 1. The project in one minute (the idea)

**The problem.** The heat of reaction at a temperature other than 298.15 K needs a heat-capacity integral for every species of the reaction. By hand that is a page of working for one reaction at one temperature, and a slip in one constant is easy to miss. So people take shortcuts (a constant ΔCp, or no ΔCp at all), and those can be badly off: for the 40 predefined reactions whose data reach 1000 K, a constant ΔCp puts ΔH° off by 9.0 kJ/mol on average and by up to 31.5 kJ/mol. A real reactor also asks two questions that one ΔG° cannot answer: what does high pressure do, and which products actually form when several reactions compete.

**The idea.** A web page that does the full textbook method (Smith, Van Ness and Abbott) for any reaction in a few seconds, shows every step and plot, explains the result in plain words, and checks itself against the textbook.

**What it does.** It checks the element balance first, then gives ΔH°, ΔS° and ΔG° at any temperature from 298.15 K up, with plots. It shows what pressure does to the heat of reaction of real gases, combines reactions by Hess's law, finds which products form in a reactor (product slate), and repeats the bomb calorimeter lab. Everything runs in the browser.

**Why it can be trusted.** 67 of 67 reference values reproduced, all five stress tests of the assignment passed, eight errors of the AI-generated solver found and corrected, and 441 automated tests that run on every change.

## 2. Numbers to know by heart

| What | Number |
|---|---|
| Species in the database | 57 (42 gases, 7 liquids, 8 solids), including all 26 the assignment suggests |
| Predefined reactions | 45, including all those the assignment names; any balanced reaction can be typed |
| CO₂ + 3 H₂ → CH₃OH + H₂O, at 298.15 K | ΔH° = −48.97 kJ/mol, ΔS° = −177.08 J/(mol·K), ΔG° = +3.83 kJ/mol |
| The same at 523.15 K | ΔH° = −57.94 kJ/mol, ΔS° = −199.76 J/(mol·K), ΔG° = +46.56 kJ/mol |
| ΔCp° of that reaction at 298.15 K | −43.95 J/(mol·K) (negative, so ΔH° falls as T rises) |
| Steam reforming becomes favourable | above 893 K (ΔG° changes sign) |
| Steam reforming at 1000 K | ΔH° = 225.3 kJ/mol with Cp(T), 238.8 with a constant ΔCp, 205.8 with ΔCp ignored |
| Constant ΔCp at 1000 K, 40 reactions | 9.0 kJ/mol off on average, up to 31.5 (benzene hydrogenation) |
| Methane combustion at 298.15 K | −890.65 kJ/mol with liquid water, −802.63 with water vapour; the gap is 2 × 44.01 kJ/mol |
| Boiling points from the solver's own data | water 373.2 K, methanol 337.1 K, ethanol 351.3 K |
| Ammonia synthesis, 723 K, 200 bar | ideal gas −106.50 kJ/mol, real gas −111.55 kJ/mol, residual part −5.05 kJ/mol (4.7 %) |
| Real-gas effect, other cases | CO₂ to methanol at 50 bar 10.6 %, steam reforming at 1100 K 0.2 % |
| Equations of state against NIST data | 24 gases, 380 points; closest: Soave/Redlich/Kwong 14 gases, Peng/Robinson 6, Redlich/Kwong 4 |
| Average error against NIST data | SRK 0.137, PR 0.160, RK 0.510, van der Waals 1.246, virial 1.349 kJ/mol |
| Product slate, CO₂ + 3 H₂, 523 K, 50 bar | everything allowed: methane 74.9 % of the carbon; methane off: methanol 20.6 %, CO 7.5 % |
| Only methanol allowed | 0.6 % at 1 bar, 24.5 % at 50 bar |
| Calorimeter constant | (1.1942 g × 6319 cal/g + 41 cal) / 2.48 °C = 3059.3 cal/°C |
| 1 g of ethanol in the calorimeter | ΔH = −1366.8 kJ/mol, ΔU = −1364.3 kJ/mol, 29.62 MJ/kg, rise 2.31 °C |
| Heating values of ethanol | HHV 29.67 MJ/kg, LHV 26.80 MJ/kg |
| Validation | 67 of 67 reference values; 8 published reactions within 0.5 kJ/mol; 441 automated tests |

## 3. The six slides in short

1. **Title.** Name of the project, what it does, my name and roll number, AI platform: Claude.
2. **The idea.** Hand calculation is long and shortcuts mislead (up to 31.5 kJ/mol); a reactor adds pressure and competing reactions. The solver does the full method every time and checks itself.
3. **How it works.** Reaction → balance check → data (57 species) → Cp integrals → ΔH°, ΔS°, ΔG° → residual enthalpy for pressure → results with plots and explanations, all in the browser.
4. **What it shows.** Temperature decides favourability (CO₂ to methanol: ΔG° = +46.6 kJ/mol at 523 K); pressure matters for real gases (ammonia 4.7 %); no single equation of state is best (the chart of average errors).
5. **Two extra features.** Product slate (methane 74.9 %, methanol 20.6 % with methane off: the catalyst decides). Bomb calorimeter (ΔU, not ΔH; 2.31 °C for 1 g of ethanol; identifies an unknown sample).
6. **Checked, and ready to try.** 67/67 reference values, 5/5 stress tests, 8 AI errors corrected, 441 automated tests. Then the live demo.

## 4. The thermodynamics behind it

### 4.1 Heat of reaction at 298.15 K

    ΔH°298 = Σ νᵢ ΔH°f,i

νᵢ is the stoichiometric number: positive for products, negative for reactants. The heats of formation are from the textbook's Table C.4. This is Hess's law: the reaction is the sum of the formation reactions of its compounds, and the elements cancel. A negative ΔH° means the reaction gives out heat (exothermic); a positive one means it takes in heat (endothermic).

Example: CO₂ + 3 H₂ → CH₃OH(g) + H₂O(g) has ΔH°298 = −48.97 kJ/mol, so it is exothermic.

### 4.2 Heat capacity and sensible heat

    Cp/R = A + B·T + C·T² + D·T⁻²
    Q = ∫ Cp dT = R ∫ (Cp/R) dT        (from T1 to T2)

The constants A, B, C, D are from the textbook's Tables C.1 (gases), C.2 (solids) and C.3 (liquids). Cp/R has no unit, so R gives J/(mol·K). Q is the sensible heat: the heat that changes the temperature, at constant pressure, with no reaction. Each formula is valid only in its own temperature range; outside it the solver warns and shades the plot.

Example: heating methane from 298.15 K to 1000 K takes 38.49 kJ/mol.

### 4.3 Heat of reaction at another temperature

    ΔH°(T) = ΔH°298 + R ∫ (ΔCp°/R) dT        (from 298.15 K to T)
    ΔCp° = Σ νᵢ Cp,i

Why it works: H is a state function, so the path does not matter. Path: cool the reactants from T to 298.15 K, let them react at 298.15 K, heat the products back to T. The two sensible heats add up to the integral of ΔCp°.

If ΔCp° is negative, ΔH° falls as T rises. For CO₂ to methanol, ΔCp° = −43.95 J/(mol·K) at 298.15 K, and ΔH° goes from −48.97 to −57.94 kJ/mol at 523 K. The bar chart of tab 1 shows each species' share: CO₂ −9.62, H₂ −19.50, CH₃OH +12.40 and H₂O +7.75 kJ, which add up to −8.97 kJ = −57.94 − (−48.97).

### 4.4 Entropy change

    ΔS°(T) = ΔS°298 + R ∫ (ΔCp°/R) dT / T

ΔS°298 comes from the heats and Gibbs energies of formation: ΔS°298 = (ΔH°298 − ΔG°298) / 298.15. Fewer gas molecules usually means a negative ΔS°. CO₂ to methanol turns 4 moles of gas into 2, so ΔS° = −177.08 J/(mol·K) at 298.15 K, and −199.76 at 523 K (more negative, again because ΔCp° is negative).

### 4.5 Gibbs energy and favourability

    ΔG°(T) = ΔH°(T) − T·ΔS°(T)
    ln K = −ΔG° / (R·T)

- ΔG° < 0: the products are favoured (K > 1). ΔG° > 0: the reactants are favoured (K < 1), but some product still forms.
- ΔH° < 0 and ΔS° < 0: favoured at low temperature (CO₂ to methanol; at 523 K ΔG° = +46.56 kJ/mol, K = 2.2 × 10⁻⁵).
- ΔH° > 0 and ΔS° > 0: favoured at high temperature (steam reforming, above 893 K).
- The temperature where ΔG° = 0 is where the favoured side changes. For CO₂ to methanol it is 276 K, below the range of tab 1.
- K here is Kp: written with partial pressures in bar divided by the standard pressure of 1 bar. It depends on temperature only. Pressure changes the equilibrium composition, not K.

### 4.6 Standard state

The ° sign means the standard state: the pure species at 1 bar, at any temperature. 298.15 K is only the reference temperature at which the tables give the formation data. So ΔH°(523 K) is still a standard value. Tab 1 works from 298.15 K upwards.

### 4.7 Phase change: liquid or vapour

For water, methanol, ethanol, benzene, cyclohexane and toluene, the database has both the liquid and the gas. The stable phase at 1 bar is the one with the lower Gibbs energy, and the boiling point is where the two are equal. The solver finds it from its own data: water 373.2 K (textbook 373.15 K), methanol 337.1 K, ethanol 351.3 K. Acetic acid is left out, because its data put the boiling point 43 K too high.

On tab 1, "Pick the stable phase" is ticked at the start: a species typed without (g) or (l) gets its stable phase. A typed phase is always kept (H₂O(g) at 25 °C gives the lower heating value on purpose).

At a boiling point the graphs have a kink or a step. ΔH° jumps by ν × the latent heat, ΔS° by ν × latent heat / T_boil, and ΔCp° jumps because liquid and vapour have different heat capacities. ΔG° does not jump, because liquid and vapour have the same Gibbs energy there, but its slope changes. Example, methane combustion: at 373.2 K, ΔH° jumps by 2 × 40.86 = 81.73 kJ/mol.

### 4.8 Real gases and the residual enthalpy

    Hᴿ = H(real gas) − H(ideal gas), at the same T and P
    ΔH(T,P) = ΔH°(T) + Σ νᵢ Hᵢᴿ(T,P)

**Why the ideal-gas H does not depend on pressure:** an ideal gas has no forces between its molecules, so U depends on T only, and PV = RT, so H = U + PV = U + RT depends on T only.

**Why a real gas is different:** its molecules attract each other. Higher pressure pushes them closer, the attraction counts for more, and H drops below the ideal value (Hᴿ < 0, Z < 1). Far above its critical temperature, a small molecule such as H₂ or N₂ is so fast that attraction hardly matters; the size of the molecules wins, Z > 1 and Hᴿ > 0.

**How Hᴿ is worked out for one gas:**

1. Tc, Pc and ω from Table B.1; Tr = T/Tc, Pr = P/Pc.
2. Solve the gas's equation of state for Z.
3. Put Z, Tr, Pr and ω into that equation's formula for Hᴿ/RT.
4. For the reaction, add up ν·Hᴿ (products plus, reactants minus).

The generic cubic equation of the textbook (Table 3.1):

    β = Ω·Pr/Tr        q = Ψ·α(Tr)/(Ω·Tr)
    Z = 1 + β − q·β·(Z − β) / [(Z + ε·β)(Z + σ·β)]
    I = ln[(Z + σ·β)/(Z + ε·β)] / (σ − ε)
    Hᴿ/(RT) = Z − 1 + [d ln α / d ln Tr − 1]·q·I

| Equation | α(Tr) | σ | ε | Ω | Ψ |
|---|---|---|---|---|---|
| van der Waals | 1 | 0 | 0 | 1/8 | 27/64 |
| Redlich/Kwong | Tr^(−1/2) | 1 | 0 | 0.08664 | 0.42748 |
| Soave/Redlich/Kwong | [1 + (0.480 + 1.574ω − 0.176ω²)(1 − Tr^½)]² | 1 | 0 | 0.08664 | 0.42748 |
| Peng/Robinson | [1 + (0.37464 + 1.54226ω − 0.26992ω²)(1 − Tr^½)]² | 1 + √2 | 1 − √2 | 0.07780 | 0.45724 |

The generalized virial correlation (for low to moderate pressure):

    Z = 1 + (B⁰ + ω·B¹)·Pr/Tr
    B⁰ = 0.083 − 0.422/Tr^1.6        B¹ = 0.139 − 0.172/Tr^4.2
    Hᴿ/(R·Tc) = Pr·[B⁰ − Tr·dB⁰/dTr + ω·(B¹ − Tr·dB¹/dTr)]

Example, methanol at 523 K and 50 bar (Soave/Redlich/Kwong): Tr = 1.02, Pr = 0.62, Z = 0.774, Hᴿ/RT = −0.948, Hᴿ = −0.948 × 8.314 × 523.15 = −4.12 kJ/mol. Hydrogen at the same conditions (Redlich/Kwong): Tr = 15.76, Z = 1.019, Hᴿ = +0.07 kJ/mol, almost ideal.

**The three steps on tab 2** reach the real-gas ΔH by a detour, like Hess's law. For ammonia at 723 K and 200 bar:

| Step | What | Value |
|---|---|---|
| 1 | real reactants to ideal gas: −[1 × Hᴿ(N₂) + 3 × Hᴿ(H₂)] = −(177 + 3 × 325) J | −1.15 kJ |
| 2 | the ideal-gas reaction, ΔH°(723 K) | −106.50 kJ |
| 3 | ideal products to real gas: 2 × Hᴿ(NH₃) = 2 × (−1949) J | −3.90 kJ |
| Sum | real-gas ΔH at 200 bar | −111.55 kJ/mol |

### 4.9 Which equation of state the solver uses

The user does not pick the equation; the solver does, for each gas. For the 24 gases NIST has measured data for, it compared the Hᴿ of all five equations with the measured Hᴿ (H at T and P minus H at T and 0.01 bar, where a gas is practically ideal) at 380 points from 300 to 1000 K and 10 to 300 bar. Each gas uses the equation with the smallest average difference:

- Soave/Redlich/Kwong for 14 gases (for example ammonia, methanol, water)
- Peng/Robinson for 6 (for example CO₂, N₂)
- Redlich/Kwong for 4 small, light molecules (methane, CO, H₂, O₂)
- the virial equation and van der Waals never

A gas without measured data (for example ethanol) uses Soave/Redlich/Kwong, the closest over all 380 points (0.137 kJ/mol on average, against 0.160 for Peng/Robinson). Each gas keeps one equation at every T and P, so the graphs stay smooth.

Why measured data and not a rule of thumb: the textbook's limit for the virial equation (molar volume at least twice the critical volume) allows it even for methanol at 523 K and 80 bar. There NIST measures Hᴿ = −9.87 kJ/mol; Peng/Robinson gives −8.63, Soave/Redlich/Kwong −8.49, Redlich/Kwong −6.49, virial −5.74 and van der Waals −4.99.

### 4.10 Several reactions at once: the product slate

The user only says which species may exist. The solver finds the amounts of all of them that make the total Gibbs energy of the mixture as low as possible, while the number of atoms of every element stays what the feed brought in:

    G/RT = Σ nᵢ [Gᵢ°/RT + ln(yᵢ·P/P°) + Gᵢᴿ/RT]

It is an iterative calculation: the amounts are changed step by step until the total cannot get lower. No list of reactions is needed. The gases are real gases, each with the equation of state chosen for it.

A switch imitates a selective catalyst: off means the catalyst cannot make that product. A faded switch would change nothing at the current settings. For CO₂ + 3 H₂ at 523 K and 50 bar: everything allowed, methane takes 74.9 % of the carbon; methane off, methanol takes 20.6 % and CO 7.5 %; methane and CO off, methanol takes 24.5 % (0.6 % at 1 bar). At 100 bar with methane off, methanol takes 39.4 %; at 700 K, CO takes 41.0 % and methanol almost nothing.

### 4.11 The bomb calorimeter

    ΔH = ΔU + Δn_gas·R·T
    C_cal = (m × calorific value + corrections) / ΔT
    ΔT = (m × calorific value + corrections) / C_cal

The bomb is closed and rigid: no volume change, no work, so the heat released is ΔU, not ΔH. Calibration with benzoic acid (handout): C_cal = (1.1942 × 6319 + 41) / 2.48 = 3059.3 cal/°C. The corrections are the heat from the burnt thread and wire.

Ethanol: C₂H₅OH(l) + 3 O₂ → 2 CO₂ + 3 H₂O(l). ΔH = −1366.8 kJ/mol from the heats of formation. Δn_gas = 2 − 3 = −1, so ΔU = ΔH − Δn_gas·RT = −1366.8 + 2.48 = −1364.3 kJ/mol. That is 29.62 MJ/kg, and 1 g raises the temperature by 2.31 °C. HHV (water as liquid) 29.67 MJ/kg, LHV (water as vapour) 26.80 MJ/kg; the gap is the latent heat of the water formed. Backwards: 1 g and 2.30 °C give 29.44 MJ/kg, closest to ethanol (0.6 % away; graphite next, 11 % away).

## 5. The website, tab by tab

| Tab | What it answers | What to show |
|---|---|---|
| Start | Cards that open each tab with an example | "Try to break it" |
| 1 Reaction | ΔH°, ΔS°, ΔG° at any T from 298.15 K, with plots, steps and the species table | CO₂ to methanol at 523 K; methane combustion with H2O typed without a phase |
| 2 Pressure and real gas | Ideal against real-gas ΔH at T and P | Ammonia at 723 K and 200 bar; the table of equations |
| 3 Combine reactions | Hess's law with multipliers | RWGS (+39.50) + methanol from CO (−97.44) = −57.94 kJ/mol at 523 K |
| 4 Product slate (extra) | Which products form when reactions compete | The three "Try this" buttons, the pressure slider |
| 5 Bomb calorimeter (extra) | ΔU, ΔH, heating values, identify a sample | Ignite 1 g of ethanol; identify 2.30 °C |
| 6 Species data | The whole database with sources; a sensible-heat calculator | The source column |
| 7 Validation | Reference values, stress tests, published values, the equations against NIST | 67 of 67 |

Every graph's axes cover only the range where it has data. On tab 2 the four graphs share one range of values, so a number can be read across from one to another.

## 6. Where the data come from

- **Smith, Van Ness and Abbott, 8th edition:** Table C.4 (ΔH°f and ΔG°f at 298.15 K), Tables C.1 to C.3 (heat-capacity constants and their ranges), Table B.1 (Tc, Pc, ω, Zc, Vc, boiling points).
- **NIST, only where the textbook has nothing:** hydrogen peroxide and acetic acid vapour; heat capacities from 200 K to 298.15 K (used outside tab 1); heat capacities above the textbook range up to 6000 K for eight gases; and the measured enthalpies of 24 real gases used to choose the equation of state.
- **Units:** J/mol, J/(mol·K), K and bar inside the solver; reaction results in kJ/mol on the page, species data in J/mol.
- **Reference state:** 298.15 K and 1 bar for the formation data, each species in a stated phase: (g), (l) or (s).
- **Checked against the printed tables:** every number was compared with the book. One value differs between editions: ΔG°f of ammonia is −16,450 J/mol in older editions and −16,400 in the 8th; NIST-JANAF (−16,367) supports the 8th edition.

## 7. How the solver was checked

1. **67 reference values** recalculated live on the Validation tab: 44 from the textbook's worked examples, 4 from the course material, 1 hand calculation, 2 steam-table values, 6 from NIST tables and 10 on phase change. All 67 pass.
2. **Five stress tests** of the assignment (section 8).
3. **Published research:** ΔH°298 of eight reactions agrees with research papers within 0.5 kJ/mol.
4. **Independent recalculation:** inside the solver every result is worked out a second time by another route (for example a numerical integral against the closed-form one).
5. **441 automated tests** run on every change, on four Python versions.
6. **The equations of state** against 380 measured NIST points (section 4.9).

## 8. The AI Error Challenge

**The five stress tests:**

| Test | What the solver does |
|---|---|
| 1. Stoichiometry | Every reaction is checked element by element before any calculation. An unbalanced one gets no numbers, only the balanced form as a suggestion. |
| 2. Cp at 1000 K | For all 40 reactions with Cp data at 1000 K: a constant ΔCp is 9.0 kJ/mol off on average, up to 31.5; ignoring ΔCp 7.5 on average, up to 26.0. Steam reforming: 225.3 against 238.8 and 205.8. |
| 3. Physical state | Methane combustion: −890.65 kJ/mol with liquid water, −802.63 with vapour; the gap is 2 × 44.01 kJ/mol. Typed as H2O, the solver picks the phase itself. |
| 4. Correlation validity | Outside a species' Cp range the result comes with a warning and a shaded band. Checked 1 K inside and outside both ends of the range for all 45 reactions. |
| 5. Published work | ΔH°298 of eight reactions within 0.5 kJ/mol of research papers. |

**The eight errors of the AI-generated solver that I found and corrected:**

| Kind | What went wrong | How it was corrected |
|---|---|---|
| Physically unreasonable | CO₂ hydrogenation at 523 K and 100 bar gave 48 % conversion, with liquid water treated as a gas. | The solver detects that a gas would be a liquid and gives no gas-phase value; tab 2 offers a pressure that works (88 bar). |
| Incorrect data | ΔG°f of ammonia −16,450 J/mol from an older edition. | Every number compared with the printed 8th-edition tables (−16,400). |
| Inconsistent results | The rounded constants 0.675 and 0.722 in the virial derivatives made two routes to the same quantity differ by 0.06 %. | The exact products 0.422 × 1.6 = 0.6752 and 0.172 × 4.2 = 0.7224. |
| Misleading text | "Practically no reaction" for ammonia at 723 K, although 43 % converts at 200 bar. | The text refers to 1 bar; the product slate shows the mixture at any pressure. |
| Misleading result | The calorimeter named ethylene oxide gas as the unknown sample, ahead of liquid ethanol. | Only liquids and solids are compared: a gas cannot be weighed into a crucible. |
| Wrong concept | The standard state described as "298.15 K and 1 bar". | It fixes only the pressure; corrected in the app and the guide. |
| Formula out of range | The textbook Cp formula stretched below 298 K and above 2000 K (29 % too low for CO₂ at 200 K). | NIST data in those two ranges. |
| Incomplete | Every species stayed in the phase that was typed, so liquid water stayed a liquid at 500 K. | The solver finds the boiling point from its own data and can use the stable phase. |

## 9. How it is built, and its honest limits

**Built:** the calculations are a Python package (`thermosolver`). The page runs that same Python inside the browser (with Pyodide), so there is no server and nothing is sent anywhere. HTML and JavaScript only draw the forms, tables and plots. It is hosted on GitHub Pages and on Vercel, and the code and tests are on GitHub. I used Claude as the AI platform to write the code; my part was to say what it must do, check every result against the textbook and the course material, find and correct its mistakes, and decide what goes on the page.

**Limits (say them plainly if asked):**

- Standard values are at 1 bar. The pressure effect treats each gas as the pure gas at T and P, so mixing is taken to change no enthalpy.
- The chosen equation of state is the closest of five, not exact (ammonia: still 0.18 kJ/mol off on average), and for a gas without NIST data it is a best guess.
- Phase change is handled at 1 bar for six compounds on tab 1. On tabs 2 and 4 a species that would condense at high pressure is flagged, not condensed.
- The calorimeter assumes complete combustion to CO₂ and liquid water.
- Thermodynamics says where a reaction can end up, not how fast it gets there.

## 10. Viva questions and answers

### A. The project and the idea

**Why did you build this?**
Because the textbook method for ΔH°, ΔS° and ΔG° at a temperature other than 298.15 K is long by hand, and the usual shortcuts can be off by up to 31.5 kJ/mol at 1000 K. The solver does the full method every time, shows the steps, and checks itself.

**Who would use it?**
Students checking their hand calculations, and anyone who needs a quick, trustworthy heat of reaction or favourability check for a reaction at process conditions.

**What is new about it compared with a textbook table?**
It works at any temperature, shows every step, picks the phase of water and other liquids by itself, chooses the equation of state for each gas from measured data, shows which products form when reactions compete, and repeats our calorimeter lab.

**What did the AI do, and what did you do?**
Claude wrote the code. I decided what it must do, compared every result with the textbook and the course material, found and corrected the AI's mistakes (eight are in the report), and decided what goes on the page and how it is worded.

**What are the two extra features, and why those?**
The product slate, because one ΔG° cannot say which products form when reactions compete, and the bomb calorimeter, because it is our own lab and it links ΔU with ΔH.

**How is the assignment brief met?**
Section 5 of the report lists each calculation the brief asks for and the tab that does it; section 6 covers the five stress tests and eight corrected errors.

### B. Basic thermodynamics

**What does exothermic mean, and how does the solver decide?**
It gives out heat: ΔH° < 0. The solver labels the reaction "Gives out heat" or "Takes in heat" from the sign of ΔH°.

**What is the difference between ΔH and ΔU?**
ΔH is the heat at constant pressure, ΔU at constant volume. ΔH = ΔU + Δ(PV), and for gases Δ(PV) = Δn_gas·R·T.

**What does the ° mean? Is 298.15 K part of the standard state?**
The standard state: the pure species at 1 bar, at any temperature. 298.15 K is only the reference temperature of the tables.

**Why is ΔS° of CO₂ to methanol negative?**
Four moles of gas become two, so the disorder falls.

**What does a positive ΔG° mean? Does nothing react?**
The reactants are favoured (K < 1). Some product still forms, only less than reactant at equilibrium.

**If ΔG° is positive at 523 K, why does industry make methanol from CO₂ there?**
Because high pressure moves the equilibrium to the side with fewer gas molecules (24.5 % of the carbon goes to methanol at 50 bar against 0.6 % at 1 bar with only methanol allowed), and a catalyst is needed for the reaction to go at a useful speed. The temperature is a compromise between a good equilibrium and a fast reaction.

**Is your K a Kp or a Kc? Does it change with pressure?**
Kp: partial pressures in bar over the standard pressure of 1 bar. It depends on temperature only; pressure changes the composition, not K.

**How does temperature change favourability?**
Through ΔG° = ΔH° − TΔS°. With ΔH° < 0 and ΔS° < 0, a higher T makes ΔG° less negative or positive (CO₂ to methanol). With both positive, a higher T helps (steam reforming, above 893 K).

**Why does ΔH° of CO₂ to methanol become more negative at higher T?**
Because ΔCp° is negative (−43.95 J/(mol·K) at 298.15 K): the products hold less heat than the reactants, so ΔH° falls as T rises, from −48.97 to −57.94 kJ/mol at 523 K.

**Where is Hess's law used?**
In ΔH°298 = Σ νᵢ ΔH°f,i, in the path through 298.15 K, in the three steps of tab 2, and on tab 3: RWGS (+39.50) plus methanol from CO (−97.44) gives −57.94 kJ/mol, exactly the direct value.

### C. Heat capacity and temperature

**What are A, B, C and D?**
The constants of Cp/R = A + BT + CT² + DT⁻² from the textbook's tables; Cp/R has no unit. Gases use A, B, C, D; each species has its own valid range.

**Why not just use a constant Cp?**
Cp changes with temperature. At 1000 K a constant ΔCp is off by 9.0 kJ/mol on average and up to 31.5 kJ/mol over 40 reactions.

**What happens outside a formula's range?**
The result is still shown, with a warning and a shaded band on the plot. Tab 1 starts at 298.15 K, where the textbook's tables start.

**What are the bars of the sensible-heat chart?**
ν·∫Cp dT of each species from 298.15 K to T. They add up to ΔH°(T) − ΔH°298.

### D. Phase change

**How does the solver know the state of water?**
It compares the Gibbs energy of the liquid and the vapour at 1 bar; the boiling point is where they are equal (373.2 K, textbook 373.15 K). Below it the liquid is stable, above it the vapour.

**Why are there kinks in the tab 1 graphs with "Pick the stable phase"?**
At a boiling point the species changes phase. ΔH° jumps by ν × latent heat (methane combustion: +81.73 kJ/mol at 373.2 K), ΔCp° jumps, and ΔG° only bends, because at the boiling point liquid and vapour have the same Gibbs energy.

**Why −890.65 and −802.63 kJ/mol for methane combustion?**
Liquid water against water vapour. The gap, 88.02 kJ/mol, is twice the heat of vaporisation of water at 298.15 K (44.01 kJ/mol).

### E. Real gases

**Why does the ideal-gas ΔH not change with pressure?**
U of an ideal gas depends on T only, and PV = RT, so H = U + RT depends on T only.

**What is the residual enthalpy?**
The real-gas H minus the ideal-gas H at the same T and P. It is a residual property, worked out from an equation of state.

**Is the residual enthalpy calculated per species or for the whole reaction?**
Per species, each as a pure gas at T and P with its own equation of state; then ν·Hᴿ is added up over the reaction.

**Why is Hᴿ of N₂ and H₂ positive at 723 K and 200 bar?**
They are far above their critical temperatures (Tr = 5.73 and 21.79), so attraction hardly matters and the size of the molecules wins: Z > 1 (1.070 and 1.058), Hᴿ > 0.

**Why is Hᴿ more negative close to the critical point?**
Near Tr = 1 a gas is almost a liquid: the molecules are close and slow enough for their attraction to matter. Methanol at 523 K has Tr = 1.02 and Hᴿ = −4.12 kJ/mol at 50 bar.

**Which equation of state does the solver use, and why not always Peng/Robinson?**
For each gas, the one closest to NIST measured data: SRK for 14 gases, PR for 6, RK for 4. Peng/Robinson is not the closest for every gas, and the average errors show it: SRK 0.137 kJ/mol against PR 0.160.

**Why is the older Redlich/Kwong chosen for methane?**
The measured data say so: for methane it is 0.046 kJ/mol off against 0.051 for SRK. The solver prefers the equation that matches the measurements, not the newest one.

**Why are van der Waals and the virial equation never chosen?**
Their average errors are about ten times larger (1.246 and 1.349 kJ/mol). Van der Waals ignores the shape of the molecule (no acentric factor), and the virial equation is meant for low to moderate pressure only.

**Is the chosen equation exact?**
No, it is the closest of the five. And for a gas without NIST data it is a best guess from the other gases.

**What is the acentric factor?**
A number from Table B.1 that measures how far a molecule is from a simple round one; SRK and PR use it.

**Why does CO₂ hydrogenation at 200 bar and 523 K give no gas-phase value?**
Water would be a liquid there: its equation of state has no gas state above about 90 bar at 523 K. The tab says so and offers 88 bar.

**Is ΔH at 200 bar a standard value?**
No. The ° values are at 1 bar. ΔH(T,P) is for the pure real gases at T and P.

### F. The product slate

**How does it work without a list of reactions?**
It looks for the amounts of all allowed species with the lowest total Gibbs energy while every element's atoms are conserved. Any reaction between the allowed species is then included automatically.

**Why does methane win?**
Making methane lowers the total Gibbs energy much more than making methanol does. Industry uses a catalyst that makes methanol but not methane, which is what the switch imitates.

**What does a faded switch mean?**
Switching that product off would change nothing at the current settings, because it holds almost none of the atoms (methanol 1.5 × 10⁻¹⁰ as a mole fraction while methane is allowed).

**Why does pressure help methanol and temperature hurt it?**
Methanol formation reduces the number of gas molecules, so higher pressure helps (39.4 % at 100 bar with methane off). It is exothermic, so a higher temperature pushes towards CO (41.0 % CO at 700 K).

**Are the gases ideal on this tab?**
No, they are real gases, each with the equation of state chosen for it. If a gas would be a liquid on its own at high pressure, it stays a vapour in the mixture, and for that point the solver describes it with the virial equation and says so.

### G. The bomb calorimeter

**Why does the bomb measure ΔU and not ΔH?**
Its volume is fixed, so no work is done, and the heat equals ΔU.

**How is the calorimeter constant found?**
From the benzoic acid run: (1.1942 g × 6319 cal/g + 41 cal) / 2.48 °C = 3059.3 cal/°C.

**What are the corrections?**
The heat from the burnt thread and wire, which is not from the sample.

**Why is ΔU of ethanol less negative than ΔH?**
Δn_gas = −1, so ΔU = ΔH − Δn_gas·RT = −1366.8 + 2.48 = −1364.3 kJ/mol.

**What is the difference between HHV and LHV?**
HHV counts the water formed as liquid (29.67 MJ/kg for ethanol), LHV as vapour (26.80 MJ/kg). The gap is the latent heat of that water.

**How does it identify an unknown sample?**
It turns the measured rise into a calorific value (2.30 °C for 1 g gives 29.44 MJ/kg) and lists the liquid and solid fuels by how close they are: ethanol 0.6 % away, graphite 11 %.

### H. Data and checking

**Where do the data come from?**
From the textbook's tables (C.1 to C.4 and B.1); NIST only where the textbook has nothing. Each species shows its source on tab 6.

**How do you know the numbers are right?**
67 of 67 reference values reproduced, published values within 0.5 kJ/mol, an independent second route inside the solver, and 441 automated tests.

**What are the 67 reference values?**
44 from the textbook's worked examples, 4 from the course material, 1 hand calculation, 2 steam-table values, 6 from NIST tables and 10 on phase change.

**What was the hardest error to find?**
The rounded constants 0.675 and 0.722: the results looked right, but two routes to the same quantity differed by 0.06 %, which only the internal comparison showed.

### I. The software

**How does Python run in a web page?**
With Pyodide, a version of Python that runs inside the browser. The browser downloads it once (about 10 MB), then everything runs on the user's computer.

**What if there is no internet?**
The page needs the internet once, to load Python and the plotting library. If only the two hosted addresses were down, the project folder has a small local server (`python serve.py`). With no internet at all, the slides and the report carry the numbers.

**What do the automated tests check?**
The data against the printed tables, every formula against an independent calculation, the reference values, the stress tests, the wording of the page, and that the hosted files fit together. They run on every change.

### J. Harder questions

**Why does ΔG° not jump at a boiling point while ΔH° does?**
At the boiling point the liquid and the vapour have the same Gibbs energy, but different enthalpies; the difference in enthalpy is the latent heat.

**What would you add next?**
An equation of state for the mixture as a whole on tab 4 (instead of pure gases), measured data for more gases, and phase change at high pressure on tabs 2 and 4.

**What can the solver not tell you?**
How fast a reaction goes. Thermodynamics gives where a reaction can end up, not its rate.

**How large is the uncertainty of the real-gas part?**
For a gas with NIST data, about the average error of its chosen equation (for example 0.18 kJ/mol for ammonia). For a gas without data, larger and unknown.

## 11. On the day

- Laptop charged, slides open, the site loaded with **Solver ready** showing, spare address and local copy ready.
- Say the idea first (slide 2), then show it live. Keep each tab to the numbers above.
- If you do not know an answer, say what you do know and where the solver shows it. Every number on the screen comes from the solver, not from memory.
