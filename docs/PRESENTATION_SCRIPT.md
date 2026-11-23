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

Now a real case: CO2 hydrogenation to methanol at 523 K. The reaction gives out heat, ΔH° = −57.94 kJ/mol. But it turns four moles of gas into two, so ΔS° is negative, −199.76 J/(mol·K). At this temperature the entropy term wins, and ΔG° is +46.56 kJ/mol. So the reactants are favoured. That does not mean nothing reacts: some product still forms, only less.

*[Type 50 in the pressure box and press Calculate]*

ΔG° belongs to the standard pressure of 1 bar, so pressure does not change it. But pressure changes how far the reaction goes. At 1 bar only 0.6 % of the CO2 converts. At 50 bar it is 21.3 %, because the reaction makes fewer gas molecules.

*[Scroll to the graphs]*

The graphs show the same quantities against temperature, and all of them use the same temperature axis. The orange line is ΔH°, the blue line is ΔG°, and where the blue line crosses zero, the favoured side changes. The dashed lines show what we would get with a constant Cp or with Cp ignored. This was one of the stress tests of the assignment: at 1000 K for steam reforming the three give 225.3, 238.8 and 205.8 kJ/mol.

### Tab 2: Pressure and real gas

*[Click tab 2. It opens on ammonia synthesis at 723 K and 200 bar]*

For an ideal gas the enthalpy does not depend on pressure. The molecules do not feel each other, so U depends on temperature only, and H = U + PV = U + RT. That is why the grey dashed line in the first graph, the ideal gas, is flat at zero.

A real gas is different. The residual enthalpy Hᴿ is the real value minus the ideal value, and I get it from an equation of state. For ammonia synthesis at 200 bar the ideal-gas ΔH is −106.50 kJ/mol, and the real gas gives −111.66 kJ/mol. So the real gas releases 4.8 % more heat.

*[Point at the list of six reactions at the top]*

This effect is not the same everywhere. It is 10.6 % for methanol from CO2 at 50 bar, because methanol and water are cold, dense and polar. But it is only 0.2 % for steam reforming at 1100 K, because hot, light gases behave almost ideally.

I use Peng/Robinson by default. Like Soave/Redlich/Kwong, it uses the acentric factor as well as Tc and Pc, and it still works at high pressure, where the virial equation does not. If I switch the model in the list, Soave/Redlich/Kwong gives almost the same answer, while van der Waals and Redlich/Kwong can be off by a few kJ.

### Tab 3: Combine reactions

*[Click tab 3]*

This tab uses Hess's law. The reverse water-gas shift plus methanol synthesis from CO gives the same CO2-to-methanol reaction. The sum of the steps and the direct calculation both give −57.94 kJ/mol at 523 K, so the two routes agree.

## 3. Extra feature 1: Product slate (2.5 minutes)

*[Click tab 4. It opens on CO2 + 3 H2 at 523 K and 50 bar]*

Tab 1 looks at one reaction at a time. But in a real reactor several reactions compete for the same atoms. CO2 and hydrogen can make methanol, but they can also make CO or methane.

So in this tab I do not choose a reaction. I only choose which species are allowed to exist. The solver then finds the mixture with the lowest total Gibbs energy, which is where the reactor ends up at equilibrium.

*[Click "1. Everything allowed"]*

With every product allowed, methane takes 74.8 % of the carbon, and only 25.1 % stays as CO2. Methanol gets 0.0 %. So thermodynamics alone does not want methanol at all.

*[Click "2. Methane off"]*

Each switch works like a selective catalyst. Switching methane off means the catalyst cannot make methane. Now 74.8 % of the carbon stays as CO2: 17.3 % goes to methanol and 7.9 % to CO.

*[Click "3. Methane and CO off"]*

With only methanol allowed, methanol takes 21.3 % of the carbon, which is exactly the conversion tab 1 gave at 50 bar. So the two tabs agree with each other.

The main point is this: thermodynamics favours methane, and it is the catalyst that makes methanol possible.

