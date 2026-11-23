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

At high pressure the molecules are close and attract each other. The gas is then a **real gas**. The difference between the real value and the ideal value is called the **residual** enthalpy, Hᴿ. The solver gets it from an equation of state such as Peng/Robinson.

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

The textbook's Cp formulas start at 298 K. They must not be stretched downwards: for CO₂ at 200 K the formula gives a Cp that is 29 % too low.

So from 200 K to 298.15 K the solver uses Cp values from NIST tables instead (the NIST-JANAF tables and the NIST Chemistry WebBook). This covers every gas of the textbook and six solids. Above 298.15 K nothing changes.

Example: CO₂ + 3 H₂ → CH₃OH + H₂O has ΔH° = −46.77 kJ/mol at 250 K. There ΔG° = −4.51 kJ/mol, so the reaction is favourable when it is cold. ΔG° changes sign at 276 K.

One thing to remember: at 250 K and 1 bar, real methanol and water are not gases. The solver still treats them as ideal gases, because that is what the standard state of a gas means. It tells you so in a note.

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

**You do:** pick a reaction or type one, set the temperature, press Calculate. The pressure box is only for the equilibrium conversion; ΔH°, ΔS°, ΔG° and K are standard values, and K is Kp.

**You read:**

- The headline at the top: "Gives out heat" or "Takes in heat", and "Products favoured" or "Reactants favoured". The second one compares K with 1. It never means that nothing reacts.
- The cards: ΔH, ΔS, ΔG and K at your temperature, and how much reacts at your pressure.
- "What the numbers mean": the same result in sentences.
- The graphs (explained below).
- The step-by-step calculation, if you want to follow the arithmetic.

**Favourable at which pressure?** K only depends on temperature. But how far a reaction goes also depends on pressure. Example: CO₂ + 3 H₂ → CH₃OH + H₂O at 523 K converts 0.6 % at 1 bar and 21.3 % at 50 bar. Four gas molecules become two, so squeezing the gas helps.

**The "Pick the stable phase" box.** Normally the solver uses the phase you type. H2O(l) stays a liquid at any temperature, even at 500 K, where it only gets a warning. Tick the box and the solver chooses for you: liquid below the boiling point, vapour above it. The plots then run across the boiling point. The orange ΔH° line has a step there (the latent heat), and the blue ΔG° line only bends. Try `H2 + 1/2 O2 -> H2O(l)`: ΔH° is −283.4 kJ/mol just below 373.2 K and −242.6 kJ/mol just above it.

The box is off at the start, because a textbook often wants the other form on purpose. The heat of burning methane to H2O(g) at 25 °C is the lower heating value, although water is not a vapour at 25 °C and 1 bar.

One more point. Below its boiling point a product is not automatically a liquid. In a gas mixture it stays a vapour as long as its partial pressure is below its vapour pressure. The "equilibrium conversion" card works this way: a product leaves as liquid only once the gas is saturated with it, and the card says when that happens.

**The five graphs of tab 1.** Each has a line under it that says how to read it. In short:

1. **Energy changes versus temperature.** Orange is ΔH° (heat), blue is ΔG° (which side is favoured), green is T·ΔS°. Blue is always orange minus green. Where the blue line crosses zero, K = 1. The dots show your temperature.
2. **Equilibrium constant Kp.** The higher the line, the more the products are favoured. Above the dotted line Kp is bigger than 1.
3. **Equilibrium conversion.** How much has reacted when the reaction comes to rest. Grey dashed is at 1 bar, blue is at your pressure.
4. **Heat-capacity change, ΔCp°.** Cp of the products minus Cp of the reactants. It is the slope of the orange ΔH° line: negative ΔCp° means ΔH° falls as it gets hotter.
5. **Sensible heat of each species.** One bar per substance: the heat it takes up between 298.15 K and your temperature. Added together, the bars are the difference between ΔH° at your temperature and ΔH° at 298.15 K.

The four graphs against temperature share the same temperature axis, so you can follow one temperature from graph to graph.

A grey band on a plot means the Cp formula is being used outside the temperature range it was made for. The solver warns you when that happens. For gases the range now starts at 200 K, so the plots start there too.

### Tab 2: Pressure and real gas

**It answers:** how different is a real gas from an ideal gas, and what does that do to the heat of reaction?

