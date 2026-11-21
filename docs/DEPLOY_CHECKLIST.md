# Deploy checklist: Thermodynamic Reaction Energy Solver v1.0

**Target:** GitHub Pages, served from the root of the `main` branch of `kirti-1307/AI-Solver`
**Live URL after deploy:** https://kirti-1307.github.io/AI-Solver/
**What ships:** a static site. `index.html`, `web/` and the Python package `thermosolver/`, which the browser runs through Pyodide. No server, no database, no secrets, no build step.

Boxes are ticked only for what has actually been verified.

## Pre-deploy

- [x] All tests pass locally: `python -m unittest discover -s tests -t .`
- [x] Textbook benchmarks all reproduced: `python -m thermosolver --validate`
- [x] Independent code review done and findings addressed (see [CODE_REVIEW.md](CODE_REVIEW.md))
- [x] No known critical bug in the release (see [DEBUG_LOG.md](DEBUG_LOG.md))
- [x] Data file verified against the printed SVN tables (see [DATA_SOURCES.md](DATA_SOURCES.md))
- [x] Site works from a local static server (`python serve.py`): engine loads, all seven tabs render, no console errors
- [x] `.nojekyll` is present at the repository root. Without it GitHub Pages silently refuses to serve `thermosolver/__init__.py` and `__main__.py` (files starting with an underscore), and the solver cannot load.
- [x] The worker's file list in `web/worker.js` matches the files in `thermosolver/` that the solver imports
- [x] No secrets, tokens or personal data in the repository
- [x] `.gitignore` keeps the course PDF and local tooling out of the repository
- [x] Rollback plan written (below)

## Deploy

- [ ] Commit and push to `main`
- [ ] GitHub repository → Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`
- [ ] Wait for the "pages build and deployment" workflow to finish (Actions tab), usually one to two minutes
- [ ] The `tests` workflow is green for all four Python versions

## Smoke test on the live URL

Do these on the hosted page, in a normal browser window and once more in a private window (to test a cold cache):

- [ ] Status pill turns green, "Solver ready"
- [ ] Tab 1: default reaction shows ΔH°₂₉₈ = −48.97 kJ/mol for CO₂ + 3 H₂ → CH₃OH + H₂O
- [ ] Tab 1: typing `CH4 + O2 -> CO2 + H2O` is rejected and offers the balanced form
- [ ] Tab 1: `CO + 2 H2 -> CH3OH` at 1073.15 K gives ΔH° = −103.57 kJ/mol
- [ ] Tab 2: ammonia synthesis at 723.15 K, 200 bar shows a negative Σ ν Hᴿ of about −5 kJ/mol
- [ ] Tab 3: the first worked example reports agreement between the two routes
- [ ] Tab 4: CO₂ hydrogenation example draws the mole-fraction plot
- [ ] Tab 5: hydrogen fuel cell at 1073.15 K shows about 0.98 V
- [ ] Tab 7: every textbook benchmark reads "pass"
- [ ] The page is usable on a phone-width screen (tabs scroll sideways, tables scroll inside their panels)

## Before the classroom demonstration

- [ ] Open the live page once on the presentation laptop while on a good connection, so the Python runtime (about 10 MB) is already cached
- [ ] Check the classroom network can reach `cdn.jsdelivr.net` (Pyodide) and `cdn.plot.ly` (Plotly)
- [ ] Fallback if the network fails: `python serve.py` on the laptop still needs those two CDNs; with no internet at all, use `python -m thermosolver "..." --T ...` in a terminal, which needs nothing
- [ ] Decide the two reactions to demonstrate (suggested: CO₂ hydrogenation to methanol on tabs 1, 2 and 4; hydrogen oxidation on tabs 1 and 5)

## Post-deploy

- [ ] Put the live URL in the report and in the repository's "About" box
- [ ] Tag the release: `git tag v1.0 && git push --tags`

## Rollback

There is no state to migrate, so rollback is a plain revert.

- **Trigger:** the status pill turns red on the live page, any benchmark on tab 7 reads "FAIL", or a tab shows "Solver error".
- **Action:** `git revert <bad commit>` and push; Pages redeploys the previous version in a minute or two. If the page is needed immediately, run it locally with `python serve.py`.
- **Most likely causes and quick checks:**
  - Solver does not load on Pages but works locally → `.nojekyll` missing, or a new Python file was not added to `FILES` in `web/worker.js`.
  - Works for you but not for someone else → their browser cached an old file. Hard-reload (Ctrl+Shift+R).
  - Plots missing, numbers present → `cdn.plot.ly` blocked on that network.
