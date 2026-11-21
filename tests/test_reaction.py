"""Heat-capacity integrals, reaction parsing, elemental balance and the
standard property changes dH, dS, dG, K as functions of temperature."""

import math
import unittest

from thermosolver import (
    DataUnavailableError, InputError, R, Reaction, SPECIES, T0,
    UnbalancedReactionError, UnknownSpeciesError,
)
from thermosolver import library
from thermosolver.audit import all_passed, audit_reaction
from thermosolver.heatcap import cp_over_r, icph, icps, mcph, mcps, simpson
from thermosolver.reaction import suggest_balance


class TestHeatCapacityIntegrals(unittest.TestCase):
    SVN_FORM = [(1.702, 9.081e-3, -2.164e-6, 0.0), (3.470, 1.450e-3, 0.0, 0.121e5),
                (-7.663, 10.815e-3, -3.450e-6, -0.135e5)]
    # with the cubic term used by NIST Shomate equations (hydrogen peroxide, and a made-up set)
    COEFFS = SVN_FORM + [(4.1204, 6.6375e-3, -4.2283e-6, -5.0777e4, 1.0930e-9),
                         (0.5, 2.0e-2, -1.5e-5, 3.0e4, 4.0e-9)]

    def test_icph_against_numerical_quadrature(self):
        for c in self.COEFFS:
            for T in (250.0, 500.0, 1000.0, 2000.0):
                num = simpson(lambda t: cp_over_r(c, t), T0, T)
                self.assertAlmostEqual(icph(T0, T, c), num, delta=1e-7 * max(1.0, abs(num)))

    def test_icps_against_numerical_quadrature(self):
        for c in self.COEFFS:
            for T in (250.0, 500.0, 1000.0, 2000.0):
                num = simpson(lambda t: cp_over_r(c, t) / t, T0, T)
                self.assertAlmostEqual(icps(T0, T, c), num, delta=1e-9 * max(1.0, abs(num)) + 1e-10)

    def test_svn_form_of_entropy_integral(self):
        # A ln(T/T0) + [B + (C + D/(T0^2 T^2)) (T+T0)/2] (T-T0), as printed in SVN
        for (A, B, C, D) in self.SVN_FORM:
            T = 873.15
            svn = A * math.log(T / T0) + (B + (C + D / (T0 ** 2 * T ** 2)) * (T + T0) / 2) * (T - T0)
            self.assertAlmostEqual(icps(T0, T, (A, B, C, D)), svn, places=10)

    def test_four_term_and_five_term_sets_agree_when_E_is_zero(self):
        for c in self.SVN_FORM:
            padded = c + (0.0,)
            for T in (400.0, 1200.0):
                self.assertEqual(icph(T0, T, c), icph(T0, T, padded))
                self.assertEqual(icps(T0, T, c), icps(T0, T, padded))
                self.assertEqual(cp_over_r(c, T), cp_over_r(padded, T))
        with self.assertRaises(ValueError):
            cp_over_r((1.0, 2.0, 3.0), 300.0)

    def test_mean_heat_capacities(self):
        c = self.COEFFS[0]
        T = 900.0
        self.assertAlmostEqual(mcph(T0, T, c) * (T - T0), icph(T0, T, c), places=8)
        self.assertAlmostEqual(mcps(T0, T, c) * math.log(T / T0), icps(T0, T, c), places=10)
        self.assertAlmostEqual(mcph(T0, T0, c), cp_over_r(c, T0), places=10)
        self.assertAlmostEqual(mcps(T0, T0, c), cp_over_r(c, T0), places=10)

    def test_integrals_reverse_and_add(self):
        c = self.COEFFS[1]
        self.assertAlmostEqual(icph(300, 800, c), -icph(800, 300, c), places=9)
        self.assertAlmostEqual(icph(300, 500, c) + icph(500, 800, c), icph(300, 800, c), places=9)
        self.assertAlmostEqual(icps(300, 500, c) + icps(500, 800, c), icps(300, 800, c), places=12)

    def test_svn_methane_example(self):
        ch4 = SPECIES["CH4(g)"]
        self.assertAlmostEqual(ch4.sensible_dH(533.15, 873.15), 19778.0, delta=1.0)


