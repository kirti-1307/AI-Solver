# Study guide for the presentation and the viva

This guide has everything needed to present the Thermodynamic Reaction Energy Solver and to answer questions on it. Every number in it is what the solver gives, so it matches the screen and the report. Read sections 1 to 3 the day before, skim sections 4 to 9, and go through the questions in section 10 out loud.

## 1. The project in one minute (the idea)

**The story.** The talk opens with Goldilocks and the three bears. Goldilocks finds three bowls of porridge and asks: how hot is each porridge? In the story she finds out by tasting (too hot, too cold, just right) and burns her tongue. The solver works it out for her instead: it gives ΔH, the heat a reaction gives out or takes in, and heat is what decides how hot something gets. Each tab then answers a part of her question, and on tab 5 (the bomb calorimeter) the solver turns heat into an actual temperature rise.

**Be careful with one point.** ΔH is heat (kJ/mol), not a temperature. The temperature follows from the heat and the heat capacity: ΔT = heat / heat capacity. That is exactly what the calorimeter does (1 g of ethanol: 2.31 °C). So say "ΔH tells how much heat", never "ΔH is the temperature".

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
| Steam reforming: products favoured | above 893 K (ΔG° changes sign) |
| Steam reforming at 700 K | ΔH° = +219.9 kJ/mol, ΔG° = +47.9 kJ/mol |
| Steam reforming at 1000 K | ΔG° = −27.0 kJ/mol; ΔH° = 225.3 kJ/mol with Cp(T), 238.8 with a constant ΔCp, 205.8 with ΔCp ignored |
| Constant ΔCp at 1000 K, 40 reactions | 9.0 kJ/mol off on average, up to 31.5 (benzene hydrogenation) |
| Methane combustion at 298.15 K | −890.65 kJ/mol with liquid water, −802.63 with water vapour; the gap is 2 × 44.01 kJ/mol |
| Boiling points from the solver's own data | water 373.2 K, methanol 337.1 K, ethanol 351.3 K |
| Ammonia synthesis, 723 K, 200 bar | ideal gas −106.50 kJ/mol, real gas −111.55 kJ/mol, residual part −5.05 kJ/mol (4.7 %) |
| Real-gas effect, other cases | CO₂ to methanol at 50 bar 10.6 %, steam reforming at 1100 K 0.2 % |
| Equations of state against NIST data | 24 gases, 380 points; closest: Soave/Redlich/Kwong 14 gases, Peng/Robinson 6, Redlich/Kwong 4 |
| Average error against NIST data | SRK 0.137, PR 0.160, RK 0.510, van der Waals 1.246, virial 1.349 kJ/mol |
| Product slate, CO₂ + 3 H₂, 523 K, 50 bar | everything allowed: methane 74.9 % of the carbon; methane off: methanol 20.6 %, CO 7.5 %; methane off at 100 bar: methanol 39.4 % |
| Only methanol allowed | 0.6 % at 1 bar, 24.5 % at 50 bar |
| Calorimeter constant | (1.1942 g × 6319 cal/g + 41 cal) / 2.48 °C = 3059.3 cal/°C |
| 1 g of ethanol in the calorimeter | ΔH = −1366.8 kJ/mol, ΔU = −1364.3 kJ/mol, 29.62 MJ/kg, rise 2.31 °C |
| Heating values of ethanol | HHV 29.67 MJ/kg, LHV 26.80 MJ/kg |
| Validation | 67 of 67 reference values; 8 published reactions within 0.5 kJ/mol; 441 automated tests |
| Hess's law on tab 3, 523 K | reverse water-gas shift +39.50 + methanol synthesis −97.44 = −57.94 kJ/mol |
| Sensible heat on tab 6 | 1 mol of methane from 298.15 K to 1000 K: 38.49 kJ |

## 3. The nine slides in short

The deck is written out in full in `presentation/PITCH_DECK.md`; the words to say are in the presentation script, and a one-page sheet of pointers is `docs/SPEAKER_POINTERS.md`.

