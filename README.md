# Thermodynamic Reaction Energy Solver

An interactive solver for the energetics of chemical reactions: heat of reaction, entropy change, Gibbs energy and equilibrium constant as functions of temperature and pressure. Built for Assignment 2 of the Chemical Engineering Thermodynamics course (Prof. M. Ali Haider), on the data and equations of Smith, Van Ness & Abbott, *Introduction to Chemical Engineering Thermodynamics* (SVN).

**Live app:** https://kirti-1307.github.io/AI-Solver/ (GitHub Pages) and https://ai-solver-seven.vercel.app/ (Vercel). Both serve the same files from the `main` branch.

The page needs no installation. The first visit takes about ten seconds while the browser downloads the Python runtime; after that everything is instant.

**New to the solver?** Read the beginner's guide, which explains every idea and every tab in plain words: [docs/LEARNERS_GUIDE.md](docs/LEARNERS_GUIDE.md), also on the site at https://kirti-1307.github.io/AI-Solver/guide.html

**Presenting it?** The seven-slide, light-theme deck that opens with Goldilocks and the three bears is written out slide by slide in [presentation/PITCH_DECK.md](presentation/PITCH_DECK.md) (an older six-slide deck is in [presentation/Thermo_Solver_Presentation.pptx](presentation/Thermo_Solver_Presentation.pptx)), the words to say and what to click in [docs/PRESENTATION_SCRIPT.md](docs/PRESENTATION_SCRIPT.md), and the preparation notes with viva questions and answers in [docs/STUDY_GUIDE.md](docs/STUDY_GUIDE.md) (both also as PDF next to them).

## What it does