*[Go back to "2. Methane off" and drag the pressure slider to 100 bar]*

The sliders change the answer live. At 100 bar methanol rises to 30.8 % of the carbon, because high pressure helps the reaction that makes fewer gas molecules.

*[Put the pressure back to 50 bar, then drag the temperature slider to 700 K]*

At 700 K methanol almost disappears, and CO takes 40.1 %, because high temperature favours the reaction that takes in heat.

The faded switches are the ones that would change nothing at the current settings, so the page only lets me click switches that matter.

## 4. Extra feature 2: Bomb calorimeter (2.5 minutes)

*[Click tab 5. The numbers of our lab handout are already filled in]*

This tab repeats our bomb calorimeter lab on screen. A sample burns in a closed steel vessel, the bomb, which sits in water. The vessel cannot change its volume, so no work is done, and the heat that comes out is ΔU, not ΔH.

First the calorimeter is calibrated, with the numbers from the handout: 1.1942 g of benzoic acid, which gives 6319 cal/g, raised the temperature by 2.48 °C, and the thread and wire gave 41 cal. So the calorimeter constant is (1.1942 × 6319 + 41) / 2.48 = 3059.3 cal/°C.

*[Ethanol is selected. Press Ignite]*

Now I burn 1 g of ethanol. The solver writes the complete combustion, C2H5OH(l) + 3 O2 → 2 CO2 + 3 H2O(l), and gets ΔH = −1366.8 kJ/mol from the heats of formation. The gas moles fall by 1, because three O2 go in and two CO2 come out, so ΔU = ΔH − Δn·R·T = −1364.3 kJ/mol. Per kilogram, that is a calorific value of 29.62 MJ/kg, and the predicted temperature rise is 2.31 °C.

*[Scroll to the steps under the result]*

The page also gives the two heating values. The HHV, 29.67 MJ/kg, has the water as liquid, and the LHV, 26.80 MJ/kg, has it as vapour. The difference is the latent heat of the water formed.

*[Click "Identify an unknown sample". Keep 1.00 g and 2.30 °C, then press Identify]*

The calorimeter can also work backwards. If 1 g of an unknown sample raises the temperature by 2.30 °C, its calorific value is 29.44 MJ/kg. The closest fuel in the database is ethanol, only 0.6 % away, while the next one, graphite, is 11 % away. So in the lab we could tell which fuel we burned.

## 5. How I checked it (1 minute)

*[Click tab 7]*

Every result is checked in three ways. First, the solver reproduces 67 out of 67 reference values from the textbook's worked examples, the course slides, the lab handout and NIST tables. Second, it passes the five stress tests of the assignment, and the heats of reaction agree with published research within 0.5 kJ/mol. Third, there are 412 automated tests, which run every time the code changes.

While building it, I also found and corrected several errors of the AI. For example, it used an older value of ΔG°f for ammonia, it treated liquid water as a gas at high pressure, and it called the standard state "298.15 K and 1 bar", although the standard state fixes only the pressure.

## 6. Closing (20 seconds)

To sum up, the solver gives the heat of reaction, entropy and Gibbs energy at any temperature, shows what pressure does for real gases, and adds two features on top: the product slate, which shows that the catalyst decides what forms, and the bomb calorimeter, which repeats our lab on screen and links ΔU to ΔH. Thank you.

---

## Questions the professor may ask

**Is your K a Kp or a Kc?**
K is not shown on tab 1, but the solver uses it for the conversion and for the soot test on tab 4. It is Kp, written with the partial pressures in bar, divided by the standard pressure of 1 bar. The standard state of a gas is 1 bar, so ΔG° = −RT ln K gives Kp.

**Does Kp change with pressure?**
No. For an ideal gas, Kp (and Kc too) depends on temperature only. Pressure changes the equilibrium composition, which is why the conversion rises from 0.6 % to 21.3 % at 50 bar.

**Why does the ideal-gas ΔH not change with pressure, but the real-gas ΔH does?**
For an ideal gas, U depends on T only, and PV = RT, so H = U + RT depends on T only. In a real gas the molecules attract each other. Higher pressure pushes them closer, so the attraction lowers the enthalpy more. That is also why Z drops below 1.

