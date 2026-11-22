"""Benchmarks: the solver against numbers printed in Smith, Van Ness & Abbott
(and cases from the course lecture slides and the bomb-calorimeter handout).

The same list feeds the automated tests and the "Validation" tab of the web
app, so the comparison the professor sees on screen is the comparison the
test-suite enforces.

Each benchmark is (group, description, expected value, computed value, unit,
relative tolerance). Expected values are quoted to the digits printed in the
book, so the tolerance reflects the book's rounding.
"""

from __future__ import annotations

from typing import Callable, List

from .constants import R, T0
from . import heatbalance
from .equilibrium import gibbs_minimize
from .heatcap import icph
from .reaction import Reaction
from .realgas import cubic_Z_roots, residual
from .species import SPECIES


def _svn_gibbs_example() -> dict:
    """SVN Gibbs-minimisation example: CH4/H2O/CO/CO2/H2 at 1000 K, 1 bar,
    feed 2 mol CH4 + 3 mol H2O, with the dGf(1000 K) values quoted in the book.
    Elements have dGf = 0 at every temperature, so H2 gets zero."""
    T = 1000.0
    dGf = {"CH4(g)": 19720.0, "H2O(g)": -192420.0, "CO(g)": -200240.0,
           "CO2(g)": -395790.0, "H2(g)": 0.0}
    g_rt = {sid: v / (R * T) for sid, v in dGf.items()}
    return gibbs_minimize(list(dGf), {"CH4(g)": 2.0, "H2O(g)": 3.0}, T, 1.0,
                          model="ideal", g_rt_override=g_rt)


