# Presentation script: Thermodynamic Reaction Energy Solver

About 12 minutes: 7.5 minutes on the nine slides (a Goldilocks story, then one slide for each tab of the website), a 4-minute live demo, and a short close. The words to say are in plain text, written to be spoken: short sentences, and a few questions to the class. What to do is in *italics* inside square brackets. Every number is what the solver shows, so it matches the screen.

The slides are designed from `presentation/PITCH_DECK.md`. A one-page sheet of pointers to keep beside you is `docs/SPEAKER_POINTERS.md`. For the questions afterwards, see the study guide (`docs/STUDY_GUIDE.md`).

**Before the class**

- Open the slides and start the slide show on slide 1.
- In the browser, open https://ai-solver-seven.vercel.app/ (spare: https://kirti-1307.github.io/AI-Solver/). Use only these two addresses: a Vercel link with extra letters in it is a frozen copy of an old version. Wait until the top right says **Solver ready**, which takes about ten seconds on the first visit.
- Check that tab 1 starts with "Pick a reaction or type your own. The solver calculates ΔH°, ΔS° and ΔG°…". If it shows a longer, older text, press **Ctrl+Shift+R** once.
- Go back to the **Start** page, keep the browser at 100 % zoom, and close every other tab.

**How to say it**

- Talk to the class, not to the screen. The slide only has pointers; you tell the story.
- When you ask a question, stop for two seconds and look at the class. It is fine if nobody answers.
- Say the numbers slowly. Round them if you like ("about 58 kJ per mole"); the slide has the exact value.
- If you lose your place, look at the pointer sheet: every slide has one line to start with.

---

## Part 1: The slides (7.5 minutes)

### Slide 1: How hot is each porridge? (50 seconds)

Good morning, everyone. I want to start with a story you all know. Goldilocks walks into the house of the three bears and finds three bowls of porridge. And she has one question: how hot is each porridge?

In the story, she finds out the hard way. She tastes them. Papa Bear's is too hot, Mama Bear's is too cold, and Baby Bear's is just right.

But what if she didn't have to burn her tongue? What if something could work it out for her? That's my project, a Thermodynamic Reaction Energy Solver. It works out ΔH, the heat a reaction gives out or takes in. And heat is what decides how hot something gets.

So let me show you, tab by tab, how the solver answers Goldilocks' question for chemical reactions.

### Slide 2: Tab 1 · Reaction (1 minute)

Tab 1 is where it all starts. You pick a reaction from the list, or you type your own.

Before anything else, the solver checks that every element balances. If it doesn't, you get no numbers, only the balanced version as a hint.

Then it gives you three numbers, at any temperature from 298.15 K up. ΔH°: how much heat. ΔS°: how the disorder changes. And ΔG°: which side is favoured.

Take CO2 to methanol at 523 K. ΔH° is −57.94 kJ/mol, so it gives out heat. But ΔG° is +46.56, so at this temperature the reactants are favoured.

### Slide 3: Tab 2 · Pressure and real gas (1 minute)

Now, real reactors don't run at 1 bar. So tab 2 asks: what does pressure do?

*[Short pause]*

For an ideal gas, the answer is nothing. Its H depends only on temperature.

But in a real gas the molecules attract each other, and the solver adds that effect for each gas. It's called the residual enthalpy. And the solver picks the equation of state for each gas by itself: the one that comes closest to measured data from NIST.

For ammonia at 723 K and 200 bar, the ideal gas gives −106.50 kJ/mol, and the real gas −111.55. That's 4.7 % more heat.

### Slide 4: Tab 3 · Combine reactions (45 seconds)

Tab 3 is Hess's law, which we all know from class. You add two or three reactions, each with a multiplier. A negative multiplier just flips a reaction around.

The solver adds them up, cancels whatever appears on both sides, and checks the sum against the direct answer.

For example, the reverse water-gas shift, +39.50, plus methanol synthesis, −97.44, gives −57.94 kJ/mol. That's exactly what tab 1 gave us for CO2 to methanol. Same answer, two routes.

### Slide 5: Tab 4 · Product slate (1 minute)

Tab 4 is my first extra feature, and it's my favourite. Let me ask you something. If I put CO2 and hydrogen into a reactor at 523 K and 50 bar, what comes out?

*[Pause, look at the class for two seconds]*

Most of you would say methanol, right?

In this tab I don't give the solver any reaction. I only choose which products are allowed, and it finds the mixture with the lowest total Gibbs energy.

