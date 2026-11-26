# A beginner's guide to the solver

This guide explains the Thermodynamic Reaction Energy Solver in plain words. You do not need to read it in order. If you only have ten minutes, read sections 1, 2 and 4.

## 1. What the solver does

You give it a chemical reaction, a temperature and a pressure. It tells you four things:

- **How much heat** the reaction gives out or takes in.
- **Which side is favoured** at that temperature: the products or the reactants.
- **How far it goes** before it stops.
- **What changes** if you raise the pressure.

Before it calculates anything, it checks that the reaction is balanced. If the atoms on the left do not match the atoms on the right, it refuses and shows you the balanced form.

All the data come from the course textbook (Smith, Van Ness and Abbott). The solver knows 57 substances and 45 ready-made reactions, and you can type your own.

## 2. Six ideas you need

### Heat of reaction, ΔH

ΔH is the heat a reaction gives out or takes in.

- **Negative ΔH** means the reaction gives out heat. It is called exothermic. Burning is an example.
- **Positive ΔH** means the reaction takes in heat. It is called endothermic. You have to keep heating it.

Example: CO₂ + 3 H₂ → CH₃OH + H₂O has ΔH = −48.97 kJ/mol at 298 K. It gives out heat.

### Heat capacity, Cp

Cp tells you how much heat a substance needs to get 1 K hotter. It is not a fixed number: it changes with temperature. The textbook gives a formula for it with four constants, A, B, C and D:

    Cp/R = A + B·T + C·T² + D/T²

The heat needed to warm something from T₁ to T₂ is called **sensible heat**. You get it by adding up Cp over that temperature range. Example: warming 1 mol of methane from 260 °C to 600 °C needs 19,778 J.

### Entropy change, ΔS

Entropy measures how spread out, or disordered, things are. Gases are very disordered.

- If a reaction makes **more gas molecules**, ΔS is positive.
- If it makes **fewer gas molecules**, ΔS is negative.

Example: CO₂ + 3 H₂ → CH₃OH + H₂O turns 4 gas molecules into 2, so ΔS is negative (−199.76 J/(mol·K) at 523 K).

### Gibbs energy, ΔG

ΔG combines the two ideas above into one number that tells which way a reaction leans:

    ΔG = ΔH − T·ΔS

- **Negative ΔG**: the products are favoured.
- **Positive ΔG**: the reactants are favoured. Some product still forms, only less.

Notice the T in the formula. The same reaction can favour the products at one temperature and the reactants at another.

Example at 523 K: ΔG = −57.94 − 523.15 × (−0.19976) = +46.56 kJ/mol. The reaction gives out heat, but the loss of entropy wins, so the reactants are favoured at this temperature.

### Equilibrium constant, K

A reaction does not always go all the way. It stops at a balance point called equilibrium. K tells you where that point is:

    ln K = −ΔG / (R·T)

- **K much bigger than 1**: mostly products.
- **K much smaller than 1**: mostly reactants.
- **K near 1**: a mixture of both.

Example: for the reaction above at 523 K, K = 2.2 × 10⁻⁵. Almost nothing reacts at 1 bar (0.6 % conversion).

**Which K is it?** The K of this solver is **Kp**: it is written with the partial pressure of each gas in bar, divided by the standard pressure of 1 bar, so it has no units. It is not Kc, which is written with concentrations. Pure liquids and solids do not appear in it. Kp changes with temperature only. Pressure changes how far the reaction goes, but not Kp.

### Real gases and residual enthalpy, Hᴿ

At low pressure, gas molecules are far apart and ignore each other. That is an ideal gas, and its enthalpy does not depend on pressure.

At high pressure the molecules are close and attract each other. The gas is then a **real gas**. The difference between the real value and the ideal value is called the **residual** enthalpy, Hᴿ. The solver gets it from an equation of state, and it picks the equation for each gas itself (see tab 2).

So at high pressure: ΔH(real) = ΔH(ideal) + the residual part.

## 3. Standard state, and why the calculation starts at 298.15 K

**Standard state** is about pressure, not temperature. It means the pure substance at 1 bar, and a gas is taken as an ideal gas. The temperature can be anything you choose. The small ° in ΔH° means "at the standard state", so ΔH° at 250 K, at 298.15 K and at 800 K are all standard values.