**You read:**

- The headline: the ideal-gas ΔH, the real-gas ΔH and the difference between them.
- The three steps: take the real reactants to the ideal-gas state, let them react as ideal gases, take the ideal-gas products to the real state. The three add up to the real-gas ΔH.
- The first plot: the ideal gas is a flat line, the real gas is a curve. The shaded gap between them is the residual part. It grows with pressure.
- The list of bars at the top: six industrial reactions, sorted by how much pressure matters. Click one to load it.

Example: ammonia synthesis at 723 K. The ideal ΔH is −106.50 kJ/mol at any pressure. At 200 bar the residual part adds −5.16 kJ/mol, so the real gas releases 4.8 % more heat.

**Why does the ideal-gas ΔH not depend on pressure?** An ideal gas has no forces between its molecules, so its internal energy U depends on temperature only. Also PV = RT for one mole. So H = U + PV = U + RT depends on temperature only, and so does the ΔH of a reaction between ideal gases. A real gas is different: its molecules attract and repel each other, so its H changes with pressure. That change is the residual enthalpy Hᴿ.

**Why Peng/Robinson?** The tab starts on Peng/Robinson, but you can pick any of the five models. Peng/Robinson and Soave/Redlich/Kwong use three properties of each gas: the critical temperature, the critical pressure and the acentric factor ω. van der Waals and Redlich/Kwong use only the first two, so they treat every molecule as if it had the same shape. The virial equation is only meant for low to moderate pressure. For the six industrial cases of the tab, Peng/Robinson and Soave/Redlich/Kwong agree within 0.05 kJ/mol, while van der Waals and Redlich/Kwong can be off by up to 3.6 kJ/mol (methanol synthesis at 80 bar: −8.63 with Peng/Robinson, −5.05 with van der Waals). The table "Same state, every model" under each result shows this.

When does it matter?

- **A lot** for cold, dense gases such as methanol, water and ammonia. CO₂ + 3 H₂ → CH₃OH + H₂O at 523 K and 50 bar: 10.6 %.
- **Hardly at all** for hot, light gases. Steam reforming at 1100 K and 30 bar: 0.2 %.
- **Less as the gas gets hotter.** For ammonia at 200 bar the residual part is −11.8 kJ/mol at 500 K and only −3.4 kJ/mol at 900 K.

**The four graphs of tab 2.** Each has a line under it that says how to read it. In short:

1. **Heat of reaction against pressure.** The grey dashed line is the ideal gas; it is flat. The orange line is the real gas. The shaded gap between them is the residual part.
2. **Where the difference comes from.** One bar per substance. The tallest bar is the gas that is furthest from ideal.
3. **Residual part against temperature.** The same gap at your pressure, at other temperatures. It shrinks as the gas gets hotter.
4. **Residual enthalpy of each pure gas.** A line near zero is an almost ideal gas. A line that falls steeply is a gas close to its critical point.

All four graphs use the same kJ/mol scale, so a height in one graph means the same number of kJ in the others. The first graph is only moved up or down, so that its ideal-gas line sits where the other graphs have zero. The gap in graph 1 at your pressure, the sum of the bars in graph 2 and the dot in graph 3 are the same number.

**"No gas-phase value".** If a substance would be a liquid at your temperature and pressure, there is no gas reaction to calculate. The tab says so in a blue box and offers a pressure, or a temperature, where it works. Example: at 523 K water is a liquid above about 90 bar, so CO₂ hydrogenation at 200 bar has no gas-phase value. This is a limit of the conditions, not an error.

This tab is about the heat of reaction only. How far a reaction goes at high pressure is shown on tab 1 (the pressure box) and on tab 4 (the pressure slider).

### Tab 3: Combine reactions

**It answers:** can I build one reaction out of others?

This is Hess's law. If you add reactions, their ΔH values add too. If you reverse a reaction, the sign of ΔH flips.

Example: (CO₂ + H₂ → CO + H₂O) plus (CO + 2 H₂ → CH₃OH) gives CO₂ + 3 H₂ → CH₃OH + H₂O. At 523 K the two steps are +39.50 and −97.44 kJ, which add up to −57.94 kJ. That is exactly what tab 1 gives for the overall reaction.

### Tab 4: Product slate (extra feature 1)

