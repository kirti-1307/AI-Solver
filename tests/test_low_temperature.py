"""Heat capacities from 200 K to 298.15 K (NIST tables).

SVN's heat-capacity tables start at 298 K. Below that the solver uses
tabulated values from the NIST-JANAF tables and the NIST Chemistry WebBook.
These tests check the transcription of those rows against the tables' own
other columns, the way the solver switches between the two sources, and that
nothing above 298.15 K has changed.
"""

import json
import math
import unittest

from thermosolver import api, data
from thermosolver import heatbalance as hb
from thermosolver.audit import audit_reaction
from thermosolver.constants import R, T0
from thermosolver.heatcap import cp_over_r, icph, quadratic_through, quadratic_with_integral, simpson
from thermosolver.reaction import Reaction
from thermosolver.species import SPECIES, low_temperature_sets


def ok(endpoint, payload):
    out = json.loads(api.call(endpoint, json.dumps(payload)))
    assert out["ok"], out
    return out["result"]


class TestQuadratics(unittest.TestCase):
    def test_quadratic_through_three_points(self):
        c = quadratic_through([(1.0, 6.0), (2.0, 11.0), (3.0, 18.0)])       # y = 3 + 2 T + T^2
        for got, want in zip(c, (3.0, 2.0, 1.0, 0.0, 0.0)):
            self.assertAlmostEqual(got, want, places=10)
        with self.assertRaises(ValueError):
            quadratic_through([(1.0, 1.0), (2.0, 2.0)])
        with self.assertRaises(ValueError):
            quadratic_through([(1.0, 1.0), (1.0, 2.0), (3.0, 3.0)])         # two points at one temperature

    def test_quadratic_with_a_prescribed_integral(self):
        # y = 3 + 2 T + T^2: integral from 3 to 1 is -(6 + 8 + 26/3)
        c = quadratic_with_integral((1.0, 6.0), (3.0, 18.0), -(6.0 + 8.0 + 26.0 / 3.0))
        for got, want in zip(c, (3.0, 2.0, 1.0, 0.0, 0.0)):
            self.assertAlmostEqual(got, want, places=10)