298.15 K (25 °C) is only the **reference temperature**. It is the one temperature at which the textbook lists the heat of formation of each substance. So every calculation starts there.

To get ΔH° at another temperature, the solver walks a three-step path:

1. Take the reactants from your temperature to 298.15 K.
2. Let them react at 298.15 K, where the data are known.
3. Take the products back to your temperature.

Steps 1 and 3 are sensible heat, calculated from Cp. The answer does not depend on the path, because enthalpy only depends on where you start and where you end.

Example from the textbook: CO + 2 H₂ → CH₃OH has ΔH° = −90,135 J at 298.15 K and −103,566 J at 800 °C. The solver gives the same numbers.

### Below 298.15 K

The textbook's Cp formulas start at 298 K, and they must not be stretched downwards: for CO₂ at 200 K the formula gives a Cp that is 29 % too low. Tab 1 therefore starts at 298.15 K, the reference temperature of the data, and does not accept a lower temperature. The solver does hold heat capacities from NIST tables between 200 K and 298.15 K; they are listed on the Species data tab.

### Above 2000 K

The textbook's Cp formula for the gases of a flame (N₂, O₂, CO₂, H₂O) ends at 2000 K. A flame is hotter than that. Beyond 2000 K the textbook formula keeps climbing, while the real Cp levels off, so it must not be stretched upwards either.

So above the textbook limit, up to 6000 K, the solver uses NIST equations for eight flame gases (N₂, O₂, CO₂, H₂O, CO, H₂, SO₂, NO). Inside the textbook range nothing changes. For every other substance the textbook limit stays, and the solver warns beyond it.

### Liquid or vapour: where a substance boils

Seven substances are in the database twice, once as a liquid and once as a gas: water, methanol, ethanol, benzene, cyclohexane, toluene and acetic acid. Which form is right depends on the temperature.

The rule is short. At 1 bar the stable form is the one with the lower Gibbs energy. At the boiling point the two are equal. So the solver can find the boiling point itself, from data it already has:

| Substance | Boiling point the solver finds | Textbook value |
|---|---|---|
| Water | 373.2 K | 373.2 K |
| Methanol | 337.1 K | 337.9 K |
| Ethanol | 351.3 K | 351.4 K |
| Benzene | 354.2 K | 353.2 K |
| Cyclohexane | 354.5 K | 353.9 K |
| Toluene | 388.4 K | 383.8 K |

Nothing was fitted to get these. The textbook boiling points are not used in the calculation, so the agreement is a check on the data of both forms.

Acetic acid is the exception. Its data put the boiling point at 434 K, which is 43 K too high. Its liquid has only one Cp value, valid from 290 to 320 K, and its real vapour is partly made of double molecules, which the data leave out. So the solver never changes the phase of acetic acid by itself, and says why.

Three things happen at a boiling point:

- **ΔH° jumps.** A reaction that makes 1 mol of water releases 40.86 kJ less once that water is vapour. The jump is the latent heat.
- **ΔS° jumps too**, by the latent heat divided by the boiling point.
- **ΔG° does not jump.** The two jumps cancel exactly, because liquid and vapour have the same Gibbs energy there. So K has no jump either.

The same data give the **vapour pressure**: the pressure at which a liquid and its vapour are in balance at a given temperature. For water the solver finds 0.0317 bar at 25 °C and 0.199 bar at 60 °C. The steam table says 0.0317 and 0.199 bar.

### Not favourable does not mean no ΔH

ΔH is the enthalpy of the products minus the enthalpy of the reactants. Both are properties of the substances, so ΔH exists for any balanced reaction, whether it goes by itself or not.

"Not favourable" only means K is smaller than 1: at equilibrium there is more reactant than product. It does not mean nothing reacts. Whatever amount does react gives out, or takes in, ΔH per mole. You also need this ΔH to design the reactor, and it is the ΔH of the reverse reaction with the sign flipped.

Example: at 523 K, CO₂ + 3 H₂ → CH₃OH + H₂O is not favourable (K = 2.2 × 10⁻⁵), and still every mole that reacts releases 57.94 kJ. A methanol plant runs this reaction at 50 bar and has to remove exactly that heat.

