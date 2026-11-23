"""Phase change from the solver's own data.

Tab 1: with "auto_phase" a species that the database holds as a liquid and as
a gas takes the phase that is stable at T and 1 bar. Tab 5: with "condense"
the water of the outlet divides itself between vapour and liquid.

Nothing here is fitted. The boiling points follow from the formation data and
heat capacities of the two phases, and are compared with SVN Table B.1; the
vapour pressure of water is compared with the NIST Chemistry WebBook.
"""

import json
import math
import os
import unittest

from thermosolver import api, heatbalance, phase
from thermosolver.constants import P0, R, T0
from thermosolver.errors import InputError
from thermosolver.reaction import Reaction
from thermosolver.species import SPECIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER = phase.TRANSITIONS["Water"]

# NIST Chemistry WebBook, "Saturation properties for water" (IAPWS-95), read on
# 23 November 2026: temperature in degrees Celsius, vapour pressure in bar.
NIST_WATER_PSAT = ((25.0, 0.031699), (40.0, 0.073849), (50.0, 0.12352), (60.0, 0.19946),
                   (70.0, 0.31201), (80.0, 0.47414), (90.0, 0.70182), (100.0, 1.0142))

BURNER = "CH4 + 2 O2 -> CO2 + 2 H2O(g)"


def burner_case(equation: str = BURNER) -> dict:
    return heatbalance.build_case(Reaction.parse(equation), excess=0.2, air=True)


# ===========================================================================
# the boiling point and the vapour pressure
# ===========================================================================
class TestBoilingPoint(unittest.TestCase):
    def test_seven_compounds_have_both_phases(self):
        self.assertEqual(set(phase.TRANSITIONS), {"Water", "Methanol", "Ethanol", "Benzene",
                                                  "Cyclohexane", "Toluene", "Acetic acid"})
        for t in phase.TRANSITIONS.values():
            self.assertEqual(SPECIES[t.liquid].phase, "l")
            self.assertEqual(SPECIES[t.gas].phase, "g")
            self.assertEqual(SPECIES[t.liquid].elements, SPECIES[t.gas].elements)

    def test_liquid_and_vapour_have_the_same_gibbs_energy_at_the_boiling_point(self):
        for t in phase.TRANSITIONS.values():
            self.assertAlmostEqual(SPECIES[t.liquid].G(t.T_boil), SPECIES[t.gas].G(t.T_boil), delta=1e-4, msg=t.compound)

    def test_the_phase_with_the_lower_gibbs_energy_is_the_one_chosen(self):
        for t in phase.TRANSITIONS.values():
            for T in (t.T_boil - 20.0, t.T_boil - 0.01, t.T_boil + 0.01, t.T_boil + 20.0):
                lower = min((t.liquid, t.gas), key=lambda sid: SPECIES[sid].G(T))
                self.assertEqual(phase.stable_id(t, T), lower, f"{t.compound} at {T:.2f} K")

    def test_boiling_points_agree_with_svn_table_b1(self):
        # The table values are not used to find the boiling point, so this is
        # a check of the SVN formation data and heat capacities of both phases.
        expected = {"Water": 373.2, "Methanol": 337.9, "Ethanol": 351.4, "Benzene": 353.2,
                    "Cyclohexane": 353.9, "Toluene": 383.8}
        for name, table in expected.items():
            t = phase.TRANSITIONS[name]
            self.assertEqual(t.T_boil_table, table)
            self.assertTrue(t.trusted, name)
            self.assertLess(abs(t.T_boil - table), 1.1 if name != "Toluene" else 4.7, name)
        self.assertAlmostEqual(WATER.T_boil, 373.19, places=2)

    def test_acetic_acid_is_not_switched_automatically(self):
        t = phase.TRANSITIONS["Acetic acid"]
        self.assertFalse(t.trusted)
        self.assertGreater(abs(t.T_boil - t.T_boil_table), phase.BOILING_POINT_TOLERANCE)
        self.assertIn("391.1", t.reason)

    def test_entropy_of_vaporisation_is_the_latent_heat_over_the_boiling_point(self):
        for t in phase.TRANSITIONS.values():
            jump = SPECIES[t.gas].S(t.T_boil) - SPECIES[t.liquid].S(t.T_boil)
            self.assertAlmostEqual(jump, t.dH_vap / t.T_boil, places=7, msg=t.compound)
            self.assertAlmostEqual(t.dS_vap, t.dH_vap / t.T_boil, places=10)
            # Trouton's rule puts it near 85 to 110 J/(mol K) for these liquids
            if t.trusted:
                self.assertTrue(80.0 < t.dS_vap < 125.0, f"{t.compound}: {t.dS_vap:.1f}")

    def test_checks_of_every_trusted_boiling_point_pass(self):
        used = [t for t in phase.TRANSITIONS.values() if t.trusted]
        checks = phase.audit(used)
        self.assertEqual(len(checks), 3 * len(used))
        for c in checks:
            self.assertTrue(c["passed"], c["name"])