class TestTheTabulatedRows(unittest.TestCase):
    def test_shape_of_the_tables(self):
        for sid, (table, rows) in data.JANAF_LOW_T.items():
            self.assertIn(sid, SPECIES, sid)
            self.assertEqual(rows[0][0], data.LOW_T_MIN, sid)
            self.assertEqual(rows[-1][0], T0, sid)
            self.assertEqual(rows[-1][3], 0.0, sid)                  # H - H(298.15 K) is zero at 298.15 K
            self.assertIn(len(rows), (2, 3), sid)
            self.assertRegex(table, r"^[A-Z][a-z]?-\d{3}$")
            for T, cp, S, H in rows:
                self.assertGreater(cp, 0.0, sid)
                self.assertGreater(S, 0.0, sid)
        for sid, (webbook_id, reference, rows) in data.WEBBOOK_LOW_T.items():
            self.assertIn(sid, SPECIES, sid)
            self.assertEqual(SPECIES[sid].phase, "g", sid)
            self.assertEqual(len(rows), 3, sid)
            self.assertEqual(rows[-1][0], T0, sid)
            self.assertIn(data.LOW_T_MIN, [T for T, _ in rows], sid)
            self.assertRegex(webbook_id, r"^C\d+$")
            self.assertTrue(reference)
        self.assertEqual(set(data.JANAF_LOW_T) & set(data.WEBBOOK_LOW_T), set())

    def test_every_tabulated_heat_capacity_is_reproduced(self):
        for sid, (_, rows) in data.JANAF_LOW_T.items():
            sp = SPECIES[sid]
            for T, cp, _, _ in (rows[0], rows[-1]):
                # just below 298.15 K, where the low-temperature set applies
                got = R * cp_over_r(sp.cp_low, T)
                self.assertAlmostEqual(got, cp, places=9, msg=f"{sid} at {T} K")
        for sid, (_, _, rows) in data.WEBBOOK_LOW_T.items():
            sp = SPECIES[sid]
            for T, cp in rows:
                self.assertAlmostEqual(R * cp_over_r(sp.cp_low, T), cp, places=9, msg=f"{sid} at {T} K")

    def test_the_tabulated_enthalpy_at_200_K_is_carried_exactly(self):
        for sid, (_, rows) in data.JANAF_LOW_T.items():
            T, _, _, H = rows[0]
            self.assertAlmostEqual(SPECIES[sid].sensible_dH(T0, T), H * 1000.0, places=6, msg=sid)

    def test_the_250_K_rows_were_not_used_and_are_reproduced(self):
        checked = 0
        for sid, (_, rows) in data.JANAF_LOW_T.items():
            if len(rows) != 3:
                continue
            T, cp, S, H = rows[1]
            self.assertEqual(T, 250.0)
            sp = SPECIES[sid]
            self.assertAlmostEqual(sp.cp_J(T), cp, delta=0.01, msg=f"{sid} Cp")            # J/(mol K)
            self.assertAlmostEqual(sp.sensible_dH(T0, T), H * 1000.0, delta=1.5, msg=f"{sid} H")   # J/mol
            self.assertAlmostEqual(sp.sensible_dS(T0, T), S - rows[-1][2], delta=0.005, msg=f"{sid} S")
            checked += 1
        self.assertEqual(checked, 14)

    def test_the_entropy_column_was_not_used_and_is_reproduced(self):
        checked = 0
        for sid, (_, rows) in data.JANAF_LOW_T.items():
            T, _, S, _ = rows[0]
            error = SPECIES[sid].sensible_dS(T0, T) - (S - rows[-1][2])
            if sid in data.LOW_T_ENTROPY_EXCEPTIONS:
                continue
            self.assertLess(abs(error), 0.03, f"{sid}: {error:+.4f} J/(mol K)")
            checked += 1
        self.assertEqual(checked, len(data.JANAF_LOW_T) - 1)

    def test_the_one_entropy_exception_is_in_the_table_not_in_the_transcription(self):
        # H2S: the enthalpy column agrees with the heat capacities (that is the
        # fit), the entropy column is 0.26 J/(mol K) away from them. A wrong
        # digit in Cp or H could not produce that, because any curve with the
        # right mean heat capacity gives nearly the same entropy change.
        self.assertEqual(set(data.LOW_T_ENTROPY_EXCEPTIONS), {"H2S(g)"})
        _, rows = data.JANAF_LOW_T["H2S(g)"]
        (T, cp200, S200, H200), (_, cp298, S298, _) = rows
        mean_cp = -H200 * 1000.0 / (T0 - T)
        self.assertTrue(cp200 < mean_cp < cp298)                               # enthalpy column is plausible
        from_cp = mean_cp * math.log(T / T0)
        self.assertAlmostEqual(SPECIES["H2S(g)"].sensible_dS(T0, T), from_cp, delta=0.02)
        self.assertAlmostEqual((S200 - S298) - from_cp, -0.26, delta=0.02)

    def test_hydrogen_peroxide_is_left_out_for_a_stated_reason(self):
        # NIST-JANAF table H-070: Cp = 36.874 at 200 K and 43.116 at 298.15 K,
        # S = 210.632 and 232.991. No heat capacity between 36.9 and 43.1 can
        # give an entropy rise of 22.4 J/(mol K) over that interval.
        self.assertIsNone(SPECIES["H2O2(g)"].cp_low)
        self.assertIn("H2O2(g)", data.LOW_T_NOT_COVERED)
        largest = 43.116 * math.log(T0 / 200.0)
        self.assertLess(largest, 232.991 - 210.632 - 5.0)

    def test_ethane_against_measured_values(self):
        sp = SPECIES["C2H6(g)"]
        for T, measured in data.ETHANE_MEASURED_CP:
            self.assertAlmostEqual(sp.cp_J(T) / measured, 1.0, delta=0.01, msg=f"{T} K")