## 4. The tabs, one by one

### Start

The first page asks "What do you want to find out?" Each card opens the right tab with a ready example. Use it when you are showing the solver to someone.

### Tab 1: Reaction

**It answers:** how much heat, and which side is favoured?

**You do:** pick a reaction or type one, set the temperature, press Calculate. ΔH°, ΔS° and ΔG° are standard values at 1 bar.

**You read:**

- The headline at the top: "Gives out heat" or "Takes in heat", and "Products favoured" or "Reactants favoured". The second one looks at the sign of ΔG°. It never means that nothing reacts.
- The cards: ΔH° at 298.15 K, and ΔH°, ΔS° and ΔG° at your temperature.
- "What the numbers mean": the same result in sentences.
- The graphs (explained below).
- The step-by-step calculation, if you want to follow the arithmetic.

**The "Pick the stable phase" box.** It is ticked at the start. If you type water, methanol, ethanol, benzene, cyclohexane or toluene without (g) or (l), the solver chooses the phase for you: it finds the boiling point from its own data and uses the liquid below it and the vapour above it, at 1 bar. Example: `CH4 + 2 O2 -> CO2 + 2 H2O` gives H2O(l) and ΔH° = −890.65 kJ/mol at 298.15 K, and H2O(g) at 500 K. The plots then run across the boiling point. The orange ΔH° line has a step there (the latent heat), and the blue ΔG° line only bends. Try `H2 + 1/2 O2 -> H2O`: ΔH° is −283.4 kJ/mol just below 373.2 K and −242.6 kJ/mol just above it.

A phase you type is always kept, because a textbook often wants the other form on purpose. The heat of burning methane to H2O(g) at 25 °C (−802.63 kJ/mol) is the lower heating value, although water is not a vapour at 25 °C and 1 bar. Then a blue box says that the typed phase is not the stable one, and its button "Let the solver choose the phase" takes the typed phase away. If you untick the box, a species typed without a phase is taken as a gas.

**The three graphs of tab 1.** Each has a line under it that says how to read it. In short:

1. **Energy changes versus temperature.** Orange is ΔH° (heat), blue is ΔG° (which side is favoured), green is T·ΔS°. Blue is always orange minus green. Where the blue line crosses zero, the favoured side changes. The dots show your temperature.
2. **Heat-capacity change, ΔCp°.** Cp of the products minus Cp of the reactants. It is the slope of the orange ΔH° line: negative ΔCp° means ΔH° falls as it gets hotter.
3. **Sensible heat of each species.** One bar per substance: the heat it takes up between 298.15 K and your temperature. Added together, the bars are the difference between ΔH° at your temperature and ΔH° at 298.15 K.

The two graphs against temperature share the same temperature axis, so you can follow one temperature from one to the other. On every tab the axes of a graph cover only the range where it has data, so no graph has an empty stretch.

A grey band on a plot means the Cp formula is being used outside the temperature range it was made for. The solver warns you when that happens. The plots start at 298.15 K, and this tab does not accept a lower temperature.

### Tab 2: Pressure and real gas

**It answers:** how different is a real gas from an ideal gas, and what does that do to the heat of reaction?

**You read:**

- The headline: the ideal-gas ΔH, the real-gas ΔH and the difference between them.
- The three steps. They reach the real-gas ΔH by a detour, in the same way as Hess's law. Step 1: take the reactants from real gas to ideal gas, which removes their Hᴿ. Step 2: let them react as ideal gases, which is ΔH° from tab 1. Step 3: take the ideal-gas products to real gas, which adds their Hᴿ. H depends only on where you start and where you end, so the detour gives the same answer as the direct route. Each Hᴿ is in the table at the bottom of the tab. Example, ammonia at 723 K and 200 bar (N₂ + 3 H₂ → 2 NH₃): step 1 = −(1 × 177 + 3 × 325) J = −1.15 kJ; step 2 = −106.50 kJ; step 3 = 2 × (−1949) J = −3.90 kJ. Total: −111.55 kJ/mol.
- The first graph: the ideal gas is the flat zero line, and the orange curve is the residual part, how much the real gas differs from it. It grows with pressure.
- The list of bars at the top: six industrial reactions, sorted by how much pressure matters. Click one to load it.

