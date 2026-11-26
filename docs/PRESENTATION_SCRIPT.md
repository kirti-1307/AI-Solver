# Presentation script: Thermodynamic Reaction Energy Solver

About 12 minutes: 5 minutes on the six slides (the idea), 6 minutes of live demo, and a short close. The words to say are in plain text. What to click is in *italics* inside square brackets. Every number below is what the solver shows, so it matches the screen. For the questions afterwards, see the study guide (`docs/STUDY_GUIDE.md`).

**Before the class**

- Open the slides (`presentation/Thermo_Solver_Presentation.pptx`) and start the slide show on slide 1.
- In the browser, open https://ai-solver-seven.vercel.app/ (spare: https://kirti-1307.github.io/AI-Solver/). Wait until the top right says **Solver ready**, which takes about ten seconds on the first visit. Then stay on the **Start** page.
- Keep the browser at 100 % zoom, and close every other tab.
- If both addresses are down but the internet works: run `python serve.py` in the project folder and open http://localhost:8000. The page always needs the internet once, to load Python and the plotting library.

---

## Part 1: The slides (5 minutes)

### Slide 1: Title (20 seconds)

Good morning. My project is a Thermodynamic Reaction Energy Solver. It is a web page that works out the heat of reaction, the entropy change and the Gibbs energy change of a chemical reaction at any temperature, and shows what pressure does to them, using the data and the equations of Smith, Van Ness and Abbott. I built it with Claude as the AI platform.

### Slide 2: The idea (1 minute 15 seconds)

Let me start with the problem. In our course, the heat of reaction at a temperature other than 298.15 K needs a heat-capacity integral for every species. By hand, that takes a page of working for one reaction at one temperature, and a slip in one constant is easy to miss.

So people use shortcuts. They take ΔCp as constant, or they ignore it. These shortcuts can be badly off: for the 40 predefined reactions whose data reach 1000 K, a constant ΔCp puts ΔH° off by 9.0 kJ/mol on average and by up to 31.5 kJ/mol.

And a real reactor adds two more questions that a single ΔG° cannot answer: what does high pressure do, and which products actually form when several reactions compete for the same atoms.

My idea was a solver that does the full textbook method every time, in a few seconds, shows every step and every plot, explains the result in plain words, and checks itself against the textbook.

### Slide 3: How it works (1 minute)

The user picks one of 45 predefined reactions, or types any reaction. First, the solver checks the balance of every element. An unbalanced reaction gets no numbers at all, only the balanced form as a suggestion.

Then it takes the data from its database: 57 species, mostly from the textbook's tables, with NIST data only where the textbook has none. It integrates the heat capacities from 298.15 K to the chosen temperature and gets ΔH°, ΔS° and ΔG°. For pressure, it adds the residual enthalpy of each gas from an equation of state.

Everything runs inside the browser. There is no server, so the page works anywhere.

### Slide 4: What it shows (1 minute)

Three results from the solver.

First, temperature decides which side is favoured. CO2 to methanol gives out heat, but it turns four moles of gas into two, so ΔS° is negative. At 523 K, ΔG° is +46.6 kJ/mol, so the reactants are favoured. Steam reforming is the opposite case: its products are favoured above 893 K.

Second, pressure matters for real gases. For ammonia synthesis at 200 bar, the real gas releases 4.7 % more heat than the ideal gas.

Third, no single equation of state is best. I compared the five equations of the course with measured data from NIST for 24 gases. The chart shows the average error: Soave/Redlich/Kwong and Peng/Robinson are far better than van der Waals and the virial equation. So the solver, not the user, chooses the equation for each gas.

### Slide 5: Two extra features (1 minute)

On top of what the assignment asks, I added two features.

The product slate is a live reactor. I only choose which species may exist, and the solver finds the mixture with the lowest total Gibbs energy. For CO2 and hydrogen at 523 K and 50 bar, methane takes 74.9 % of the carbon. If I switch methane off, like a selective catalyst would, methanol takes 20.6 %. So thermodynamics favours methane, and it is the catalyst that makes methanol possible.

The second feature repeats our bomb calorimeter lab. The bomb is a closed vessel, so it measures ΔU and not ΔH. After a calibration with the benzoic acid run of the handout, it predicts the temperature rise of any fuel, 2.31 °C for 1 g of ethanol, and it can work backwards to name an unknown sample.

### Slide 6: Checked, and ready to try (40 seconds)