class TestParsing(unittest.TestCase):
    def test_arrows_and_coefficients(self):
        ref = Reaction.parse("N2 + 3 H2 -> 2 NH3").stoich
        for text in ["N2 + 3H2 -> 2NH3", "N2+3 H2=2 NH3", "N2 + 3 H2 → 2 NH3", "N2 + 3 H2 <=> 2 NH3",
                     "N2 + 3 H2 ⇌ 2 NH3", "N₂ + 3 H₂ → 2 NH₃", "nitrogen + 3 hydrogen -> 2 ammonia",
                     "N2(g) + 3*H2(g) => 2 NH3(g)"]:
            self.assertEqual(Reaction.parse(text).stoich, ref, text)

    def test_fractional_coefficients(self):
        a = Reaction.parse("H2 + 1/2 O2 -> H2O(g)").stoich
        b = Reaction.parse("H2 + 0.5 O2 -> H2O(g)").stoich
        self.assertEqual(a, b)
        self.assertEqual(a["O2(g)"], -0.5)

    def test_phase_selection(self):
        gas = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
        liq = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)")
        self.assertIn("H2O(g)", gas.stoich)
        self.assertIn("H2O(l)", liq.stoich)
        default = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O")
        self.assertIn("H2O(g)", default.stoich)
        self.assertTrue(any("assumed" in n for n in default.notes))

    def test_species_on_both_sides_cancels(self):
        rxn = Reaction.parse("CO + H2O(g) + N2 -> CO2 + H2 + N2")
        self.assertNotIn("N2(g)", rxn.stoich)
        self.assertTrue(any("cancels" in n for n in rxn.notes))

    def test_bad_input_is_rejected_with_a_message(self):
        for text in ["", "   ", "CH4 + 2 O2", "-> CO2", "CH4 -> ", "CH4 + -> CO2", "A -> B -> C",
                     "CH4 + 2 O2 -> CO2 + 2 H2O -> x", "0 CH4 -> C + 2 H2", "CH4 -> CH4"]:
            with self.assertRaises((InputError, UnknownSpeciesError), msg=repr(text)):
                Reaction.parse(text)

    def test_unknown_species(self):
        with self.assertRaises(UnknownSpeciesError):
            Reaction.parse("CS2 + 3 O2 -> CO2 + 2 SO2")
        with self.assertRaises(UnknownSpeciesError):
            Reaction.parse("Xe + F2 -> XeF2")

    def test_equation_round_trip(self):
        for _, _, eq, *_ in library.REACTIONS:
            rxn = Reaction.parse(eq)
            again = Reaction.parse(rxn.equation)
            self.assertEqual(rxn.stoich, again.stoich, eq)


