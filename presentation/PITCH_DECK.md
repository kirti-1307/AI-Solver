# Pitch deck brief: Thermodynamic Reaction Energy Solver

This file is the full content of a 7-slide pitch deck, slide by slide: the words on each slide, the picture or chart, and what I say (the speaker notes). It is written to be handed to Claude to design the deck.

## How to use this file

1. Open Claude and attach this file. If you want the exact graphs from the report, also attach `presentation/figure_slate.png` and `presentation/figure_calorimeter.png` (optional: the data for every chart are in the section "Data for the charts").
2. Ask: **"Design a light-theme pitch deck from this brief, one slide per section under 'The slides'. Keep every number and every word on the slides exactly as written, and put the 'What I say' text in the speaker notes."**
3. After the slides, I switch to the live demo (part 2 of `docs/PRESENTATION_SCRIPT.md`).

---

## The deck at a glance

| | |
|---|---|
| Presenter | Kirti Roshankumar Thakar, Roll No. 25A1CHEB0107 |
| Course | Chemical Engineering Thermodynamics, Assignment 2, Prof. M. Ali Haider |
| Audience | the professor and my classmates (chemical engineering students) |
| Length | 7 slides, about 6 minutes, then a live demo of the website |
| Goal | present the idea of the solver, opening with a story |
| Live site | https://ai-solver-seven.vercel.app/ and https://kirti-1307.github.io/AI-Solver/ |
| AI platform used | Claude |

**The story thread.** The deck opens with Goldilocks and the three bears: Goldilocks asks Baby Bear "How hot is the porridge?", and the answer is "too hot, too cold, just right". Every reaction has the same question: how much heat (ΔH°), and is it "just right" at this temperature, meaning are the products favoured (ΔG°)? The three bowls come back on slides 2 and 4, and the last slide closes the story.

---

## Design direction

- **Light theme on every slide.** No dark slides.
- **Colours** (hex):

| Use | Colour |
|---|---|
| Background | warm white `#FFFDF8` |
| Panels and cards | pale cream `#F5EFE3` or pale grey-blue `#EEF2F7` |
| Text and headings | navy `#16233A` |
| Second text (captions, footer) | slate `#5B6778` |
| Main accent, one key number per slide, "too hot" | orange `#C2410C` |
| "Too cold", second chart series | blue `#0B5CAD` |
| "Just right" only | green `#2F7D4A` |

- **Fonts.** Headings in a friendly serif (Cambria or similar), body in a clean sans (Calibri or similar). Slide 1 may use a storybook-style serif for the question.
- **The motif: three bowls.** A big, a medium and a small bowl of porridge, with steam lines. They are the picture on slide 1, the three quantities ΔH°, ΔS°, ΔG° on slide 2, and "too hot, too cold, just right" on slide 4. Keep them simple and flat (outline or soft fill), the same drawing every time.
- **Few words, big numbers.** One message per slide. Key numbers large (about 40 to 60 pt) with a short label under them.
- **Charts native** (editable), from the data at the end of this file.
- **Chemistry and symbols typed properly:** CO₂, H₂, CH₃OH, H₂O, CH₄, NH₃, ΔH°, ΔS°, ΔG°, Cₚ, Hᴿ. Units with a space: 46.6 kJ/mol, 893 K, 4.7 %.
- **Footer** on slides 2 to 7: "Thermodynamic Reaction Energy Solver · Assignment 2" on the left, the slide number on the right.
- **16:9.**

**Rules for the wording.** I have to be able to explain every word on the slides, so:

- Use the slide text as written. It may be shortened, but do not add facts, numbers or technical terms that are not in this file.
- Keep every number exactly as given (they are the solver's own results).
- Say "the reactants are favoured" or "the products are favoured", never "not favourable" or "not feasible".
- The standard state (°) is the pure species at 1 bar, at any temperature; 298.15 K is only the temperature of the tables. Do not write "standard conditions of 298 K".

---

## The slides

### Slide 1: The story (cover)

**Purpose:** a catchy opening. The picture fills the slide.

**Picture** (an original storybook illustration of the folk tale, not in the style of any film studio or existing book):

> A warm, light storybook illustration in a soft, flat watercolour style. Inside a cosy wooden cottage kitchen, Goldilocks, a young girl with golden curly hair, sits at a wooden table with three bowls of porridge: a big bowl with lots of steam, a medium bowl with no steam, and a small bowl with a little steam. Baby Bear, small and friendly, stands next to the table holding a kitchen thermometer. Goldilocks looks at Baby Bear and asks the question in a speech bubble. Light, airy colours: cream, honey, soft orange, soft blue. No other text in the picture.

**On the slide:**
- Speech bubble (Goldilocks): **How hot is the porridge?**
- Small labels under the bowls (optional): *too hot* (big bowl), *too cold* (medium bowl), *just right* (small bowl)
- A slim band along the bottom: **Thermodynamic Reaction Energy Solver** · Kirti Roshankumar Thakar · Roll No. 25A1CHEB0107

**What I say** (45 seconds):

Good morning. Before I start, a short story. You all know Goldilocks and the three bears. In my version, Goldilocks is a little more careful: before she eats, she asks Baby Bear one question. "How hot is the porridge?" And Baby Bear says: "Papa's bowl is too hot, Mama's is too cold, and mine is just right."

Notice that the bear did not give her a number. Whether it is too hot or just right depends on the temperature, and on what you want from it.

---

### Slide 2: Goldilocks' question, for every reaction

**Purpose:** connect the story to the project, and state the problem and the idea.

**Visual:** the three bowls in a row at the top, each labelled with a quantity. Below them, two columns: "The problem" (left) and "My idea" (right, in a card).

**On the slide:**

Title: **Goldilocks' question, for every reaction**

Three bowls:
- Big bowl: **ΔH°** · How hot? The heat the reaction gives out or takes in
- Medium bowl: **ΔS°** · The change in disorder
- Small bowl (green): **ΔG°** · Just right? Which side is favoured

The problem:
- The textbook tables answer it at one temperature only: 298.15 K.
- At any other temperature: a Cₚ integral for every species, a page of working each time.
- Shortcuts mislead: a constant ΔCₚ is 9.0 kJ/mol off on average at 1000 K, and up to 31.5 kJ/mol.

My idea:
- A solver that does the full textbook method for **any reaction at any temperature**, in a few seconds.
- It shows every step and plot, explains the result in plain words, and checks itself against the textbook.

**What I say** (1 minute):

As chemical engineers, we ask Goldilocks' question about every reaction. How hot: how much heat does the reaction give out or take in? That is ΔH°. And is it just right: at this temperature, are the products favoured? That is ΔG°, which comes from ΔH° and the entropy change ΔS°.

The problem is that the textbook tables give these numbers at one temperature only, 298.15 K. At any other temperature we need a heat-capacity integral for every species, which is a page of working for one reaction at one temperature. So people use shortcuts, like taking ΔCp as constant. For the 40 predefined reactions whose data reach 1000 K, that shortcut is off by 9.0 kJ/mol on average, and by up to 31.5 kJ/mol.

My idea was a solver that does the full textbook method every time, for any reaction at any temperature, in a few seconds. It shows every step and every plot, explains the result in plain words, and checks itself against the textbook.

---

### Slide 3: How it works

**Purpose:** the method in one picture.

**Visual:** five numbered step cards in a row, joined by arrows; step 4 in orange. Under them, one strip with the three main equations. Under that, three short facts.

**On the slide:**

Title: **How it works**

1. **Reaction:** 45 predefined, or type any reaction
2. **Balance check:** every element; an unbalanced reaction gets no numbers
3. **Data:** 57 species from the textbook's tables, NIST data only where the textbook has none
4. **Calculation:** Cₚ integrals → ΔH°, ΔS°, ΔG°; residual enthalpy for pressure
5. **Results:** numbers, plots, every step, a plain-word explanation

Equations strip:

    ΔH°(T) = ΔH°₂₉₈ + R ∫ (ΔCₚ°/R) dT        ΔG° = ΔH° − TΔS°        ΔH(T,P) = ΔH°(T) + Σ νᵢ Hᵢᴿ

Facts:
- Runs in any browser: the Python solver works inside the page
- Seven tabs, from one reaction to a whole reactor
- No server: nothing is sent anywhere

**What I say** (1 minute):

The user picks one of 45 predefined reactions, or types any reaction. First, the solver checks the balance of every element. An unbalanced reaction gets no numbers at all, only the balanced form as a suggestion.

Then it takes the data from its database: 57 species, mostly from the textbook's tables, with NIST data only where the textbook has none. It integrates the heat capacities from 298.15 K to the chosen temperature and gets ΔH°, ΔS° and ΔG°. For pressure, it adds the residual enthalpy of each gas from an equation of state.

Everything runs inside the browser. There is no server, so the page works anywhere.

---

### Slide 4: Too hot, too cold, just right

**Purpose:** the story's three bowls, with real reactions. The main result about temperature.

**Visual:** the three bowls again, as three cards side by side: orange "Too hot", blue "Too cold", green "Just right". Each card has the reaction, the temperature, and ΔG° as the big number.

**On the slide:**

Title: **Too hot, too cold, just right**

| Too hot (orange) | Too cold (blue) | Just right (green) |
|---|---|---|
| CO₂ + 3H₂ → CH₃OH + H₂O at 523 K | CH₄ + H₂O → CO + 3H₂ at 700 K | CH₄ + H₂O → CO + 3H₂ at 1000 K |
| **ΔG° = +46.6 kJ/mol** | **ΔG° = +47.9 kJ/mol** | **ΔG° = −27.0 kJ/mol** |
| Gives out heat (ΔH° = −57.9 kJ/mol), so heating favours the reactants | Takes in heat (ΔH° = +219.9 kJ/mol), and the reactants are still favoured | The products are favoured above 893 K, where ΔG° = 0 |

Bottom line: **For any reaction, the solver shows ΔG° at every temperature from 298.15 K up, and where it changes sign.**

**What I say** (1 minute):

So let's go back to the three bowls, with real reactions. Too hot: CO2 to methanol gives out heat, but it turns four moles of gas into two, so ΔS° is negative. At 523 K, ΔG° is +46.6 kJ/mol, so the reactants are favoured, and heating it more makes this worse. That does not mean nothing reacts: some methanol still forms, only less.

Too cold: steam reforming takes in heat. At 700 K, ΔG° is +47.9 kJ/mol, so the reactants are still favoured. Just right: the same reaction at 1000 K has ΔG° = −27.0 kJ/mol, so the products are favoured. The turning point is 893 K, where ΔG° is zero.

The solver shows this for any reaction, as a graph from 298.15 K up.

---

### Slide 5: Real gases at high pressure

**Purpose:** the pressure result, and why the solver chooses the equation of state.

**Visual:** left, one big stat with a short explanation. Right, a native horizontal bar chart (chart A).

**On the slide:**

Title: **Real gases at high pressure**

Left:
- Big number (orange): **4.7 %**
- Label: **more heat from real-gas ammonia at 723 K and 200 bar**
- Small text: −111.55 instead of −106.50 kJ/mol. The difference is the residual enthalpy of each gas, from an equation of state.

Right (chart A): **Average error against NIST measured residual enthalpy (kJ/mol)**, then under the chart:
- 24 gases, 380 measured points. Closest for each gas: Soave/Redlich/Kwong 14, Peng/Robinson 6, Redlich/Kwong 4.
- **So the solver, not the user, picks the equation for each gas.** (orange)

**What I say** (1 minute):

Real reactors also run at high pressure. For an ideal gas, H depends on temperature only, but a real gas is different. For ammonia synthesis at 723 K and 200 bar, the real gas releases 4.7 % more heat than the ideal gas: −111.55 instead of −106.50 kJ/mol. The difference is the residual enthalpy of each gas, which comes from an equation of state.

But which equation? I compared the five equations of the course with measured data from NIST, for 24 gases and 380 points. The chart shows the average error. No single equation is the best for every gas, so the solver, not the user, picks the closest one for each gas: Soave/Redlich/Kwong for 14 gases, Peng/Robinson for 6 and Redlich/Kwong for 4.

---

### Slide 6: Two extra features

**Purpose:** the two features beyond the assignment.

**Visual:** two cards side by side, each with a small icon tile, a title, a chart, and two or three short lines. Left chart: chart B (or `figure_slate.png`). Right chart: chart C (or `figure_calorimeter.png`).

**On the slide:**

Title: **Two extra features**

Left card, icon tile "G": **Product slate**
- The mixture with the lowest total Gibbs energy of the allowed species
- Methane takes 74.9 % of the carbon; with methane switched off, methanol takes 20.6 %
- **The catalyst decides what forms.** (orange)

Right card, icon tile "ΔU": **Bomb calorimeter**
- A closed vessel gives ΔU, not ΔH: ΔH = ΔU + Δn_gas RT (set "gas" as a subscript of Δn)
- Calibrated with benzoic acid: 3059.3 cal/°C
- **1 g of ethanol: 2.31 °C. It also names an unknown sample.** (orange)

**What I say** (1 minute):

On top of what the assignment asks, I added two features. The product slate is a live reactor. I only choose which species may exist, and the solver finds the mixture with the lowest total Gibbs energy. For CO2 and hydrogen at 523 K and 50 bar, methane takes 74.9 % of the carbon. If I switch methane off, like a selective catalyst would, methanol takes 20.6 %, and at 100 bar 39.4 %. So thermodynamics favours methane, and it is the catalyst that makes methanol possible.

The second feature answers Goldilocks' question quite literally: how hot does it get? It repeats our bomb calorimeter lab. The bomb is a closed vessel, so it measures ΔU and not ΔH. After a calibration with the benzoic acid run of the handout, it predicts the temperature rise of any fuel, 2.31 °C for 1 g of ethanol, and it can work backwards to name an unknown sample.

---

### Slide 7: Checked, and ready to try

**Purpose:** why the numbers can be trusted, the close of the story, and the hand-over to the demo.

**Visual:** four stat cards in a row (the first number in orange). Below, a small Baby Bear with the thermometer and the three bowls (a smaller copy of the slide 1 drawing), next to "Live demo now" and the links.

**On the slide:**

Title: **Checked, and ready to try**

| 67/67 | 5/5 | 8 | 441 |
|---|---|---|---|
| reference values from the textbook, the course and NIST | stress tests of the assignment passed | errors of the AI-generated solver found and corrected | automated tests run on every change |

- **Live demo now**
- ai-solver-seven.vercel.app · kirti-1307.github.io/AI-Solver · github.com/kirti-1307/AI-Solver

**What I say** (40 seconds):

Finally, why the numbers can be trusted. The solver reproduces 67 of 67 reference values from the textbook, the course material and NIST. It passes all five stress tests of the assignment. I found and corrected eight errors of the AI-generated solver. And 441 automated tests run every time the code changes.

So, how hot is the porridge? For any reaction, at any temperature, the solver can now tell you, and whether it is just right. Let me show you the solver live.

---

## Data for the charts

**Chart A (slide 5): average error of each equation of state against NIST measured residual enthalpy, kJ/mol** (24 gases, 380 points). Horizontal bars, smallest at the top. Soave/Redlich/Kwong in orange, Peng/Robinson in blue, the rest in a pale grey-blue. Show the values on the bars.

| Equation | Average error (kJ/mol) |
|---|---|
| Soave/Redlich/Kwong | 0.137 |
| Peng/Robinson | 0.160 |
| Redlich/Kwong | 0.510 |
| van der Waals | 1.246 |
| Virial | 1.349 |

**Chart B (slide 6, left): where the carbon goes, CO₂ + 3H₂ at 523 K** (share of carbon atoms, %). A 100 % stacked bar for each case: methane grey, methanol blue, CO orange, unreacted CO₂ pale grey-blue.

| Case | CH₄ | CH₃OH | CO | Unreacted CO₂ |
|---|---|---|---|---|
| Everything allowed, 50 bar | 74.9 | 0 | 0 | 25.1 |
| Methane off, 50 bar | 0 | 20.6 | 7.5 | 71.9 |
| Methane off, 100 bar | 0 | 39.4 | 3.5 | 57.0 |

**Chart C (slide 6, right): temperature rise in the lab bomb calorimeter for 1 g of each fuel, °C** (calorimeter constant 3059.3 cal/°C from the benzoic acid run). Vertical bars, ethanol in orange, the rest in blue, values on top.

| Fuel | Temperature rise (°C) |
|---|---|
| C₆H₁₂ (cyclohexane) | 3.63 |
| C₇H₈ (toluene) | 3.31 |
| C₆H₆ (benzene) | 3.26 |
| C (graphite) | 2.56 |
| C₂H₅OH (ethanol) | 2.31 |
| CH₃OH (methanol) | 1.77 |
| CH₃COOH (acetic acid) | 1.14 |

---

## Where every number comes from

All numbers are the solver's own results, so they match the website in the live demo.

| Number | Where to see it on the website |
|---|---|
| ΔG° = +46.6 kJ/mol, ΔH° = −57.9 kJ/mol (CO₂ to methanol, 523 K) | tab 1, "CO2 hydrogenation to methanol" at 523.15 K |
| ΔG° = +47.9 kJ/mol, ΔH° = +219.9 kJ/mol (steam reforming, 700 K) | tab 1, "Methane steam reforming" at 700 K |
| ΔG° = −27.0 kJ/mol (steam reforming, 1000 K); ΔG° = 0 at 893 K | tab 1, "Methane steam reforming" at 1000 K; the explanation says "ΔG° changes sign at 893 K" |
| 9.0 and 31.5 kJ/mol (constant ΔCₚ, 40 reactions at 1000 K) | tab 7, stress test 2 |
| 4.7 %, −111.55 and −106.50 kJ/mol (ammonia, 723 K, 200 bar) | tab 2, ammonia synthesis |
| Chart A; 14, 6 and 4 gases | tab 7, the equation of state check |
| 74.9 %, 20.6 %, 39.4 % (product slate) | tab 4, CO₂ + 3H₂ at 523 K, buttons and pressure slider |
| 3059.3 cal/°C, 2.31 °C (ethanol) | tab 5 |
| 67/67, 5/5, 8 | tab 7, and the report, section 6 |
| 441 tests | the test suite (`python -m unittest discover -s tests`) |

---

## Timing

| Slide | Time |
|---|---|
| 1. The story | 45 s |
| 2. Goldilocks' question, for every reaction | 1 min |
| 3. How it works | 1 min |
| 4. Too hot, too cold, just right | 1 min |
| 5. Real gases at high pressure | 1 min |
| 6. Two extra features | 1 min |
| 7. Checked, and ready to try | 40 s |
| **Slides in total** | **about 6.5 minutes** |
| Live demo (`docs/PRESENTATION_SCRIPT.md`, part 2) | 7 minutes |
