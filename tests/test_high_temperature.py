"""Heat capacities above the SVN range (NIST Shomate equations, up to 6000 K).

SVN's formula for the gases of a flame ends at 2000 K. Above its range the
solver uses the Shomate equations of the NIST Chemistry WebBook. These tests
check the transcription against NIST's own enthalpy and entropy functions and
against rows of the NIST-JANAF tables, the way the solver joins the two
sources, and that nothing inside the SVN range has changed.
"""

import json
import math
import unittest

from thermosolver import api, data
from thermosolver import heatbalance as hb
from thermosolver.audit import audit_reaction
from thermosolver.constants import R, T0
from thermosolver.heatcap import cp_over_r, icph, icps
from thermosolver.reaction import Reaction
from thermosolver.species import SPECIES

from tests import janaf_reference as janaf


def ok(endpoint, payload):
    out = json.loads(api.call(endpoint, json.dumps(payload)))
    assert out["ok"], out
    return out["result"]


def shomate_cp(c, T):
    a, b, cc, d, e = c
    t = T / 1000.0
    return a + b * t + cc * t * t + d * t ** 3 + e / (t * t)


def nist_h(c, fgh, T):          # H(T) - H(298.15 K), kJ/mol
    a, b, cc, d, e = c
    f, _, h = fgh
    t = T / 1000.0
    return a * t + b * t ** 2 / 2 + cc * t ** 3 / 3 + d * t ** 4 / 4 - e / t + f - h


def nist_s(c, fgh, T):          # S(T), J/(mol K)
    a, b, cc, d, e = c
    _, g, _ = fgh
    t = T / 1000.0
    return a * math.log(t) + b * t + cc * t ** 2 / 2 + d * t ** 3 / 3 - e / (2 * t * t) + g


class TestTheNistEquations(unittest.TestCase):
    def test_shape_of_the_table(self):
        self.assertEqual(set(data.NIST_HIGH_T), {"N2(g)", "O2(g)", "CO2(g)", "H2O(g)", "CO(g)", "H2(g)", "SO2(g)", "NO(g)"})
        for sid, (webbook_id, (tmin, tmax), shomate, fgh) in data.NIST_HIGH_T.items():
            sp = SPECIES[sid]
            self.assertEqual(sp.phase, "g")
            self.assertTrue(sp.from_svn)
            self.assertRegex(webbook_id, r"^C\d+$")
            self.assertEqual((len(shomate), len(fgh)), (5, 3))
            # the NIST equation must cover everything from the end of the SVN range to 6000 K
            self.assertLessEqual(tmin, sp.cp_main_Tmax, sid)
            self.assertEqual(tmax, data.HIGH_T_MAX, sid)
            self.assertEqual(sp.cp_Tmax, 6000.0, sid)
            self.assertIn("NIST", sp.cp_high_source)
        self.assertEqual({SPECIES[s].cp_main_Tmax for s in ("N2(g)", "O2(g)", "CO2(g)", "H2O(g)", "SO2(g)", "NO(g)")}, {2000.0})
        self.assertEqual((SPECIES["CO(g)"].cp_main_Tmax, SPECIES["H2(g)"].cp_main_Tmax), (2500.0, 3000.0))

    def test_the_equation_is_used_exactly_as_published(self):
        for sid, (_, _, shomate, _) in data.NIST_HIGH_T.items():
            sp = SPECIES[sid]
            for T in (sp.cp_main_Tmax + 1.0, 3500.0, 4800.0, 6000.0):
                self.assertAlmostEqual(sp.cp_J(T), shomate_cp(shomate, T), places=9, msg=f"{sid} at {T} K")

    def test_integrals_match_the_nist_enthalpy_and_entropy_functions(self):
        # NIST gives H(T) - H(298.15) and S(T) with the constants F, G, H. Their
        # differences between two temperatures test the solver's own integrals.
        for sid, (_, _, shomate, fgh) in data.NIST_HIGH_T.items():
            sp = SPECIES[sid]
            T1 = sp.cp_main_Tmax + 50.0
            for T2 in (4000.0, 6000.0):
                dh = (nist_h(shomate, fgh, T2) - nist_h(shomate, fgh, T1)) * 1000.0
                ds = nist_s(shomate, fgh, T2) - nist_s(shomate, fgh, T1)
                self.assertAlmostEqual(sp.sensible_dH(T1, T2), dh, delta=1e-6 * abs(dh), msg=sid)
                self.assertAlmostEqual(sp.sensible_dS(T1, T2), ds, delta=1e-6 * abs(ds), msg=sid)

    def test_against_rows_of_the_janaf_tables(self):
        # an outside check of the transcription: the tables themselves
        checked = 0
        for sid in data.NIST_HIGH_T:
            sp = SPECIES[sid]
            rows = {T: (cp, S, H) for T, cp, S, H in janaf.ROWS[sid][1]}
            join = sp.cp_main_Tmax
            for T, (cp, S, H) in rows.items():
                if T <= join:
                    continue
                self.assertAlmostEqual(sp.cp_J(T) / cp, 1.0, delta=0.004, msg=f"{sid} Cp at {T} K")
                # enthalpy and entropy gained above the join, against the same difference in the table
                dH = (H - rows[join][2]) * 1000.0
                dS = S - rows[join][1]
                self.assertAlmostEqual(sp.sensible_dH(join, T) / dH, 1.0, delta=0.002, msg=f"{sid} H at {T} K")
                self.assertAlmostEqual(sp.sensible_dS(join, T) / dS, 1.0, delta=0.002, msg=f"{sid} S at {T} K")
                checked += 1
        self.assertGreaterEqual(checked, 28)