class TestElementalBalance(unittest.TestCase):
    def test_unbalanced_reactions_are_rejected(self):
        for text in ["CH4 + O2 -> CO2 + H2O", "N2 + H2 -> NH3", "CO2 + H2 -> CH3OH + H2O",
                     "H2 + O2 -> H2O", "C2H4 + H2O -> C2H5OH + H2", "CaCO3 -> CaO + CO",
                     "CH4 + 2 O2 -> CO2 + 2.01 H2O"]:
            with self.assertRaises(UnbalancedReactionError, msg=text):
                Reaction.parse(text)

    def test_error_names_the_elements_and_suggests_a_fix(self):
        with self.assertRaises(UnbalancedReactionError) as ctx:
            Reaction.parse("C3H8 + O2 -> CO2 + H2O")
        err = ctx.exception
        self.assertEqual(set(err.details["imbalance"]), {"C", "H", "O"})
        fixed = Reaction.parse(err.details["suggestion"])
        self.assertEqual(fixed.stoich, {"C3H8(g)": -1, "O2(g)": -5, "CO2(g)": 3, "H2O(g)": 4})

    def test_no_suggestion_when_balancing_is_not_unique(self):
        # CH4 + O2 -> CO + CO2 + H2O has infinitely many balanced forms
        self.assertIsNone(suggest_balance(["CH4(g)", "O2(g)"], ["CO(g)", "CO2(g)", "H2O(g)"]))
        # and none at all when an element is missing on one side
        self.assertIsNone(suggest_balance(["CH4(g)"], ["CO2(g)"]))

    def test_every_library_reaction_is_balanced(self):
        self.assertGreaterEqual(len(library.REACTIONS), 20)
        for rid, _, eq, *_ in library.REACTIONS:
            self.assertTrue(Reaction.parse(eq).is_balanced(), rid)

    def test_library_ids_are_unique(self):
        ids = [r[0] for r in library.REACTIONS]
        self.assertEqual(len(ids), len(set(ids)))


