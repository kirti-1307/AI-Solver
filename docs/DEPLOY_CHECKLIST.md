# Deploy checklist: Thermodynamic Reaction Energy Solver v1.2

**Target:** GitHub Pages, served from the root of the `main` branch of `kirti-1307/AI-Solver`
**Live URL:** https://kirti-1307.github.io/AI-Solver/
**What ships:** a static site. `index.html`, `web/` and the Python package `thermosolver/`, which the browser runs through Pyodide. No server, no database, no secrets, no build step.

**What changed in v1.1:** the electrochemical tab is replaced by the heat lab (reactor energy balance and virtual bomb calorimeter), the product slate became a live reactor with sliders, and the page got a light/dark switch.

**What changed in v1.2:** a start page with question cards, a headline on the result of tab 1, one-line explanations behind a small "i" on every result card, a loading card, and a beginner's guide (`guide.html`, built from `docs/LEARNERS_GUIDE.md`).

Boxes are ticked only for what has actually been verified.

## Pre-deploy

- [x] All tests pass locally: `python -m unittest discover -s tests -t .`
- [x] Reference values all reproduced: `python -m thermosolver --validate`
- [x] Independent code review of the new code done and findings addressed (see [CODE_REVIEW.md](CODE_REVIEW.md), second review)
- [x] No known critical bug in the release (see [DEBUG_LOG.md](DEBUG_LOG.md))
- [x] Site works from a local static server (`python serve.py`): engine loads, all seven tabs render, no console errors
- [x] `.nojekyll` is present at the repository root. Without it GitHub Pages silently refuses to serve `thermosolver/__init__.py` and `__main__.py` (files starting with an underscore), and the solver cannot load.
- [x] The worker's file list in `web/worker.js` matches the files in `thermosolver/` that the solver imports
- [x] The `?v=` tag on the local scripts in `index.html` and on the worker in `web/ui.js` was raised for this release (a test checks that all of them agree), so no browser mixes old and new files
- [x] No secrets, tokens or personal data in the repository
- [x] Rollback plan written (below)

## Deploy

- [x] Commit and push to `main`
- [x] "pages build and deployment" workflow finished (Actions tab), usually one to two minutes
- [x] The `tests` workflow is green for all four Python versions

**Result, 22 November 2026, commit `ec82e15`:** both workflows finished with success.

## Smoke test on the live URL

- [x] Status pill turns green, "Solver ready"
- [x] Tab 1: default reaction shows ΔH°₂₉₈ = −48.97 kJ/mol for CO₂ + 3 H₂ → CH₃OH + H₂O
- [x] Tab 1: typing `CH4 + O2 -> CO2 + H2O` is rejected and offers the balanced form
- [x] Tab 2: ammonia synthesis at 723.15 K, 200 bar shows a negative Σ ν Hᴿ of about −5 kJ/mol
- [x] Tab 3: the first worked example reports agreement between the two routes
- [x] Tab 4: with CH₄ switched off at 523 K and 50 bar the CO₂ conversion is 25.2 %; dragging the temperature slider moves the bars
- [x] Tab 5, reactor: methane with 20 % excess air shows 2,066 K; the steam-reformer example shows a heat duty of +328.0 kJ
- [x] Tab 5, bomb calorimeter: 1 g of ethanol with the handout calibration shows a rise of 2.31 °C
- [x] Tab 7: every reference value reads "pass"
- [x] The "start here" buttons open the right tabs, and the light/dark switch repaints the page
- [x] v1.2: the start page shows nine cards and each opens its tab with a result
- [x] v1.2: tab 1 shows the headline ("Gives out heat", "Not favourable", "Balanced") and the "i" buttons open an explanation
- [x] v1.2: `guide.html` opens from the header and from the start page, with ten sections
- [x] The page is usable on a phone-width screen (tabs scroll sideways, tables scroll inside their panels)

**Result, 22 November 2026, on https://kirti-1307.github.io/AI-Solver/:** all eleven pass. What the live page showed:

| Check | Seen on the live page |
|---|---|
| Status | "Solver ready", no console errors, no failed downloads |
| Tab 1 | ΔH°₂₉₈ = −48.97 kJ/mol; the unbalanced reaction is rejected with the balanced form offered |
| Tab 2, ammonia, 723.15 K, 200 bar | Σ ν Hᴿ = −5.158 kJ/mol |
| Tab 3 | "the two routes agree" |
| Tab 4, CH₄ switched off, 50 bar | CO₂ conversion 25.2 % at 523 K; moving the slider to 600 K changed it to 27.6 % without a reload; four plots drawn on release |
| Tab 5, methane, 20 % excess air | 2,066 K |
| Tab 5, steam reformer | +328.0 kJ per mol CH₄ |
| Tab 5, bomb calorimeter, 1 g ethanol | rise 2.31 °C, calorific value 29.62 MJ/kg |
| Tab 7 | "57 of 57 reference values reproduced" (51 of 51 before v1.3), no "FAIL" |
| Theme switch | page background changed to dark and back |
| Phone width (375 px) | page does not scroll sideways; the tab bar and the tables scroll inside their own boxes |

The test was run in one browser (Chromium) in a background tab. There the animated calorimeter readout stayed at 0.00 although the result below it was right, because a background tab gets no animation frames. This was fixed (a timer now sets the final value) and the files were given version tags; see [DEBUG_LOG.md](DEBUG_LOG.md), items 17 to 19.

**Checked again after the review fixes, 22 November 2026, commit `b4a988a`, version tag 1.1.2:** both workflows green; on the live page the same values as in the table above (−48.97 kJ/mol, −5.158 kJ/mol, 25.2 %, 2,066 K, +328.0 kJ, 2.31 °C, 51 of 51), the temperature-limit card shows 97 % excess air for 1,500 K, and a hydrogen flame calculated right after a single-reactant reaction shows 2,252 K with the 20 % excess air that the page displays (review finding R2). No console errors, no failed downloads.

**v1.2 checked on the live page, 22 November 2026, commit `1e40f8e`, version tag 1.2.0:** both workflows green. The start page shows nine cards and the eight that run an example each produced a result (−57.94 kJ/mol headline, the rejected reaction, −5.158 kJ/mol, the Hess check, 25.2 %, 2,066 K, 2.31 °C, 51 of 51). Tab 1 shows six "i" buttons and the first opens "Heat of reaction at 298.15 K". `guide.html` loads with ten sections and the stylesheet of this release. No console errors, no failed downloads.

**v1.3 (heat capacities below 298.15 K, standard-state wording, headline):**

- [x] v1.3: tab 1, CO₂ + 3 H₂ → CH₃OH + H₂O at 250 K shows ΔH° = −46.77 kJ/mol, "Products favoured", K = 8.76, no extrapolation warning, and plots that start at 200 K
- [x] v1.3: the same reaction at 523.15 K shows "Reactants favoured ... Some product still forms" and −57.94 kJ/mol as before
- [x] v1.3: tab 6 lists "Heat capacities below 298.15 K (47 species ...)"
- [x] v1.3: tab 7 reports 57 of 57

**v1.3 checked on the live page, 22 November 2026, commit `b75fddb`, version tag 1.3.0:** both workflows green. Tab 1 at 250 K: ΔH° = −46.77 kJ/mol, "Products favoured", K = 8.76, the NIST note and no extrapolation warning, plots from 200 K. At 523.15 K: −57.94 kJ/mol and "Reactants favoured ... Some product still forms". Tab 6 lists the 47 species with heat capacities below 298.15 K. Tab 7: 57 of 57, the six new rows among them. `guide.html` shows the rewritten section 3 with the stylesheet of this release. No console errors.

**v1.4 (tab 2: ideal gas against real gas, no fugacity):**

- [x] v1.4: tab 2, ammonia at 723.15 K and 200 bar shows "Ideal gas: −106.50 kJ/mol", "Real gas: −111.66 kJ/mol", "Difference: −5.16 kJ/mol" and the three-step path
- [x] v1.4: the overview lists six reactions, CO₂ hydrogenation to methanol first (10.6 %), and a click on it loads the case
- [x] v1.4: the words "fugacity" and "φ" do not appear anywhere on tab 2