class TestVapourPressure(unittest.TestCase):
    def test_is_one_bar_at_the_boiling_point(self):
        for t in phase.TRANSITIONS.values():
            self.assertAlmostEqual(phase.vapour_pressure(t, t.T_boil), P0, places=9, msg=t.compound)

    def test_rises_with_temperature(self):
        for t in phase.TRANSITIONS.values():
            values = [phase.vapour_pressure(t, T) for T in range(275, 371, 5)]
            self.assertEqual(values, sorted(values), t.compound)

    def test_water_against_the_nist_saturation_table(self):
        # within 0.1 % at 25 C and 1.6 % at 100 C: the liquid is taken as
        # incompressible and the vapour as an ideal gas, nothing else
        for celsius, expected in NIST_WATER_PSAT:
            value = phase.vapour_pressure(WATER, celsius + 273.15)
            self.assertAlmostEqual(value / expected, 1.0, delta=0.016, msg=f"{celsius} C")
        self.assertAlmostEqual(phase.vapour_pressure(WATER, 298.15) / 0.031699, 1.0, delta=0.001)

    def test_clausius_clapeyron_slope(self):
        for T in (290.0, 330.0, 370.0):
            h = 0.01
            slope = (math.log(phase.vapour_pressure(WATER, T + h)) - math.log(phase.vapour_pressure(WATER, T - h))) / (2 * h)
            self.assertAlmostEqual(slope, phase.latent_heat(WATER, T) / (R * T * T), delta=1e-6 * slope)

    def test_latent_heat_of_water(self):
        # NIST saturation table: 45.876 - 1.8885 kJ/mol at 25 C and 46.999 - 4.5251 kJ/mol at 60 C
        self.assertAlmostEqual(phase.latent_heat(WATER, 298.15), 43987.5, delta=90.0)
        self.assertAlmostEqual(phase.latent_heat(WATER, 333.15), 42473.9, delta=130.0)
        self.assertLess(phase.latent_heat(WATER, 360.0), phase.latent_heat(WATER, 300.0))   # falls as T rises

    def test_vapour_moles_follows_the_saturation_limit(self):
        # 2 mol water with 10 mol dry gas at 1 bar and P_sat = 0.1 bar: the gas holds 10 * 0.1/0.9
        self.assertAlmostEqual(phase.vapour_moles(2.0, 10.0, 0.1), 10.0 / 9.0, places=12)
        n_v = phase.vapour_moles(2.0, 10.0, 0.1)
        self.assertAlmostEqual(n_v / (n_v + 10.0) * P0, 0.1, places=12)          # saturated
        self.assertEqual(phase.vapour_moles(2.0, 10.0, 0.5), 2.0)                 # room for all of it
        self.assertEqual(phase.vapour_moles(2.0, 10.0, 1.0), 2.0)                 # at the boiling point
        self.assertEqual(phase.vapour_moles(2.0, 10.0, 3.0), 2.0)                 # above it
        self.assertEqual(phase.vapour_moles(2.0, 0.0, 0.5), 0.0)                  # no other gas: all liquid below boiling
        self.assertEqual(phase.vapour_moles(0.0, 10.0, 0.1), 0.0)

    def test_dew_point(self):
        for y in (0.02, 0.16, 0.5, 0.9):
            T = phase.dew_point(WATER, y)
            self.assertAlmostEqual(phase.vapour_pressure(WATER, T), y * P0, places=9)
        self.assertAlmostEqual(phase.dew_point(WATER, 1.0), WATER.T_boil, places=6)   # pure steam condenses at the boiling point
        self.assertIsNone(phase.dew_point(WATER, 0.0))
        self.assertIsNone(phase.dew_point(WATER, 1.5))
        self.assertLess(phase.dew_point(WATER, 0.1), phase.dew_point(WATER, 0.2))    # wetter gas, higher dew point