Example: ammonia synthesis at 723 K. The ideal ΔH is −106.50 kJ/mol at any pressure. At 200 bar the residual part adds −5.05 kJ/mol, so the real gas releases 4.7 % more heat.

**Why does the ideal-gas ΔH not depend on pressure?** An ideal gas has no forces between its molecules, so its internal energy U depends on temperature only. Also PV = RT for one mole. So H = U + PV = U + RT depends on temperature only, and so does the ΔH of a reaction between ideal gases. A real gas is different: its molecules attract and repel each other, so its H changes with pressure. That change is the residual enthalpy Hᴿ.

**How is the residual part calculated?** In four steps, for each gas:

1. Take its critical temperature Tc, critical pressure Pc and acentric factor ω from the textbook's Table B.1, and work out Tr = T/Tc and Pr = P/Pc.
2. Solve the equation of state chosen for that gas (see below) for its compressibility factor Z.
3. Put Z, Tr, Pr and ω into the textbook's formula for Hᴿ/RT that belongs to that equation of state.
4. Add up ν·Hᴿ over the reaction: products count plus, reactants minus.

Example, methanol at 523 K and 50 bar, which uses Soave/Redlich/Kwong: Tr = 1.02, Pr = 0.62, Z = 0.774, Hᴿ/RT = −0.948, so Hᴿ = −0.948 × 8.314 × 523.15 = −4.12 kJ/mol.

**Why does Hᴿ get more negative close to the critical point?** Near the critical point (Tr close to 1) a gas is almost a liquid: the molecules are close together and slow enough for their attraction to hold them. That attraction lowers the enthalpy, and Hᴿ measures exactly how much. Methanol at 523 K has Tr = 1.02, so it is just above its critical temperature, and it is also polar, so it attracts strongly: Hᴿ = −4.12 kJ/mol and Z = 0.774. Hydrogen at the same conditions has Tr = 15.8, so it is far from its critical point: Hᴿ = +0.07 kJ/mol and Z = 1.02, almost ideal.

**Which equation of state does the solver use?** You do not choose it: the solver does, for each gas, because a wrong choice would give a wrong answer without any warning. It has compared the five equations of the course (the virial equation, van der Waals, Redlich/Kwong, Soave/Redlich/Kwong and Peng/Robinson) with measured data. For 24 gases of the database, NIST gives the measured enthalpy at 300 to 1000 K and up to 300 bar, and the measured Hᴿ is H(T, P) − H(T, 0.01 bar), because at 0.01 bar a gas is practically ideal. At each of these 380 points the solver works out Hᴿ with all five equations, and each gas gets the equation with the smallest average difference.

The result: Soave/Redlich/Kwong is closest for 14 gases, Peng/Robinson for 6 and Redlich/Kwong for 4 (methane, CO, hydrogen and oxygen, all small, light molecules). The virial equation and van der Waals are never the closest. A gas that NIST does not cover, such as ethanol, uses Soave/Redlich/Kwong, which is the closest on average over all 380 points (0.137 kJ/mol, against 0.160 for Peng/Robinson). The table at the bottom of tab 2 shows the equation of each gas, and the Validation tab shows the whole comparison.

One reaction can therefore use different equations for different gases. That is fine, because each gas is treated on its own as the pure species at T and P. Each gas keeps its one equation at every temperature and pressure, so its Hᴿ changes smoothly along the graphs.

**Is the chosen equation exact?** No. It is only the closest of the five. For ammonia, Soave/Redlich/Kwong is still 0.18 kJ/mol off on average. For a gas that NIST does not cover, the choice is the best guess from the other gases, not a measured check.

When does it matter?

- **A lot** for cold, dense gases such as methanol, water and ammonia. CO₂ + 3 H₂ → CH₃OH + H₂O at 523 K and 50 bar: 10.6 %.
- **Hardly at all** for hot, light gases. Steam reforming at 1100 K and 30 bar: 0.2 %.
- **Less as the gas gets hotter.** For ammonia at 200 bar the residual part is −11.9 kJ/mol at 500 K and only −3.3 kJ/mol at 900 K.

**The four graphs of tab 2.** Each has a line under it that says how to read it. In short:

1. **Real gas minus ideal gas, against pressure.** The grey dashed line at zero is the ideal gas; it is flat. The orange line is the residual part, Σ ν Hᴿ. Add it to the ideal-gas ΔH to get the real-gas ΔH.
2. **Where the difference comes from.** One bar per substance. The tallest bar is the gas that is furthest from ideal.
3. **Residual part against temperature.** The same gap at your pressure, at other temperatures. It shrinks as the gas gets hotter. It starts at the temperature from which every gas of the reaction has a gas state at your pressure; below that there is nothing to plot.
4. **Residual enthalpy of each pure gas.** A line near zero is an almost ideal gas. A line that falls steeply is a gas close to its critical point.

All four graphs cover exactly the same range of values, in kJ/mol, so you can read a number across from one graph to another. The value of graph 1 at your pressure, the sum of the bars in graph 2 and the dot in graph 3 are the same number.

**"No gas-phase value".** If a substance would be a liquid at your temperature and pressure, there is no gas reaction to calculate. The tab says so in a blue box and offers a pressure, or a temperature, where it works. Example: at 523 K water is a liquid above about 90 bar, so CO₂ hydrogenation at 200 bar has no gas-phase value. This is a limit of the conditions, not an error.

### Tab 3: Combine reactions

**It answers:** can I build one reaction out of others?

This is Hess's law. If you add reactions, their ΔH, ΔS and ΔG values add too. If you reverse a reaction, their signs flip.

Example: (CO₂ + H₂ → CO + H₂O) plus (CO + 2 H₂ → CH₃OH) gives CO₂ + 3 H₂ → CH₃OH + H₂O. At 523 K the two steps are +39.50 and −97.44 kJ, which add up to −57.94 kJ. That is exactly what tab 1 gives for the overall reaction.

### Tab 4: Product slate (extra feature 1)

**It answers:** if I put these gases in a reactor and wait, what comes out?

Tab 1 looks at one reaction at a time. In a real reactor several reactions compete for the same atoms. Here you only say which substances are allowed to exist. The solver then finds the mixture with the lowest total Gibbs energy, like a ball rolling to the lowest point of a valley. The only rule is that atoms are not created or destroyed.

**You do:** drag the temperature, pressure and feed-ratio sliders. Click a product to switch it off. Or press the numbered "Try this" buttons, which do the switching for you.

**Real gases.** The gases of tab 4 are real gases, each with the equation of state chosen for it (see tab 2). If a gas would be a liquid on its own at that temperature and pressure (water at 523 K above about 90 bar), its equation has no gas state there. In the mixture it is diluted and stays a vapour, so for that point the solver describes it with the virial equation, which has a gas state at any pressure, and says so in a note.

**What a switch means:** off means the catalyst cannot make that product. So a switch imitates a selective catalyst.

**Why some switches are faded:** a switch can only change the result if its product holds a real share of the atoms. If a product holds nothing, there is nothing to take away. The solver checks this for every switch, each time you move something:

- A normal switch shows the share its product holds, for example "74.9 % of C". You can click it.
- A **faded** switch says "no effect now". Blocking it would change nothing, so it cannot be clicked. It wakes up when it starts to matter.
- A **dashed** switch is either fed to the reactor, or "needed": without it nothing could react at all, because the atoms would have nowhere to go.

Example: CO₂ + 3 H₂ at 523 K and 50 bar. Press the three "Try this" buttons in turn.

1. **Everything allowed.** 74.9 % of the carbon ends up as methane. Methanol and CO hold 0.0 %, so their switches are faded. Only the methane switch can be clicked.
2. **Methane off.** Now 71.9 % of the carbon stays as CO₂, 20.6 % goes to methanol and 7.5 % to CO. The methanol and CO switches have woken up.
3. **Methane and CO off.** Only methanol can form, and it takes 24.5 % of the carbon. Methanol is now "needed", because it is the only product left.

Water is "needed" in all three steps. The oxygen atoms of CO₂ have to go somewhere, and water is the only place.

What this teaches: thermodynamics prefers methane. A methanol plant works because its catalyst does not make methane.

If you want to allow or block any substance freely, open "Build your own system" under the switches.

### Tab 5: Bomb calorimeter (extra feature 2)

**It answers:** how much heat does a fuel give, and which fuel is an unknown sample?

