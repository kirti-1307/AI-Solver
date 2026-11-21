# Deploy checklist: Thermodynamic Reaction Energy Solver v1.0

**Target:** GitHub Pages, served from the root of the `main` branch of `kirti-1307/AI-Solver`
**Live URL:** https://kirti-1307.github.io/AI-Solver/
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

- [x] Commit and push to `main`
- [x] GitHub repository → Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`
- [x] Wait for the "pages build and deployment" workflow to finish (Actions tab), usually one to two minutes
- [x] The `tests` workflow is green for all four Python versions

**Result, 21 November 2026, commit `7df9d71`:** the repository is public, "pages build and deployment" finished with success, and the `tests` workflow passed on Python 3.10, 3.11, 3.12 and 3.13.

## Smoke test on the live URL

Do these on the hosted page, in a normal browser window and once more in a private window (to test a cold cache):

- [x] Status pill turns green, "Solver ready"
- [x] Tab 1: default reaction shows ΔH°₂₉₈ = −48.97 kJ/mol for CO₂ + 3 H₂ → CH₃OH + H₂O
- [x] Tab 1: typing `CH4 + O2 -> CO2 + H2O` is rejected and offers the balanced form
- [x] Tab 1: `CO + 2 H2 -> CH3OH` at 1073.15 K gives ΔH° = −103.57 kJ/mol
- [x] Tab 2: ammonia synthesis at 723.15 K, 200 bar shows a negative Σ ν Hᴿ of about −5 kJ/mol
- [x] Tab 3: the first worked example reports agreement between the two routes
- [x] Tab 4: CO₂ hydrogenation example draws the mole-fraction plot
- [x] Tab 5: hydrogen fuel cell at 1073.15 K shows about 0.98 V
- [x] Tab 7: every textbook benchmark reads "pass"
- [x] The page is usable on a phone-width screen (tabs scroll sideways, tables scroll inside their panels)

**Result, 21 November 2026, on https://kirti-1307.github.io/AI-Solver/ (commit `7df9d71`):** all ten pass. What the live page showed:

| Check | Seen on the live page |
|---|---|
| Status | "Solver ready", no console errors, no failed downloads |
| Tab 1, default reaction | ΔH°₂₉₈ = −48.97 kJ/mol, ΔH°(523 K) = −57.94 kJ/mol, K = 2.244 × 10⁻⁵ |
| Tab 1, unbalanced reaction | "Reaction rejected", H and O imbalance listed, balanced form CH₄ + 2 O₂ → CO₂ + 2 H₂O offered |
| Tab 1, methanol synthesis at 1073.15 K | ΔH° = −103.57 kJ/mol (ΔH°₂₉₈ = −90.14 kJ/mol) |
| Tab 2, ammonia, 723.15 K, 200 bar, Peng/Robinson | Σ ν Hᴿ = −5.158 kJ/mol, ΔH(T,P) = −111.662 kJ/mol |
| Tab 3, first worked example | "the two routes agree to 7.3 × 10⁻¹² J/mol" |
| Tab 4, CO₂ hydrogenation | mole-fraction plot drawn with six species, plus the three other plots |
| Tab 5, hydrogen fuel cell, 1073.15 K | reversible voltage 0.977 V, ideal efficiency 75.9 % |
| Tab 7 | "47 of 47 textbook values reproduced", no "FAIL" anywhere |
| Phone width (375 px) | page does not scroll sideways; the tab bar and the tables scroll inside their own boxes |

The test was run in one browser (Chromium). It was the first time that browser had opened the address, so it was a cold load, but a private window and a second browser were not tried.

## Before the classroom demonstration

- [ ] Open the live page once on the presentation laptop while on a good connection, so the Python runtime (about 10 MB) is already cached
- [ ] Check the classroom network can reach `cdn.jsdelivr.net` (Pyodide) and `cdn.plot.ly` (Plotly)
- [ ] Fallback if the network fails: `python serve.py` on the laptop still needs those two CDNs; with no internet at all, use `python -m thermosolver "..." --T ...` in a terminal, which needs nothing
- [ ] Decide the two reactions to demonstrate (suggested: CO₂ hydrogenation to methanol on tabs 1, 2 and 4; hydrogen oxidation on tabs 1 and 5)

## Post-deploy

- [x] Put the live URL in the report
- [ ] Put the live URL in the repository's "About" box
- [ ] Tag the release: `git tag v1.0 && git push --tags`

## Rollback

There is no state to migrate, so rollback is a plain revert.

- **Trigger:** the status pill turns red on the live page, any benchmark on tab 7 reads "FAIL", or a tab shows "Solver error".
- **Action:** `git revert <bad commit>` and push; Pages redeploys the previous version in a minute or two. If the page is needed immediately, run it locally with `python serve.py`.
- **Most likely causes and quick checks:**
  - Solver does not load on Pages but works locally → `.nojekyll` missing, or a new Python file was not added to `FILES` in `web/worker.js`.
  - Works for you but not for someone else → their browser cached an old file. Hard-reload (Ctrl+Shift+R).
  - Plots missing, numbers present → `cdn.plot.ly` blocked on that network.