def build() -> List[dict]:
    rows: List[dict] = []

    def add(group: str, description: str, expected: float, computed: Callable[[], float],
            unit: str, rel_tol: float, source: str) -> None:
        try:
            value = computed()
            error = None
        except Exception as exc:  # a benchmark must never crash the page
            value, error = None, str(exc)
        if value is None:
            passed, rel = False, None
        else:
            rel = abs(value - expected) / abs(expected) if expected else abs(value)
            passed = rel <= rel_tol
        rows.append({
            "group": group, "description": description, "expected": expected,
            "computed": value, "unit": unit, "rel_error": rel, "rel_tol": rel_tol,
            "passed": passed, "source": source, "error": error,
        })

    # --- Sensible heat (SVN Ch. 4) -------------------------------------------
    ch4 = SPECIES["CH4(g)"]
    add("Sensible heat", "Methane heated from 260 C to 600 C: ∫(Cp/R)dT",
        2378.8, lambda: icph(533.15, 873.15, ch4.cp), "K", 1e-4,
        "SVN Ch. 4 example (also on the course Chapter 4 slides)")
    add("Sensible heat", "Methane heated from 260 C to 600 C: Q = ΔH",
        19778.0, lambda: ch4.sensible_dH(533.15, 873.15), "J/mol", 1e-4,
        "SVN Ch. 4 example")

    # --- Heat of reaction (SVN Ch. 4) ----------------------------------------
    meoh = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
    add("Heat of reaction", "Methanol synthesis: ΔH° at 298.15 K",
        -90135.0, lambda: meoh.dH0, "J/mol", 1e-6, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: ΔA", -7.663,
        lambda: meoh.delta_coeffs()[0], "-", 1e-4, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: 10³ × ΔB", 10.815,
        lambda: meoh.delta_coeffs()[1] * 1e3, "1/K", 1e-4, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: 10⁶ × ΔC", -3.450,
        lambda: meoh.delta_coeffs()[2] * 1e6, "1/K^2", 1e-4, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: 10⁻⁵ × ΔD", -0.135,
        lambda: meoh.delta_coeffs()[3] * 1e-5, "K^2", 1e-4, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: ∫(ΔCp°/R)dT, 298.15 to 1073.15 K",
        -1615.5, lambda: icph(T0, 1073.15, meoh.delta_coeffs()), "K", 1e-4, "SVN Ch. 4 example")
    add("Heat of reaction", "Methanol synthesis: ΔH° at 800 C",
        -103566.0, lambda: meoh.dH(1073.15), "J/mol", 2e-5, "SVN Ch. 4 example")
    deacon = Reaction.parse("4 HCl + O2 -> 2 H2O(g) + 2 Cl2")
    add("Heat of reaction", "4 HCl + O2 -> 2 H2O(g) + 2 Cl2: ΔH° at 298.15 K",
        -114408.0, lambda: deacon.dH0, "J/mol", 1e-6, "SVN Ch. 4 example")
    comb_l = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)")
    add("Heat of reaction", "Methane combustion to liquid water: ΔH° at 298.15 K",
        -890649.0, lambda: comb_l.dH0, "J/mol", 1e-6, "SVN Table C.4 (hand calculation)")
    comb_g = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
    add("Heat of reaction", "Methane combustion to water vapour: ΔH° at 298.15 K",
        -802625.0, lambda: comb_g.dH0, "J/mol", 1e-6, "SVN Ch. 4 flame-temperature example")

    # --- Gibbs energy and K (SVN chemical-equilibria chapter) -----------------
    hyd = Reaction.parse("C2H4 + H2O(g) -> C2H5OH(g)")
    add("Gibbs energy and K", "Ethylene hydration: ΔH° at 298.15 K",
        -45792.0, lambda: hyd.dH0, "J/mol", 1e-6, "SVN equilibrium-constant example")
    add("Gibbs energy and K", "Ethylene hydration: ΔG° at 298.15 K",
        -8378.0, lambda: hyd.dG0, "J/mol", 1e-6, "SVN equilibrium-constant example")
    add("Gibbs energy and K", "Ethylene hydration: K at 298.15 K",
        29.366, lambda: hyd.K(T0), "-", 5e-4, "SVN equilibrium-constant example")
    add("Gibbs energy and K", "Ethylene hydration: ∫(ΔCp°/R)dT, 298.15 to 418.15 K",
        -23.121, lambda: icph(T0, 418.15, hyd.delta_coeffs()), "K", 1e-3, "SVN equilibrium-constant example")
    add("Gibbs energy and K", "Ethylene hydration: K at 145 C",
        1.443e-1, lambda: hyd.K(418.15), "-", 1e-3, "SVN equilibrium-constant example")
    add("Gibbs energy and K", "Ethylene hydration: K at 320 C",
        2.942e-3, lambda: hyd.K(593.15), "-", 1e-3, "SVN equilibrium-constant example")

    # --- Real gas (SVN Ch. 3 and 6) -------------------------------------------
    but = SPECIES["n-C4H10(g)"]
    crit = but.critical
    add("Real gas", "n-Butane at 510 K, 25 bar: Z from the generalized virial correlation",
        0.879, lambda: residual(but, 510.0, 25.0, "virial").Z, "-", 1e-3, "SVN Ch. 3 example")
    add("Real gas", "n-Butane at 350 K, 9.4573 bar: vapour Z, Redlich/Kwong",
        0.8305, lambda: cubic_Z_roots("rk", 350.0 / crit.Tc, 9.4573 / crit.Pc, crit.omega)[-1],
        "-", 1e-3, "SVN Ch. 3 example")
    add("Real gas", "n-Butane at 350 K, 9.4573 bar: liquid Z, Redlich/Kwong",
        0.0433, lambda: cubic_Z_roots("rk", 350.0 / crit.Tc, 9.4573 / crit.Pc, crit.omega)[0],
        "-", 5e-3, "SVN Ch. 3 example")
    table = {
        "vdw": (0.6608, -3937.0, -5.424),
        "rk": (0.6850, -4505.0, -6.546),
        "srk": (0.7222, -4824.0, -7.413),
        "pr": (0.6907, -4988.0, -7.426),
    }
    names = {"vdw": "van der Waals", "rk": "Redlich/Kwong", "srk": "Soave/Redlich/Kwong", "pr": "Peng/Robinson"}
    for key, (z, hr, sr) in table.items():
        add("Residual properties", f"n-Butane at 500 K, 50 bar, {names[key]}: Z",
            z, lambda k=key: residual(but, 500.0, 50.0, k).Z, "-", 1e-3, "SVN Ch. 6 example table")
        add("Residual properties", f"n-Butane at 500 K, 50 bar, {names[key]}: Hᴿ",
            hr, lambda k=key: residual(but, 500.0, 50.0, k).HR, "J/mol", 1.5e-3, "SVN Ch. 6 example table")
        add("Residual properties", f"n-Butane at 500 K, 50 bar, {names[key]}: Sᴿ",
            sr, lambda k=key: residual(but, 500.0, 50.0, k).SR, "J/(mol K)", 1.5e-3, "SVN Ch. 6 example table")

    # Course slide: Peng/Robinson roots for CO2 at 283 K, 49 bar (slide uses omega = 0.225)
    co2 = SPECIES["CO2(g)"].critical
    slide = lambda: cubic_Z_roots("pr", 283.0 / co2.Tc, 49.0 / co2.Pc, 0.225)
    add("Real gas", "CO2 at 283 K, 49 bar, Peng/Robinson: vapour root Z",
        0.5501, lambda: slide()[-1], "-", 1e-3, "Course EOS slides (cubic-EOS program output)")
    add("Real gas", "CO2 at 283 K, 49 bar, Peng/Robinson: liquid root Z",
        0.1099, lambda: slide()[0], "-", 2e-3, "Course EOS slides (cubic-EOS program output)")

    # --- Gibbs minimisation (SVN multireaction example) ------------------------
    expected_y = {"CH4(g)": 0.0196, "H2O(g)": 0.0980, "CO(g)": 0.1743, "CO2(g)": 0.0371, "H2(g)": 0.6710}
    for sid, y in expected_y.items():
        add("Gibbs minimisation", f"Steam reforming at 1000 K, 1 bar: y of {sid}",
            y, lambda s=sid: _svn_gibbs_example()["y"][s], "-", 6e-3,
            "SVN Gibbs-minimisation example")

    # --- Formation of water vapour at 60 C (values quoted in SVN) -----------------
    h2o = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
    add("Gibbs energy and K", "H2 + 1/2 O2 -> H2O(g): ΔH° at 60 C",
        -242168.0, lambda: h2o.dH(333.15), "J/mol", 2e-5, "SVN, value quoted for 333.15 K")
    add("Gibbs energy and K", "H2 + 1/2 O2 -> H2O(g): ΔG° at 60 C",
        -226997.0, lambda: h2o.dG(333.15), "J/mol", 2e-5, "SVN, value quoted for 333.15 K")

    # --- Heat effects of industrial reactions (SVN Ch. 4) -------------------------
    def flame():
        burn = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
        return heatbalance.solve(heatbalance.build_case(burn, excess=0.2, air=True), T0, "adiabatic")

    def reformer():
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        case = heatbalance.build_case(smr, excess_species="H2O(g)", excess=1.0, side=[(wgs, 0.13)])
        return heatbalance.solve(case, 600.0, "duty", T_out=1300.0)

    add("Reactor heat balance", "Methane burned with 20 % excess air, both entering at 25 C: flame temperature",
        2066.0, lambda: flame()["T_out"], "K", 5e-4, "SVN Ch. 4 example (theoretical flame temperature)")
    add("Reactor heat balance", "Steam reformer, feed at 600 K: heat to cool the reactants to 298.15 K",
        -34390.0, lambda: reformer()["path"]["dH_R"], "J", 2e-4, "SVN Ch. 4 example (reformer heat requirement)")
    add("Reactor heat balance", "Steam reformer: heat of the two reactions at 298.15 K",
        200460.0, lambda: reformer()["path"]["dH_298"], "J", 2e-5, "SVN Ch. 4 example (reformer heat requirement)")
    add("Reactor heat balance", "Steam reformer: heat to bring the products to 1300 K",
        161940.0, lambda: reformer()["path"]["dH_P"], "J", 2e-4, "SVN Ch. 4 example (reformer heat requirement)")
    add("Reactor heat balance", "Steam reformer: total heat requirement",
        328010.0, lambda: reformer()["Q"], "J", 2e-5, "SVN Ch. 4 example (reformer heat requirement)")

    # --- Bomb calorimeter (course lab handout, benzoic acid calibration) -----------
    cal = heatbalance.JOULE_PER_CAL
    add("Bomb calorimeter", "Calibration with 1.1942 g benzoic acid, rise 2.48 C: calorimeter constant",
        3059.33, lambda: heatbalance.calorimeter_constant(1.1942, 2.48, 6319.0 * cal, 41.0 * cal) / cal,
        "cal/K", 1e-5, "Course bomb-calorimeter handout")
    add("Bomb calorimeter", "Benzoic acid: ΔH from ΔU = −3228.7 kJ/mol with Δn(gas) = −0.5 at 303.15 K",
        -3230.0, lambda: heatbalance.enthalpy_from_internal_energy(-3228.7e3, -0.5, 303.15) / 1000.0, "kJ/mol", 3e-5,
        "Course bomb-calorimeter handout (ΔH = ΔU + Δn·RT)")

    # --- Independent physical check -------------------------------------------
    vap = Reaction.parse("H2O(l) -> H2O(g)")
    add("Physical sanity", "Water: K of vaporisation at 100 C, which should equal Psat/P°",
        1.01325, lambda: vap.K(373.15), "-", 3e-2,
        "Steam tables: Psat = 1.01325 bar at 373.15 K")
    add("Physical sanity", "Water: heat of vaporisation at 100 C",
        40660.0, lambda: vap.dH(373.15), "J/mol", 1e-2,
        "Steam tables: 2257 kJ/kg x 18.015 g/mol")
    return rows


def summary(rows: List[dict]) -> dict:
    return {"total": len(rows), "passed": sum(1 for r in rows if r["passed"])}