This is our bomb calorimeter lab on screen. A sample burns in a closed steel vessel, the bomb, which sits in water. The vessel cannot change its volume, so no work is done and the heat released is ΔU, not ΔH. The two are linked by:

    ΔH = ΔU + Δn·R·T

where Δn is the change in the number of gas molecules.

**You do:**

1. Calibrate the calorimeter with benzoic acid. The numbers of the lab handout are filled in: 1.1942 g, 6319 cal/g, a rise of 2.48 °C and 41 cal for the thread and wire. They give a calorimeter constant of (1.1942 × 6319 + 41) / 2.48 = 3059.3 cal/°C.
2. Then either burn a known fuel to see its temperature rise, or type a measured rise to find the fuel that fits best.

Example: 1 g of ethanol. The solver writes the complete combustion, C₂H₅OH(l) + 3 O₂ → 2 CO₂ + 3 H₂O(l), and gets ΔH = −1366.8 kJ/mol from the heats of formation. The gas moles fall by 1, so ΔU = ΔH − Δn·R·T = −1364.3 kJ/mol. That is a calorific value of 29.62 MJ/kg and a temperature rise of 2.31 °C.

Working backwards: if 1 g of an unknown sample raises the temperature by 2.30 °C, its calorific value is 29.44 MJ/kg. The closest fuel is ethanol, only 0.6 % away; the next one, graphite, is 11 % away.

Two more words from this tab:

- **HHV** (higher heating value): the water formed ends up as liquid. For ethanol 29.67 MJ/kg.
- **LHV** (lower heating value): the water stays as vapour. It is smaller, 26.80 MJ/kg for ethanol, because the heat of condensing the water is not collected.

### Tab 6: Species data

The full table of the 57 substances, with the source of every number. There is also a small calculator for the sensible heat of one substance.

### Tab 7: Validation

This is the proof that the numbers are right. It has three parts:

- **67 reference values** from textbook examples, course slides, the lab handout and the NIST tables. The solver recalculates each one while you watch. All 67 pass. Ten of them are about phase change: six boiling points, the vapour pressure and latent heat of water, and the temperature at which the water vapour of a flue gas becomes saturated.
- **Five stress tests** from the assignment (see section 6).
- **Comparison with published research** values.

## 5. Why you can trust the answers

- **The data are traceable.** From 298.15 K upwards, 54 of the 57 substances use only the textbook tables. The other three come from the NIST database and are labelled. Below 298.15 K, where the textbook has no data, the heat capacities come from NIST tables, and the solver says so whenever it uses them.
- **It checks itself.** Every result is calculated a second time by a different route. The two must agree. These checks run in the automated tests every time the code changes.
- **It has more than 200 automated tests.** They run every time the code changes.
- **It refuses bad input.** An unbalanced reaction gets no answer at all.
- **It warns you.** If a formula is used outside its valid temperature range, you see a warning.

## 6. Mistakes the AI made, and how they were caught

The assignment asks for mistakes of the AI-built solver that were found and fixed. These are the main ones, in plain words.

| What went wrong | Why it was wrong | How it is fixed |
|---|---|---|
| Liquid water was treated as a gas at high pressure | It predicted 48 % conversion, which is far too high | The solver notices when a gas would really be a liquid and refuses to give a gas value |
| An old data value for ammonia | The AI remembered a number from an older edition of the book | Every number was compared with the printed tables |
| Two rounded constants in a formula | Two results that should agree differed slightly | The exact constants are used |
| "Practically no reaction" for ammonia | True at 1 bar, but at 200 bar 43 % reacts | The text now speaks of 1 bar only, and tab 4 shows the mixture at any pressure |
| The calorimeter named a gas as the unknown sample | A gas cannot be weighed into a crucible | Only liquids and solids are compared |
| "Standard state" was explained as 298.15 K and 1 bar | Standard state fixes only the pressure (1 bar). 298.15 K is just where the tables list the data | The guide and the page now keep the two apart |
| Below 298 K the textbook Cp formulas were simply stretched | They are valid from 298 K only. For CO₂ at 200 K the stretched formula is 29 % too low | NIST table values are used from 200 K to 298.15 K |
| The headline said "Not favourable" | It read as if the reaction could not happen, so its ΔH looked meaningless | It now says "Reactants favoured" and adds that some product still forms |
| Tab 2 showed a red error for CO₂ hydrogenation | The pressure was still 200 bar from the ammonia example. Water is a liquid there, so there is no gas value | The example opens at its own conditions (50 bar), and a blue box offers a pressure that works |
| After tab 2 was narrowed down to the heat of reaction, no tab said how pressure changes favourability | The assignment asks for favourability at a given pressure and temperature | Tab 4 has a pressure slider and shows the mixture that forms at that pressure |
| Every substance stayed in the phase that was typed | Liquid water stayed liquid at 500 K | The solver finds the boiling point from its own data, and tab 1 can pick the stable phase |

