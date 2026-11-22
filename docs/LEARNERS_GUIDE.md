# A beginner's guide to the solver

This guide explains the Thermodynamic Reaction Energy Solver in plain words. You do not need to read it in order. If you only have ten minutes, read sections 1, 2 and 4.

## 1. What the solver does

You give it a chemical reaction, a temperature and a pressure. It tells you four things:

- **How much heat** the reaction gives out or takes in.
- **Whether the reaction can go** at that temperature.
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

ΔG combines the two ideas above into one number that decides whether a reaction can go:

    ΔG = ΔH − T·ΔS

- **Negative ΔG**: the reaction can go forward.
- **Positive ΔG**: it would rather go backward.

Notice the T in the formula. The same reaction can be favourable at one temperature and unfavourable at another.

Example at 523 K: ΔG = −57.94 − 523.15 × (−0.19976) = +46.56 kJ/mol. The reaction gives out heat, but the loss of entropy wins, so it is not favourable at this temperature.

### Equilibrium constant, K

A reaction does not always go all the way. It stops at a balance point called equilibrium. K tells you where that point is:

    ln K = −ΔG / (R·T)

- **K much bigger than 1**: mostly products.
- **K much smaller than 1**: mostly reactants.
- **K near 1**: a mixture of both.

Example: for the reaction above at 523 K, K = 2.2 × 10⁻⁵. Almost nothing reacts at 1 bar (0.6 % conversion).

### Real gases and residual enthalpy, Hᴿ

At low pressure, gas molecules are far apart and ignore each other. That is an ideal gas, and its enthalpy does not depend on pressure.

At high pressure the molecules are close and attract each other. The gas is then a **real gas**. The difference between the real value and the ideal value is called the **residual** enthalpy, Hᴿ. The solver gets it from an equation of state such as Peng/Robinson.

So at high pressure: ΔH(real) = ΔH(ideal) + the residual part.

## 3. Why everything starts at 298.15 K

The textbook lists the heat of formation of each substance at one temperature only: 298.15 K (25 °C), at 1 bar. That is the **standard state**. The small ° in ΔH° means "standard state".

To get ΔH at another temperature, the solver walks a three-step path:

1. Take the reactants from your temperature to 298.15 K.
2. Let them react at 298.15 K, where the data are known.
3. Take the products back to your temperature.

Steps 1 and 3 are sensible heat, calculated from Cp. The answer does not depend on the path, because enthalpy only depends on where you start and where you end.

Example from the textbook: CO + 2 H₂ → CH₃OH has ΔH° = −90,135 J at 298.15 K and −103,566 J at 800 °C. The solver gives the same numbers.

## 4. The tabs, one by one

### Start

The first page asks "What do you want to find out?" Each card opens the right tab with a ready example. Use it when you are showing the solver to someone.

### Tab 1: Reaction

**It answers:** how much heat, and can the reaction go?

**You do:** pick a reaction or type one, set the temperature, press Calculate.

**You read:**

- The headline at the top: "Gives out heat" or "Takes in heat", and "Favourable" or "Not favourable".
- The cards: ΔH, ΔS, ΔG and K at your temperature.
- "What the numbers mean": the same result in sentences.
- The plots: how ΔH, ΔG and K change with temperature.
- The step-by-step calculation, if you want to follow the arithmetic.

A grey band on a plot means the Cp formula is being used outside the temperature range it was made for. The solver warns you when that happens.

### Tab 2: Pressure and real gas

**It answers:** what does pressure change?

**You read:** the ideal-gas ΔH, the residual part, and their sum.

Example: ammonia synthesis at 723 K. The ideal ΔH is −106.50 kJ/mol at any pressure. At 200 bar the residual part adds −5.16 kJ/mol. The conversion at equilibrium rises from 39.8 % to 42.8 %.

Why pressure helps here: N₂ + 3 H₂ → 2 NH₃ turns 4 gas molecules into 2. Squeezing the gas pushes the reaction towards the side with fewer molecules.

### Tab 3: Combine reactions

**It answers:** can I build one reaction out of others?

This is Hess's law. If you add reactions, their ΔH values add too. If you reverse a reaction, the sign of ΔH flips.

