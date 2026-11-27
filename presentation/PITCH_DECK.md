# Pitch deck brief: Thermodynamic Reaction Energy Solver

This file is the full content of a 9-slide deck: a Goldilocks opening, one slide for each of the seven tabs of the website, and a closing slide. For every slide it gives the words on the slide (short pointers), the picture, and what I say (the speaker notes). It is written to be handed to Claude to design the deck.

## How to use this file

1. Open Claude and attach this file. If you want the exact graphs from the report, also attach `presentation/figure_slate.png` and `presentation/figure_calorimeter.png` (optional: the data for every chart are in the section "Data for the charts").
2. Ask: **"Design a light-theme deck from this brief, one slide per section under 'The slides'. Keep every number and every word on the slides exactly as written, keep the pointers short, and put the 'What I say' text in the speaker notes."**
3. The words to say are also in `docs/PRESENTATION_SCRIPT.md`, and a one-page sheet of pointers to keep beside me is `docs/SPEAKER_POINTERS.md`.

---

## The deck at a glance

| | |
|---|---|
| Presenter | Kirti Roshankumar Thakar, Roll No. 25A1CHEB0107 |
| Course | Chemical Engineering Thermodynamics, Assignment 2, Prof. M. Ali Haider |
| Audience | the professor and my classmates (chemical engineering students) |
| Length | 9 slides, about 7.5 minutes, then a short live demo (about 4 minutes) |
| Goal | present the idea of the solver and what each tab does, opening with a story |
| Live site | https://ai-solver-seven.vercel.app/ and https://kirti-1307.github.io/AI-Solver/ (only these two addresses; they always show the latest version) |
| AI platform used | Claude |

**The story thread.** Goldilocks finds three bowls of porridge and asks: how hot is each porridge? In the story she finds out by tasting, and burns her tongue. The solver answers for her: it works out ΔH, the heat a reaction gives out or takes in, and heat is what decides how hot something gets. Each tab then answers a part of her question, and on slide 6 (the bomb calorimeter) the solver turns heat into an actual temperature rise. The last slide closes the story.

**A point to get right (I may be asked).** ΔH is heat, in kJ/mol, not a temperature. The temperature follows from the heat and the heat capacity: ΔT = heat / heat capacity, which is exactly what the calorimeter of tab 5 does. So the slides say "ΔH: how much heat", never "ΔH is the temperature".

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
| Main accent, the one key number per slide | orange `#C2410C` |
| Second accent, charts | blue `#0B5CAD` |

- **Fonts.** Headings in a friendly serif (Cambria or similar), body in a clean sans (Calibri or similar). Slide 1 may use a storybook-style serif for the question.
- **The motif: the tab tiles of the website.** Every tab slide has one square tile at the top left, like the cards on the website's start page: a big symbol with a small label under it, and the tab number above. Use the same tile shape on every slide:

| Slide | Tile symbol | Tile label |
|---|---|---|
| Tab 1 | ΔH | HEAT |
| Tab 2 | P | PRESSURE |
| Tab 3 | Σ | HESS |
| Tab 4 | G | SLATE |
| Tab 5 | ΔU | BOMB |
| Tab 6 | Cₚ | DATA |
| Tab 7 | ✓ | CHECK |

- **Layout of a tab slide:** the tile and the title at the top; three or four short pointers on the left; one "Example" box at the bottom with the key number in orange; on the right a small chart or a big number where this file gives one. Lots of white space.
- **A small bowl icon** (a bowl of porridge with steam lines) in the corner of the "Example" box of each tab slide, to keep the story going. Keep it small and simple.
- **Chemistry and symbols typed properly:** CO₂, H₂, CH₃OH, H₂O, CH₄, NH₃, ΔH°, ΔS°, ΔG°, Cₚ, Hᴿ. Units with a space: 46.56 kJ/mol, 723 K, 4.7 %.
- **Footer** on slides 2 to 9: "Thermodynamic Reaction Energy Solver · Assignment 2" on the left, the slide number on the right.
- **16:9.**

**Rules for the wording.** I have to be able to explain every word on the slides, so:

- Use the slide text as written. It may be shortened, but do not add facts, numbers or technical terms that are not in this file.
- Keep every number exactly as given (they are the solver's own results).
- Say "the reactants are favoured" or "the products are favoured", never "not favourable" or "not feasible".
- ΔH is heat, not temperature (see above).
- The standard state (°) is the pure species at 1 bar, at any temperature; 298.15 K is only the temperature of the tables.

---

## The slides

### Slide 1: How hot is each porridge? (cover)

**Purpose:** a catchy opening. The picture fills most of the slide.

**Picture** (an original storybook illustration of the folk tale, not in the style of any film studio or existing book):

> A warm, light storybook illustration in a soft, flat watercolour style. Inside a cosy wooden cottage kitchen, Goldilocks, a young girl with golden curly hair, sits at a wooden table with three bowls of porridge: a big bowl with lots of steam, a medium bowl with no steam, and a small bowl with a little steam. She looks puzzled and asks her question in a speech bubble. Beside the bowls stands a small, friendly open laptop whose screen shows "ΔH", answering her in a second speech bubble. Light, airy colours: cream, honey, soft orange, soft blue. No other text in the picture.

**On the slide:**
- Goldilocks' speech bubble: **How hot is each porridge?**
- The laptop's speech bubble: **Let me work out ΔH: the heat!**
- A slim band along the bottom: **Thermodynamic Reaction Energy Solver** · Kirti Roshankumar Thakar · Roll No. 25A1CHEB0107 · Prof. M. Ali Haider

**What I say** (50 seconds):

Good morning, everyone. I want to start with a story you all know. Goldilocks walks into the house of the three bears and finds three bowls of porridge. And she has one question: how hot is each porridge?

In the story, she finds out the hard way. She tastes them. Papa Bear's is too hot, Mama Bear's is too cold, and Baby Bear's is just right.

But what if she didn't have to burn her tongue? What if something could work it out for her? That's my project, a Thermodynamic Reaction Energy Solver. It works out ΔH, the heat a reaction gives out or takes in. And heat is what decides how hot something gets.

So let me show you, tab by tab, how the solver answers Goldilocks' question for chemical reactions.

---

### Slide 2: Tab 1 · Reaction

**Tile:** ΔH · HEAT

**On the slide:**

Title: **Tab 1 · Heat, entropy and Gibbs energy of a reaction**

- Pick a reaction, or type your own
- Checks the element balance first
- ΔH°, ΔS°, ΔG° at any temperature from 298.15 K
- Tells you: gives out or takes in heat? Which side is favoured?

Example box: CO₂ + 3H₂ → CH₃OH + H₂O at 523 K · **ΔH° = −57.94 kJ/mol** (gives out heat) · ΔG° = +46.56 kJ/mol (reactants favoured)

**What I say** (1 minute):

Tab 1 is where it all starts. You pick a reaction from the list, or you type your own.

Before anything else, the solver checks that every element balances. If it doesn't, you get no numbers, only the balanced version as a hint.

Then it gives you three numbers, at any temperature from 298.15 K up. ΔH°: how much heat. ΔS°: how the disorder changes. And ΔG°: which side is favoured.

Take CO2 to methanol at 523 K. ΔH° is −57.94 kJ/mol, so it gives out heat. But ΔG° is +46.56, so at this temperature the reactants are favoured.

---

### Slide 3: Tab 2 · Pressure and real gas

**Tile:** P · PRESSURE

**On the slide:**

Title: **Tab 2 · What does pressure change?**

- Ideal gas: ΔH does not change with pressure
- Real gas: adds the residual enthalpy Hᴿ of each gas
- The solver picks the equation of state for each gas, from measured NIST data

Right side, big number (orange): **4.7 %**, with the label: more heat from real-gas ammonia

Example box: N₂ + 3H₂ → 2NH₃ at 723 K and 200 bar · ideal gas −106.50 kJ/mol · **real gas −111.55 kJ/mol**

**What I say** (1 minute):

Now, real reactors don't run at 1 bar. So tab 2 asks: what does pressure do?

For an ideal gas, the answer is nothing. Its H depends only on temperature.

But in a real gas the molecules attract each other, and the solver adds that effect for each gas. It's called the residual enthalpy. And the solver picks the equation of state for each gas by itself: the one that comes closest to measured data from NIST.

For ammonia at 723 K and 200 bar, the ideal gas gives −106.50 kJ/mol, and the real gas −111.55. That's 4.7 % more heat.

---

### Slide 4: Tab 3 · Combine reactions

**Tile:** Σ · HESS

**On the slide:**

Title: **Tab 3 · Build a reaction from others (Hess's law)**

- Add two or three reactions, each with a multiplier
- A negative multiplier reverses a reaction
- The sum is checked against the direct answer

Example box: reverse water-gas shift (+39.50) + methanol synthesis (−97.44) = **−57.94 kJ/mol** at 523 K, the same as tab 1

**What I say** (45 seconds):

Tab 3 is Hess's law, which we all know from class. You add two or three reactions, each with a multiplier. A negative multiplier just flips a reaction around.

The solver adds them up, cancels whatever appears on both sides, and checks the sum against the direct answer.

For example, the reverse water-gas shift, +39.50, plus methanol synthesis, −97.44, gives −57.94 kJ/mol. That's exactly what tab 1 gave us for CO2 to methanol. Same answer, two routes.

---

### Slide 5: Tab 4 · Product slate (extra feature 1)

**Tile:** G · SLATE, with a small tag "extra feature 1"

**On the slide:**

Title: **Tab 4 · What actually forms?**

- You choose which products the catalyst may form
- The solver finds the mixture with the lowest total Gibbs energy
- Sliders for temperature and pressure

Right side: chart B (or `figure_slate.png`).

Example box: CO₂ + 3H₂ at 523 K and 50 bar · **methane 74.9 %** of the carbon · methane off: methanol 20.6 % · at 100 bar: 39.4 %

**What I say** (1 minute):

Tab 4 is my first extra feature, and it's my favourite. Let me ask you something. If I put CO2 and hydrogen into a reactor at 523 K and 50 bar, what comes out?

Most of you would say methanol, right?

In this tab I don't give the solver any reaction. I only choose which products are allowed, and it finds the mixture with the lowest total Gibbs energy.

And the answer is methane. Methane takes 74.9 % of the carbon. If I switch methane off, the way a selective catalyst would, methanol gets 20.6 %, and at 100 bar, 39.4 %. So thermodynamics prefers methane, and the catalyst is what gives us methanol. I'll show you this live in a minute.

---

### Slide 6: Tab 5 · Bomb calorimeter (extra feature 2)

**Tile:** ΔU · BOMB, with a small tag "extra feature 2"

**On the slide:**

Title: **Tab 5 · Our bomb calorimeter lab, on screen**

- Calibrated with benzoic acid: 3059.3 cal/°C
- A closed vessel measures ΔU, not ΔH
- Turns heat into a temperature rise
- Works backwards: names an unknown sample

Right side: chart C (or `figure_calorimeter.png`).

Example box: 1 g of ethanol → **2.31 °C** · and a small line: "Goldilocks finally gets her temperature"

**What I say** (1 minute):

Tab 5 is my second extra feature, and this is where Goldilocks finally gets a temperature. It's our bomb calorimeter lab, on screen.

First, it calibrates with the benzoic acid run from our handout: 3059.3 calories per degree.

Then it burns a sample. The bomb is a closed vessel, so it measures ΔU, not ΔH. And it turns that heat into a temperature rise.

1 g of ethanol: the temperature goes up by 2.31 °C. And it works backwards too. Give it a temperature rise, and it tells you which fuel you most likely burned.

---

### Slide 7: Tab 6 · Species data

**Tile:** Cₚ · DATA

**On the slide:**

Title: **Tab 6 · The data behind every number**

- 57 species: 42 gases, 7 liquids, 8 solids
- From the textbook's tables; NIST only where the textbook has none
- Every value shows its source
- A calculator for the heat to warm one species

Example box: 1 mol of methane, 298.15 K → 1000 K · **38.49 kJ**

**What I say** (30 seconds):

Tab 6 is the data behind everything. There are 57 species: gases, liquids and solids. The values come from our textbook's tables, and from NIST only where the textbook has nothing. Every number shows where it came from.

There's also a small calculator for warming one species. Heating one mole of methane from 298.15 K to 1000 K takes 38.49 kJ. That's Goldilocks warming her porridge, only with methane.

---

### Slide 8: Tab 7 · Validation

**Tile:** ✓ · CHECK

**On the slide:**

Title: **Tab 7 · Can we trust the numbers?**

- Every check runs live, in the browser
- Reference values, stress tests, published values

Four stat cards in a row (the first number in orange):

| 67/67 | 5/5 | 8 | 441 |
|---|---|---|---|
| reference values from the textbook, the course and NIST | stress tests of the assignment passed | errors of the AI-generated solver found and corrected | automated tests run on every change |

Small line under the cards: 8 published reactions agree within 0.5 kJ/mol.

**What I say** (45 seconds):

And finally, the big question: can we trust these numbers?

Tab 7 runs every check live, in the browser, while you watch. 67 out of 67 reference values from the textbook, the course and NIST. All five stress tests of the assignment. And eight published reactions, within 0.5 kJ/mol.

Along the way, I found and fixed eight mistakes in the AI-generated code. And 441 automated tests run every time the code changes.

---

### Slide 9: So, how hot is the porridge?

**Purpose:** close the story and hand over to the demo and the questions.

**Picture:** a smaller copy of the slide 1 drawing, now with Goldilocks happily eating from the small bowl, and the laptop beside her.

**On the slide:**

Title: **So, how hot is the porridge?**

- ΔH: how much heat
- ΔG: which side is favoured
- The calorimeter: heat turned into degrees

Bottom: **Live demo now** · ai-solver-seven.vercel.app · kirti-1307.github.io/AI-Solver · **Thank you!**

**What I say** (30 seconds):

So, back to Goldilocks. How hot is the porridge? The solver tells her how much heat there is: that's ΔH. It tells her which side wins: that's ΔG. And with the calorimeter, it even turns that heat into degrees. No burnt tongues.

Let me quickly show you the solver live.

---

## Data for the charts

**Chart B (slide 5): where the carbon goes, CO₂ + 3H₂ at 523 K** (share of carbon atoms, %). A 100 % stacked bar for each case: methane grey, methanol blue, CO orange, unreacted CO₂ pale grey-blue.

| Case | CH₄ | CH₃OH | CO | Unreacted CO₂ |
|---|---|---|---|---|
| Everything allowed, 50 bar | 74.9 | 0 | 0 | 25.1 |
| Methane off, 50 bar | 0 | 20.6 | 7.5 | 71.9 |
| Methane off, 100 bar | 0 | 39.4 | 3.5 | 57.0 |

**Chart C (slide 6): temperature rise in the lab bomb calorimeter for 1 g of each fuel, °C** (calorimeter constant 3059.3 cal/°C from the benzoic acid run). Vertical bars, ethanol in orange, the rest in blue, values on top.

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
| ΔH° = −57.94 kJ/mol, ΔG° = +46.56 kJ/mol (CO₂ to methanol, 523 K) | tab 1, "CO2 hydrogenation to methanol" at 523.15 K |
| −106.50, −111.55 kJ/mol, 4.7 % (ammonia, 723 K, 200 bar) | tab 2, it opens on ammonia synthesis |
| +39.50 + (−97.44) = −57.94 kJ/mol | tab 3, the first worked example |
| 74.9 %, 20.6 %, 39.4 % (product slate) | tab 4, buttons "1. Everything allowed" and "2. Methane off", pressure slider at 100 bar |
| 3059.3 cal/°C, 2.31 °C (ethanol) | tab 5, Ignite |
| 57 species, 38.49 kJ (methane, 298.15 K to 1000 K) | tab 6, the database and the sensible-heat calculator |
| 67/67, 5/5, 0.5 kJ/mol | tab 7 |
| 8 errors, 441 tests | the report (section 6) and the test suite |

---

## Timing

| Slide | Time |
|---|---|
| 1. How hot is each porridge? | 50 s |
| 2. Tab 1 · Reaction | 1 min |
| 3. Tab 2 · Pressure and real gas | 1 min |
| 4. Tab 3 · Combine reactions | 45 s |
| 5. Tab 4 · Product slate | 1 min |
| 6. Tab 5 · Bomb calorimeter | 1 min |
| 7. Tab 6 · Species data | 30 s |
| 8. Tab 7 · Validation | 45 s |
| 9. So, how hot is the porridge? | 30 s |
| **Slides in total** | **about 7.5 minutes** |
| Live demo (`docs/PRESENTATION_SCRIPT.md`, part 2) | about 4 minutes |