class TestStandardProperties(unittest.TestCase):
    def test_svn_methanol_synthesis_example(self):
        rxn = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
        self.assertAlmostEqual(rxn.dH0, -90135.0, places=6)
        self.assertAlmostEqual(rxn.dH(1073.15), -103566.0, delta=1.0)

    def test_svn_ethylene_hydration_example(self):
        rxn = Reaction.parse("C2H4 + H2O(g) -> C2H5OH(g)")
        self.assertAlmostEqual(rxn.K(T0), 29.366, delta=0.005)
        self.assertAlmostEqual(rxn.K(418.15), 0.1443, delta=0.0001)
        self.assertAlmostEqual(rxn.K(593.15), 2.942e-3, delta=2e-6)

    def test_values_at_T0_are_the_table_values(self):
        for _, _, eq, *_ in library.REACTIONS:
            rxn = Reaction.parse(eq)
            self.assertAlmostEqual(rxn.dH(T0), rxn.dH0, places=6)
            self.assertAlmostEqual(rxn.dG(T0), rxn.dG0, delta=1e-6)

    def test_reverse_reaction(self):
        rxn = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        rev = rxn.reversed()
        for T in (400.0, 800.0, 1200.0):
            self.assertAlmostEqual(rev.dH(T), -rxn.dH(T), places=6)
            self.assertAlmostEqual(rev.dS(T), -rxn.dS(T), places=9)
            self.assertAlmostEqual(rev.K(T) * rxn.K(T), 1.0, places=10)

    def test_scaling(self):
        rxn = Reaction.parse("1/2 N2 + 3/2 H2 -> NH3")
        dbl = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for T in (298.15, 700.0):
            self.assertAlmostEqual(dbl.dH(T), 2 * rxn.dH(T), places=6)
            self.assertAlmostEqual(dbl.K(T), rxn.K(T) ** 2, delta=1e-12 * dbl.K(T) + 1e-300)

    def test_exothermic_and_endothermic_labels(self):
        self.assertEqual(Reaction.parse("N2 + 3 H2 -> 2 NH3").evaluate(T0)["thermicity0"], "exothermic")
        self.assertEqual(Reaction.parse("CH4 + H2O(g) -> CO + 3 H2").evaluate(T0)["thermicity0"], "endothermic")

    def test_consistency_audit_passes_for_every_library_reaction(self):
        for rid, _, eq, *_ in library.REACTIONS:
            rxn = Reaction.parse(eq)
            rng = rxn.valid_range()
            temps = [T0] if rng is None else [rng[0] + f * (rng[1] - rng[0]) for f in (0.02, 0.3, 0.6, 1.0)]
            for T in temps:
                checks = audit_reaction(rxn, T)
                failed = [c for c in checks if not c["passed"]]
                self.assertTrue(all_passed(checks), f"{rid} at {T:.1f} K: {failed}")

    def test_hess_path_adds_up(self):
        rxn = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        ev = rxn.evaluate(1000.0)
        path = ev["path"]
        # cool reactants (T -> T0), react at T0, heat products (T0 -> T)
        total = path["cool_reactants"] + path["react_at_T0"] + path["heat_products"]
        self.assertAlmostEqual(total, ev["dH"], places=6)

    def test_species_route_equals_reaction_route(self):
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        for T in (350.0, 523.15, 900.0):
            by_species_H = sum(nu * SPECIES[s].H(T) for s, nu in rxn.stoich.items())
            by_species_G = sum(nu * SPECIES[s].G(T) for s, nu in rxn.stoich.items())
            self.assertAlmostEqual(by_species_H, rxn.dH(T), delta=1e-6)
            self.assertAlmostEqual(by_species_G, rxn.dG(T), delta=1e-6)

    def test_le_chatelier_in_temperature(self):
        exo = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        endo = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        self.assertGreater(exo.K(500.0), exo.K(800.0))     # exothermic: K falls with T
        self.assertLess(endo.K(800.0), endo.K(1200.0))     # endothermic: K rises with T

    def test_crossover_temperature(self):
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        roots = smr.crossover_temperatures()
        self.assertEqual(len(roots), 1)
        self.assertAlmostEqual(smr.dG(roots[0]), 0.0, delta=1e-3)
        self.assertTrue(850 < roots[0] < 950)
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        self.assertTrue(1050 < wgs.crossover_temperatures()[0] < 1150)   # SVN: K = 1 near 1100 K

    def test_water_vaporisation_as_a_reaction(self):
        vap = Reaction.parse("H2O(l) -> H2O(g)")
        self.assertAlmostEqual(vap.K(373.15), 1.013, delta=0.03)       # K = Psat/P0
        self.assertAlmostEqual(vap.dH(373.15), 40660.0, delta=400.0)   # steam-table latent heat

    def test_species_without_heat_capacity(self):
        # Every species in the database now has a heat capacity, so a temporary
        # one without it is added to check that the solver still refuses to
        # invent a temperature dependence.
        from thermosolver.species import Species
        SPECIES["X(l)"] = Species("X(l)", "Test liquid", "CH4O", "l", -238660.0, -166270.0,
                                  None, None, None, None, None, "none", {"C": 1, "H": 4, "O": 1})
        try:
            rxn = Reaction({"CH3OH(g)": -1.0, "X(l)": 1.0})
            self.assertTrue(rxn.is_balanced())
            self.assertAlmostEqual(rxn.dH(T0), -38000.0, places=6)
            self.assertIsNone(rxn.valid_range())
            self.assertIsNone(rxn.evaluate(T0)["dA"])
            with self.assertRaises(DataUnavailableError):
                rxn.dH(400.0)
            with self.assertRaises(DataUnavailableError):
                rxn.evaluate(400.0)
        finally:
            del SPECIES["X(l)"]

    def test_reactions_with_nist_species(self):
        # Acetaldehyde oxidation to liquid acetic acid: SVN formation data
        rxn = Reaction.parse("CH3CHO + 1/2 O2 -> CH3COOH(l)")
        self.assertAlmostEqual(rxn.dH(T0), -318310.0, places=6)
        self.assertEqual(rxn.valid_range(), (298.0, 320.0))
        self.assertTrue(any(w["kind"] == "cp_extrapolation" for w in rxn.range_warnings(400.0)))
        # every use of a NIST species is announced
        for eq in ("H2 + O2 -> H2O2", "CH3OH(g) + CO -> CH3COOH(g)", "CH3CHO + 1/2 O2 -> CH3COOH(l)"):
            notes = [w for w in Reaction.parse(eq).range_warnings(T0) if w["kind"] == "data_source"]
            self.assertEqual(len(notes), 1, eq)
            self.assertIn("NIST", notes[0]["message"])
        self.assertEqual([w for w in Reaction.parse("N2 + 3 H2 -> 2 NH3").range_warnings(T0)
                          if w["kind"] == "data_source"], [])
        # hydrogen peroxide: dH0 is just the NIST enthalpy of formation
        h2o2 = Reaction.parse("H2 + O2 -> H2O2")
        self.assertEqual(h2o2.dH0, -136110.0)
        self.assertNotEqual(h2o2.delta_coeffs()[4], 0.0)             # the cubic term is in use
        self.assertEqual(Reaction.parse("N2 + 3 H2 -> 2 NH3").delta_coeffs()[4], 0.0)
        # decomposition to water and oxygen is strongly exothermic and favourable
        dec = Reaction.parse("2 H2O2 -> 2 H2O(g) + O2")
        self.assertAlmostEqual(dec.dH0, 2 * (-241818.0) + 2 * 136110.0, places=6)
        self.assertGreater(dec.lnK(400.0), 50.0)

    def test_temperature_must_be_positive_kelvin(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for bad in (0.0, -10.0, float("nan"), float("inf")):
            with self.assertRaises(InputError):
                rxn.dH(bad)


class TestCpAssumptions(unittest.TestCase):
    """Assignment stress test 2: constant versus temperature-dependent Cp."""

    def test_constant_cp_differs_measurably_at_1000K(self):
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        full = smr.dH(1000.0)
        const = smr.dH_constant_cp(1000.0)
        self.assertGreater(abs(full - const), 5000.0)      # more than 5 kJ/mol apart
        self.assertAlmostEqual(smr.dH_constant_cp(T0), smr.dH0, places=6)

    def test_constant_cp_is_exact_when_dCp_is_constant(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        # near T0 the two treatments must agree to first order
        self.assertAlmostEqual(rxn.dH(T0 + 1.0), rxn.dH_constant_cp(T0 + 1.0), delta=0.05)

    def test_ignoring_cp_changes_K_by_a_large_factor(self):
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        T = 1000.0
        lnK_full = smr.lnK(T)
        lnK_none = -smr.dG_no_cp(T) / (R * T)
        self.assertGreater(abs(lnK_full - lnK_none), 1.0)   # K off by more than a factor e


class TestWarnings(unittest.TestCase):
    """Assignment stress test 4: extrapolated Cp correlations must be flagged."""

    def test_warning_above_tmax(self):
        rxn = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        self.assertEqual([w for w in rxn.range_warnings(1400.0) if w["kind"] == "cp_extrapolation"], [])
        warned = {w["species"] for w in rxn.range_warnings(1600.0) if w["kind"] == "cp_extrapolation"}
        self.assertEqual(warned, {"CH4(g)"})
        warned = {w["species"] for w in rxn.range_warnings(2600.0) if w["kind"] == "cp_extrapolation"}
        self.assertEqual(warned, {"CH4(g)", "H2O(g)", "CO(g)"})

    def test_warning_below_298K(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        self.assertEqual(len([w for w in rxn.range_warnings(250.0) if w["kind"] == "cp_extrapolation"]), 3)

    def test_liquid_range(self):
        rxn = Reaction.parse("H2 + 1/2 O2 -> H2O(l)")
        kinds = {w["kind"] for w in rxn.range_warnings(450.0)}
        self.assertIn("cp_extrapolation", kinds)
        self.assertIn("phase", kinds)

    def test_no_warning_inside_range(self):
        for _, _, eq, _, T, _ in library.REACTIONS:
            rxn = Reaction.parse(eq)
            w = [x for x in rxn.range_warnings(T) if x["level"] in ("warning", "error")]
            self.assertEqual(w, [], f"{eq} at its suggested temperature {T} K")


if __name__ == "__main__":
    unittest.main()