And the answer is methane. Methane takes 74.9 % of the carbon. If I switch methane off, the way a selective catalyst would, methanol gets 20.6 %, and at 100 bar, 39.4 %. So thermodynamics prefers methane, and the catalyst is what gives us methanol. I'll show you this live in a minute.

### Slide 6: Tab 5 · Bomb calorimeter (1 minute)

Tab 5 is my second extra feature, and this is where Goldilocks finally gets a temperature. It's our bomb calorimeter lab, on screen.

First, it calibrates with the benzoic acid run from our handout: 3059.3 calories per degree.

Then it burns a sample. The bomb is a closed vessel, so it measures ΔU, not ΔH. And it turns that heat into a temperature rise.

1 g of ethanol: the temperature goes up by 2.31 °C. And it works backwards too. Give it a temperature rise, and it tells you which fuel you most likely burned.

### Slide 7: Tab 6 · Species data (30 seconds)

Tab 6 is the data behind everything. There are 57 species: gases, liquids and solids. The values come from our textbook's tables, and from NIST only where the textbook has nothing. Every number shows where it came from.

There's also a small calculator for warming one species. Heating one mole of methane from 298.15 K to 1000 K takes 38.49 kJ. That's Goldilocks warming her porridge, only with methane.

### Slide 8: Tab 7 · Validation (45 seconds)

And finally, the big question: can we trust these numbers?

Tab 7 runs every check live, in the browser, while you watch. 67 out of 67 reference values from the textbook, the course and NIST. All five stress tests of the assignment. And eight published reactions, within 0.5 kJ/mol.

Along the way, I found and fixed eight mistakes in the AI-generated code. And 441 automated tests run every time the code changes.

### Slide 9: So, how hot is the porridge? (30 seconds)

So, back to Goldilocks. How hot is the porridge? The solver tells her how much heat there is: that's ΔH. It tells her which side wins: that's ΔG. And with the calorimeter, it even turns that heat into degrees. No burnt tongues.

Let me quickly show you the solver live.

---

## Part 2: The live demo (4 minutes)

*[Switch to the browser. It is on the Start page]*

### Tab 1 (1 minute 30 seconds)

*[Click the card "Try to break it"]*

Let me try to break it first. This is methane burning, but I typed it without any numbers in front. Watch. The solver refuses to calculate. It tells me which elements don't balance, and it suggests the balanced version.

*[Pick "CO2 hydrogenation to methanol" from the list]*

Now the reaction from my slide. There's the −57.94 for ΔH°, and the +46.56 for ΔG°.

*[Scroll to the first graph]*

This graph shows the same numbers at every temperature. Orange is ΔH°, blue is ΔG°. See how the blue line stays above zero the whole way? That means the reactants are favoured over this whole range.

### Tab 4 (2 minutes)

*[Click tab 4. It opens with "1. Everything allowed"]*

Remember my question: what comes out of CO2 and hydrogen? Here's the answer. Methane, with 74.9 % of the carbon.

Why not 100 %? Because methane needs four hydrogens for every CO2, and we only fed three. So the hydrogen simply runs out at 75 %.

*[Click "2. Methane off"]*

Now I play the catalyst, and I switch methane off. Methanol jumps to 20.6 %, and CO gets 7.5 %.

*[Drag the pressure slider to 100 bar]*

And if I push the pressure up to 100 bar, methanol goes up to 39.4 %. Making methanol turns four moles of gas into two, so high pressure helps it.

*[Only if there is time: type 450 in the temperature box and press Enter]*

And if I cool it down to 450 K, methanol goes up to 64.3 %, because making methanol gives out heat.

### Tab 5 (30 seconds)

*[Click tab 5. Ethanol is selected. Press Ignite]*

And here's Goldilocks' thermometer. One gram of ethanol, and the temperature rises by 2.31 °C. Just like in our lab.

---

## Part 3: Close (15 seconds)

That's my solver. It answers Goldilocks' question, how much heat and how hot, for any reaction, and every number is checked against the textbook. Thank you! I'm happy to take any questions.

---

## If something goes wrong

- **The page says "Starting…" for long:** the first visit downloads Python once (about 10 MB). Switch to the spare address, or keep talking over the slides while it loads.
- **A tab shows an error box:** press Calculate again, or reload the page (Ctrl+R). The solver keeps no state, so nothing is lost.
- **The page looks older than expected:** press Ctrl+Shift+R once.
- **No internet at all:** the page cannot load Python. Skip the demo, say "the numbers on my slides come straight from the solver", and offer the report PDF.
- **Questions:** the study guide has the likely questions with answers, by topic.