**v1.4 checked on the live page, 22 November 2026, commit `8588e64`, version tag 1.4.0:** both workflows green. Tab 2, ammonia at 723.15 K and 200 bar: "Ideal gas: −106.50 kJ/mol", "Real gas: −111.66 kJ/mol", "Difference: −5.16 kJ/mol, 4.84 %", the three steps (−0.76, −106.50, −4.40 kJ), four plots, 9 of 9 identities. The overview lists six reactions; a click on the first loads CO₂ hydrogenation to methanol at 50 bar (−57.94 against −64.06 kJ/mol, 10.56 %). No "fugacity" or "φ" on the tab or in the guide. Tab 7: 57 of 57. No console errors.

**v1.5 (tab 4: switches that show what they do):**

- [x] v1.5: tab 4 opens on CO₂ hydrogenation with the methanol and CO switches faded ("no effect now"), water "needed" and methane showing its share
- [x] v1.5: "Try this" step 2 (Methane off) gives the methanol and CO switches their shares and one line with the change in conversion
- [x] v1.5: a click on a faded switch does nothing; a click on methane changes the bars

**v1.5 checked on the live page, 22 November 2026, commit `f0f2a0a`, version tag 1.5.0:** both workflows green. Tab 4 opens at 523 K and 50 bar with methanol and CO faded ("no effect now"), water "needed" and methane at 74.8 % of C. A click on the faded methanol switch changed nothing. "Methane off" gave methanol 17.3 % and CO 7.9 % of C, conversion 25.2 %, with the line of the step under the switches. Switching methane back on reported "conversion of CO2(g) went from 25.2 % to 74.9 %". Four plots drawn. Tab 7: 57 of 57. No console errors.

**v1.5.1 (no fugacity symbol on tab 4):**

- [x] v1.5.1: the gas-model menu of tab 4 reads "Peng/Robinson (real gas)", and with that model the method line shows G^R/RT and no φ

**v1.5.1 checked on the live page, 22 November 2026, commit `1df7a95`, version tag 1.5.1:** both workflows green. The gas-model menu of tab 4 reads "Peng/Robinson (real gas)"; with that model the method line shows the term G^R/RT, and with the ideal gas it does not. None of the seven tabs shows the word "fugacity" or the symbol φ. No console errors.

## Before the classroom demonstration

- [ ] Open the live page once on the presentation laptop while on a good connection, so the Python runtime (about 10 MB) is already cached
- [ ] Check the classroom network can reach `cdn.jsdelivr.net` (Pyodide) and `cdn.plot.ly` (Plotly)
- [ ] Fallback if the network fails: `python serve.py` on the laptop still needs those two CDNs; with no internet at all, use `python -m thermosolver "..." --T ...` in a terminal, which needs nothing
- [ ] Decide what to demonstrate (suggested: the "start here" strip from left to right)
- [ ] Compare the two SVN Chapter 4 heat-balance examples with the printed book (see [DATA_SOURCES.md](DATA_SOURCES.md))

## Post-deploy

- [x] Put the live URL in the report
- [ ] Put the live URL in the repository's "About" box
- [ ] Tag the release: `git tag v1.1 && git push --tags`

## Rollback

There is no state to migrate, so rollback is a plain revert.

- **Trigger:** the status pill turns red on the live page, any reference value on tab 7 reads "FAIL", or a tab shows "Solver error".
- **Action:** `git revert <bad commit>` and push; Pages redeploys the previous version in a minute or two. The last v1.0 commit is `9bad90c`. If the page is needed immediately, run it locally with `python serve.py`.
- **Most likely causes and quick checks:**
  - Solver does not load on Pages but works locally → `.nojekyll` missing, or a new Python file was not added to `FILES` in `web/worker.js`.
  - Works for you but not for someone else → their browser cached an old file. Hard-reload (Ctrl+Shift+R).
  - Plots missing, numbers present → `cdn.plot.ly` blocked on that network.

## Release history

**v1.0, 21 November 2026, commit `7df9d71`.** Repository public, Pages build and the `tests` workflow (Python 3.10 to 3.13) green. All ten smoke tests of that version passed on the live URL in one browser (Chromium), including "47 of 47 textbook values reproduced" and the phone-width check.
