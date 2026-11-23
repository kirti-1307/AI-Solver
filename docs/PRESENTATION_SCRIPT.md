# Presentation script: Thermodynamic Reaction Energy Solver

About 10 minutes in total. The words to say are in plain text. What to click is in *italics* inside square brackets. Every number below is what the solver shows, so it will match the screen.

**Before the class**

- Open https://ai-solver-seven.vercel.app/ (spare: https://kirti-1307.github.io/AI-Solver/). Wait until the top right says **Solver ready**, which takes about ten seconds on the first visit.
- Stay on the **Start** page. Keep the browser at 100 % zoom.
- If there is no internet: run `python serve.py` in the project folder and open http://localhost:8000.

---

## 1. Opening (30 seconds)

*[Start page]*

Good morning. For this assignment I built a thermodynamic solver for reaction energetics. It runs in any browser, and it answers three questions about a reaction: how much heat it gives out or takes in, which side is favoured, and how both of these change with temperature and pressure.

All the equations come from Smith, Van Ness and Abbott, and so does the data wherever the textbook has it. The database has 57 species, including all 26 that the assignment suggests, and there are 45 predefined reactions. You can also type your own.

## 2. The core of the solver (3 minutes)

### Tab 1: Reaction

*[Click the card "Try to break it"]*

The first thing the solver does is check the elemental balance. Here I typed methane plus oxygen giving CO2 and water, without coefficients. The solver refuses to calculate anything. It tells me that hydrogen is 4 on the left and 2 on the right, and oxygen is 2 against 3, and it offers the balanced form, CH4 + 2 O2 → CO2 + 2 H2O.

*[Pick "CO2 hydrogenation to methanol" from the list. The temperature is 523.15 K]*

Now a real case: CO2 hydrogenation to methanol at 523 K. The reaction gives out heat, ΔH° = −57.94 kJ/mol. But it turns four moles of gas into two, so ΔS° is negative, −199.76 J/(mol·K). At this temperature the entropy term wins, and ΔG° is +46.56 kJ/mol. So the reactants are favoured, and Kp is only 2.2 × 10⁻⁵.

Kp here means the equilibrium constant written with partial pressures in bar. It changes with temperature only, never with pressure.

*[Type 50 in the pressure box and press Calculate]*

Pressure does not change Kp, but it changes how far the reaction goes. At 1 bar only 0.6 % of the CO2 converts. At 50 bar it is 21.3 %, because the reaction makes fewer gas molecules.

*[Scroll to the graphs]*

The graphs show the same quantities against temperature, and all of them use the same temperature axis. The orange line is ΔH°, the blue line is ΔG°, and where the blue line crosses zero, Kp equals 1. The dashed lines show what we would get with a constant Cp or with Cp ignored. This was one of the stress tests of the assignment: at 1000 K for steam reforming the three give 225.3, 238.8 and 205.8 kJ/mol.

### Tab 2: Pressure and real gas

*[Click tab 2. It opens on ammonia synthesis at 723 K and 200 bar]*

For an ideal gas the enthalpy does not depend on pressure. The molecules do not feel each other, so U depends on temperature only, and H = U + PV = U + RT. That is why the grey dashed line is flat.

A real gas is different. The residual enthalpy Hᴿ is the real value minus the ideal value, and I get it from an equation of state. For ammonia synthesis at 200 bar the ideal-gas ΔH is −106.50 kJ/mol, and the real gas gives −111.66 kJ/mol. So the real gas releases 4.8 % more heat.

*[Point at the list of six reactions at the top]*

This effect is not the same everywhere. It is 10.6 % for methanol from CO2 at 50 bar, because methanol and water are cold, dense and polar. But it is only 0.2 % for steam reforming at 1100 K, because hot, light gases behave almost ideally.

I use Peng/Robinson by default. Like Soave/Redlich/Kwong, it uses the acentric factor as well as Tc and Pc, and it still works at high pressure, where the virial equation does not. The table under the result compares all five models: Peng/Robinson and Soave/Redlich/Kwong agree within 0.05 kJ/mol, while van der Waals and Redlich/Kwong can be off by a few kJ.