1. **How hot is each porridge?** Goldilocks and the three bowls. She tastes and burns her tongue; the solver works out ΔH, the heat, instead. Project title, my name and roll number along the bottom.
2. **Tab 1, Reaction.** Pick or type a reaction; balance check first; ΔH°, ΔS°, ΔG° from 298.15 K up; gives out or takes in heat, which side is favoured. CO₂ to methanol at 523 K: −57.94 and +46.56 kJ/mol.
3. **Tab 2, Pressure and real gas.** Ideal gas: pressure changes nothing. Real gas: residual enthalpy of each gas, with the equation of state the solver picks from NIST data. Ammonia at 723 K and 200 bar: −106.50 → −111.55 kJ/mol, 4.7 %.
4. **Tab 3, Combine reactions.** Hess's law with multipliers; a negative one reverses a reaction. +39.50 + (−97.44) = −57.94 kJ/mol, the same as tab 1.
5. **Tab 4, Product slate (extra feature 1).** Choose the allowed products; lowest total Gibbs energy. Methane 74.9 %; methane off: methanol 20.6 %; 100 bar: 39.4 %. The catalyst decides.
6. **Tab 5, Bomb calorimeter (extra feature 2).** Benzoic acid calibration 3059.3 cal/°C; ΔU, not ΔH; heat into a temperature rise: 1 g of ethanol, 2.31 °C; names an unknown sample.
7. **Tab 6, Species data.** 57 species; textbook tables, NIST only where needed; every source shown; warming 1 mol of methane to 1000 K: 38.49 kJ.
8. **Tab 7, Validation.** 67/67 reference values, 5/5 stress tests, 8 published reactions within 0.5 kJ/mol, 8 AI errors corrected, 441 automated tests.
9. **So, how hot is the porridge?** ΔH: how much heat. ΔG: which side wins. The calorimeter: heat into degrees. Then the live demo.

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
- ΔH° > 0 and ΔS° > 0: favoured at high temperature (steam reforming, above 893 K: ΔG° = +47.9 kJ/mol at 700 K, −27.0 at 1000 K).
- The temperature where ΔG° = 0 is where the favoured side changes. For CO₂ to methanol it is 276 K, below the range of tab 1.
- K here is Kp: written with partial pressures in bar divided by the standard pressure of 1 bar. It depends on temperature only. Pressure changes the equilibrium composition, not K.

**Why the lines of the energy graph on tab 1 look almost straight.** The graph shows ΔH°, ΔG° and T·ΔS° against temperature. They are not exactly straight, only nearly:

- ΔH° changes with T at a rate of ΔCp°, which is small: for CO₂ to methanol about −44 J/(mol·K), so over 225 K ΔH° moves only by about 9 kJ/mol (from −48.97 to −57.94). On a scale of tens of kJ that looks almost flat. Because ΔCp° itself changes a little with T, the line bends a little.
- ΔG° = ΔH° − T·ΔS°. If ΔH° and ΔS° did not change at all, ΔG° would be an exact straight line, starting at ΔH°298 with a slope of −ΔS°298. They change only slowly, so the real ΔG° line is very close to a straight line. For CO₂ to methanol it rises from +3.83 kJ/mol at 298.15 K to +46.56 kJ/mol at 523 K, a slope of about +0.19 kJ/(mol·K), which is −ΔS°.
- T·ΔS° is T times a slowly changing ΔS°, so it is also close to a straight line through zero.
- At a boiling point (with "Pick the stable phase" ticked) the lines have a step or a kink: that is real, not a mistake (section 4.7).

**The two shortcut lines (dashed and dotted) on that graph, and the table "How much does the heat-capacity treatment matter?":**

- **Constant ΔCp:** ΔCp° is taken at its 298.15 K value and used at every temperature. Then ΔH°(T) = ΔH°298 + ΔCp°298·(T − 298.15), an exact straight line.
- **ΔCp ignored:** ΔCp° is taken as zero, so ΔH° and ΔS° keep their 298.15 K values at every temperature (the page used to say "frozen" for this). Then ΔG°(T) = ΔH°298 − T·ΔS°298, also an exact straight line. For CO₂ to methanol at 523.15 K this gives −48.97 + 523.15 × 0.17708 = +43.67 kJ/mol, against the correct +46.56.
- The solid lines use Cp(T) = A + BT + CT² + DT⁻² for every species, which is the full textbook method. The gap between a solid line and its shortcut line is the error of that shortcut (stress test 2).

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