class TestCoverage(unittest.TestCase):
    def test_every_svn_gas_and_six_solids_are_covered(self):
        sets = low_temperature_sets()
        self.assertEqual(len(sets), 47)
        gases = [sp for sp in SPECIES.values() if sp.phase == "g"]
        self.assertEqual([sp.id for sp in gases if sp.cp_low is None], ["H2O2(g)"])
        self.assertEqual(sum(1 for sp in gases if sp.from_svn and sp.cp_low is not None), 40)
        solids = {sp.id for sp in SPECIES.values() if sp.phase == "s"}
        self.assertEqual({s for s in solids if SPECIES[s].cp_low is None}, {"CaCO3(s)", "CaC2(s)"})
        self.assertTrue(all(sp.cp_low is None for sp in SPECIES.values() if sp.phase == "l"))
        missing = {sp.id for sp in SPECIES.values() if sp.phase != "l" and sp.cp_low is None}
        self.assertEqual(missing, set(data.LOW_T_NOT_COVERED))

    def test_ranges_and_sources(self):
        for sp in SPECIES.values():
            if sp.cp_low is None:
                if sp.cp is not None:
                    self.assertEqual(sp.cp_main_Tmin, sp.cp_Tmin, sp.id)
                continue
            self.assertEqual(sp.cp_Tmin, 200.0, sp.id)
            self.assertEqual(sp.cp_main_Tmin, 298.0, sp.id)
            self.assertIn("NIST", sp.cp_low_source, sp.id)
            self.assertEqual(sp.cp_source_at(250.0), sp.cp_low_source)
            self.assertEqual(sp.cp_source_at(T0), sp.cp_source)
            self.assertEqual(sp.cp_low[3:], (0.0, 0.0), sp.id)        # a quadratic: no D, no E
            self.assertTrue(sp.in_cp_range(200.0) and sp.in_cp_range(250.0))
            self.assertFalse(sp.in_cp_range(199.0))
            for i in range(21):                                         # positive and rising smoothly enough
                T = 200.0 + (T0 - 200.0) * i / 20
                self.assertGreater(sp.cp_R(T), 0.0, f"{sp.id} at {T} K")

    def test_svn_data_above_298_K_are_untouched(self):
        ch4 = SPECIES["CH4(g)"]
        self.assertEqual(ch4.cp, (1.702, 9.081e-3, -2.164e-6, 0.0, 0.0))
        self.assertIs(ch4.coeffs_at(T0), ch4.cp)
        self.assertIs(ch4.coeffs_at(1000.0), ch4.cp)
        self.assertIs(ch4.coeffs_at(T0 - 1e-9), ch4.cp_low)
        self.assertAlmostEqual(ch4.sensible_dH(533.15, 873.15), 19778.0, delta=1.0)     # SVN example
        meoh = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
        self.assertAlmostEqual(meoh.dH(1073.15), -103566.0, delta=2.0)                  # SVN example
        self.assertEqual(meoh.delta_coeffs(), meoh.delta_coeffs(500.0))
        self.assertNotEqual(meoh.delta_coeffs(), meoh.delta_coeffs(250.0))