Example: (CO₂ + H₂ → CO + H₂O) plus (CO + 2 H₂ → CH₃OH) gives CO₂ + 3 H₂ → CH₃OH + H₂O. At 523 K the two steps are +39.50 and −97.44 kJ, which add up to −57.94 kJ. That is exactly what tab 1 gives for the overall reaction.

### Tab 4: Product slate (extra feature 1)

**It answers:** if I put these gases in a reactor and wait, what comes out?

Tab 1 looks at one reaction at a time. In a real reactor several reactions compete for the same atoms. Here you only say which substances are allowed to exist. The solver then finds the mixture with the lowest total Gibbs energy, like a ball rolling to the lowest point of a valley. The only rule is that atoms are not created or destroyed.

**You do:** drag the temperature, pressure and feed-ratio sliders. Click a product to switch it off.

Example: CO₂ + 3 H₂ at 523 K and 50 bar.

- With methane allowed, 74.8 % of the carbon ends up as methane. Almost no methanol forms.
- With methane switched off, 25.2 % of the CO₂ reacts, and most of that becomes methanol.

What this teaches: thermodynamics prefers methane. A methanol plant works because its catalyst does not make methane. Switching a product off is how you imitate such a catalyst.

The "solid carbon" card tells you whether soot (coke) can form. A carbon activity above 1 means it can.

### Tab 5: Heat lab (extra feature 2)

**Reactor and flame** answers two questions: how hot does it get, and how much heat is needed?

It is an energy balance: heat added = enthalpy out − enthalpy in. It uses the same three-step path as section 3:

1. Feed from its inlet temperature to 298.15 K.
2. Reaction at 298.15 K.
3. Products from 298.15 K to the outlet temperature.

If no heat is added or removed, the three steps must add up to zero. The solver finds the outlet temperature that makes this true. For a burner, that is the flame temperature.

Examples:

- Methane with 20 % excess air, entering at 25 °C: the flame is at 2066 K.
- With no excess air it is 2311 K. With 100 % excess air it is 1486 K. Extra air cools the flame, because the extra air has to be heated too.
- To stay below 1500 K you need 97 % excess air.
- A steam reformer fed at 600 K with products at 1300 K needs 328 kJ per mole of methane (−34.4 + 200.5 + 161.9 kJ for the three steps).

**Bomb calorimeter** is the lab experiment on screen. A sample burns in a closed steel vessel. The vessel cannot change its volume, so the heat released is ΔU, not ΔH. The two are linked by:

    ΔH = ΔU + Δn·R·T

where Δn is the change in the number of gas molecules.

Example: 1 g of ethanol, with the calorimeter constant from the lab handout (3059 cal/°C), gives a temperature rise of 2.31 °C and a calorific value of 29.62 MJ/kg.

Two more words from this tab:

- **HHV** (higher heating value): the water formed ends up as liquid.
- **LHV** (lower heating value): the water stays as vapour. It is smaller, because the heat of condensing the water is not collected.

### Tab 6: Species data

The full table of the 57 substances, with the source of every number. There is also a small calculator for the sensible heat of one substance.

### Tab 7: Validation

This is the proof that the numbers are right. It has three parts:

- **51 reference values** from textbook examples, course slides and the lab handout. The solver recalculates each one while you watch. All 51 pass.
- **Five stress tests** from the assignment (see section 6).
- **Comparison with published research** values.

## 5. Why you can trust the answers

- **The data are traceable.** 54 of the 57 substances use only the textbook tables. The other three come from the NIST database and are labelled.
- **It checks itself.** Every result is calculated a second time by a different route. The two must agree. This appears as "Consistency audit" under each result.
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
| "Practically no reaction" for ammonia | True at 1 bar, but at 200 bar 43 % reacts | The text now gives a separate verdict at your pressure |
| The calorimeter named a gas as the unknown sample | A gas cannot be weighed into a crucible | Only liquids and solids are compared |
| The "excess air for a temperature limit" search gave a wrong value | It never checked its own answer | It now solves again with its answer before showing it |

The five stress tests of the assignment:

1. **Unbalanced reaction.** CH₄ + O₂ → CO₂ + H₂O is rejected, and CH₄ + 2 O₂ → CO₂ + 2 H₂O is offered.
2. **Shortcut on Cp.** For steam reforming at 1000 K, the proper Cp gives ΔH = 225.3 kJ/mol. A constant Cp gives 238.8, and ignoring Cp gives 205.8. K changes from 25.8 to 50.3 or 2.8.
3. **Liquid or vapour water.** Burning methane gives −890.65 kJ/mol with liquid water and −802.63 with vapour. The gap is the heat needed to boil 2 moles of water.
4. **Formula out of range.** The solver warns you.
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
| ΔG | Decides if the reaction can go; negative means yes |
| K | Where the reaction stops; bigger than 1 means mostly products |
| ° (as in ΔH°) | Standard state: pure substance at 1 bar |
| Cp | Heat needed to warm a substance by 1 K |
| Sensible heat | Heat that changes temperature without any reaction |
| Exothermic / endothermic | Gives out heat / takes in heat |
| Conversion | The fraction of a reactant that has reacted |
| Stoichiometric | Exactly the amounts the balanced reaction asks for |
| Excess air | Air beyond what the reaction needs |
| Adiabatic | No heat goes in or out through the walls |
| Residual property, Hᴿ | Real-gas value minus ideal-gas value |
| Fugacity coefficient, φ | How far a real gas is from ideal; 1 for an ideal gas |
| Equation of state | A formula linking pressure, volume and temperature of a gas |
| Hess's law | Adding reactions adds their ΔH |
| Gibbs minimisation | Finding the mixture with the lowest total Gibbs energy |
| Carbon activity | Above 1 means solid carbon (coke) can form |
| HHV / LHV | Heating value with liquid water / with water vapour |
| ΔU | Heat released at constant volume, as in a bomb calorimeter |

## 9. Check yourself

Try to answer before you read the answer.

1. **A reaction has ΔH = −50 kJ/mol. Does it give out or take in heat?** It gives out heat. It is exothermic.
2. **A reaction turns 4 gas molecules into 2. Is ΔS positive or negative?** Negative. There is less gas, so less disorder.
3. **Can an exothermic reaction be unfavourable?** Yes. If ΔS is negative, the −T·ΔS term is positive and grows with temperature. Methanol from CO₂ at 523 K is an example.
4. **K = 0.00002. Mostly products or mostly reactants?** Mostly reactants.
5. **Why does pressure help ammonia synthesis?** The reaction reduces the number of gas molecules from 4 to 2. Higher pressure favours the side with fewer molecules.
6. **Why is the heat of formation given at 298.15 K only?** That is the temperature the tables use. Other temperatures are reached with Cp.
7. **Why does extra air cool a flame?** The extra air does not react. It only has to be heated, so the same heat is shared by more gas.
8. **Why does a bomb calorimeter measure ΔU and not ΔH?** Its volume is fixed, so no work is done. Heat at constant volume equals ΔU.
9. **Why is LHV smaller than HHV?** With LHV the water leaves as vapour, so the heat of condensing it is not collected.
10. **In tab 4, why does switching methane off change the answer?** Methane is the most stable product. Remove it, and the atoms settle into the next best mixture, which contains methanol.
11. **What does the consistency audit prove?** That two different ways of calculating the same quantity agree. A wrong sign or unit would break it.
12. **Does a favourable ΔG mean the reaction is fast?** No. Thermodynamics says where a reaction can end up, not how quickly. That is why catalysts are needed.

## 10. A five-minute tour

1. Open the **Start** page and click "Try to break it". The unbalanced reaction is rejected.
2. Click "Heat, entropy and Gibbs energy". Point at the headline, the four cards and the plot of ΔG against temperature.
3. Click "What does pressure change?" Show that the residual part is −5.16 kJ/mol at 200 bar.
4. Click "What actually forms?" Switch methane off and on. Drag the temperature slider.
5. Click "How hot does it get?" Drag the excess-air slider and watch the flame cool.
6. Click "Bomb calorimeter" and press Ignite.
7. Finish on **Validation**: 51 of 51 reference values reproduced.