### Tab 3: Combine reactions

*[Click tab 3]*

This tab uses Hess's law. The reverse water-gas shift plus methanol synthesis from CO gives the same CO2-to-methanol reaction. The sum of the steps and the direct calculation both give −57.94 kJ/mol at 523 K, so the two routes agree.

## 3. Extra feature 1: Product slate (2.5 minutes)

*[Click tab 4. It opens on CO2 + 3 H2 at 523 K and 50 bar]*

Tab 1 looks at one reaction at a time. But in a real reactor several reactions compete for the same atoms. CO2 and hydrogen can make methanol, but they can also make CO or methane.

So in this tab I do not choose a reaction. I only choose which species are allowed to exist. The solver then finds the mixture with the lowest total Gibbs energy, which is where the reactor ends up at equilibrium.

*[Click "1. Everything allowed"]*

With every product allowed, methane takes 74.8 % of the carbon, and 74.9 % of the CO2 converts. Methanol gets 0.0 %. So thermodynamics alone does not want methanol at all.

*[Click "2. Methane off"]*

Each switch works like a selective catalyst. Switching methane off means the catalyst cannot make methane. Now only 25.2 % of the CO2 converts: 17.3 % of the carbon goes to methanol and 7.9 % to CO.

*[Click "3. Methane and CO off"]*

With only methanol allowed, the conversion is 21.3 %, which is exactly the number tab 1 gave at 50 bar. So the two tabs agree with each other.

The main point is this: thermodynamics favours methane, and it is the catalyst that makes methanol possible.

*[Go back to "2. Methane off" and drag the pressure slider to 100 bar]*

The sliders change the answer live. At 100 bar methanol rises to 30.8 % of the carbon, because high pressure helps the reaction that makes fewer gas molecules.

*[Put the pressure back to 50 bar, then drag the temperature slider to 700 K]*

At 700 K methanol almost disappears, and CO takes 40.1 %, because high temperature favours the reaction that takes in heat.

The faded switches are the ones that would change nothing at the current settings, so the page only lets me click switches that matter.

## 4. Extra feature 2: Heat lab (2.5 minutes)

*[Click tab 5. "Reactor and flame" opens on the methane burner with 20 % excess air]*

The heat of reaction alone does not tell us how hot a reactor gets. So this tab makes an energy balance around the reactor, using the same three-step path as the textbook: bring the feed to 298.15 K, react there, then heat the products to the outlet.

With no heat loss, methane burned with 20 % excess air reaches 2069 K. The textbook example gives 2066 K, because it stretches its Cp formula beyond its 2000 K limit. Above 2000 K my solver uses NIST data instead, and the note on the page shows both numbers.

*[Drag the excess-air slider]*

Extra air cools the flame, because the extra nitrogen and oxygen also have to be heated. With no excess air the flame is at 2326 K, and with 100 % excess air it is 1486 K.

*[Put the excess air back to 20 %. Open "More settings" and type 1500 in "Temperature limit"]*

If I set a temperature limit of 1500 K, the solver finds that I need 97 % excess air.

*[Pick the example "Condensing boiler: flue gas of a methane burner cooled to 40 C"]*

The flue gas also contains water vapour. A gas can hold water vapour only up to the vapour pressure of water, so when it is cooled far enough the water starts to condense. For this flue gas that happens at 328.7 K, which is 55.5 °C.

At 40 °C, 1.17 of the 2 moles of water condense, and their latent heat comes out as a fourth step. So 847.7 kJ can be recovered instead of 796.9 kJ.

*[Untick "Let the water change phase"]*

If I keep the water as vapour, it is back to 796.9 kJ, with a warning that heat is left out. This is how a condensing boiler gets more heat out of the same fuel. Cooled to 25 °C the flue gas gives 875.6 kJ, which lies between the LHV of 802.6 and the HHV of 890.6 kJ/mol. It cannot reach the HHV, because the gas leaves saturated and still carries some water vapour away.

*[Click "Bomb calorimeter"]*

The second view repeats our lab experiment. The calibration uses the numbers from the lab handout: 1.1942 g of benzoic acid and a rise of 2.48 °C, which give a calorimeter constant of 3059.3 cal/°C.