The five stress tests of the assignment:

1. **Unbalanced reaction.** CH₄ + O₂ → CO₂ + H₂O is rejected, and CH₄ + 2 O₂ → CO₂ + 2 H₂O is offered.
2. **Shortcut on Cp.** The Validation tab runs this for every predefined reaction at 1000 K. For the 40 reactions whose Cp data reach 1000 K, a constant ΔCp puts ΔH off by 9.0 kJ/mol on average and by up to 31.5 kJ/mol (benzene hydrogenation); ignoring ΔCp puts it off by 7.5 kJ/mol on average and by up to 26.0 kJ/mol (CO₂ methanation). The other 5 contain a liquid or a solid whose Cp data stop below 1000 K, so they get no numbers. Example, steam reforming: the proper Cp gives ΔH = 225.3 kJ/mol, a constant Cp gives 238.8, and ignoring Cp gives 205.8.
3. **Liquid or vapour water.** Burning methane gives −890.65 kJ/mol with liquid water and −802.63 with vapour. The gap is the heat needed to boil 2 moles of water. Typed as just H2O, the solver chooses liquid water at 25 °C by itself.
4. **Formula out of range.** The solver warns you, and shades that part of the plots. This was checked 1 K inside and 1 K outside both ends of the range for all 45 predefined reactions: a warning every time outside, never inside.
5. **Published values.** The solver agrees with research papers within 0.5 kJ/mol.

## 7. How it is built

- The calculations are written in **Python**.
- The web page runs that same Python **inside your browser**, using a tool called Pyodide. Nothing is sent to a server.
- The page itself (HTML and JavaScript) only draws forms, tables and plots. It does no thermodynamics.

This is why the first visit takes about ten seconds: the browser downloads Python once.

## 8. Words you will meet

| Word or symbol | Plain meaning |
|---|---|
| ΔH | Heat given out (negative) or taken in (positive) by the reaction |
| ΔS | Change in disorder; positive when more gas is made |
| ΔG | Tells which side is favoured; negative means the products |
| K | Where the reaction stops; bigger than 1 means mostly products |
| ° (as in ΔH°) | Standard state: pure substance at 1 bar, at whatever temperature you choose |
| Reference temperature | 298.15 K, where the tables list the heats of formation |
| Cp | Heat needed to warm a substance by 1 K |
| Sensible heat | Heat that changes temperature without any reaction |
| Exothermic / endothermic | Gives out heat / takes in heat |
| Conversion | The fraction of a reactant that has reacted |
| Stoichiometric | Exactly the amounts the balanced reaction asks for |
| Residual property, Hᴿ | Real-gas value minus ideal-gas value |
| Equation of state | A formula linking pressure, volume and temperature of a gas |
| Hess's law | Adding reactions adds their ΔH |
| Lowest total Gibbs energy | How tab 4 finds the mixture that forms: of all mixtures the atoms allow, the one whose Gibbs energy is lowest |
| HHV / LHV | Heating value with liquid water / with water vapour |
| Latent heat | Heat needed to turn a liquid into vapour without changing its temperature |
| Vapour pressure | The pressure at which a liquid and its vapour are in balance at a given temperature |
| Saturated | A gas that holds as much water vapour as it can; cooled further, it drops liquid water |
| ΔU | Heat released at constant volume, as in a bomb calorimeter |

## 9. Check yourself

Try to answer before you read the answer.