# ===========================================================================
# tab 1: a reaction with every species in its stable phase
# ===========================================================================
class TestStablePhaseOfAReaction(unittest.TestCase):
    def test_swaps_to_the_stable_phase(self):
        typed = Reaction.parse("H2 + 1/2 O2 -> H2O(l)")
        hot, swaps = phase.at_temperature(typed, 500.0)
        self.assertIn("H2O(g)", hot.stoich)
        self.assertNotIn("H2O(l)", hot.stoich)
        self.assertEqual([(s["typed"], s["used"]) for s in swaps], [("H2O(l)", "H2O(g)")])
        cold, swaps = phase.at_temperature(Reaction.parse("H2 + 1/2 O2 -> H2O(g)"), 320.0)
        self.assertIn("H2O(l)", cold.stoich)
        same, swaps = phase.at_temperature(typed, 320.0)
        self.assertIs(same, typed)
        self.assertEqual(swaps, [])

    def test_swapped_reaction_stays_balanced_and_keeps_its_coefficients(self):
        typed = Reaction.parse("C7H8(l) + 9 O2 -> 7 CO2 + 4 H2O(l)")
        for T in (300.0, 380.0, 450.0):
            variant, _ = phase.at_temperature(typed, T)
            self.assertTrue(variant.is_balanced())
            self.assertEqual(sorted(variant.stoich.values()), sorted(typed.stoich.values()))

    def test_a_reaction_that_is_the_phase_change_itself_is_left_alone(self):
        typed = Reaction.parse("H2O(l) -> H2O(g)")
        used, skipped = phase.choices(typed)
        self.assertEqual(used, [])
        self.assertEqual([s["why"] for s in skipped], ["both_phases"])
        self.assertIs(phase.at_temperature(typed, 450.0)[0], typed)

    def test_acetic_acid_is_skipped_with_the_reason(self):
        used, skipped = phase.choices(Reaction.parse("CH3OH(g) + CO -> CH3COOH(l)"))
        self.assertEqual([t.compound for t in used], ["Methanol"])
        self.assertEqual([s["why"] for s in skipped], ["data"])
        self.assertIn("434", skipped[0]["message"])

    def test_pieces_cover_the_whole_temperature_axis(self):
        typed = Reaction.parse("CO2 + 3 H2 -> CH3OH + H2O")
        pieces = phase.segments(typed)
        self.assertEqual(len(pieces), 3)
        self.assertEqual(pieces[0][0], 0.0)
        self.assertEqual(pieces[-1][1], math.inf)
        for (_, hi, _), (lo, _, _) in zip(pieces, pieces[1:]):
            self.assertEqual(hi, lo)
        self.assertEqual(set(pieces[0][2].stoich), {"CO2(g)", "H2(g)", "CH3OH(l)", "H2O(l)"})
        self.assertEqual(set(pieces[1][2].stoich), {"CO2(g)", "H2(g)", "CH3OH(g)", "H2O(l)"})
        self.assertEqual(set(pieces[2][2].stoich), {"CO2(g)", "H2(g)", "CH3OH(g)", "H2O(g)"})

    def test_heat_of_reaction_jumps_by_the_latent_heat_and_gibbs_energy_does_not(self):
        typed = Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)")
        (jump,) = phase.jumps(typed)
        self.assertEqual(jump["nu"], 2.0)
        self.assertAlmostEqual(jump["dH_jump"], 2.0 * WATER.dH_vap, places=9)
        below, _ = phase.at_temperature(typed, WATER.T_boil - 1.0)
        above, _ = phase.at_temperature(typed, WATER.T_boil + 1.0)
        T = WATER.T_boil
        self.assertAlmostEqual(above.dH(T) - below.dH(T), jump["dH_jump"], places=6)
        self.assertAlmostEqual(above.dS(T) - below.dS(T), jump["dH_jump"] / T, places=8)
        self.assertAlmostEqual(above.dG(T), below.dG(T), delta=1e-4)
        self.assertAlmostEqual(jump["dH_jump"] / 1000.0, 81.73, places=2)        # 2 x 40.86 kJ

    def test_a_reactant_that_boils_makes_the_jump_negative(self):
        typed = Reaction.parse("C6H6(l) + 3 H2 -> C6H12(l)")
        by_name = {j["compound"]: j for j in phase.jumps(typed)}
        self.assertLess(by_name["Benzene"]["dH_jump"], 0.0)
        self.assertGreater(by_name["Cyclohexane"]["dH_jump"], 0.0)