**The three steps** (not shown on the website; only in case you are asked how the real-gas ΔH is put together). They reach the real-gas ΔH by a detour, like Hess's law: take the real reactants to ideal gas (this removes their Hᴿ), let the ideal gases react (ΔH° from tab 1), then take the ideal products to real gas (this adds their Hᴿ). H is a state function, so the detour gives the same answer as the direct route. It also shows why Hᴿ is worked out for each species: steps 1 and 3 are sums over the gases. For ammonia at 723 K and 200 bar:

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

Ethanol: C₂H₅OH(l) + 3 O₂ → 2 CO₂ + 3 H₂O(l). ΔH = −1366.8 kJ/mol from the heats of formation. Δn_gas = 2 − 3 = −1, so ΔU = ΔH − Δn_gas·RT = −1366.8 + 2.48 = −1364.3 kJ/mol. That is 29.62 MJ/kg, and 1 g raises the temperature by 2.31 °C. HHV (water as liquid) 29.67 MJ/kg, LHV (water as vapour) 26.80 MJ/kg; the gap is the latent heat of the water formed.

**The lab handout's shortcut for the LHV** (not shown on the website; only in case you are asked). The handout works out the lower heating value as LHV = HHV − m_w·h_fg: start from the bomb value, and take away the latent heat of the water formed. Here m_w is the mass of water formed per gram of fuel (ethanol: 3 × 18.015 / 46.07 = 1.173 g/g) and h_fg is the latent heat of water at 298.15 K, 2443 J/g (that is 44.01 kJ/mol ÷ 18.015 g/mol). For ethanol: 29.62 − 1.173 × 2.443 = 26.75 MJ/kg. The solver's LHV from the formation data (water as vapour) is 26.80 MJ/kg. The small difference is the Δn_gas·R·T term: the bomb value is −ΔU/M, while the heating values at constant pressure use −ΔH/M, and the two differ by Δn_gas·R·T/M = 2.48 kJ/mol ÷ 46.07 g/mol = 0.054 MJ/kg for ethanol. So the handout's shortcut is a very good approximation, off by much less than 1 %.

Backwards: 1 g and 2.30 °C give 29.44 MJ/kg, closest to ethanol (0.6 % away; graphite next, 11 % away).

## 5. The website, tab by tab

| Tab | What it answers | What to show |
|---|---|---|
| Start | Cards that open each tab with an example | "Try to break it" |
| 1 Reaction | ΔH°, ΔS°, ΔG° at any T from 298.15 K, with plots, steps and the species table | CO₂ to methanol at 523 K; methane combustion with H2O typed without a phase |
| 2 Pressure and real gas | Ideal against real-gas ΔH at T and P | Ammonia at 723 K and 200 bar; the four graphs |
| 3 Combine reactions | Hess's law with multipliers | RWGS (+39.50) + methanol from CO (−97.44) = −57.94 kJ/mol at 523 K |
| 4 Product slate (extra) | Which products form when reactions compete | The three "Try this" buttons, the pressure slider |
| 5 Bomb calorimeter (extra) | ΔU, ΔH, heating values, identify a sample | Ignite 1 g of ethanol; identify 2.30 °C |
| 6 Species data | The whole database with sources; a sensible-heat calculator | The source column |
| 7 Validation | Reference values, stress tests, published values, the equations against NIST | 67 of 67 |

Every graph's axes cover only the range where it has data. On tab 2 the four graphs share one range of values, so a number can be read across from one to another.

### Tab 4, explained

**What it does, in one sentence.** You put the feed gases in a reactor and say which products the catalyst is allowed to make; the solver finds the mixture that comes out at equilibrium (the one with the lowest total Gibbs energy that keeps every atom) and shows where the carbon atoms end up.