*[Choose ethanol and press Ignite]*

For 1 g of ethanol the solver predicts a temperature rise of 2.31 °C. The bomb has a fixed volume, so it measures ΔU, not ΔH, and ΔH = ΔU + Δn·R·T links the two.

## 5. How I checked it (1 minute)

*[Click tab 7]*

Every result is checked in three ways. First, the solver reproduces 67 out of 67 reference values from the textbook's worked examples, the course slides, the lab handout and NIST tables. Second, it passes the five stress tests of the assignment, and the heats of reaction agree with published research within 0.5 kJ/mol. Third, there are 407 automated tests, which run every time the code changes.

While building it, I also found and corrected several errors of the AI. For example, it used an older value of ΔG°f for ammonia, it treated liquid water as a gas at high pressure, and it called the standard state "298.15 K and 1 bar", although the standard state fixes only the pressure.

## 6. Closing (20 seconds)

To sum up, the solver gives the heat of reaction, entropy, Gibbs energy and Kp at any temperature, shows what pressure does for real gases, and adds two features on top: the product slate, which shows that the catalyst decides what forms, and the heat lab, which turns the heat of reaction into a reactor temperature, or into the heat to add or remove, for a real burner. Thank you.

---

## Questions the professor may ask

**Is your K a Kp or a Kc?**
It is Kp, written with the partial pressures in bar, divided by the standard pressure of 1 bar. The standard state of a gas is 1 bar, so ΔG° = −RT ln K gives Kp.

**Does Kp change with pressure?**
No. For an ideal gas, Kp (and Kc too) depends on temperature only. Pressure changes the equilibrium composition, which is why the conversion rises from 0.6 % to 21.3 % at 50 bar.

**Why does the ideal-gas ΔH not change with pressure?**
For an ideal gas, U depends on T only, and PV = RT, so H = U + RT depends on T only.

**Why Peng/Robinson?**
It uses Tc, Pc and the acentric factor, and it works at high pressure. Soave/Redlich/Kwong gives almost the same answer. van der Waals and Redlich/Kwong use only Tc and Pc, and the virial equation is only for low to moderate pressure. For methanol synthesis at 80 bar, the residual part is −8.63 kJ/mol with Peng/Robinson but −5.05 with van der Waals.

**Why does methane win on tab 4, if industry makes methanol?**
Making methane from CO2 and hydrogen lowers the total Gibbs energy much more than making methanol does. Industry uses a catalyst that makes methanol but not methane, which is exactly what the switch imitates.

**Why is your flame 2069 K and the textbook's 2066 K?**
The textbook uses its Cp formula up to 2066 K, but the formula is only valid to 2000 K. My solver uses NIST data above 2000 K. With the stretched formula it also gives 2066 K, as shown in the Validation tab.

**Is a real flame really that hot?**
A little cooler. Above about 2000 K, some of the CO2 and H2O break apart, which takes up heat, and the energy balance does not include that. The page says so in a note.

**A reaction is "reactants favoured". Why does it still have a ΔH?**
ΔH is the enthalpy of the products minus that of the reactants, so it exists for every balanced reaction. A small Kp only means that less product forms, and every mole that does react still gives out ΔH.

**What does "standard state" mean?**
The pure species at 1 bar, at any temperature. 298.15 K is only the reference temperature at which the tables give the heats of formation.

**Where does the data come from below 298 K and above 2000 K?**
The textbook's Cp tables start at 298 K. From 200 K to 298.15 K, the heat capacities come from NIST tables. Above 2000 K, for the eight flame gases, they come from NIST equations. Everything in between is from the textbook.

**Why does the bomb calorimeter give ΔU?**
Its volume is fixed, so no work is done, and the heat released equals ΔU. Then ΔH = ΔU + Δn·R·T.

**What are the limitations?**
Phase change is handled on tab 1 and in the heat lab only. On tabs 2 and 4, a species that would condense at high pressure is flagged but not condensed. The heat lab ignores the breaking apart of CO2 and H2O above 2000 K. And equilibrium tells us where a reaction ends up, not how fast it gets there.
