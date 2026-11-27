# Speaker pointers: keep this beside you

One block per slide: the line to start with, the points to cover, and the number to say. The full words are in the presentation script; this sheet is only to keep you on track.

## The slides (about 7.5 minutes)

### 1 · How hot is each porridge? (50 s)

- **Start:** "Good morning, everyone. I want to start with a story you all know."
- Three bowls. Her question: how hot is each porridge?
- She tastes: too hot, too cold, just right. Burnt tongue!
- My solver works it out instead: **ΔH = the heat** a reaction gives out or takes in
- Heat decides how hot something gets
- **Next:** "Let me show you, tab by tab."

### 2 · Tab 1, Reaction (1 min)

- **Start:** "Tab 1 is where it all starts."
- Pick a reaction or type your own
- Checks the element balance first; unbalanced → no numbers
- ΔH° heat · ΔS° disorder · ΔG° which side is favoured, from 298.15 K up
- **Say:** CO₂ → methanol, 523 K: ΔH° **−57.94** (gives out heat), ΔG° **+46.56** (reactants favoured)

### 3 · Tab 2, Pressure and real gas (1 min)

- **Start:** "Real reactors don't run at 1 bar."
- Ideal gas: pressure changes nothing (H depends on T only)
- Real gas: molecules attract → residual enthalpy Hᴿ, for each gas
- Solver picks the equation of state per gas, closest to NIST data
- **Say:** ammonia, 723 K, 200 bar: **−106.50 → −111.55** kJ/mol, **4.7 %** more heat

### 4 · Tab 3, Combine reactions (45 s)

- **Start:** "Tab 3 is Hess's law."
- Add 2 or 3 reactions with multipliers; negative = reversed
- Cancels what is on both sides; checks against the direct answer
- **Say:** **+39.50 + (−97.44) = −57.94** kJ/mol, same as tab 1. "Same answer, two routes."

### 5 · Tab 4, Product slate (1 min) · extra feature 1

- **Start:** "My first extra feature, and my favourite."
- **Ask:** "CO₂ and hydrogen, 523 K, 50 bar: what comes out?" *(pause)* "Methanol, right?"
- No reactions given: I choose the allowed products; lowest total Gibbs energy
- **Say:** methane **74.9 %** · methane off: methanol **20.6 %** · 100 bar: **39.4 %**
- Thermodynamics prefers methane; the catalyst gives us methanol
- "I'll show you live in a minute."

### 6 · Tab 5, Bomb calorimeter (1 min) · extra feature 2

- **Start:** "Here Goldilocks finally gets a temperature."
- Our lab on screen; calibrated with benzoic acid: **3059.3 cal/°C**
- Closed vessel → measures **ΔU, not ΔH**
- Heat → temperature rise; also works backwards (names the fuel)
- **Say:** 1 g ethanol → **2.31 °C**

### 7 · Tab 6, Species data (30 s)

- **Start:** "Tab 6 is the data behind everything."
- **57 species**; textbook tables, NIST only where needed; every value shows its source
- Calculator for warming one species
- **Say:** methane, 298.15 → 1000 K: **38.49 kJ**. "Goldilocks warming her porridge."

### 8 · Tab 7, Validation (45 s)

- **Start:** "The big question: can we trust these numbers?"
- Every check runs live in the browser
- **Say:** **67/67** reference values · **5/5** stress tests · 8 published reactions within **0.5 kJ/mol**
- **8** AI mistakes found and fixed · **441** automated tests

### 9 · So, how hot is the porridge? (30 s)

- **Start:** "So, back to Goldilocks."
- ΔH: how much heat · ΔG: which side wins · calorimeter: heat into degrees
- "No burnt tongues." → "Let me quickly show you the solver live."

## The demo (about 4 minutes)

1. **Tab 1:** card "Try to break it" → refused, balanced form offered. Pick "CO2 hydrogenation to methanol": **−57.94**, **+46.56**. Graph: blue ΔG° line stays above zero.
2. **Tab 4:** "1. Everything allowed": methane **74.9 %** (hydrogen runs out at 75 %: methane needs 4 H₂ per CO₂, we fed 3). "2. Methane off": methanol **20.6 %**, CO **7.5 %**. Pressure to 100 bar: **39.4 %** (4 moles of gas become 2). *If time:* 450 K → **64.3 %**.
3. **Tab 5:** Ignite ethanol → **2.31 °C**. "Goldilocks' thermometer."
4. **Close:** "It answers how much heat and how hot, for any reaction, checked against the textbook. Thank you! Happy to take questions."

## If they ask (one-line answers)

- **Is ΔH the temperature?** No. ΔH is heat (kJ/mol). The temperature follows from heat and heat capacity, ΔT = heat / heat capacity, which is what tab 5 does.
- **ΔG° is positive: does nothing react?** Some product still forms; there is just less product than reactant at equilibrium.
- **Why ΔU in the bomb?** Fixed volume, so no work is done: the heat released is ΔU. ΔH = ΔU + Δn_gas·RT.
- **Why does methane take only 74.9 %?** Hydrogen runs out: methane needs 4 H₂ per CO₂ and the feed has 3.
- **How does the solver choose the equation of state?** For each gas, the one closest to NIST measured data (SRK for 14 gases, PR for 6, RK for 4).
- **Why does pressure not change the ideal-gas ΔH?** U depends on T only and PV = RT, so H = U + RT depends on T only.
- **Don't know?** Say what you do know and where the solver shows it.