**Why it is needed.** Tab 1 handles one reaction at a time. But from CO₂ + H₂, three reactions compete for the same carbon atoms. At 523 K:

| Reaction | ΔG° at 523 K | ΔH° at 523 K |
|---|---|---|
| CO₂ + 3H₂ → CH₃OH + H₂O (methanol) | +46.56 kJ/mol | −57.94 kJ/mol |
| CO₂ + 4H₂ → CH₄ + 2H₂O (methane) | −71.07 kJ/mol | −175.32 kJ/mol |
| CO₂ + H₂ → CO + H₂O (reverse water-gas shift) | +19.58 kJ/mol | +39.50 kJ/mol |

Three separate ΔG° values cannot say how the carbon is shared between them. Tab 4 can, because it works on the whole mixture at once.

**How the solver finds the mixture, in plain words.** At a fixed temperature and pressure, a mixture settles where its total Gibbs energy is as low as it can get, like a ball rolling to the bottom of a valley. The solver changes the amounts of all the allowed species step by step, always keeping the number of C, H and O atoms equal to what the feed brought in, until G cannot get any lower:

    G/RT = Σ nᵢ [Gᵢ°/RT + ln(yᵢ·P/P°) + Gᵢᴿ/RT]

The first term is each species' standard Gibbs energy (from the tables, as on tab 1), the second is the effect of its mole fraction and the pressure, and the third is the real-gas correction. No list of reactions is needed: every reaction between the allowed species is included automatically.

**What is on the screen, from top to bottom:**

| Item | What it is |
|---|---|
| Example system | Three ready systems: CO₂ hydrogenation (opens first), methane steam reforming, dry reforming of methane |
| Temperature and Pressure sliders | The reactor conditions. The bars follow while you drag; the two graphs are redrawn when you let go |
| "The catalyst may form" switches | One per species. On: the catalyst can make it. Off: it cannot. The small label says what the switch does now |
| Label "feed" (dashed) | Fed to the reactor (CO₂ and H₂), so it cannot be switched off |
| Label "needed" | Without it nothing can react: water, because the oxygen atoms of CO₂ have to go somewhere |
| Label "no effect now" (faded) | It holds almost none of the carbon, so switching it off would change nothing at these settings |
| A percentage | The share of the carbon atoms that species holds now |
| "Try this" buttons 1, 2, 3 | Ready settings of the switches: everything allowed; methane off; methane and CO off. The line under them says what changed |
| "Where the C atoms go" | Bars: the share of the carbon atoms in each species. They add up to 100 % |
| "Mole fractions at equilibrium" | Bars: the mole fraction y of each species in the gas that leaves |
| "Moles of gas" card | Total moles at equilibrium, from 4 mol of feed (1 CO₂ + 3 H₂) |
| "What it means" | The result in sentences |
| Two graphs | Mole fractions, and where the carbon goes, against temperature from 400 to 900 K; the line marks your temperature |

**The numbers to know (CO₂ + 3H₂):**

| Setting | Where the carbon goes | Other numbers |
|---|---|---|
| 1. Everything allowed, 523 K, 50 bar | CH₄ 74.9 %, unreacted CO₂ 25.1 % | 2.50 mol of gas; y(H₂O) = 0.598, y(H₂) = 0.002; methanol 1.5 × 10⁻¹⁰ |
| 2. Methane off, 523 K, 50 bar | CH₃OH 20.6 %, CO 7.5 %, CO₂ 71.9 % | 3.59 mol of gas |
| 3. Methane and CO off, 523 K, 50 bar | CH₃OH 24.5 %, CO₂ 75.5 % | 0.6 % methanol at 1 bar |
| Methane off, 450 K, 50 bar | CH₃OH 45.9 %, CO 0.6 % | colder helps methanol |
| Methane off, 700 K, 50 bar | CO 41.0 %, CH₃OH 0.3 % | hotter helps CO |
| Methane off, 523 K, 100 bar | CH₃OH 39.4 %, CO 3.5 % | higher pressure helps methanol |