class TestTheJoinAt298K(unittest.TestCase):
    def test_enthalpy_entropy_and_gibbs_energy_are_continuous(self):
        eps = 1e-7
        for sp in SPECIES.values():
            if sp.cp_low is None:
                continue
            self.assertAlmostEqual(sp.H(T0 - eps), sp.H(T0 + eps), delta=1e-3, msg=sp.id)
            self.assertAlmostEqual(sp.S(T0 - eps), sp.S(T0 + eps), delta=1e-6, msg=sp.id)
            self.assertAlmostEqual(sp.G(T0 - eps), sp.G(T0 + eps), delta=1e-3, msg=sp.id)
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        self.assertAlmostEqual(rxn.dH(T0 - eps), rxn.dH0, delta=1e-3)
        self.assertAlmostEqual(rxn.lnK(T0 - eps), rxn.lnK(T0), delta=1e-8)

    def test_size_of_the_step_in_heat_capacity(self):
        # The two sources do not give the same Cp at 298.15 K. The step is
        # reported, not hidden: these are the numbers quoted in the data notes.
        step = {sp.id: cp_over_r(sp.cp, T0) / cp_over_r(sp.cp_low, T0) - 1.0
                for sp in SPECIES.values() if sp.cp_low is not None}
        self.assertEqual(sum(1 for v in step.values() if abs(v) < 0.01), 25)
        self.assertEqual(max(step, key=lambda s: abs(step[s])), "C2H5OH(g)")
        self.assertAlmostEqual(step["C2H5OH(g)"], 0.141, delta=0.002)
        self.assertAlmostEqual(step["C8H8(g)"], 0.075, delta=0.002)
        self.assertAlmostEqual(step["Ca(OH)2(s)"], 0.066, delta=0.002)
        self.assertAlmostEqual(step["CH3OH(g)"], 0.047, delta=0.002)
        self.assertLess(abs(step["CO2(g)"]), 0.001)
        self.assertLess(abs(step["H2(g)"]), 0.001)
        self.assertLess(abs(step["H2O(g)"]), 0.001)

    def test_sensible_heat_across_the_join(self):
        for sid in ("CO2(g)", "CH3OH(g)", "C2H5OH(g)", "C(s)"):
            sp = SPECIES[sid]
            whole = sp.sensible_dH(220.0, 400.0)
            parts = sp.sensible_dH(220.0, T0) + sp.sensible_dH(T0, 400.0)
            self.assertAlmostEqual(whole, parts, places=8, msg=sid)
            self.assertAlmostEqual(sp.sensible_dH(400.0, 220.0), -whole, places=8, msg=sid)
            numeric = (R * simpson(lambda t: cp_over_r(sp.cp_low, t), 220.0, T0)
                       + R * simpson(lambda t: cp_over_r(sp.cp, t), T0, 400.0))
            self.assertAlmostEqual(whole, numeric, delta=1e-6 * abs(whole), msg=sid)
            ds = sp.sensible_dS(220.0, 400.0)
            self.assertAlmostEqual(ds, sp.sensible_dS(220.0, T0) + sp.sensible_dS(T0, 400.0), places=10)
            self.assertTrue(sp.cp_J(220.0) * math.log(400 / 220) < ds < sp.cp_J(400.0) * math.log(400 / 220))

    def test_extrapolating_svn_downwards_would_have_been_wrong(self):
        # the reason the low-temperature data exist at all
        co2 = SPECIES["CO2(g)"]
        extrapolated = R * cp_over_r(co2.cp, 200.0)
        self.assertAlmostEqual(extrapolated / 32.359, 0.71, delta=0.01)        # 29 % too low
        graphite = SPECIES["C(s)"]
        self.assertLess(cp_over_r(graphite.cp, 200.0), 0.0)                    # a negative heat capacity
        self.assertAlmostEqual(co2.cp_J(200.0), 32.359, places=9)
        self.assertAlmostEqual(graphite.cp_J(200.0), 5.006, places=9)