class TestTheJoin(unittest.TestCase):
    def test_which_constants_apply_where(self):
        co2 = SPECIES["CO2(g)"]
        self.assertIs(co2.coeffs_at(1999.0), co2.cp)
        self.assertIs(co2.coeffs_at(2000.0), co2.cp)                    # the SVN range includes its end point
        self.assertIs(co2.coeffs_at(2000.001), co2.cp_high)
        self.assertEqual(co2.offsets_at(2000.0), (0.0, 0.0))
        self.assertEqual(co2.offsets_at(2500.0), co2.cp_high_offsets)
        self.assertEqual(co2.breakpoints(), [T0, 2000.0])
        self.assertEqual(co2.cp_source_at(1500.0), co2.cp_source)
        self.assertEqual(co2.cp_source_at(2500.0), co2.cp_high_source)
        methane = SPECIES["CH4(g)"]                                      # no high-temperature data
        self.assertIsNone(methane.cp_high)
        self.assertEqual((methane.cp_main_Tmax, methane.cp_Tmax), (1500.0, 1500.0))
        self.assertEqual(methane.breakpoints(), [T0])
        self.assertEqual(SPECIES["H2O(l)"].breakpoints(), [])

    def test_the_offset_is_what_the_definition_says(self):
        for sid in data.NIST_HIGH_T:
            sp = SPECIES[sid]
            Tj = sp.cp_main_Tmax
            oh, os_ = sp.cp_high_offsets
            self.assertAlmostEqual(oh, icph(T0, Tj, sp.cp) - icph(T0, Tj, sp.cp_high), places=9)
            self.assertAlmostEqual(os_, icps(T0, Tj, sp.cp) - icps(T0, Tj, sp.cp_high), places=12)
            # so that H(T) above the join is the SVN integral to the join plus the NIST integral beyond it
            T = Tj + 700.0
            two_pieces = R * (icph(T0, Tj, sp.cp) + icph(Tj, T, sp.cp_high))
            self.assertAlmostEqual(sp.sensible_dH(T0, T), two_pieces, delta=1e-7, msg=sid)
            two_pieces = R * (icps(T0, Tj, sp.cp) + icps(Tj, T, sp.cp_high))
            self.assertAlmostEqual(sp.sensible_dS(T0, T), two_pieces, places=9, msg=sid)

    def test_enthalpy_entropy_and_gibbs_energy_are_continuous(self):
        eps = 1e-6
        for sid in data.NIST_HIGH_T:
            sp = SPECIES[sid]
            Tj = sp.cp_main_Tmax
            self.assertAlmostEqual(sp.H(Tj + eps), sp.H(Tj - eps), delta=1e-3, msg=sid)
            self.assertAlmostEqual(sp.S(Tj + eps), sp.S(Tj - eps), delta=1e-6, msg=sid)
            self.assertAlmostEqual(sp.G(Tj + eps), sp.G(Tj - eps), delta=1e-2, msg=sid)

    def test_svn_runs_high_at_the_end_of_its_range(self):
        # the reason the NIST data are used: at its upper limit SVN's formula is
        # already above the tabulated heat capacity, and it keeps rising beyond it
        step = {sid: cp_over_r(SPECIES[sid].cp, SPECIES[sid].cp_main_Tmax) / cp_over_r(SPECIES[sid].cp_high, SPECIES[sid].cp_main_Tmax) - 1.0
                for sid in data.NIST_HIGH_T}
        for sid in ("N2(g)", "O2(g)", "CO2(g)", "H2O(g)", "CO(g)", "SO2(g)", "NO(g)"):
            self.assertTrue(0.02 < step[sid] < 0.09, f"{sid}: {step[sid]:+.3f}")
        self.assertTrue(abs(step["H2(g)"]) < 0.02)
        co2 = SPECIES["CO2(g)"]
        extrapolated = R * cp_over_r(co2.cp, 3000.0)
        self.assertGreater(extrapolated / 62.229, 1.07)                 # JANAF: 62.229 J/(mol K) at 3000 K
        self.assertAlmostEqual(co2.cp_J(3000.0), 62.229, delta=0.05)

    def test_sensible_heat_across_all_three_ranges(self):
        sp = SPECIES["N2(g)"]
        whole = sp.sensible_dH(250.0, 2600.0)
        parts = sp.sensible_dH(250.0, T0) + sp.sensible_dH(T0, 2000.0) + sp.sensible_dH(2000.0, 2600.0)
        self.assertAlmostEqual(whole, parts, places=6)
        self.assertAlmostEqual(sp.sensible_dH(2600.0, 250.0), -whole, places=6)
        self.assertAlmostEqual(sp.sensible_dS(250.0, 2600.0),
                               sp.sensible_dS(250.0, T0) + sp.sensible_dS(T0, 2000.0) + sp.sensible_dS(2000.0, 2600.0), places=9)


