"""Hess-law combination, single-reaction equilibrium, Gibbs-energy
minimisation."""

import math
import unittest

from thermosolver import InputError, R, Reaction, SPECIES, T0
from thermosolver import library
from thermosolver.combine import combine_reactions, formation_reaction
from thermosolver.equilibrium import atom_distribution, gibbs_minimize, reaction_equilibrium


class TestCombination(unittest.TestCase):
    def test_every_library_combination_is_consistent(self):
        for combo in library.COMBINATIONS:
            steps = [(Reaction.parse(eq), m) for eq, m in combo["steps"]]
            res = combine_reactions(steps, combo["T"])
            self.assertLess(res["max_difference_J"], 1e-6, combo["id"])
            self.assertTrue(res["reaction"].is_balanced())

    def test_co2_to_methanol_from_two_steps(self):
        rwgs = Reaction.parse("CO2 + H2 -> CO + H2O(g)")
        meoh = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
        res = combine_reactions([(rwgs, 1), (meoh, 1)], 523.15)
        direct = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        self.assertEqual(res["reaction"].stoich, direct.stoich)
        self.assertEqual(res["cancelled_intermediates"], ["CO(g)"])
        self.assertAlmostEqual(res["hess"]["dH"], direct.dH(523.15), delta=1e-6)
        self.assertAlmostEqual(res["hess"]["lnK"], rwgs.lnK(523.15) + meoh.lnK(523.15), places=10)

    def test_subtraction_and_fractional_multipliers(self):
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        res = combine_reactions([(smr, 1), (wgs, -1)], 1000.0)
        self.assertEqual(res["reaction"].stoich, Reaction.parse("CH4 + CO2 -> 2 CO + 2 H2").stoich)
        half = combine_reactions([(smr, 0.5), (wgs, 0.5)], 1000.0)
        full = combine_reactions([(smr, 1), (wgs, 1)], 1000.0)
        self.assertAlmostEqual(2 * half["hess"]["dG"], full["hess"]["dG"], delta=1e-6)

    def test_three_formation_reactions_give_methane_combustion(self):
        steps = [(Reaction.parse("C(s) + O2 -> CO2"), 1), (Reaction.parse("H2 + 1/2 O2 -> H2O(g)"), 2),
                 (Reaction.parse("C(s) + 2 H2 -> CH4"), -1)]
        res = combine_reactions(steps, T0)
        self.assertAlmostEqual(res["hess"]["dH0"], -802625.0, delta=1e-6)
        self.assertEqual(set(res["cancelled_intermediates"]), {"C(s)", "H2(g)"})

    def test_bad_combinations(self):
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        with self.assertRaises(InputError):
            combine_reactions([(wgs, 1)], 500.0)
        with self.assertRaises(InputError):
            combine_reactions([(wgs, 1), (wgs, -1)], 500.0)
        with self.assertRaises(InputError):
            combine_reactions([(wgs, 1), (wgs, 0)], 500.0)

    def test_formation_reactions(self):
        rxn = formation_reaction(SPECIES["CH3OH(g)"])
        self.assertEqual(rxn.stoich, {"CH3OH(g)": 1.0, "C(s)": -1.0, "H2(g)": -2.0, "O2(g)": -0.5})
        self.assertAlmostEqual(rxn.dH0, SPECIES["CH3OH(g)"].dHf)
        self.assertAlmostEqual(rxn.dG0, SPECIES["CH3OH(g)"].dGf)
        with self.assertRaises(InputError):
            formation_reaction(SPECIES["SO2(g)"])      # SVN has no usable Cp for sulfur
        with self.assertRaises(InputError):
            formation_reaction(SPECIES["H2(g)"])