class TestReactionsBelow298K(unittest.TestCase):
    def test_water_gas_shift_at_200_K_from_the_table_columns(self):
        # dH(200 K) = dH298 (SVN) + sum of nu * [H(200) - H(298.15)] (NIST-JANAF)
        rxn = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        increments = -3414.0 - 2774.0 + 2858.0 + 3282.0
        self.assertAlmostEqual(rxn.dH0, -41166.0, places=6)
        self.assertAlmostEqual(rxn.dH(200.0), -41166.0 + increments, places=6)
        entropy = (199.975 - 213.795) + (119.412 - 130.680) - (186.025 - 197.653) - (175.485 - 188.834)
        self.assertAlmostEqual(rxn.dS(200.0) - rxn.dS0, entropy, delta=0.02)

    def test_ammonia_synthesis_at_200_K(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        self.assertAlmostEqual(rxn.dH(200.0), -92220.0 + 2 * (-3394.0) + 2857.0 + 3 * 2774.0, places=6)

    def test_co2_to_methanol_below_298_K(self):
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        self.assertEqual(rxn.valid_range(), (200.0, 1500.0))
        # the methanol term is the integral of its NIST curve; the others are table columns
        meoh = SPECIES["CH3OH(g)"].sensible_dH(T0, 200.0)
        # straight lines between the three tabulated points, J/mol
        by_hand = -((39.71 + 42.59) / 2 * 73.15 + (42.59 + 44.06) / 2 * 25.0)
        self.assertAlmostEqual(meoh, by_hand, delta=20.0)
        self.assertAlmostEqual(rxn.dH(200.0), -48969.0 + meoh - 3282.0 + 3414.0 + 3 * 2774.0, places=6)
        self.assertAlmostEqual(rxn.dH(250.0), -46770.0, delta=5.0)
        # exothermic with fewer gas moles: it turns favourable when the gas is cold enough
        self.assertGreater(rxn.dG(T0), 0.0)
        self.assertLess(rxn.dG(250.0), 0.0)
        cross = rxn.crossover_temperatures()
        self.assertEqual(len(cross), 1)
        self.assertAlmostEqual(cross[0], 276.3, delta=0.3)
        self.assertAlmostEqual(rxn.dG(cross[0]), 0.0, delta=1e-4)

    def test_consistency_audit_passes_below_and_right_at_the_join(self):
        for eq in ("CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "C2H4 + H2O(g) -> C2H5OH(g)", "N2 + 3 H2 -> 2 NH3",
                   "C(s) + CO2 -> 2 CO", "Fe2O3 + 3 H2 -> 2 Fe + 3 H2O(g)"):
            rxn = Reaction.parse(eq)
            for T in (200.0, 231.7, 273.15, 298.0, 298.14, 298.149, 298.151, 298.16, 298.3, 350.0):
                failed = [c["name"] for c in audit_reaction(rxn, T) if not c["passed"]]
                self.assertEqual(failed, [], f"{eq} at {T} K")

    def test_evaluate_reports_which_constants_were_used(self):
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        cold, warm = rxn.evaluate(250.0), rxn.evaluate(400.0)
        self.assertEqual(cold["low_T_species"], ["CO2(g)", "H2(g)", "CH3OH(g)", "H2O(g)"])
        self.assertEqual(warm["low_T_species"], [])
        self.assertEqual(cold["dD"], 0.0)                         # the low-temperature sets have no D term
        self.assertNotEqual(warm["dD"], 0.0)
        self.assertEqual(cold["dCp0"], warm["dCp0"])              # the SVN value at 298.15 K in both
        self.assertAlmostEqual(cold["dH"], cold["dH0"] + R * icph(T0, 250.0, rxn.delta_coeffs(250.0)), places=6)
        rows = {r["id"]: r for r in rxn.species_table(250.0)}
        self.assertTrue(all(r["cp_from_low_T_table"] and r["in_cp_range"] for r in rows.values()))
        self.assertFalse(any(r["cp_from_low_T_table"] for r in rxn.species_table(400.0)))


class TestApiBelow298K(unittest.TestCase):
    def test_analyze_at_250_K(self):
        res = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 250})
        self.assertEqual(res["valid_range"], [200.0, 1500.0])
        kinds = [w["kind"] for w in res["warnings"] if "kind" in w]
        self.assertNotIn("cp_extrapolation", kinds)
        self.assertEqual(kinds.count("low_T_data"), 1)
        self.assertTrue(all(c["passed"] for c in res["audit"]))
        self.assertIn("NIST", res["steps"][3]["title"])
        sweep = res["sweep"]
        self.assertEqual((sweep["T"][0], sweep["T"][-1]), (200.0, 1500.0))
        self.assertTrue(all(sweep["in_range"]))
        self.assertIn(T0, sweep["T"])
        i = sweep["T"].index(T0)
        self.assertAlmostEqual(sweep["T"][i - 1], T0, delta=1e-5)                 # the point just below
        self.assertAlmostEqual(sweep["dH"][i - 1], sweep["dH"][i], delta=1e-3)   # dH is continuous
        self.assertGreater(abs(sweep["dCp"][i - 1] - sweep["dCp"][i]), 1.0)      # dCp steps (methanol)
        self.assertAlmostEqual(res["crossover"][0], 276.3, delta=0.3)
        # above 298.15 K the same request is exactly what it was before
        warm = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15})
        self.assertAlmostEqual(warm["at_T"]["dH"], -57940.0, delta=5.0)
        self.assertNotIn("NIST", warm["steps"][3]["title"])

    def test_below_200_K_is_still_flagged(self):
        res = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 150})
        warned = {w["species"] for w in res["warnings"] if w.get("kind") == "cp_extrapolation"}
        self.assertEqual(warned, {"CO2(g)", "H2(g)", "CH3OH(g)", "H2O(g)"})

    def test_a_plot_that_starts_at_298_K_has_no_extra_points(self):
        res = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 400, "T_min": 298.15, "T_max": 800})
        self.assertEqual(len(res["sweep"]["T"]), 81)
        res = ok("analyze", {"equation": "H2 + O2 -> H2O2", "T": 400})         # no low-temperature data
        self.assertEqual(res["sweep"]["T"][0], T0)
        self.assertEqual(len(res["sweep"]["T"]), 81)

    def test_sensible_heat_endpoint_across_the_join(self):
        res = ok("sensible", {"species": "CO2", "T1": 200, "T2": 400})
        sp = SPECIES["CO2(g)"]
        self.assertAlmostEqual(res["dH_molar"], 3414.0 + sp.sensible_dH(T0, 400.0), places=6)
        self.assertAlmostEqual(res["mean_cp_H"] * 200.0, res["dH_molar"], places=6)
        self.assertAlmostEqual(res["mean_cp_S"] * math.log(2.0), res["dS_molar"], places=9)
        self.assertEqual([w["kind"] for w in res["warnings"]], ["low_T_data"])
        self.assertIn(T0, res["curve"]["T"])
        self.assertEqual(res["species"]["cp_Tmin"], 200.0)
        self.assertEqual(res["species"]["cp_main_Tmin"], 298.0)
        self.assertEqual(len(res["species"]["cp_low"]), 5)
        same = ok("sensible", {"species": "CO2", "T1": 250, "T2": 250})
        self.assertAlmostEqual(same["mean_cp_H"], sp.cp_J(250.0), places=9)
        warm = ok("sensible", {"species": "CH4", "T1": 533.15, "T2": 873.15})
        self.assertEqual(warm["warnings"], [])
        self.assertAlmostEqual(warm["dH_molar"], 19778.0, delta=1.0)

    def test_database_describes_the_low_temperature_data(self):
        db = ok("database", {})
        self.assertEqual(db["low_T"]["T_min"], 200.0)
        self.assertEqual(db["low_T"]["covered"], 47)
        self.assertEqual(set(db["low_T"]["not_covered"]), {"H2O2(g)", "CaCO3(s)", "CaC2(s)"})
        notes = {n["species"]: n["reason"] for n in db["data_notes"]}
        self.assertIn("NIST-JANAF", notes["Below 298.15 K"])
        self.assertIn("14 %", notes["Step at 298.15 K"])
        co2 = next(s for s in db["species"] if s["id"] == "CO2(g)")
        self.assertAlmostEqual(co2["cp298_R_low"] * R, 37.129, places=9)
        self.assertIn("C-095", co2["cp_low_source"])
        water = next(s for s in db["species"] if s["id"] == "H2O(l)")
        self.assertIsNone(water["cp_low"])
        self.assertEqual(water["cp_main_Tmin"], 273.15)

    def test_heat_balance_with_a_cold_feed(self):
        # hydrogen burned in air that enters at 250 K
        rxn = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
        case = hb.build_case(rxn, excess=1.0, air=True)
        cold = hb.solve(case, 250.0, "adiabatic")
        warm = hb.solve(case, T0, "adiabatic")
        self.assertTrue(all(c["passed"] for c in cold["audit"]))
        self.assertEqual(cold["warnings"], [])
        self.assertLess(cold["T_out"], warm["T_out"])
        feed = hb.Stream(case["feed"])
        by_species = sum(n * SPECIES[s].sensible_dH(250.0, T0) for s, n in case["feed"].items())
        self.assertAlmostEqual(feed.sensible(250.0, T0), by_species, places=6)
        self.assertAlmostEqual(cold["path"]["dH_R"], by_species, places=6)
        # a stream of species without low-temperature data behaves as before
        liquid = hb.Stream({"H2O(l)": 2.0})
        self.assertEqual(liquid.breakpoints, [])
        self.assertEqual(liquid.coeffs_at(280.0), liquid.coeffs)
        self.assertAlmostEqual(liquid.sensible(280.0, 350.0), 2 * SPECIES["H2O(l)"].sensible_dH(280.0, 350.0), places=9)

    def test_product_slate_at_250_K_uses_the_same_gibbs_energies(self):
        res = ok("network", {"species": ["CO2", "H2", "CH3OH(g)", "H2O(g)"], "feed": {"CO2": 1, "H2": 3},
                             "T": 250, "P": 1, "sweep": "none"})
        self.assertEqual(res["warnings"], [])
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        y = res["y"]
        K = y["CH3OH(g)"] * y["H2O(g)"] / (y["CO2(g)"] * y["H2(g)"] ** 3)
        self.assertAlmostEqual(math.log(K), rxn.lnK(250.0), delta=1e-6)


if __name__ == "__main__":
    unittest.main()