class TestReactionsAboveTheSvnRange(unittest.TestCase):
    def test_formation_of_water_and_co2_against_janaf(self):
        # NIST-JANAF heats of formation at 3000 K: H2O(g) -253.024, CO2 -400.111, CO -127.415 kJ/mol
        water = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
        self.assertAlmostEqual(water.dH(3000.0), -253024.0, delta=300.0)
        self.assertAlmostEqual(water.dG(3000.0), -77163.0, delta=400.0)
        # For CO the SVN formula is kept up to its stated limit of 2500 K, where its enthalpy is
        # already 1.3 % (about 1 kJ/mol) above JANAF. That difference stays in everything above.
        burn = Reaction.parse("CO + 1/2 O2 -> CO2")
        self.assertAlmostEqual(burn.dH(3000.0), -400111.0 + 127415.0, delta=1200.0)
        co = SPECIES["CO(g)"]
        self.assertAlmostEqual(co.sensible_dH(T0, 2500.0) / 75027.0, 1.013, delta=0.002)
        # stretched SVN formulas would be far off at 5000 K; JANAF gives -256.763 kJ/mol for water
        self.assertAlmostEqual(water.dH(5000.0), -256763.0, delta=300.0)
        stretched = water.dH0 + R * icph(T0, 5000.0, water.delta_coeffs())
        self.assertGreater(abs(stretched + 256763.0), 3000.0)

    def test_delta_coeffs_and_offsets(self):
        rxn = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        self.assertEqual(rxn.delta_offsets(1900.0), (0.0, 0.0))
        self.assertEqual(rxn.delta_coeffs(1900.0), rxn.delta_coeffs())
        self.assertEqual(rxn.uses_high_T_data(1900.0), [])
        self.assertEqual(rxn.uses_high_T_data(2200.0), ["H2O(g)"])
        self.assertEqual(rxn.uses_high_T_data(2700.0), ["H2O(g)", "CO(g)"])
        self.assertEqual(rxn.uses_high_T_data(3500.0), ["H2O(g)", "CO(g)", "H2(g)"])
        self.assertEqual(rxn.breakpoints(), [T0, 2000.0, 2500.0, 3000.0])
        oh, os_ = rxn.delta_offsets(2700.0)
        h2o, co = SPECIES["H2O(g)"], SPECIES["CO(g)"]
        self.assertAlmostEqual(oh, -h2o.cp_high_offsets[0] + co.cp_high_offsets[0], places=9)
        self.assertAlmostEqual(os_, -h2o.cp_high_offsets[1] + co.cp_high_offsets[1], places=12)
        # dH from the reaction formula equals the sum over the species at any temperature
        for T in (1500.0, 2000.0, 2200.0, 2700.0, 3500.0, 5900.0):
            by_species = sum(nu * SPECIES[s].H(T) for s, nu in rxn.stoich.items())
            self.assertAlmostEqual(rxn.dH(T), by_species, delta=1e-6, msg=str(T))

    def test_ranges(self):
        water = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
        self.assertEqual(water.valid_range(), (200.0, 6000.0))
        self.assertEqual(water.plot_range(), (200.0, 2000.0))          # a plot stops where SVN stops
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        self.assertEqual(smr.valid_range(), (200.0, 1500.0))           # methane has no data above 1500 K
        self.assertEqual(smr.plot_range(), (200.0, 1500.0))

    def test_consistency_audit_passes_across_the_joins(self):
        for eq in ("H2 + 1/2 O2 -> H2O(g)", "CO + 1/2 O2 -> CO2", "CO + H2O(g) -> CO2 + H2", "N2 + O2 -> 2 NO",
                   "SO2 + 1/2 O2 -> SO3(g)"):
            rxn = Reaction.parse(eq)
            for T in (1900.0, 1999.995, 2000.0, 2000.004, 2100.0, 2499.99, 2500.01, 2999.0, 3000.02, 4500.0, 6000.0):
                failed = [c["name"] for c in audit_reaction(rxn, T) if not c["passed"]]
                self.assertEqual(failed, [], f"{eq} at {T} K")

    def test_notes_and_step_by_step_text(self):
        res = ok("analyze", {"equation": "H2 + 1/2 O2 -> H2O(g)", "T": 2500})
        kinds = [w["kind"] for w in res["warnings"] if "kind" in w]
        self.assertEqual(kinds.count("high_T_data"), 1)
        self.assertNotIn("cp_extrapolation", kinds)
        self.assertEqual(res["at_T"]["high_T_species"], ["O2(g)", "H2O(g)"])
        self.assertIn("NIST", res["steps"][3]["title"])
        self.assertIn("two pieces", res["steps"][4]["formula"])
        self.assertTrue(all(c["passed"] for c in res["audit"]))
        # the plot still ends at the SVN limit unless the user asks for more
        self.assertEqual(res["sweep"]["T"][-1], 2000.0)
        wide = ok("analyze", {"equation": "H2 + 1/2 O2 -> H2O(g)", "T": 2500, "T_max": 3500})
        Ts = wide["sweep"]["T"]
        self.assertEqual(Ts[-1], 3500.0)
        for join in (2000.0, 3000.0):                                   # a point right after each join shows the step in dCp
            self.assertIn(join, Ts)
            self.assertAlmostEqual(Ts[Ts.index(join) + 1], join, delta=1e-5)
        self.assertTrue(all(wide["sweep"]["in_range"]))
        cool = ok("analyze", {"equation": "H2 + 1/2 O2 -> H2O(g)", "T": 1500})
        self.assertEqual(cool["at_T"]["high_T_species"], [])
        self.assertNotIn("NIST", cool["steps"][3]["title"])

    def test_inside_the_svn_range_nothing_changed(self):
        meoh = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
        self.assertAlmostEqual(meoh.dH(1073.15), -103566.0, delta=2.0)                   # SVN example
        hyd = Reaction.parse("C2H4 + H2O(g) -> C2H5OH(g)")
        self.assertAlmostEqual(hyd.K(593.15), 2.942e-3, delta=3e-6)                      # SVN example
        n2 = SPECIES["N2(g)"]
        self.assertAlmostEqual(n2.sensible_dH(T0, 2000.0), R * icph(T0, 2000.0, n2.cp), places=9)