The words to say while showing it are in the presentation script, part 2, tab 4.

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
- Phase change is handled at 1 bar for six compounds on tab 1. At high pressure nothing is condensed: on tab 2 a gas that would be a liquid at that T and P gets no gas-phase value (the tab says so and offers a pressure that works); on tab 4 water diluted in the mixture is kept as a vapour.
- The calorimeter assumes complete combustion to CO₂ and liquid water.
- Thermodynamics says where a reaction can end up, not how fast it gets there.

## 10. Viva questions and answers

### A. The project and the idea

**Why did you start with Goldilocks?**
Because her question, "how hot is each porridge?", is a question about heat, and heat is what my solver works out. She finds out by tasting and burns her tongue; the solver works it out instead, through ΔH. And on tab 5 it even turns the heat into a temperature rise, like our calorimeter lab.

**Does ΔH tell you the temperature of the porridge?**
Not directly. ΔH is heat, in kJ per mole of reaction. The temperature follows from the heat and the heat capacity: ΔT = heat / heat capacity. That is exactly what the bomb calorimeter does: the heat of 1 g of ethanol divided by the calorimeter constant (3059.3 cal/°C) gives 2.31 °C. So ΔH tells how much heat; with the heat capacity, that gives how hot.

**Why do you need ΔG as well as ΔH?**
ΔH tells how much heat; it does not tell which side is favoured. That needs ΔG° = ΔH° − TΔS°. CO₂ to methanol gives out heat (ΔH° = −57.94 kJ/mol at 523 K), but ΔG° = +46.56 kJ/mol, so the reactants are favoured there. A positive ΔG° still gives some product, only less than reactant at equilibrium.

**Why is steam reforming only favoured at high temperature?**
CH₄ + H₂O → CO + 3H₂ takes in heat (ΔH° = +219.9 kJ/mol at 700 K) but turns 2 moles of gas into 4, so ΔS° is positive. In ΔG° = ΔH° − TΔS° the −TΔS° term only outweighs ΔH° above 893 K. That is why steam reforming is run hot; the predefined reaction opens at 1073 K.

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
In ΔH°298 = Σ νᵢ ΔH°f,i, in the path through 298.15 K, in the three steps behind the real-gas ΔH (section 4.8), and on tab 3: RWGS (+39.50) plus methanol from CO (−97.44) gives −57.94 kJ/mol, exactly the direct value.

### C. Heat capacity and temperature

**What are A, B, C and D?**
The constants of Cp/R = A + BT + CT² + DT⁻² from the textbook's tables; Cp/R has no unit. Gases use A, B, C, D; each species has its own valid range.

**Why not just use a constant Cp?**
Cp changes with temperature. At 1000 K a constant ΔCp is off by 9.0 kJ/mol on average and up to 31.5 kJ/mol over 40 reactions.

**What happens outside a formula's range?**
The result is still shown, with a warning and a shaded band on the plot. Tab 1 starts at 298.15 K, where the textbook's tables start.

**Why does the energy graph of tab 1 look linear?**
It is only nearly linear. ΔH° changes at the rate ΔCp°, which is small (about −44 J/(mol·K) for CO₂ to methanol, so ΔH° moves only about 9 kJ/mol over 225 K). And ΔG° = ΔH° − TΔS°: with ΔH° and ΔS° changing only slowly, ΔG° is almost a straight line with slope −ΔS°. It would be exactly straight if ΔCp were zero; that is the dotted shortcut line (section 4.5).

**What does "ΔCp ignored" mean?**
ΔCp° is taken as zero, so ΔH° and ΔS° keep their 298.15 K values at every temperature, and ΔG° = ΔH°298 − T·ΔS°298. It is a shortcut; the gap to the solid line is its error (+43.67 against +46.56 kJ/mol for CO₂ to methanol at 523 K). "Constant ΔCp" is the other shortcut: ΔCp° kept at its 298.15 K value.

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
For each gas, the one closest to NIST measured data: SRK for 14 gases, PR for 6, RK for 4. Peng/Robinson is not the closest for every gas, and the average errors show it: SRK 0.137 kJ/mol against PR 0.160. The Validation tab (tab 7) shows the comparison for every gas, with the column "Used by the solver".