**It answers:** if I put these gases in a reactor and wait, what comes out?

Tab 1 looks at one reaction at a time. In a real reactor several reactions compete for the same atoms. Here you only say which substances are allowed to exist. The solver then finds the mixture with the lowest total Gibbs energy, like a ball rolling to the lowest point of a valley. The only rule is that atoms are not created or destroyed.

**You do:** drag the temperature, pressure and feed-ratio sliders. Click a product to switch it off. Or press the numbered "Try this" buttons, which do the switching for you.

**What a switch means:** off means the catalyst cannot make that product. So a switch imitates a selective catalyst.

**Why some switches are faded:** a switch can only change the result if its product holds a real share of the atoms. If a product holds nothing, there is nothing to take away. The solver checks this for every switch, each time you move something:

- A normal switch shows the share its product holds, for example "74.8 % of C". You can click it.
- A **faded** switch says "no effect now". Blocking it would change nothing, so it cannot be clicked. It wakes up when it starts to matter.
- A **dashed** switch is either fed to the reactor, or "needed": without it nothing could react at all, because the atoms would have nowhere to go.

Example: CO₂ + 3 H₂ at 523 K and 50 bar. Press the three "Try this" buttons in turn.

1. **Everything allowed.** 74.8 % of the carbon ends up as methane. Methanol and CO hold 0.0 %, so their switches are faded. Only the methane switch can be clicked.
2. **Methane off.** Only 25.2 % of the CO₂ reacts now: 17.3 % to methanol and 7.9 % to CO. The methanol and CO switches have woken up.
3. **Methane and CO off.** Only methanol can form: 21.3 % of the CO₂ reacts. Methanol is now "needed", because it is the only product left.

Water is "needed" in all three steps. The oxygen atoms of CO₂ have to go somewhere, and water is the only place.

What this teaches: thermodynamics prefers methane. A methanol plant works because its catalyst does not make methane.

If you want to allow or block any substance freely, open "Build your own system" under the switches.

The "solid carbon" card tells you whether solid carbon (soot) can form. It can form when making it would lower the total Gibbs energy; otherwise it cannot.

### Tab 5: Heat lab (extra feature 2)

**Reactor and flame** answers two questions: how hot does it get, and how much heat is needed?

It is an energy balance: heat added = enthalpy out − enthalpy in. It uses the same three-step path as section 3:

1. Feed from its inlet temperature to 298.15 K.
2. Reaction at 298.15 K.
3. Products from 298.15 K to the outlet temperature.

If no heat is added or removed, the three steps must add up to zero. The solver finds the outlet temperature that makes this true. For a burner, that is the flame temperature.

Examples:

- Methane with 20 % excess air, entering at 25 °C: the flame is at 2069 K.
- The textbook's answer for this example is 2066 K. The textbook uses its Cp formula 66 K beyond its 2000 K limit; the solver uses NIST data up there, which gives 3 K more. A note on the page shows both numbers.
- With no excess air it is 2326 K. With 100 % excess air it is 1486 K. Extra air cools the flame, because the extra air has to be heated too.
- A real flame above 2000 K is a little cooler than these numbers, because the hot CO₂ and H₂O partly break apart. The page says so in a note.
- To stay below 1500 K you need 97 % excess air.
- A steam reformer fed at 600 K with products at 1300 K needs 328 kJ per mole of methane (−34.4 + 200.5 + 161.9 kJ for the three steps).

**When the outlet is cool, the water condenses.** A gas can carry water vapour only up to the vapour pressure. The flue gas of the methane burner is 16 % water, and its water vapour becomes saturated at 55.5 °C. Below that temperature the gas drops liquid water, and the path gets a fourth step:

4. Part of the water condenses at the outlet temperature and gives up its latent heat.

Examples (methane with 20 % excess air, feed at 25 °C):

- Cooled to 40 °C: 1.17 of the 2 mol of water condense, and 847.7 kJ must be removed. With all the water kept as vapour it would be 796.9 kJ.
- Cooled to 25 °C: 1.66 mol condense and 875.6 kJ comes out. This lies between the LHV (802.6 kJ) and the HHV (890.6 kJ). It does not reach the HHV, because the gas leaves saturated and still carries 0.34 mol of water vapour.