class TestAnalyzeWithAutoPhase(unittest.TestCase):
    def test_off_by_default_and_nothing_changes(self):
        base = {"equation": "H2 + 1/2 O2 -> H2O(l)", "T": 500.0}
        plain = api.analyze(base)
        off = api.analyze({**base, "auto_phase": False})
        self.assertEqual(plain["at_T"], off["at_T"])
        self.assertFalse(plain["phase"]["auto"])
        self.assertIn("H2O(l)", plain["stoich"])
        # the page is still told what the stable phase would be
        self.assertEqual([(s["typed"], s["used"]) for s in plain["phase"]["swaps"]], [("H2O(l)", "H2O(g)")])
        self.assertTrue(any(w.get("kind") == "phase" for w in plain["warnings"]))

    def test_on_uses_the_stable_phase(self):
        r = api.analyze({"equation": "H2 + 1/2 O2 -> H2O(l)", "T": 500.0, "auto_phase": True})
        gas = api.analyze({"equation": "H2 + 1/2 O2 -> H2O(g)", "T": 500.0})
        self.assertIn("H2O(g)", r["stoich"])
        for key in ("dH", "dS", "dG", "lnK", "dH0"):
            self.assertAlmostEqual(r["at_T"][key], gas["at_T"][key], places=9)
        self.assertEqual(r["phase"]["equation_typed"], Reaction.parse("H2 + 1/2 O2 -> H2O(l)").equation)
        self.assertFalse(any(w.get("kind") == "phase" for w in r["warnings"]))
        self.assertFalse(any(w["level"] == "warning" for w in r["warnings"]))      # no extrapolated liquid any more
        self.assertTrue(all(c["passed"] for c in r["audit"]))
        self.assertTrue(any("Clausius" in c["name"] for c in r["audit"]))
        json.dumps(r)

    def test_typed_gas_below_the_boiling_point_becomes_liquid(self):
        r = api.analyze({"equation": "CH4 + 2 O2 -> CO2 + 2 H2O(g)", "T": 298.15, "auto_phase": True})
        self.assertAlmostEqual(r["at_T"]["dH"], -890649.0, places=3)             # the higher heating value
        self.assertIn("H2O(l)", r["stoich"])

    def test_the_plot_has_the_jump_at_the_boiling_point(self):
        r = api.analyze({"equation": "H2 + 1/2 O2 -> H2O(l)", "T": 298.15, "auto_phase": True})
        s = r["sweep"]
        self.assertAlmostEqual(s["T"][0], 273.15)
        self.assertAlmostEqual(s["T"][-1], 2000.0)                               # far beyond the liquid's 373.15 K
        at = [i for i, T in enumerate(s["T"]) if abs(T - WATER.T_boil) < 2e-6]
        self.assertEqual(len(at), 2)
        i, j = at
        self.assertAlmostEqual(s["dH"][j] - s["dH"][i], WATER.dH_vap, delta=0.01)
        self.assertAlmostEqual(s["dG"][j], s["dG"][i], delta=0.01)
        self.assertAlmostEqual(s["lnK"][j], s["lnK"][i], places=6)
        self.assertEqual(s["T"], sorted(s["T"]))
        self.assertEqual(r["valid_range"], [273.15, 6000.0])
        self.assertEqual(len(r["phase"]["pieces"]), 2)

    def test_gibbs_energy_is_continuous_along_the_whole_plot(self):
        r = api.analyze({"equation": "C7H8(l) + 9 O2 -> 7 CO2 + 4 H2O(l)", "T": 300.0, "auto_phase": True})
        s = r["sweep"]
        for a, b, Ta, Tb in zip(s["dG"], s["dG"][1:], s["T"], s["T"][1:]):
            if Tb - Ta < 1e-5:
                self.assertAlmostEqual(a, b, delta=0.05)

    def test_reaction_without_a_condensable_species_is_untouched(self):
        base = {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700.0, "P": 200.0}
        on, off = api.analyze({**base, "auto_phase": True}), api.analyze(base)
        self.assertEqual(on["at_T"], off["at_T"])
        self.assertEqual(on["sweep"], off["sweep"])
        self.assertEqual(on["equilibrium_P"]["conversion"], off["equilibrium_P"]["conversion"])
        self.assertEqual(on["phase"]["transitions"], [])
        self.assertIsNone(on["phase"]["pieces"])

    def test_crossover_is_found_in_the_right_piece(self):
        r = api.analyze({"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 300.0, "auto_phase": True})
        (Tx,) = r["crossover"]
        self.assertAlmostEqual(Tx, 320.32, places=2)
        liquid = Reaction.parse("CO2 + 3 H2 -> CH3OH(l) + H2O(l)")
        self.assertAlmostEqual(liquid.dG(Tx), 0.0, delta=1e-3)

    def test_flag_must_be_true_or_false(self):
        with self.assertRaises(InputError):
            api.analyze({"equation": "H2 + 1/2 O2 -> H2O(l)", "auto_phase": "yes"})
        with self.assertRaises(InputError):
            api.analyze({"equation": "H2 + 1/2 O2 -> H2O(l)", "auto_phase": 1})

    def test_every_library_reaction_runs_with_the_switch_on(self):
        for entry in api.get_library()["reactions"]:
            for T in (entry["T"], 298.15, 350.0):
                r = api.analyze({"equation": entry["equation"], "T": T, "auto_phase": True})
                self.assertTrue(all(c["passed"] for c in r["audit"]), f"{entry['id']} at {T}")
                json.dumps(r)


class TestConversionWhenAProductCanCondense(unittest.TestCase):
    RXN = Reaction.parse("CO2 + 3 H2 -> CH3OH + H2O")

    def setUp(self):
        self.used = phase.choices(self.RXN)[0]

    def test_an_unsaturated_vapour_stays_a_vapour(self):
        # At 350 K water is below its boiling point, yet its partial pressure
        # (0.03 bar) is far below its vapour pressure (0.41 bar): no liquid.
        e = phase.equilibrium(self.RXN, self.used, 350.0, 1.0)
        self.assertEqual(e["condensed"], [])
        gas = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        from thermosolver.equilibrium import reaction_equilibrium
        self.assertAlmostEqual(e["conversion"], reaction_equilibrium(gas, 350.0, 1.0)["conversion"], places=12)
        (row,) = [s for s in e["saturation"] if s["species"] == "H2O(g)"]
        self.assertLess(row["partial_pressure"], row["P_sat"])

    def test_no_jump_at_the_boiling_points(self):
        for t in self.used:
            below = phase.equilibrium(self.RXN, self.used, t.T_boil - 1e-6, 1.0)["conversion"]
            above = phase.equilibrium(self.RXN, self.used, t.T_boil + 1e-6, 1.0)["conversion"]
            self.assertAlmostEqual(below, above, places=6, msg=t.compound)

    def test_no_jump_where_water_starts_to_condense(self):
        # Water reaches saturation between 312 and 313 K at 1 bar.
        previous = phase.equilibrium(self.RXN, self.used, 314.0, 1.0)
        self.assertEqual(previous["condensed"], [])
        T = 314.0
        while T > 310.0:
            T -= 0.05
            e = phase.equilibrium(self.RXN, self.used, T, 1.0)
            self.assertLess(abs(e["conversion"] - previous["conversion"]), 0.003, f"at {T:.2f} K")
            previous = e
        self.assertEqual(previous["condensed"], ["H2O(l)"])

    def test_the_gas_above_a_liquid_is_saturated(self):
        e = phase.equilibrium(self.RXN, self.used, 311.0, 1.0)
        (row,) = [s for s in e["saturation"] if s["condensed"]]
        self.assertAlmostEqual(row["partial_pressure"], row["P_sat"], places=12)
        self.assertAlmostEqual(e["P_other_gases"], 1.0 - row["P_sat"], places=12)
        self.assertGreater(row["liquid_moles"], 0.0)
        self.assertGreater(row["vapour_moles"], 0.0)
        # the vapour left in the gas is what saturation allows
        other = sum(n for sid, n in e["moles"].items() if SPECIES[sid].phase == "g")
        self.assertAlmostEqual(row["vapour_moles"] / (row["vapour_moles"] + other), row["P_sat"] / 1.0, places=9)

    def test_condensing_products_pull_the_reaction_forward(self):
        gas = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        from thermosolver.equilibrium import reaction_equilibrium
        e = phase.equilibrium(self.RXN, self.used, 311.0, 1.0)
        self.assertGreater(e["conversion"], reaction_equilibrium(gas, 311.0, 1.0)["conversion"])
        # with both products liquid the gas keeps its composition, so the reaction runs to the end
        cold = phase.equilibrium(self.RXN, self.used, 290.0, 1.0)
        self.assertEqual(sorted(cold["condensed"]), ["CH3OH(l)", "H2O(l)"])
        self.assertEqual(cold["status"], "complete")

    def test_pure_water_product_condenses_below_the_boiling_point(self):
        rxn = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
        used = phase.choices(rxn)[0]
        self.assertEqual(phase.equilibrium(rxn, used, 372.0, 1.0)["condensed"], ["H2O(l)"])
        self.assertEqual(phase.equilibrium(rxn, used, 375.0, 1.0)["condensed"], [])

    def test_at_high_pressure_condensation_reaches_above_the_normal_boiling_point(self):
        e = phase.equilibrium(self.RXN, self.used, 400.0, 50.0)
        self.assertIn("H2O(l)", e["condensed"])
        self.assertTrue(e["extrapolated"])           # the liquid data end at 373.15 K
        hot = phase.equilibrium(self.RXN, self.used, 523.0, 50.0)
        self.assertEqual(hot["condensed"], [])
        self.assertFalse(hot["extrapolated"])
        self.assertAlmostEqual(hot["conversion"], 0.2135, places=3)       # the value of the report: 21.3 %

    def test_nothing_condenses_above_the_critical_temperature(self):
        e = phase.equilibrium(self.RXN, self.used, 700.0, 4000.0)
        self.assertEqual(e["saturation"], [])
        self.assertEqual(e["condensed"], [])

    def test_analyze_reports_the_same_conversion(self):
        r = api.analyze({"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 311.0, "auto_phase": True})
        self.assertAlmostEqual(r["equilibrium"]["conversion"], phase.equilibrium(self.RXN, self.used, 311.0, 1.0)["conversion"])
        self.assertEqual(r["equilibrium"]["condensed"], ["H2O(l)"])
        conv = r["sweep"]["conversion_1bar"]
        self.assertTrue(all(c is not None and 0.0 <= c <= 1.0 for c in conv))


# ===========================================================================
# tab 5: the water of the outlet finds its phase
# ===========================================================================
class TestWaterSplit(unittest.TestCase):
    def setUp(self):
        self.split = heatbalance.WaterSplit(burner_case()["outlet"])

    def test_dew_point_of_the_flue_gas(self):
        s = self.split
        self.assertAlmostEqual(s.n_water, 2.0)
        self.assertAlmostEqual(s.n_other_gas, 0.4 + 2.4 * 79.0 / 21.0 + 1.0, places=9)
        self.assertAlmostEqual(s.y_all_vapour, 0.16092, places=5)
        # NIST WebBook: water boils at 328.58 K under 0.16092 bar
        self.assertAlmostEqual(s.T_dew, 328.58, delta=0.15)
        self.assertAlmostEqual(phase.vapour_pressure(WATER, s.T_dew), s.y_all_vapour, places=9)

    def test_all_vapour_above_the_dew_point_and_saturated_below(self):
        s = self.split
        for T in (s.T_dew + 0.01, 400.0, 1000.0, 2500.0):
            self.assertEqual(s.vapour(T), s.n_water)
        for T in (s.T_dew - 0.01, 320.0, 298.15, 280.0):
            n_v = s.vapour(T)
            self.assertLess(n_v, s.n_water)
            self.assertAlmostEqual(n_v / (n_v + s.n_other_gas) * P0, phase.vapour_pressure(WATER, T), places=10)

    def test_enthalpy_is_continuous_and_rises_with_temperature(self):
        s = self.split
        self.assertAlmostEqual(s.H(s.T_dew - 1e-7), s.H(s.T_dew + 1e-7), delta=0.05)
        Ts = [275.0 + 0.5 * i for i in range(260)]
        Hs = [s.H(T) for T in Ts]
        self.assertEqual(Hs, sorted(Hs))
        # below the dew point the stream gives up much more heat per kelvin
        self.assertGreater((s.H(320.0) - s.H(319.0)) / (s.H(340.0) - s.H(339.0)), 5.0)

    def test_written_phase_of_the_water_does_not_matter(self):
        liquid_form = heatbalance.WaterSplit(burner_case("CH4 + 2 O2 -> CO2 + 2 H2O(l)")["outlet"])
        self.assertAlmostEqual(liquid_form.n_written_liquid, 2.0)
        for T in (290.0, 320.0, 500.0):
            self.assertAlmostEqual(liquid_form.H(T), self.split.H(T), places=6)
            self.assertAlmostEqual(liquid_form.vapour(T), self.split.vapour(T), places=12)

    def test_first_and_second_law_agree_along_the_saturation_line(self):
        s = self.split
        for T in (285.0, 300.0, 320.0):
            h = 0.01
            self.assertAlmostEqual((s.H(T + h) - s.H(T - h)), T * (s.S(T + h) - s.S(T - h)), delta=1e-5 * abs(s.H(T + h) - s.H(T - h)))


class TestHeatBalanceWithCondensation(unittest.TestCase):
    def solve(self, equation=BURNER, **kw):
        return heatbalance.solve(burner_case(equation), T0, **kw)

    def test_off_by_default(self):
        flame = self.solve(mode="adiabatic")
        self.assertAlmostEqual(flame["T_out"], 2068.8, places=1)
        self.assertFalse(flame["water"]["applied"])
        self.assertEqual(flame["path"]["dH_phase"], 0.0)
        cold = self.solve(mode="duty", T_out=310.0)
        self.assertAlmostEqual(cold["Q"], -798126.7, delta=0.5)
        self.assertEqual([n["kind"] for n in cold["notes"]], ["would_condense"])      # it says what is left out

    def test_no_effect_above_the_dew_point(self):
        for T_out in (330.0, 400.0, 1500.0):
            on = self.solve(mode="duty", T_out=T_out, condense=True)
            off = self.solve(mode="duty", T_out=T_out)
            self.assertAlmostEqual(on["Q"], off["Q"], places=6)
            self.assertEqual(on["water"]["n_liquid"], 0.0)
            self.assertEqual(on["path"]["dH_phase"], 0.0)
        self.assertAlmostEqual(self.solve(mode="adiabatic", condense=True)["T_out"],
                               self.solve(mode="adiabatic")["T_out"], places=6)

    def test_below_the_dew_point_the_latent_heat_is_recovered(self):
        on = self.solve(mode="duty", T_out=310.0, condense=True)
        off = self.solve(mode="duty", T_out=310.0)
        w = on["water"]
        self.assertAlmostEqual(w["n_liquid"], 1.3081, places=4)
        self.assertAlmostEqual(w["n_vapour"] + w["n_liquid"], 2.0, places=12)
        self.assertAlmostEqual(on["Q"] - off["Q"], -w["n_liquid"] * phase.latent_heat(WATER, 310.0), places=6)
        self.assertAlmostEqual(on["Q"] / 1000.0, -855.05, places=2)
        self.assertAlmostEqual(off["Q"] / 1000.0, -798.13, places=2)
        self.assertAlmostEqual(w["as_written"]["Q"], off["Q"], places=6)
        self.assertAlmostEqual(on["path"]["dH_phase"], on["Q"] - off["Q"], places=6)
        self.assertAlmostEqual(on["path"]["total"], on["Q"], places=6)
        # the gas leaves saturated
        self.assertAlmostEqual(w["n_vapour"] / (w["n_vapour"] + w["n_other_gas"]), w["P_sat"], places=10)
        self.assertEqual(on["outlet"]["H2O(l)"], w["n_liquid"])
        self.assertEqual([n["kind"] for n in on["notes"]], ["condensation"])
        self.assertEqual(on["warnings"], [])

    def test_at_25_degrees_the_heat_lies_between_the_two_heating_values(self):
        on = self.solve(mode="duty", T_out=T0, condense=True)
        fuel = heatbalance.fuel_facts(Reaction.parse(BURNER))
        self.assertAlmostEqual(fuel["LHV"], 802625.0, places=3)
        self.assertAlmostEqual(fuel["HHV"], 890649.0, places=3)
        self.assertTrue(fuel["LHV"] < -on["Q"] < fuel["HHV"])
        self.assertAlmostEqual(-on["Q"] / 1000.0, 875.63, places=2)
        # not all of the water condenses: the flue gas stays saturated and carries 0.34 mol away
        self.assertAlmostEqual(on["water"]["n_vapour"], 0.3412, places=4)
        self.assertAlmostEqual(-on["Q"], fuel["LHV"] + on["water"]["n_liquid"] * 44012.0, places=3)

    def test_with_nothing_but_water_in_the_outlet_the_full_higher_heating_value_comes_out(self):
        case = heatbalance.build_case(Reaction.parse("H2 + 1/2 O2 -> H2O(g)"))
        on = heatbalance.solve(case, T0, "duty", T_out=T0, condense=True)
        self.assertAlmostEqual(on["Q"], -285830.0, places=6)                 # dHf of liquid water
        self.assertEqual(on["outlet"], {"H2O(l)": 1.0})
        self.assertAlmostEqual(heatbalance.solve(case, T0, "duty", T_out=T0)["Q"], -241818.0, places=6)

    def test_reaction_written_with_liquid_water_gives_the_same_answers(self):
        liquid_form = "CH4 + 2 O2 -> CO2 + 2 H2O(l)"
        for kw in ({"mode": "adiabatic"}, {"mode": "duty", "T_out": 310.0}, {"mode": "duty", "T_out": 900.0}):
            a = self.solve(condense=True, **kw)
            b = self.solve(liquid_form, condense=True, **kw)
            self.assertAlmostEqual(a["T_out"], b["T_out"], places=6)
            self.assertAlmostEqual(a["Q"], b["Q"], places=4)
            self.assertAlmostEqual(a["path"]["dH_298"], b["path"]["dH_298"], places=4)   # both on the vapour basis
            self.assertTrue(all(c["passed"] for c in b["audit"]))
        hot = self.solve(liquid_form, mode="adiabatic", condense=True)
        self.assertIn("evaporation", [n["kind"] for n in hot["notes"]])
        self.assertEqual(hot["warnings"], [])                                # no liquid stretched to 2000 K
        # with the switch off the old behaviour and its warning remain
        kept = self.solve(liquid_form, mode="adiabatic")
        self.assertTrue(any(w["species"] == "H2O(l)" for w in kept["warnings"]))
        self.assertIn("would_evaporate", [n["kind"] for n in kept["notes"]])

    def test_adiabatic_mode_finds_the_same_state_as_the_duty_mode(self):
        for T_out in (290.0, 310.0, 325.0, 340.0):
            duty = self.solve(mode="duty", T_out=T_out, condense=True)
            back = self.solve(mode="adiabatic", Q=duty["Q"], condense=True)
            self.assertAlmostEqual(back["T_out"], T_out, places=6)
            self.assertAlmostEqual(back["water"]["n_vapour"], duty["water"]["n_vapour"], places=7)
            self.assertTrue(all(c["passed"] for c in back["audit"]), T_out)

    def test_heat_duty_has_no_jump_at_the_dew_point_and_rises_with_the_outlet_temperature(self):
        T_dew = heatbalance.WaterSplit(burner_case()["outlet"]).T_dew
        below = self.solve(mode="duty", T_out=T_dew - 1e-6, condense=True)["Q"]
        above = self.solve(mode="duty", T_out=T_dew + 1e-6, condense=True)["Q"]
        self.assertAlmostEqual(below, above, delta=0.5)
        Qs = [self.solve(mode="duty", T_out=T, condense=True)["Q"] for T in range(285, 400, 5)]
        self.assertEqual(Qs, sorted(Qs))

    def test_pure_steam_outlet_boils_at_one_temperature(self):
        case = heatbalance.build_case(Reaction.parse("H2 + 1/2 O2 -> H2O(g)"))
        # between all liquid (-282.4 kJ) and all vapour (-239.3 kJ) at the boiling point
        r = heatbalance.solve(case, T0, "adiabatic", Q=-260e3, condense=True)
        self.assertAlmostEqual(r["T_out"], WATER.T_boil, places=6)
        self.assertTrue(0.0 < r["water"]["n_vapour"] < 1.0)
        self.assertAlmostEqual(r["H_out"] - r["H_in"], -260e3, places=4)
        self.assertTrue(all(c["passed"] for c in r["audit"]))
        self.assertEqual(r["warnings"], [])
        # the lever rule: the vapour fraction is the share of the latent heat that is left
        liquid = heatbalance.solve(case, T0, "duty", T_out=WATER.T_boil - 1e-9, condense=True)["Q"]
        self.assertAlmostEqual(r["water"]["n_vapour"], (-260e3 - liquid) / WATER.dH_vap, places=6)
        cold = heatbalance.solve(case, T0, "adiabatic", Q=-284e3, condense=True)
        self.assertLess(cold["T_out"], WATER.T_boil)
        self.assertEqual(cold["outlet"], {"H2O(l)": 1.0})
        hot = heatbalance.solve(case, T0, "adiabatic", Q=-230e3, condense=True)
        self.assertGreater(hot["T_out"], WATER.T_boil)
        self.assertEqual(hot["outlet"], {"H2O(g)": 1.0})

    def test_every_check_passes_when_water_condenses(self):
        r = self.solve(mode="duty", T_out=305.0, condense=True)
        names = [c["name"] for c in r["audit"]]
        for expected in ("Atoms are conserved", "Two routes to the heat Q", "Energy balance closes",
                         "The gas is saturated with water", "Clausius/Clapeyron equation for water",
                         "Enthalpy and entropy of the outlet agree while water condenses"):
            self.assertIn(expected, names)
        for c in r["audit"]:
            self.assertTrue(c["passed"], c["name"])

    def test_textbook_examples_are_untouched_by_the_switch(self):
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        case = heatbalance.build_case(smr, excess_species="H2O(g)", excess=1.0, side=[(wgs, 0.13)])
        on = heatbalance.solve(case, 600.0, "duty", T_out=1300.0, condense=True)
        off = heatbalance.solve(case, 600.0, "duty", T_out=1300.0)
        self.assertAlmostEqual(on["Q"], off["Q"], places=6)
        self.assertAlmostEqual(on["Q"], 328010.0, delta=10.0)
        for key in ("dH_R", "dH_298", "dH_P"):
            self.assertAlmostEqual(on["path"][key], off["path"][key], places=6)

    def test_freezing_is_flagged(self):
        r = self.solve(mode="duty", T_out=265.0, condense=True)
        self.assertIn("freezing", [n["kind"] for n in r["notes"]])

    def test_other_vapours_that_would_condense_are_named(self):
        case = heatbalance.build_case(Reaction.parse("CO + 2 H2 -> CH3OH(g)"), conversion=0.5)
        r = heatbalance.solve(case, 500.0, "duty", T_out=300.0, condense=True)
        (note,) = r["notes"]
        self.assertEqual(note["kind"], "other_condensable")
        self.assertIn("CH3OH(g)", note["message"])
        self.assertIsNone(r["water"])                                       # no water in this outlet
        warm = heatbalance.solve(case, 500.0, "duty", T_out=330.0, condense=True)
        self.assertEqual(warm["notes"], [])

    def test_work_potential_counts_the_condensation_on_the_way_down(self):
        case = burner_case()
        dry = heatbalance.work_potential(case, 2000.0)
        wet = heatbalance.work_potential(case, 2000.0, condense=True)
        self.assertAlmostEqual(wet["water_condensed"], 1.6588, places=4)
        self.assertLess(wet["dH"], dry["dH"])                 # more heat comes out
        self.assertLess(wet["W_ideal"], dry["W_ideal"])       # and a little more work
        # Above the dew point nothing condenses, and the two routes (entropy of the
        # mixture against the integral of Cp dT/T) must give the same numbers.
        a = heatbalance.work_potential(case, 2000.0, T_surroundings=350.0)
        b = heatbalance.work_potential(case, 2000.0, T_surroundings=350.0, condense=True)
        self.assertAlmostEqual(a["dH"], b["dH"], places=5)
        self.assertAlmostEqual(a["dS"], b["dS"], places=8)
        self.assertEqual(b["water_condensed"], 0.0)


class TestHeatBalanceEndpointWithCondensation(unittest.TestCase):
    BASE = {"equation": BURNER, "excess": 0.2, "air": True, "T_in": 298.15}

    def test_endpoint_passes_the_setting_on(self):
        on = api.heat_balance({**self.BASE, "mode": "duty", "T_out": 310.0, "condense": True})
        off = api.heat_balance({**self.BASE, "mode": "duty", "T_out": 310.0})
        self.assertTrue(on["settings"]["condense"])
        self.assertFalse(off["settings"]["condense"])
        self.assertAlmostEqual(on["point"]["Q"] / 1000.0, -855.05, places=2)
        self.assertAlmostEqual(off["point"]["Q"] / 1000.0, -798.13, places=2)
        self.assertIn(on["point"]["water"]["T_dew"], on["curves"]["T"])       # the bend of the enthalpy line is a plot point
        json.dumps(on)

    def test_sweep_and_goal_seek_use_it(self):
        r = api.heat_balance({**self.BASE, "mode": "duty", "T_out": 310.0, "condense": True,
                              "sweep": "T_out", "sweep_min": 290, "sweep_max": 400, "n_points": 12})
        liquid = r["sweep"]["water_liquid"]
        self.assertGreater(liquid[0], 1.5)
        self.assertEqual(liquid[-1], 0.0)
        self.assertEqual(r["sweep"]["Q"], sorted(r["sweep"]["Q"]))
        goal = api.heat_balance({**self.BASE, "mode": "adiabatic", "condense": True, "target_T": 1500})
        plain = api.heat_balance({**self.BASE, "mode": "adiabatic", "target_T": 1500})
        self.assertAlmostEqual(goal["target"]["excess"], plain["target"]["excess"], places=8)

    def test_flag_must_be_true_or_false(self):
        with self.assertRaises(InputError):
            api.heat_balance({**self.BASE, "condense": "true"})

    def test_every_example_runs_with_the_switch_on_and_hot_examples_do_not_change(self):
        for ex in api.get_library()["heat_examples"]:
            payload = {k: ex[k] for k in ("equation", "mode", "T_in", "conversion", "excess", "air", "side") if k in ex}
            if ex.get("excess_species"):
                payload["excess_species"] = ex["excess_species"]
            if ex.get("T_out"):
                payload["T_out"] = ex["T_out"]
            off = api.heat_balance(payload)
            on = api.heat_balance({**payload, "condense": True})
            self.assertTrue(all(c["passed"] for c in on["point"]["audit"]), ex["id"])
            if ex.get("condense"):
                # the one example that is about condensation: 40 C is below the dew point
                self.assertEqual(ex["id"], "condensing_boiler")
                self.assertAlmostEqual(off["point"]["Q"] / 1000.0, -796.93, places=2)
                self.assertAlmostEqual(on["point"]["Q"] / 1000.0, -847.69, places=2)
                self.assertGreater(on["point"]["water"]["n_liquid"], 1.0)
                continue
            self.assertAlmostEqual(on["point"]["T_out"], off["point"]["T_out"], places=6, msg=ex["id"])
            self.assertAlmostEqual(on["point"]["Q"], off["point"]["Q"], places=4, msg=ex["id"])


class TestThePage(unittest.TestCase):
    """The two switches exist on the page and are sent to the solver."""

    def read(self, *parts):
        with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
            return fh.read()

    def test_tab_1_has_the_stable_phase_box_and_it_is_off_at_the_start(self):
        html = self.read("index.html")
        self.assertRegex(html, r'<input type="checkbox" id="rx-auto-phase">')       # not ticked: typed phases are respected
        script = self.read("web", "tab-reaction.js")
        self.assertIn('auto_phase: $("#rx-auto-phase").checked', script)
        self.assertIn("rx-use-stable", script)

    def test_condensing_water_stays_in_the_solver_after_the_reactor_view_left_the_page(self):
        # Tab 5 no longer shows the reactor view (23 November 2026), but the calculation is kept.
        self.assertNotIn("hb-condense", self.read("index.html"))
        r = api.heat_balance({"equation": BURNER, "excess": 0.2, "air": True, "T_in": 298.15,
                              "mode": "duty", "T_out": 310.0, "condense": True})
        self.assertAlmostEqual(r["point"]["Q"] / 1000.0, -855.05, places=2)

    def test_the_page_does_not_work_out_the_phase_itself(self):
        # boiling points, vapour pressures and latent heats come from the solver
        for name in ("tab-reaction.js", "tab-heat.js"):
            script = self.read("web", name)
            for number in ("373.15", "373.2", "44012", "40.66", "2257"):
                self.assertNotIn(number, script, f"{number} in {name}")


if __name__ == "__main__":
    unittest.main()
