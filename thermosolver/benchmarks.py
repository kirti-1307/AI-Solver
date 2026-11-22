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
from . import heatbalance, phase
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
    def flame_case():
        burn = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
        return heatbalance.build_case(burn, excess=0.2, air=True)

    def reformer():
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        case = heatbalance.build_case(smr, excess_species="H2O(g)", excess=1.0, side=[(wgs, 0.13)])
        return heatbalance.solve(case, 600.0, "duty", T_out=1300.0)

    # The book reaches 2066 K with heat-capacity formulas that are valid to
    # 2000 K. The benchmark does the same (SVN formulas only), so that it
    # checks the method against the book. The page itself uses NIST data above
    # 2000 K and gives 2069 K; a test pins that value too.
    add("Reactor heat balance", "Methane burned with 20 % excess air, both entering at 25 C: flame temperature "
        "(SVN formulas extrapolated above 2000 K, as in the book)",
        2066.0, lambda: heatbalance.svn_outlet_temperature(flame_case(), T0), "K", 5e-4,
        "SVN Ch. 4 example (theoretical flame temperature)")
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

    # --- Below 298.15 K (NIST tables) ----------------------------------------------
    # The low-temperature heat capacities are fixed by the 200 K and 298.15 K
    # rows of each table. Every value below comes from a row or a column that
    # was NOT used for that, so it is an independent check.
    h2, co2_gas = SPECIES["H2(g)"], SPECIES["CO2(g)"]
    add("Below 298.15 K", "Hydrogen cooled from 298.15 K to 250 K: H(250 K) − H(298.15 K)",
        -1378.0, lambda: h2.sensible_dH(T0, 250.0), "J/mol", 1e-3,
        "NIST-JANAF table H-050, 250 K row (not used for the fit)")
    add("Below 298.15 K", "Methane: heat capacity at 250 K",
        34.216, lambda: ch4.cp_J(250.0), "J/(mol K)", 5e-4,
        "NIST-JANAF table C-067, 250 K row (not used for the fit)")
    add("Below 298.15 K", "Carbon dioxide: S(200 K) − S(298.15 K)",
        -13.820, lambda: co2_gas.sensible_dS(T0, 200.0), "J/(mol K)", 1e-3,
        "NIST-JANAF table C-095, entropy column (not used for the fit)")
    no = Reaction.parse("N2 + O2 -> 2 NO")
    add("Below 298.15 K", "N2 + O2 -> 2 NO: ΔH° at 250 K",
        180430.0, lambda: no.dH(250.0), "J/mol", 2e-5,
        "SVN ΔH°f plus the 250 K rows of NIST-JANAF tables N-005, N-023, O-029")
    form_co2 = Reaction.parse("C(s) + O2 -> CO2")
    add("Below 298.15 K", "C + O2 -> CO2: ΔH° at 200 K minus ΔH° at 298.15 K",
        118.0, lambda: form_co2.dH(200.0) - form_co2.dH0, "J/mol", 2e-2,
        "NIST-JANAF table C-095, ΔfH° column: −393.404 and −393.522 kJ/mol")
    ethane = SPECIES["C2H6(g)"]
    add("Below 298.15 K", "Ethane: heat capacity at 272.07 K against a measured value",
        49.51, lambda: ethane.cp_J(272.07), "J/(mol K)", 5e-3,
        "NIST Chemistry WebBook, measured value (not used for the fit)")

    # --- Independent physical check -------------------------------------------
    vap = Reaction.parse("H2O(l) -> H2O(g)")
    add("Physical sanity", "Water: K of vaporisation at 100 C, which should equal Psat/P°",
        1.01325, lambda: vap.K(373.15), "-", 3e-2,
        "Steam tables: Psat = 1.01325 bar at 373.15 K")
    add("Physical sanity", "Water: heat of vaporisation at 100 C",
        40660.0, lambda: vap.dH(373.15), "J/mol", 1e-2,
        "Steam tables: 2257 kJ/kg x 18.015 g/mol")

    # --- Phase change at 1 bar ---------------------------------------------------
    # The boiling point is where the liquid and the gas of the database have the
    # same Gibbs energy. Nothing is fitted: the normal boiling points of SVN
    # Table B.1 are not used anywhere in that calculation, so they are an
    # independent check of the formation data and heat capacities of both phases.
    for name, table, tol in (("Water", 373.2, 5e-4), ("Methanol", 337.9, 3e-3), ("Ethanol", 351.4, 5e-4),
                             ("Benzene", 353.2, 3.5e-3), ("Cyclohexane", 353.9, 2.5e-3), ("Toluene", 383.8, 1.3e-2)):
        add("Phase change at 1 bar", f"{name}: boiling point from G(liquid) = G(gas)",
            table, lambda n=name: phase.TRANSITIONS[n].T_boil, "K", tol,
            "SVN Table B.1, normal boiling point (not used in the calculation)")
    water = phase.TRANSITIONS["Water"]
    add("Phase change at 1 bar", "Water: vapour pressure at 25 C from the Gibbs energies",
        0.031699, lambda: phase.vapour_pressure(water, 298.15), "bar", 2e-3,
        "NIST Chemistry WebBook, saturation properties of water")
    add("Phase change at 1 bar", "Water: vapour pressure at 60 C from the Gibbs energies",
        0.19946, lambda: phase.vapour_pressure(water, 333.15), "bar", 6e-3,
        "NIST Chemistry WebBook, saturation properties of water")
    add("Phase change at 1 bar", "Water: latent heat at 25 C",
        43987.5, lambda: phase.latent_heat(water, 298.15), "J/mol", 2e-3,
        "NIST Chemistry WebBook, saturation properties of water: 45.876 - 1.8885 kJ/mol")
    add("Phase change at 1 bar", "Methane burned with 20 % excess air: dew point of the flue gas "
        "(water vapour at 0.16092 bar)",
        328.58, lambda: heatbalance.WaterSplit(flame_case()["outlet"]).T_dew, "K", 5e-4,
        "NIST Chemistry WebBook, saturation temperature of water at 0.16092 bar")
    return rows


def summary(rows: List[dict]) -> dict:
    return {"total": len(rows), "passed": sum(1 for r in rows if r["passed"])}