**What are the three steps behind the real-gas ΔH?**
Real reactants to ideal gas (removes their Hᴿ), the ideal-gas reaction (ΔH° from tab 1), ideal products to real gas (adds their Hᴿ). Like Hess's law, the detour gives the same answer because H is a state function. Ammonia at 723 K and 200 bar: −1.15 − 106.50 − 3.90 = −111.55 kJ/mol (section 4.8).

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
No, they are real gases, each with the equation of state chosen for it. If a gas would be a liquid on its own at high pressure (water at 523 K above about 90 bar), it is diluted in the mixture and stays a vapour, and for that point the solver describes it with the virial equation, which has a gas state at any pressure. (The page does not show a note about this.)

**Why does methane take 74.9 % of the carbon, and not all of it?**
Hydrogen runs out. Making methane needs 4 H₂ per CO₂, and the feed has only 3, so at most 3/4 = 75 % of the CO₂ can become methane. At equilibrium almost no hydrogen is left (y = 0.002).

**Why is water the largest mole fraction (0.598) when methane is allowed?**
Every CH₄ comes with 2 H₂O: CO₂ + 4H₂ → CH₄ + 2H₂O. And the hydrogen is almost used up.

**Why does the number of moles of gas fall from 4 to 2.50?**
CO₂ + 4H₂ → CH₄ + 2H₂O turns 5 moles of gas into 3. Fewer moles is also why high pressure favours methane and methanol.

**Why is water "needed"?**
The oxygen atoms of CO₂ have to go somewhere. Methanol and CO keep only one of the two oxygen atoms, and methane none, so every route needs water. Without water nothing can react.

**Is this how fast the reactor gets there?**
No. It is the equilibrium mixture: what the reactor would reach with unlimited time. Thermodynamics gives the limit; the catalyst and the reaction rates decide how close a real reactor gets.

**How is this different from tab 1's ΔG°?**
Tab 1 is one reaction between pure species at 1 bar. Tab 4 is a whole mixture: it includes the mole fractions (the ln y term), the pressure and the real-gas correction, and all the reactions at once.

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

**The lab handout gets the LHV differently. Why does it give a slightly different number?**
The handout uses LHV = HHV − m_w·h_fg, starting from the bomb value: 29.62 − 1.173 × 2.443 = 26.75 MJ/kg for ethanol, against 26.80 from the formation data. The bomb value is −ΔU/M, but heating values are at constant pressure (−ΔH/M); the two differ by Δn_gas·R·T/M = 0.054 MJ/kg. That small term is the whole difference (section 4.11).

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

**Why are there two web addresses?**
The same files from the GitHub repository are hosted twice, as a spare: on GitHub Pages (kirti-1307.github.io/AI-Solver) and on Vercel (ai-solver-seven.vercel.app). Every change pushed to GitHub updates both within a minute or two. Vercel also makes a separate, frozen copy of every single update, each with its own long address; those are snapshots of old versions, so only the two addresses above are used.

**After an update, why did the old page still show?**
A browser may keep a copy of the page for up to 10 minutes. The page now checks the server's version when it opens and reloads itself once if it is out of date; Ctrl+Shift+R also loads the latest version.

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
- Use only https://ai-solver-seven.vercel.app/ or https://kirti-1307.github.io/AI-Solver/. Check that tab 1 starts with the short line "Pick a reaction or type your own. The solver calculates ΔH°, ΔS° and ΔG°…"; if not, press Ctrl+Shift+R once.
- Tell the story (slide 1), give each tab its slide (slides 2 to 8), close the story (slide 9), then show it live. Keep each tab to the numbers above.
- Keep the one-page pointer sheet (`docs/SPEAKER_POINTERS.md`, printed) beside you: one block per slide, with the line to start with and the number to say.
- If you do not know an answer, say what you do know and where the solver shows it. Every number on the screen comes from the solver, not from memory.
