# Deploy checklist: Thermodynamic Reaction Energy Solver v1.1

**Target:** GitHub Pages, served from the root of the `main` branch of `kirti-1307/AI-Solver`
**Live URL:** https://kirti-1307.github.io/AI-Solver/
**What ships:** a static site. `index.html`, `web/` and the Python package `thermosolver/`, which the browser runs through Pyodide. No server, no database, no secrets, no build step.

**What changed in v1.1:** the electrochemical tab is replaced by the heat lab (reactor energy balance and virtual bomb calorimeter), the product slate became a live reactor with sliders, and the page got a "start here" strip and a light/dark switch.

Boxes are ticked only for what has actually been verified.

## Pre-deploy

- [x] All tests pass locally: `python -m unittest discover -s tests -t .`
- [x] Reference values all reproduced: `python -m thermosolver --validate`
- [ ] Independent code review of the new code done and findings addressed (see [CODE_REVIEW.md](CODE_REVIEW.md))
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
| Tab 7 | "51 of 51 reference values reproduced", no "FAIL" |
| Theme switch | page background changed to dark and back |
| Phone width (375 px) | page does not scroll sideways; the tab bar and the tables scroll inside their own boxes |

The test was run in one browser (Chromium) in a background tab. There the animated calorimeter readout stayed at 0.00 although the result below it was right, because a background tab gets no animation frames. This was fixed (a timer now sets the final value) and the files were given version tags; see [DEBUG_LOG.md](DEBUG_LOG.md), items 17 to 19.

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