class TestSingleReactionEquilibrium(unittest.TestCase):
    def test_water_gas_shift_has_a_closed_form(self):
        # Equimolar CO + H2O, no change in moles: eps = sqrt(K) / (1 + sqrt(K))
        rxn = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        for T in (500.0, 800.0, 1100.0, 1400.0):
            rootK = math.sqrt(rxn.K(T))
            res = reaction_equilibrium(rxn, T, 1.0)
            self.assertAlmostEqual(res["extent"], rootK / (1 + rootK), places=9)
            self.assertAlmostEqual(res["conversion"], res["extent"], places=12)

    def test_solution_satisfies_the_equilibrium_expression(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for T, P in ((600.0, 1.0), (700.0, 100.0), (800.0, 300.0)):
            res = reaction_equilibrium(rxn, T, P)
            y = res["y"]
            lhs = y["NH3(g)"] ** 2 / (y["N2(g)"] * y["H2(g)"] ** 3)
            self.assertAlmostEqual(lhs, rxn.K(T) * P ** 2, delta=1e-8 * lhs)

    def test_le_chatelier_in_pressure(self):
        nh3 = Reaction.parse("N2 + 3 H2 -> 2 NH3")                 # fewer moles: pressure helps
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")          # more moles: pressure hurts
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")            # same moles: no effect
        self.assertLess(reaction_equilibrium(nh3, 700.0, 10.0)["conversion"],
                        reaction_equilibrium(nh3, 700.0, 200.0)["conversion"])
        self.assertGreater(reaction_equilibrium(smr, 1000.0, 1.0)["conversion"],
                           reaction_equilibrium(smr, 1000.0, 30.0)["conversion"])
        self.assertAlmostEqual(reaction_equilibrium(wgs, 700.0, 1.0)["conversion"],
                               reaction_equilibrium(wgs, 700.0, 50.0)["conversion"], places=9)

    def test_inert_dilution(self):
        # An inert helps a mole-increasing reaction (lower partial pressures)
        rxn = Reaction.parse("C2H6 -> C2H4 + H2")
        plain = reaction_equilibrium(rxn, 1000.0, 1.0, {"C2H6": 1})
        steam = reaction_equilibrium(rxn, 1000.0, 1.0, {"C2H6": 1, "H2O(g)": 5})
        self.assertGreater(steam["conversion"], plain["conversion"])
        self.assertAlmostEqual(steam["moles"]["H2O(g)"], 5.0)

    def test_gas_solid_reaction_goes_to_one_extreme(self):
        rxn = Reaction.parse("CaCO3 -> CaO + CO2")
        # K = P_CO2/P0 at equilibrium. Below the decomposition temperature nothing happens.
        self.assertEqual(reaction_equilibrium(rxn, 900.0, 1.0)["status"], "no_forward_reaction")
        self.assertEqual(reaction_equilibrium(rxn, 1200.0, 1.0)["status"], "complete")
        T_dec = rxn.crossover_temperatures()[0]
        self.assertTrue(1100 < T_dec < 1200, T_dec)     # limestone calcines near 1160-1170 K at 1 bar

    def test_real_gas_shifts_ammonia_equilibrium_upward(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        ideal = reaction_equilibrium(rxn, 723.15, 300.0, model="ideal")["conversion"]
        real = reaction_equilibrium(rxn, 723.15, 300.0, model="pr")["conversion"]
        self.assertGreater(real, ideal)

    def test_feed_validation(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        with self.assertRaises(InputError):
            reaction_equilibrium(rxn, 700.0, 1.0, {"N2": -1, "H2": 3})
        with self.assertRaises(InputError):
            reaction_equilibrium(rxn, 700.0, 0.0)
        with self.assertRaises(InputError):
            reaction_equilibrium(rxn, 700.0, 1.0, {"CO2": 1})


class TestGibbsMinimisation(unittest.TestCase):
    def test_svn_example(self):
        T = 1000.0
        dGf = {"CH4(g)": 19720.0, "H2O(g)": -192420.0, "CO(g)": -200240.0, "CO2(g)": -395790.0, "H2(g)": 0.0}
        res = gibbs_minimize(list(dGf), {"CH4": 2, "H2O(g)": 3}, T, 1.0,
                             g_rt_override={k: v / (R * T) for k, v in dGf.items()})
        expected = {"CH4(g)": 0.0196, "H2O(g)": 0.0980, "CO(g)": 0.1743, "CO2(g)": 0.0371, "H2(g)": 0.6710}
        for sid, y in expected.items():
            self.assertAlmostEqual(res["y"][sid], y, delta=1.5e-4, msg=sid)
        self.assertAlmostEqual(res["total_moles"], 8.6608, delta=2e-3)   # SVN: sum n_i = 8.6608

    def test_same_example_with_the_solvers_own_data(self):
        res = gibbs_minimize(["CH4", "H2O(g)", "CO", "CO2", "H2"], {"CH4": 2, "H2O(g)": 3}, 1000.0, 1.0)
        expected = {"CH4(g)": 0.0196, "H2O(g)": 0.0980, "CO(g)": 0.1743, "CO2(g)": 0.0371, "H2(g)": 0.6710}
        for sid, y in expected.items():
            self.assertAlmostEqual(res["y"][sid], y, delta=4e-3, msg=sid)

    def test_elements_are_conserved(self):
        feed = {"CO2(g)": 1.0, "H2(g)": 3.0}
        res = gibbs_minimize(["CO2", "H2", "CH3OH", "CO", "H2O(g)", "CH4"], feed, 600.0, 30.0)
        for el in ("C", "H", "O"):
            fed = sum(SPECIES[s].elements.get(el, 0) * n for s, n in feed.items())
            out = sum(SPECIES[s].elements.get(el, 0) * n for s, n in res["moles"].items())
            self.assertAlmostEqual(fed, out, delta=1e-9, msg=el)
        self.assertLess(res["kkt_residual"], 1e-8)

    def test_agrees_with_single_reaction_solver(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for T, P, model in ((700.0, 100.0, "ideal"), (723.15, 200.0, "pr"), (600.0, 30.0, "srk")):
            single = reaction_equilibrium(rxn, T, P, {"N2": 1, "H2": 3}, model)
            multi = gibbs_minimize(["N2", "H2", "NH3"], {"N2": 1, "H2": 3}, T, P, model)
            for sid in ("N2(g)", "H2(g)", "NH3(g)"):
                self.assertAlmostEqual(multi["y"][sid], single["y"][sid], delta=1e-8, msg=f"{sid} {T} {P} {model}")

    def test_every_independent_reaction_is_at_equilibrium(self):
        T, P = 1000.0, 5.0
        res = gibbs_minimize(["CH4", "H2O(g)", "CO", "CO2", "H2"], {"CH4": 1, "H2O(g)": 2}, T, P)
        y = res["y"]
        for eq in ("CH4 + H2O(g) -> CO + 3 H2", "CO + H2O(g) -> CO2 + H2", "CH4 + CO2 -> 2 CO + 2 H2"):
            rxn = Reaction.parse(eq)
            lnQ = sum(nu * math.log(y[s] * P) for s, nu in rxn.stoich.items())
            self.assertAlmostEqual(lnQ, rxn.lnK(T), delta=1e-7, msg=eq)

    def test_result_does_not_depend_on_how_the_feed_is_written(self):
        # Same atoms in, same equilibrium out (it is a state function of T, P and elements)
        species = ["CH4", "H2O(g)", "CO", "CO2", "H2"]
        a = gibbs_minimize(species, {"CH4": 1, "H2O(g)": 2}, 1000.0, 1.0)
        b = gibbs_minimize(species, {"CO": 1, "H2": 3, "H2O(g)": 1}, 1000.0, 1.0)
        for sid in a["y"]:
            self.assertAlmostEqual(a["y"][sid], b["y"][sid], delta=1e-9, msg=sid)

    def test_methane_is_the_thermodynamic_sink_for_co2_hydrogenation(self):
        with_ch4 = gibbs_minimize(["CO2", "H2", "CH3OH", "CO", "H2O(g)", "CH4"], {"CO2": 1, "H2": 3}, 523.15, 50.0)
        without = gibbs_minimize(["CO2", "H2", "CH3OH", "CO", "H2O(g)"], {"CO2": 1, "H2": 3}, 523.15, 50.0)
        d1 = atom_distribution(with_ch4, "C")
        d2 = atom_distribution(without, "C")
        self.assertGreater(d1["CH4(g)"], 0.7)
        self.assertLess(d1["CH3OH(g)"], 1e-6)
        self.assertGreater(d2["CH3OH(g)"], 0.1)
        self.assertAlmostEqual(sum(d1.values()), 1.0, places=12)

    def test_carbon_activity(self):
        # Dry reforming cokes at low temperature. A 1:1 feed sits exactly on the
        # O/C = 1 line, so it stays marginally carbon-forming far above 1000 K;
        # extra CO2 (O/C > 1) removes the driving force when hot.
        species = ["CH4", "CO2", "CO", "H2", "H2O(g)"]
        cold = gibbs_minimize(species, {"CH4": 1, "CO2": 1}, 800.0, 1.0)
        hot = gibbs_minimize(species, {"CH4": 1, "CO2": 2}, 1300.0, 1.0)
        self.assertGreater(cold["carbon_activity"], 1.0)
        self.assertLess(hot["carbon_activity"], 1.0)
        # carbon activity falls monotonically with temperature for the 1:1 feed
        series = [gibbs_minimize(species, {"CH4": 1, "CO2": 1}, T, 1.0)["carbon_activity"]
                  for T in (800.0, 1000.0, 1200.0, 1400.0)]
        self.assertTrue(all(a > b for a, b in zip(series, series[1:])), series)
        # Cross-check against the Boudouard reaction: a_C = K * (y_CO P)^2 / (y_CO2 P)
        boud = Reaction.parse("2 CO -> C(s) + CO2")
        for res, T in ((cold, 800.0), (hot, 1300.0)):
            a_c = boud.K(T) * res["y"]["CO(g)"] ** 2 / res["y"]["CO2(g)"]
            self.assertAlmostEqual(res["carbon_activity"], a_c, delta=1e-6 * a_c)

    def test_trace_species_and_inerts(self):
        res = gibbs_minimize(["N2", "O2", "NO", "NO2", "N2O"], {"N2": 0.79, "O2": 0.21}, 1500.0, 1.0)
        self.assertTrue(0 < res["y"]["NO(g)"] < 0.01)
        self.assertTrue(0 < res["y"]["N2O(g)"] < 1e-5)
        rxn = Reaction.parse("N2 + O2 -> 2 NO")
        self.assertAlmostEqual(res["y"]["NO(g)"] ** 2 / (res["y"]["N2(g)"] * res["y"]["O2(g)"]),
                               rxn.K(1500.0), delta=1e-8 * rxn.K(1500.0))

    def test_species_that_cannot_form_are_excluded(self):
        res = gibbs_minimize(["N2", "H2", "NH3", "CO2"], {"N2": 1, "H2": 3}, 700.0, 100.0)
        self.assertEqual(res["excluded"], ["CO2(g)"])
        self.assertEqual(res["moles"]["CO2(g)"], 0.0)

    def test_input_validation(self):
        with self.assertRaises(InputError):
            gibbs_minimize(["N2", "H2", "NH3"], {}, 700.0, 1.0)
        with self.assertRaises(InputError):
            gibbs_minimize(["CO", "CO2", "C(s)"], {"CO": 1}, 900.0, 1.0)
        with self.assertRaises(InputError):
            gibbs_minimize(["N2", "H2", "NH3"], {"N2": 1, "H2": 3}, 700.0, -1.0)

    def test_robust_over_a_wide_range(self):
        from thermosolver.errors import PhaseError
        species = ["CO2", "H2", "CH3OH", "CO", "H2O(g)", "CH4"]
        solved = refused = 0
        for T in (300.0, 400.0, 600.0, 900.0, 1200.0, 1500.0):
            for P in (0.1, 1.0, 50.0, 300.0):
                for model in ("ideal", "pr"):
                    try:
                        res = gibbs_minimize(species, {"CO2": 1, "H2": 3}, T, P, model)
                    except PhaseError:
                        # only the real-gas model may refuse, and only where water
                        # or methanol would be a liquid (below their critical temperatures)
                        self.assertEqual(model, "pr")
                        self.assertLess(T, 647.1)
                        refused += 1
                        continue
                    solved += 1
                    self.assertAlmostEqual(sum(res["y"].values()), 1.0, places=10)
                    self.assertLess(res["kkt_residual"], 1e-7, f"{T} {P} {model}")
        self.assertEqual(solved + refused, 48)
        self.assertGreaterEqual(solved, 40)


if __name__ == "__main__":
    unittest.main()