**How is the residual part calculated?**
For each gas: take Tc, Pc and ω from Table B.1, work out Tr and Pr, solve the Peng/Robinson equation for Z, and put these into the textbook's formula for Hᴿ/RT. Then add up ν·Hᴿ over the reaction. For methanol at 523 K and 50 bar: Tr = 1.02, Pr = 0.62, Z = 0.753, Hᴿ = −4.22 kJ/mol.

**Why is Hᴿ more negative close to the critical point?**
Near the critical point a gas is almost a liquid: the molecules are close and slow enough for their attraction to matter a lot. Methanol at 523 K has Tr = 1.02 and Hᴿ = −4.22 kJ/mol. Hydrogen has Tr = 15.8 and Hᴿ = +0.03 kJ/mol, almost ideal.

**What do the three steps on tab 2 mean?**
They reach the real-gas ΔH by a detour, like Hess's law: real reactants to ideal gases, react as ideal gases, ideal products back to real gases. H depends only on the start and the end, so the detour gives the same answer.

**Does the solver use Peng/Robinson for every calculation?**
No. Only tab 2 needs an equation of state, and it starts on Peng/Robinson; the list lets me pick any other. Tab 4 can use Peng/Robinson if I choose "real gas", but it starts on the ideal gas. Tabs 1, 3 and 5 use standard values at 1 bar, which need no equation of state.

**What if another equation is better in some cases?**
That can happen. Each equation is a model, and the best one depends on the gas and the conditions. That is why the list is there: switching the model shows how much the answer depends on it. For the six industrial cases, Peng/Robinson and Soave/Redlich/Kwong agree within 0.05 kJ/mol, so the answer hardly depends on which of the two I use. Only measured data could say which equation is closest to the truth, and the course tables do not give measured residual enthalpies.

**Why Peng/Robinson?**
It uses Tc, Pc and the acentric factor, and it works at high pressure. Soave/Redlich/Kwong gives almost the same answer. van der Waals and Redlich/Kwong use only Tc and Pc, and the virial equation is only for low to moderate pressure. For methanol synthesis at 80 bar, the residual part is −8.63 kJ/mol with Peng/Robinson but −5.05 with van der Waals.

**How do you know whether solid carbon (soot) can form?**
The solver takes the gas it found and a reaction that makes carbon from it, for example 2 CO → C(s) + CO2. If the gas ratio p(CO2)/p(CO)² is smaller than the Kp of that reaction, the reaction can still go forward, so carbon can form. At 700 K with methane off the ratio is 0.30 and Kp is 4142, so carbon can form.

**Why does methane win on tab 4, if industry makes methanol?**
Making methane from CO2 and hydrogen lowers the total Gibbs energy much more than making methanol does. Industry uses a catalyst that makes methanol but not methane, which is exactly what the switch imitates.

**A reaction is "reactants favoured". Why does it still have a ΔH?**
ΔH is the enthalpy of the products minus that of the reactants, so it exists for every balanced reaction. A small Kp only means that less product forms, and every mole that does react still gives out ΔH.

**What does "standard state" mean?**
The pure species at 1 bar, at any temperature. 298.15 K is only the reference temperature at which the tables give the heats of formation.

**Where does the data come from below 298 K and above 2000 K?**
The textbook's Cp tables start at 298 K. From 200 K to 298.15 K, the heat capacities come from NIST tables. Above 2000 K, for eight common gases, they come from NIST equations. Everything in between is from the textbook.

**Why does the bomb calorimeter give ΔU?**
Its volume is fixed, so no work is done, and the heat released equals ΔU. Then ΔH = ΔU + Δn·R·T.

**What are the limitations?**
Phase change is handled on tab 1 only. On tabs 2 and 4, a species that would condense at high pressure is flagged but not condensed. The calorimeter assumes complete combustion to CO2 and liquid water. And equilibrium tells us where a reaction ends up, not how fast it gets there.