class TestApi(unittest.TestCase):
    def test_sensible_heat_endpoint_above_the_svn_range(self):
        res = ok("sensible", {"species": "CO2", "T1": 1500, "T2": 3000})
        sp = SPECIES["CO2(g)"]
        self.assertEqual([w["kind"] for w in res["warnings"]], ["high_T_data"])
        self.assertAlmostEqual(res["dH_molar"], sp.sensible_dH(1500.0, 2000.0) + sp.sensible_dH(2000.0, 3000.0), places=6)
        self.assertAlmostEqual(res["mean_cp_H"] * 1500.0, res["dH_molar"], places=6)
        self.assertIn(2000.0, res["curve"]["T"])
        # JANAF: H(3000) - H(1500) = 152.852 - 61.705 kJ/mol
        self.assertAlmostEqual(res["dH_molar"] / 1000.0, 152.852 - 61.705, delta=0.5)
        self.assertEqual(ok("sensible", {"species": "CH4", "T1": 300, "T2": 1500})["warnings"], [])
        beyond = ok("sensible", {"species": "CH4", "T1": 300, "T2": 2500})["warnings"]
        self.assertEqual([w["level"] for w in beyond], ["warning"])       # methane has no data up there

    def test_database_describes_the_high_temperature_data(self):
        db = ok("database", {})
        self.assertEqual(db["high_T"], {"T_max": 6000.0, "covered": 8})
        notes = {n["species"]: n["reason"] for n in db["data_notes"]}
        self.assertIn("Shomate", notes["Above the SVN range"])
        n2 = next(s for s in db["species"] if s["id"] == "N2(g)")
        self.assertEqual((n2["cp_main_Tmax"], n2["cp_Tmax"]), (2000.0, 6000.0))
        self.assertAlmostEqual(n2["cp_join_high_J"], 35.971, delta=0.05)             # JANAF at 2000 K
        self.assertTrue(2.0 < n2["cp_join_step_percent"] < 4.5)
        ch4 = next(s for s in db["species"] if s["id"] == "CH4(g)")
        self.assertIsNone(ch4["cp_high"])
        self.assertEqual(ch4["cp_main_Tmax"], 1500.0)

    def test_product_slate_plots_stop_at_the_svn_limit(self):
        res = ok("network", {"species": ["N2", "O2", "NO"], "feed": {"N2": 0.79, "O2": 0.21}, "T": 1800, "P": 1, "n_points": 5})
        self.assertEqual(res["sweep"]["x"][-1], 2000.0)
        hot = ok("network", {"species": ["N2", "O2", "NO"], "feed": {"N2": 0.79, "O2": 0.21}, "T": 3000, "P": 1, "sweep": "none"})
        self.assertEqual(hot["warnings"], [])                                # NIST data: no extrapolation at 3000 K
        rxn = Reaction.parse("N2 + O2 -> 2 NO")
        K = hot["y"]["NO(g)"] ** 2 / (hot["y"]["N2(g)"] * hot["y"]["O2(g)"])
        self.assertAlmostEqual(math.log(K), rxn.lnK(3000.0), delta=1e-6)


