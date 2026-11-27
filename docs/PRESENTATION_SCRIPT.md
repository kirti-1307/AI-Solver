# Presentation script: Thermodynamic Reaction Energy Solver

About 14 minutes: 6.5 minutes on the seven slides (the idea, opening with the story of Goldilocks and the three bears), 7 minutes of live demo, and a short close. The words to say are in plain text. What to click is in *italics* inside square brackets. Every number below is what the solver shows, so it matches the screen. For the questions afterwards, see the study guide (`docs/STUDY_GUIDE.md`).

**Before the class**

- Open the slides (the light-theme deck designed from `presentation/PITCH_DECK.md`) and start the slide show on slide 1. The older six-slide deck, `presentation/Thermo_Solver_Presentation.pptx`, is a spare.
- In the browser, open https://ai-solver-seven.vercel.app/ (spare: https://kirti-1307.github.io/AI-Solver/). Wait until the top right says **Solver ready**, which takes about ten seconds on the first visit. Then stay on the **Start** page.
- Keep the browser at 100 % zoom, and close every other tab.
- If both addresses are down but the internet works: run `python serve.py` in the project folder and open http://localhost:8000. The page always needs the internet once, to load Python and the plotting library.

---

## Part 1: The slides (6.5 minutes)

### Slide 1: The story (45 seconds)

Good morning. Before I start, a short story. You all know Goldilocks and the three bears. In my version, Goldilocks is a little more careful: before she eats, she asks Baby Bear one question. "How hot is the porridge?" And Baby Bear says: "Papa's bowl is too hot, Mama's is too cold, and mine is just right."

Notice that the bear did not give her a number. Whether it is too hot or just right depends on the temperature, and on what you want from it.

### Slide 2: Goldilocks' question, for every reaction (1 minute)

As chemical engineers, we ask Goldilocks' question about every reaction. How hot: how much heat does the reaction give out or take in? That is ΔH°. And is it just right: at this temperature, are the products favoured? That is ΔG°, which comes from ΔH° and the entropy change ΔS°.

The problem is that the textbook tables give these numbers at one temperature only, 298.15 K. At any other temperature we need a heat-capacity integral for every species, which is a page of working for one reaction at one temperature. So people use shortcuts, like taking ΔCp as constant. For the 40 predefined reactions whose data reach 1000 K, that shortcut is off by 9.0 kJ/mol on average, and by up to 31.5 kJ/mol.

My idea was a solver that does the full textbook method every time, for any reaction at any temperature, in a few seconds. It shows every step and every plot, explains the result in plain words, and checks itself against the textbook.

### Slide 3: How it works (1 minute)

The user picks one of 45 predefined reactions, or types any reaction. First, the solver checks the balance of every element. An unbalanced reaction gets no numbers at all, only the balanced form as a suggestion.

Then it takes the data from its database: 57 species, mostly from the textbook's tables, with NIST data only where the textbook has none. It integrates the heat capacities from 298.15 K to the chosen temperature and gets ΔH°, ΔS° and ΔG°. For pressure, it adds the residual enthalpy of each gas from an equation of state.

Everything runs inside the browser. There is no server, so the page works anywhere.

### Slide 4: Too hot, too cold, just right (1 minute)

So let's go back to the three bowls, with real reactions. Too hot: CO2 to methanol gives out heat, but it turns four moles of gas into two, so ΔS° is negative. At 523 K, ΔG° is +46.6 kJ/mol, so the reactants are favoured, and heating it more makes this worse. That does not mean nothing reacts: some methanol still forms, only less.

Too cold: steam reforming takes in heat. At 700 K, ΔG° is +47.9 kJ/mol, so the reactants are still favoured. Just right: the same reaction at 1000 K has ΔG° = −27.0 kJ/mol, so the products are favoured. The turning point is 893 K, where ΔG° is zero.

The solver shows this for any reaction, as a graph from 298.15 K up.

### Slide 5: Real gases at high pressure (1 minute)

Real reactors also run at high pressure. For an ideal gas, H depends on temperature only, but a real gas is different. For ammonia synthesis at 723 K and 200 bar, the real gas releases 4.7 % more heat than the ideal gas: −111.55 instead of −106.50 kJ/mol. The difference is the residual enthalpy of each gas, which comes from an equation of state.

But which equation? I compared the five equations of the course with measured data from NIST, for 24 gases and 380 points. The chart shows the average error. No single equation is the best for every gas, so the solver, not the user, picks the closest one for each gas: Soave/Redlich/Kwong for 14 gases, Peng/Robinson for 6 and Redlich/Kwong for 4.

### Slide 6: Two extra features (1 minute)

On top of what the assignment asks, I added two features. The product slate is a live reactor. I only choose which species may exist, and the solver finds the mixture with the lowest total Gibbs energy. For CO2 and hydrogen at 523 K and 50 bar, methane takes 74.9 % of the carbon. If I switch methane off, like a selective catalyst would, methanol takes 20.6 %, and at 100 bar 39.4 %. So thermodynamics favours methane, and it is the catalyst that makes methanol possible.

The second feature answers Goldilocks' question quite literally: how hot does it get? It repeats our bomb calorimeter lab. The bomb is a closed vessel, so it measures ΔU and not ΔH. After a calibration with the benzoic acid run of the handout, it predicts the temperature rise of any fuel, 2.31 °C for 1 g of ethanol, and it can work backwards to name an unknown sample.

### Slide 7: Checked, and ready to try (40 seconds)