This is how a condensing boiler gets more heat out of the same fuel. The box "Let the water change phase" is on at the start. Untick it to keep every substance in the phase that is written, as the textbook examples do. While the outlet is too warm for water to condense, the box changes nothing, so the flame temperature and the reformer example stay as they are.

Only water can change phase in this tab, and the liquid is taken as pure water.

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

- **67 reference values** from textbook examples, course slides, the lab handout and the NIST tables. The solver recalculates each one while you watch. All 67 pass. Ten of them are about phase change: six boiling points, the vapour pressure and latent heat of water, and the temperature at which the water vapour of a flue gas becomes saturated.
- **Five stress tests** from the assignment (see section 6).
- **Comparison with published research** values.

## 5. Why you can trust the answers

- **The data are traceable.** From 298.15 K upwards, 54 of the 57 substances use only the textbook tables. The other three come from the NIST database and are labelled. Below 298.15 K, where the textbook has no data, the heat capacities come from NIST tables, and the solver says so whenever it uses them.
- **It checks itself.** Every result is calculated a second time by a different route. The two must agree. This appears as "Consistency checks" under the results of tabs 2 and 5.
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
| "Practically no reaction" for ammonia | True at 1 bar, but at 200 bar 43 % reacts | The text now says that K belongs to 1 bar, and tab 4 shows the conversion at your pressure |
| The calorimeter named a gas as the unknown sample | A gas cannot be weighed into a crucible | Only liquids and solids are compared |
| The "excess air for a temperature limit" search gave a wrong value | It never checked its own answer | It now solves again with its answer before showing it |
| "Standard state" was explained as 298.15 K and 1 bar | Standard state fixes only the pressure (1 bar). 298.15 K is just where the tables list the data | The guide and the page now keep the two apart |
| Below 298 K the textbook Cp formulas were simply stretched | They are valid from 298 K only. For CO₂ at 200 K the stretched formula is 29 % too low | NIST table values are used from 200 K to 298.15 K |
| The headline said "Not favourable" | It read as if the reaction could not happen, so its ΔH looked meaningless | It now says "Reactants favoured" and adds that some product still forms |
| Tab 2 showed a red error for CO₂ hydrogenation | The pressure was still 200 bar from the ammonia example. Water is a liquid there, so there is no gas value | The example opens at its own conditions (50 bar), and a blue box offers a pressure that works |
| The two burner examples showed an "extrapolated" warning | The flame is hotter than the 2000 K limit of the textbook Cp formula | NIST data are used above the limit. The answer moves from 2066 K to 2069 K, and a note shows both |
| After tab 2 was narrowed down to the heat of reaction, no tab said how pressure changes favourability | The assignment asks for favourability at a given pressure and temperature | Tab 1 has a pressure box and shows the equilibrium conversion at that pressure |
| Every substance stayed in the phase that was typed | Liquid water stayed liquid at 500 K, and a flue gas cooled to 25 °C never gave up the latent heat of its water | The solver finds the boiling point from its own data. Tab 1 can pick the stable phase, and in tab 5 the water condenses when the outlet is cold enough |

The five stress tests of the assignment:

1. **Unbalanced reaction.** CH₄ + O₂ → CO₂ + H₂O is rejected, and CH₄ + 2 O₂ → CO₂ + 2 H₂O is offered.
2. **Shortcut on Cp.** For steam reforming at 1000 K, the proper Cp gives ΔH = 225.3 kJ/mol. A constant Cp gives 238.8, and ignoring Cp gives 205.8. K changes from 25.8 to 50.3 or 2.8.
3. **Liquid or vapour water.** Burning methane gives −890.65 kJ/mol with liquid water and −802.63 with vapour. The gap is the heat needed to boil 2 moles of water. With the "Pick the stable phase" box the solver chooses liquid water at 25 °C by itself.
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
| ΔG | Tells which side is favoured; negative means the products |
| K | Where the reaction stops; bigger than 1 means mostly products |
| ° (as in ΔH°) | Standard state: pure substance at 1 bar, at whatever temperature you choose |
| Reference temperature | 298.15 K, where the tables list the heats of formation |
| Cp | Heat needed to warm a substance by 1 K |
| Sensible heat | Heat that changes temperature without any reaction |
| Exothermic / endothermic | Gives out heat / takes in heat |
| Conversion | The fraction of a reactant that has reacted |
| Stoichiometric | Exactly the amounts the balanced reaction asks for |
| Excess air | Air beyond what the reaction needs |
| Adiabatic | No heat goes in or out through the walls |
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
7. **Why does extra air cool a flame?** The extra air does not react. It only has to be heated, so the same heat is shared by more gas.
8. **Why does a bomb calorimeter measure ΔU and not ΔH?** Its volume is fixed, so no work is done. Heat at constant volume equals ΔU.
9. **Why is LHV smaller than HHV?** With LHV the water leaves as vapour, so the heat of condensing it is not collected.
10. **In tab 4, why does switching methane off change the answer?** Methane is the most stable product. Remove it, and the atoms settle into the next best mixture, which contains methanol.
11. **What do the consistency checks prove?** That two different ways of calculating the same quantity agree. A wrong sign or unit would break it.
12. **Does a favourable ΔG mean the reaction is fast?** No. Thermodynamics says where a reaction can end up, not how quickly. That is why catalysts are needed.
13. **A reaction is not favourable. Why does it still have a ΔH?** ΔH is the enthalpy of the products minus that of the reactants, so it exists for any balanced reaction. "Not favourable" only means K is below 1. Some product still forms, and each mole that reacts exchanges ΔH.
14. **Where do the heat capacities below 298.15 K come from?** From NIST tables, between 200 K and 298.15 K. The textbook formulas start at 298 K and are not used below it.
15. **In tab 4, why can the methanol switch not be clicked while methane is allowed?** Methanol holds 0.0 % of the carbon then, so blocking it would change nothing. Switch methane off and methanol holds 17.3 %; now its switch matters.
16. **Why is the methane flame 2069 K on the page and 2066 K in the textbook?** The textbook stretches its Cp formula 66 K beyond its 2000 K limit. The solver uses NIST data above 2000 K. Stretched, the formula gives a Cp that is a little too high, so the textbook's flame comes out 3 K cooler.
17. **A reaction is favoured at 50 bar but not at 1 bar. Did K change?** No. K depends on temperature only. Pressure changes how far the reaction goes when the number of gas molecules changes.
18. **Why does ΔH° jump at a boiling point while ΔG° does not?** Liquid and vapour have different enthalpies; the difference is the latent heat. But at the boiling point they have the same Gibbs energy, so ΔG° and K pass through without a jump.
19. **A flue gas is cooled to 25 °C. Why does less than the HHV come out?** The gas leaves saturated with water. Of the 2 mol of water from one mole of methane, 0.34 mol stay vapour and keep their latent heat.
20. **Water is in a gas mixture at 80 °C and 1 bar. Is it a liquid?** Only if its partial pressure reaches its vapour pressure, which is 0.47 bar at 80 °C. Below that it stays a vapour, although 80 °C is below the boiling point.
21. **Is the K of this solver Kp or Kc?** Kp: it is written with partial pressures in bar. It changes with temperature only; pressure changes the conversion, not Kp.
22. **Why does the ideal-gas ΔH not change with pressure?** For an ideal gas U depends on T only and PV = RT, so H = U + RT depends on T only.
23. **Why does tab 2 start on Peng/Robinson?** It uses the acentric factor as well as Tc and Pc, and it holds at high pressure. Soave/Redlich/Kwong gives almost the same answer; van der Waals and Redlich/Kwong do not.

## 10. A five-minute tour

1. Open the **Start** page and click "Try to break it". The unbalanced reaction is rejected.
2. Click "Heat, entropy and Gibbs energy". Point at the headline, the four cards and the plot of ΔG against temperature.
3. Click "What does pressure change?" Show the ideal gas next to the real gas: −106.50 against −111.66 kJ/mol at 200 bar. Then click "CO₂ hydrogenation to methanol" in the list of bars: 10.6 %.
4. Click "What actually forms?" Press the three "Try this" buttons: everything allowed, methane off, methane and CO off. Point at the faded switches and say why they are faded. Then drag the temperature slider.
5. Click "How hot does it get?" Drag the excess-air slider and watch the flame cool. Then pick the "Condensing boiler" example and drag the outlet temperature across 329 K: the heat line bends where the water starts to condense.
6. Click "Bomb calorimeter" and press Ignite.
7. Finish on **Validation**: 67 of 67 reference values reproduced.