class TestHeatLab(unittest.TestCase):
    def test_below_2000_K_the_two_ways_agree(self):
        case = hb.build_case(Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)"), excess=1.0, air=True)
        res = hb.solve(case, T0)
        self.assertLess(res["T_out"], 2000.0)
        self.assertAlmostEqual(hb.svn_outlet_temperature(case, T0), res["T_out"], delta=1e-6)
        self.assertIsNone(res["svn_only"])
        self.assertEqual((res["notes"], res["high_T_species"]), ([], []))

    def test_stream_enthalpy_equals_the_sum_over_species_at_any_temperature(self):
        moles = {"CO2(g)": 1.0, "H2O(g)": 2.0, "O2(g)": 0.4, "N2(g)": 9.03, "CH4(g)": 0.1, "H2(g)": 0.2, "CO(g)": 0.3}
        stream = hb.Stream(moles)
        self.assertEqual(stream.breakpoints, [T0, 2000.0, 2500.0, 3000.0])
        for T in (250.0, 900.0, 2000.0, 2300.0, 2700.0, 3200.0, 5500.0):
            by_species = sum(n * SPECIES[s].H(T) for s, n in moles.items())
            self.assertAlmostEqual(stream.H(T), by_species, delta=1e-6 * abs(by_species), msg=str(T))
            self.assertAlmostEqual(stream.cp(T), sum(n * SPECIES[s].cp_J(T) for s, n in moles.items()), places=8)
        self.assertAlmostEqual(stream.entropy_change(400.0, 3200.0),
                               sum(n * SPECIES[s].sensible_dS(400.0, 3200.0) for s, n in moles.items()), places=8)
        svn = hb.SvnStream(moles)
        self.assertAlmostEqual(svn.H(1800.0), stream.H(1800.0), delta=1e-6)
        self.assertNotAlmostEqual(svn.H(3200.0), stream.H(3200.0), delta=100.0)

    def test_duty_mode_reports_the_textbook_style_value_too(self):
        case = hb.build_case(Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(g)"), excess=0.2, air=True)
        res = hb.solve(case, T0, "duty", T_out=2400.0)
        self.assertIsNotNone(res["svn_only"])
        self.assertNotAlmostEqual(res["svn_only"]["Q"], res["Q"], delta=500.0)
        self.assertIn("heat duty would be", res["notes"][0]["message"])
        self.assertTrue(all(c["passed"] for c in res["audit"]))


if __name__ == "__main__":
    unittest.main()