Finally, why the numbers can be trusted. The solver reproduces 67 of 67 reference values from the textbook, the course material and NIST. It passes all five stress tests of the assignment. I found and corrected eight errors of the AI-generated solver. And 441 automated tests run every time the code changes.

So, how hot is the porridge? For any reaction, at any temperature, the solver can now tell you, and whether it is just right. Let me show you the solver live.

---

## Part 2: The live demo (7 minutes)

*[Switch to the browser. It is on the Start page]*

### Tab 1: one reaction (2 minutes)

*[Click the card "Try to break it"]*

First, the balance check. Here methane plus oxygen gives CO2 and water, typed without coefficients. The solver refuses to calculate anything, says which elements do not balance, and offers the balanced form.

*[Pick "CO2 hydrogenation to methanol" from the list. The temperature is 523.15 K]*

Now the "too hot" bowl from the slides, at 523 K. The cards show ΔH° = −57.94 kJ/mol, so it gives out heat, ΔS° = −199.76 J/(mol·K), and ΔG° = +46.56 kJ/mol, so the reactants are favoured. That does not mean nothing reacts: some product still forms, only less.

*[Scroll to the graphs]*

The first graph shows the same three quantities against temperature, from 298.15 K up. Orange is ΔH°, blue is ΔG°. For this reaction ΔG° stays positive over the whole graph. The dashed lines show what the shortcuts would give. The bars show the sensible heat of each species, and the table under them gives every number of the calculation.

*[Pick "Methane steam reforming" from the list, type the temperature 1000 K and press Calculate]*

And the "just right" bowl: steam reforming at 1000 K has ΔG° = −27.03 kJ/mol, so the products are favoured. The explanation under the cards says that ΔG° changes sign at 893 K.

*[Type `CH4 + 2 O2 -> CO2 + 2 H2O` with the temperature 298.15 K and press Calculate]*

A last reaction: methane combustion, with water typed without a phase. The solver finds the boiling point of water from its own data, 373.2 K, and uses the phase that is stable at my temperature. At 298.15 K that is liquid water, and ΔH° is −890.65 kJ/mol. If I type H2O(g) on purpose, it keeps the vapour and gives −802.63 kJ/mol, the lower heating value.

### Tab 2: pressure (1 minute)

*[Click tab 2. It opens on ammonia synthesis at 723 K and 200 bar]*

For an ideal gas, H depends on temperature only, so the ideal-gas ΔH is −106.50 kJ/mol at any pressure. At 200 bar the real gas gives −111.55 kJ/mol, so it releases 4.7 % more heat. The difference is the residual enthalpy.

*[Scroll to the graphs]*

In the first graph the ideal gas is the flat line at zero, and the orange curve is the real-gas difference, which grows with pressure. In the second graph each bar is one gas. The tallest is ammonia: it is the gas closest to its critical point, so it is the furthest from an ideal gas.

### Tab 4: product slate (2 minutes 30 seconds)

*[Click tab 4. It opens on CO2 hydrogenation at 523 K and 50 bar, with "1. Everything allowed" selected]*

Let me start with a question. If I put CO2 and hydrogen into a reactor at 523 K and 50 bar, and wait until nothing changes any more, what comes out? Most of us would say methanol, because that is why we make this mixture.

Here I do not give the solver any reaction. I only say which species are allowed to exist: these switches. The solver then finds the mixture with the lowest total Gibbs energy that keeps every carbon, hydrogen and oxygen atom. A mixture settles where its Gibbs energy is lowest, like a ball rolling to the bottom of a valley.

*[Point at the bars "Where the C atoms go"]*

And the answer is not methanol. Methane takes 74.9 % of the carbon, and methanol almost nothing: the line under the bars says its mole fraction is 1.5 × 10⁻¹⁰. Why 74.9 and not 100? Because methane needs four hydrogens per CO2 and we fed only three, so the hydrogen runs out at 75 %.

*[Click "2. Methane off"]*

Now I switch methane off. That is what a selective catalyst does: it simply cannot make methane. Now methanol takes 20.6 % of the carbon, CO 7.5 %, and the rest stays as CO2. So thermodynamics prefers methane, and it is the catalyst that makes methanol possible.

*[Type 450 in the temperature box and press Enter]*

What if I cool the reactor? At 450 K methanol goes up to 45.9 %, because making methanol gives out heat.

*[Type 700 and press Enter]*

And if I heat it? At 700 K, CO takes 41.0 % and methanol almost nothing, because making CO from CO2 takes in heat.

*[Type 523 again, then drag the pressure slider to 100 bar]*

Last, pressure. At 100 bar methanol rises to 39.4 %, because the methanol reaction turns four moles of gas into two, and high pressure favours fewer moles.

So in one line: tab 4 shows what thermodynamics allows when reactions compete, and the switches show how much the catalyst decides.

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

To sum up: the solver does the full textbook method for any reaction, tells you whether it is too hot, too cold or just right at any temperature, shows what pressure does to real gases with the equation of state that fits each gas best, shows which products really form, and repeats our calorimeter lab. Every number is checked against the textbook. Thank you, and I am happy to take questions.

---

## If something goes wrong

- **The page says "Starting…" for long:** the first visit downloads Python once (about 10 MB). Switch to the spare address, or keep talking over slide 3 while it loads.
- **A tab shows an error box:** press Calculate again, or reload the page (Ctrl+R). The solver keeps no state, so nothing is lost.
- **No internet at all:** the page cannot load Python, so show the slides and quote the numbers from them (they are the solver's), and offer the report PDF.
- **Questions:** the study guide has the likely questions with answers, by topic.