1. **A reaction has ΔH = −50 kJ/mol. Does it give out or take in heat?** It gives out heat. It is exothermic.
2. **A reaction turns 4 gas molecules into 2. Is ΔS positive or negative?** Negative. There is less gas, so less disorder.
3. **Can an exothermic reaction be unfavourable?** Yes. If ΔS is negative, the −T·ΔS term is positive and grows with temperature. Methanol from CO₂ at 523 K is an example.
4. **K = 0.00002. Mostly products or mostly reactants?** Mostly reactants.
5. **Why does pressure help ammonia synthesis?** The reaction reduces the number of gas molecules from 4 to 2. Higher pressure favours the side with fewer molecules.
6. **Does "standard state" mean 298.15 K?** No. It fixes the pressure at 1 bar. The temperature is whatever you choose. 298.15 K is only the temperature at which the tables list the heats of formation; other temperatures are reached with Cp.
7. **Why does a bomb calorimeter measure ΔU and not ΔH?** Its volume is fixed, so no work is done. Heat at constant volume equals ΔU.
8. **Why is LHV smaller than HHV?** With LHV the water leaves as vapour, so the heat of condensing it is not collected.
9. **In tab 4, why does switching methane off change the answer?** Methane is the most stable product. Remove it, and the atoms settle into the next best mixture, which contains methanol.
10. **What do the consistency checks prove?** That two different ways of calculating the same quantity agree. A wrong sign or unit would break it.
11. **Does a favourable ΔG mean the reaction is fast?** No. Thermodynamics says where a reaction can end up, not how quickly. That is why catalysts are needed.
12. **A reaction is not favourable. Why does it still have a ΔH?** ΔH is the enthalpy of the products minus that of the reactants, so it exists for any balanced reaction. "Not favourable" only means K is below 1. Some product still forms, and each mole that reacts exchanges ΔH.
13. **Where do the heat capacities below 298.15 K come from?** From NIST tables, between 200 K and 298.15 K. The textbook formulas start at 298 K and are not used below it.
14. **In tab 4, why can the methanol switch not be clicked while methane is allowed?** Methanol holds 0.0 % of the carbon then, so blocking it would change nothing. Switch methane off and methanol holds 20.6 %; now its switch matters.
15. **A reaction is favoured at 50 bar but not at 1 bar. Did K change?** No. K depends on temperature only. Pressure changes how far the reaction goes when the number of gas molecules changes.
16. **Why does ΔH° jump at a boiling point while ΔG° does not?** Liquid and vapour have different enthalpies; the difference is the latent heat. But at the boiling point they have the same Gibbs energy, so ΔG° and K pass through without a jump.
17. **Water is in a gas mixture at 80 °C and 1 bar. Is it a liquid?** Only if its partial pressure reaches its vapour pressure, which is 0.47 bar at 80 °C. Below that it stays a vapour, although 80 °C is below the boiling point.
18. **Is the K of this solver Kp or Kc?** Kp: it is written with partial pressures in bar. It changes with temperature only; pressure changes the conversion, not Kp.
19. **Why does the ideal-gas ΔH not change with pressure?** For an ideal gas U depends on T only and PV = RT, so H = U + RT depends on T only.
20. **Who chooses the equation of state, and how?** The solver, for each gas: the one of the five equations whose Hᴿ is closest to measured NIST data for that gas. A gas without measured data uses Soave/Redlich/Kwong, the closest over all 24 measured gases.

## 10. A five-minute tour

1. Open the **Start** page and click "Try to break it". The unbalanced reaction is rejected.
2. Click "Heat, entropy and Gibbs energy". Point at the headline, the four cards and the plot of ΔG against temperature.
3. Click "What does pressure change?" Show the ideal gas next to the real gas: −106.50 against −111.55 kJ/mol at 200 bar, and the equation each gas uses in the table at the bottom. Then click "CO₂ hydrogenation to methanol" in the list of bars: 10.6 %.
4. Click "What actually forms?" Press the three "Try this" buttons: everything allowed, methane off, methane and CO off. Point at the faded switches and say why they are faded. Then drag the temperature slider.
5. Click "Bomb calorimeter" and press Ignite: 1 g of ethanol raises the temperature by 2.31 °C. Then click "Identify an unknown sample" and press Identify.
6. Finish on **Validation**: 67 of 67 reference values reproduced.