| Tab | What you get |
|---|---|
| Start | "What do you want to find out?" Nine question cards, each of which opens the right tab with a worked example. |
| 1 · Reaction | ΔH°, ΔS° and ΔG° at any temperature for 45 predefined reactions or your own. Elemental balance check, exothermic/endothermic label, sensible heat of each species, step-by-step working, plots against temperature, plain-language explanation, and a line under every graph on how to read it. The solver also works out K and the equilibrium conversion; since v1.8.5 neither is shown on this tab. A box lets the solver pick the stable phase (liquid or vapour) itself: it finds the boiling point from its own data, and the ΔH° plot then shows the latent heat as a step. |
| 2 · Pressure & real gas | The ideal-gas heat of reaction next to the real-gas one at constant temperature: ΔH(T,P) = ΔH°(T) + Σ νᵢHᵢᴿ. The residual part is shown as a three-step path, species by species, against pressure and against temperature, and an overview of six industrial reactions sorted by how much pressure matters. The user does not pick the equation of state: for each gas the solver uses the one of the five course equations (generalized virial, van der Waals, Redlich/Kwong, SRK, Peng/Robinson) whose residual enthalpy is closest to measured NIST data (24 gases, 380 points; SRK for gases without data). Tab 4 uses the same choice. |
| 3 · Combine reactions | Add and subtract two or more reactions with multipliers (Hess's law). The net reaction is evaluated two ways and the difference is shown. |
| 4 · Product slate (extra feature) | A live equilibrium reactor: competing reactions by Gibbs-energy minimisation. Drag temperature, pressure and feed ratio and the mixture follows; switch a product off to mimic a selective catalyst. Each switch shows the share its product holds; a switch that would change nothing at the current settings is faded, and a short "Try this" sequence walks through the example. |
| 5 · Bomb calorimeter (extra feature) | A virtual bomb calorimeter that follows the course lab: calibration with benzoic acid, the temperature rise of a known fuel, or the closest fuels for a measured rise, with ΔU, ΔH, HHV and LHV. The solver also has an energy balance around a reactor (flame temperature, heat to add or remove, condensing water); it is not shown on the page since v1.8.4. |
| 6 · Species data | The full database (57 species) with the source of every entry, and a sensible-heat calculator for one species. |
| 7 · Validation | The solver against the textbook's worked examples, the course slides and the lab handout, the assignment's five AI-error stress tests, and published research values, all computed live. |

## Why you can trust the numbers

- **Traceable data.** 54 of the 57 species use SVN Tables B.1 and C.1 to C.4 only. The other three (hydrogen peroxide gas, acetic acid vapour, and the heat capacity of liquid acetic acid) are not in SVN and come from the NIST Chemistry WebBook; they are labelled wherever they appear. See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
- **Checked against the book.** The solver reproduces the numbers printed in SVN's worked examples, for instance ΔH° = −103,566 J for methanol synthesis at 800 °C and K = 2.942 × 10⁻³ for ethylene hydration at 320 °C.
- **Self-auditing.** Each result is re-derived through an independent thermodynamic identity (Kirchhoff, van 't Hoff, Gibbs-Helmholtz and others) and the outcome is shown under the result.
- **Honest about limits.** Unbalanced reactions are rejected. Heat-capacity correlations used outside their range raise a warning. Species that would condense at the chosen pressure are flagged.

Every equation, with the SVN section it comes from and the function that implements it: [docs/THEORY.md](docs/THEORY.md).

## Run it on your own computer

You need Python 3.9 or newer. Nothing else has to be installed.

```
python serve.py
```

Then open http://localhost:8000. (An internet connection is still needed for the plotting library and the in-browser Python runtime.)

Use the solver without the web page:

```
python -m thermosolver "CO + 2 H2 -> CH3OH(g)" --T 1073.15
python -m thermosolver "N2 + 3 H2 -> 2 NH3" --T 723.15 --P 200 --model pr
python -m thermosolver --validate
```

Or from Python:

```python
from thermosolver import Reaction

rxn = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
rxn.dH(1073.15)     # -103565.95 J/mol   (SVN: -103,566)
rxn.K(523.15)       # equilibrium constant at 250 C
```

## Run the tests

```
python -m unittest discover -s tests -t .
```

The test strategy is described in [docs/TESTING.md](docs/TESTING.md), and the bugs found along the way in [docs/DEBUG_LOG.md](docs/DEBUG_LOG.md).

## How it is built

```
index.html, web/        the page: forms, tables, plots (no thermodynamics in JavaScript)
guide.html              the beginner's guide as a page, built from docs/LEARNERS_GUIDE.md
thermosolver/           the solver, pure Python, standard library only
    data.py             SVN tables, transcribed
    heatcap.py          Cp polynomial and its integrals
    species.py          species objects and name lookup
    reaction.py         parsing, elemental balance, ΔH°, ΔS°, ΔG°, K
    realgas.py          virial and cubic equations of state, residual properties
    combine.py          Hess's-law combination of reactions
    equilibrium.py      single-reaction equilibrium and Gibbs minimisation
    heatbalance.py      heat lab: reactor energy balance and bomb calorimeter
    audit.py            consistency checks
    benchmarks.py       reference values the solver must reproduce
    literature.py       published research values for comparison
    api.py              JSON interface used by the page
tests/                  automated tests (unittest)
docs/                   beginner's guide, presentation script, study guide (build_print.py makes their PDFs), theory, data sources, testing, debug log, review, deploy checklist
presentation/           the six slides (make_slides.py builds them with python-pptx)
report/                 the two-page assignment report (Word and PDF; make_pdf.ps1 makes the PDF from the Word file)
```

The web page runs the *same* Python files in the browser through [Pyodide](https://pyodide.org) (Python compiled to WebAssembly), inside a web worker. So the numbers on the hosted page are produced by exactly the code the tests exercise.

## Limitations

- Heat capacities are valid from 200 K to 1000-3000 K for gases (SVN from 298 K upwards, NIST tables from 200 K to 298.15 K) and from 273 to 373 K for liquids. For eight flame gases (N2, O2, CO2, H2O, CO, H2, SO2, NO) NIST equations extend the range to 6000 K. Outside these ranges the solver extrapolates and warns. Tab 1 starts at 298.15 K and accepts no lower temperature. The standard state fixes the pressure at 1 bar, not the temperature; a gas used below its boiling point is the hypothetical ideal gas, and the solver says so.
- Phase change is covered at 1 bar for the six substances whose liquid and gas data reproduce the boiling point (water, methanol, ethanol, benzene, cyclohexane, toluene): tab 1 picks the stable phase for any of them typed without a phase, and keeps a phase that is typed. Not covered: acetic acid (its data put the boiling point 43 K too high), melting and solids, and liquid mixtures (two liquids are taken as separate pure phases). On tabs 2 and 4 a species that would condense at high pressure is still only flagged.
- Pressure effects use pure-species residual properties (ideal-solution mixing). Solids and liquids are taken as incompressible.
- Hydrogen peroxide is available as a gas only (NIST data) and, having no critical constants in SVN Table B.1, is treated as an ideal gas under pressure. Liquid acetic acid has a constant heat capacity that is valid from 290 to 320 K only, and acetic acid vapour is the ideal-gas monomer (the real vapour is partly dimerised).
- The reactor energy balance of the solver (not shown on the page) takes the reaction to the conversion you set and ignores dissociation, so flame temperatures above about 2000 K are higher than real ones.
- Equilibrium results say where a reaction can go, not how fast.

## Data sources

- Smith, J. M., Van Ness, H. C., Abbott, M. M., *Introduction to Chemical Engineering Thermodynamics*, McGraw-Hill: Table B.1 (characteristic properties of pure species), Tables C.1 to C.3 (heat capacities), Table C.4 (standard enthalpies and Gibbs energies of formation at 298.15 K). This is the source for everything the textbook covers.
- NIST Chemistry WebBook, NIST Standard Reference Database 69 (webbook.nist.gov), for hydrogen peroxide gas and acetic acid, which the textbook does not fully cover.
- CODATA Key Values for Thermodynamics, for the entropies of the elements.