Finally, why the numbers can be trusted. The solver reproduces 67 of 67 reference values from the textbook, the course material and NIST. It passes all five stress tests of the assignment. I found and corrected eight errors of the AI-generated solver. And 441 automated tests run every time the code changes.

Let me show you the solver live.

---

## Part 2: The live demo (6 minutes)

*[Switch to the browser. It is on the Start page]*

### Tab 1: one reaction (2 minutes)

*[Click the card "Try to break it"]*

First, the balance check. Here methane plus oxygen gives CO2 and water, typed without coefficients. The solver refuses to calculate anything, says which elements do not balance, and offers the balanced form.

*[Pick "CO2 hydrogenation to methanol" from the list. The temperature is 523.15 K]*

Now a real reaction at 523 K. The cards show ΔH° = −57.94 kJ/mol, so it gives out heat, ΔS° = −199.76 J/(mol·K), and ΔG° = +46.56 kJ/mol, so the reactants are favoured. That does not mean nothing reacts: some product still forms, only less.

*[Scroll to the graphs]*

The first graph shows the same three quantities against temperature, from 298.15 K up. Orange is ΔH°, blue is ΔG°. For this reaction ΔG° stays positive over the whole graph. The dashed lines show what the shortcuts would give. The bars show the sensible heat of each species, and the table under them gives every number of the calculation.

*[Type `CH4 + 2 O2 -> CO2 + 2 H2O` with the temperature 298.15 K and press Calculate]*

A second reaction: methane combustion, with water typed without a phase. The solver finds the boiling point of water from its own data, 373.2 K, and uses the phase that is stable at my temperature. At 298.15 K that is liquid water, and ΔH° is −890.65 kJ/mol. If I type H2O(g) on purpose, it keeps the vapour and gives −802.63 kJ/mol, the lower heating value.

### Tab 2: pressure (1 minute)

*[Click tab 2. It opens on ammonia synthesis at 723 K and 200 bar]*

For an ideal gas, H depends on temperature only, so the ideal-gas ΔH is −106.50 kJ/mol at any pressure. At 200 bar the real gas gives −111.55 kJ/mol, so it releases 4.7 % more heat. The difference is the residual enthalpy.

*[Point at the three steps, then scroll to the table at the bottom]*

The three steps reach the real value like Hess's law: real reactants to ideal gas, the ideal-gas reaction, then ideal products to real gas. The table shows each gas with the equation of state the solver chose for it.

### Tab 4: product slate (1 minute 30 seconds)

*[Click tab 4. Click "1. Everything allowed", then "2. Methane off"]*

With every product allowed, methane takes 74.9 % of the carbon. With methane off, methanol takes 20.6 % and CO 7.5 %.

*[Drag the pressure slider to 100 bar]*

At 100 bar methanol rises to 39.4 %, because high pressure helps the reaction that makes fewer gas molecules.

### Tab 5: bomb calorimeter (1 minute)

*[Click tab 5. Ethanol is selected. Press Ignite]*

1 g of ethanol: ΔH = −1366.8 kJ/mol from the heats of formation, ΔU = −1364.3 kJ/mol because the gas moles fall by one, a calorific value of 29.62 MJ/kg, and a temperature rise of 2.31 °C.

*[Click "Identify an unknown sample". Keep 1.00 g and 2.30 °C, then press Identify]*

Backwards: a rise of 2.30 °C for 1 g gives 29.44 MJ/kg, and the closest fuel is ethanol, only 0.6 % away.

### Tab 7: validation (30 seconds)

*[Click tab 7]*

And this tab runs all the reference values and the five stress tests live, in the browser, while you watch.

---

## Part 3: Close (20 seconds)

To sum up: the solver does the full textbook method for any reaction, shows what pressure does to real gases with the equation of state that fits each gas best, shows which products really form, and repeats our calorimeter lab. Every number is checked against the textbook. Thank you, and I am happy to take questions.

---

## If something goes wrong

- **The page says "Starting…" for long:** the first visit downloads Python once (about 10 MB). Switch to the spare address, or keep talking over slide 3 while it loads.
- **A tab shows an error box:** press Calculate again, or reload the page (Ctrl+R). The solver keeps no state, so nothing is lost.
- **No internet at all:** the page cannot load Python, so show the slides and quote the numbers from them (they are the solver's), and offer the report PDF.
- **Questions:** the study guide has the likely questions with answers, by topic.
