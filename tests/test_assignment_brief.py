"""The assignment brief, requirement by requirement.

Each test quotes one requirement of "Assignment 2: Thermodynamic Solver for
Reaction Energetics" and checks that the solver meets it. The details are
tested elsewhere; this file is the checklist.
"""

import json
import os
import re
import unittest

from thermosolver import api, library
from thermosolver.reaction import Reaction
from thermosolver.species import SPECIES, find_species

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(endpoint, payload):
    return json.loads(api.call(endpoint, json.dumps(payload)))


def ok(endpoint, payload):
    out = call(endpoint, payload)
    assert out["ok"], out
    return out["result"]


class TestDatabase(unittest.TestCase):
    SUGGESTED = ["H2", "O2", "N2", "CO", "CO2", "H2O", "NH3", "CH4", "C2H6", "C2H4", "C2H2", "C3H8", "C3H6", "C4H10", "C4H8",
                 "CH3OH", "C2H5OH", "CH2O", "CH3CHO", "CH3COOH", "H2O2", "NO", "NO2", "N2O", "H2S", "SO2"]

    def test_at_least_20_to_30_species_with_states_identified(self):
        self.assertGreaterEqual(len(SPECIES), 30)
        self.assertEqual({sp.phase for sp in SPECIES.values()}, {"g", "l", "s"})
        for sid, sp in SPECIES.items():
            self.assertTrue(sid.endswith(f"({sp.phase})"), sid)          # the state is part of the name

    def test_every_suggested_species_is_there(self):
        self.assertEqual(len(self.SUGGESTED), 26)
        for name in self.SUGGESTED:
            sp, _ = find_species(name)
            self.assertIsNotNone(sp, name)

    def test_formation_enthalpy_gibbs_energy_entropy_and_cp_for_each(self):
        for name in self.SUGGESTED:
            sp, _ = find_species(name)
            row = sp.to_dict()
            for key in ("dHf", "dGf", "S298_absolute", "cp"):
                self.assertIsNotNone(row[key], f"{sp.id} {key}")
            self.assertEqual(len(row["cp"]), 5)                        # A, B, C, D (and E for NIST species)

    def test_critical_properties_and_acentric_factor_for_real_gas_work(self):
        with_critical = [sp for sp in SPECIES.values() if sp.phase == "g" and sp.critical is not None]
        self.assertGreaterEqual(len(with_critical), 35)
        for sp in with_critical:
            self.assertGreater(sp.critical.Tc, 0.0)
            self.assertGreater(sp.critical.Pc, 0.0)
            self.assertTrue(-0.3 < sp.critical.omega < 0.7)

    def test_sources_units_reference_temperature_pressure_and_phase_are_documented(self):
        db = ok("database", {})
        self.assertEqual(db["constants"], {"R": 8.314, "T0": 298.15, "P0": 1.0})
        self.assertIn("Smith, Van Ness", db["sources"]["book"])
        for sp in db["species"]:
            self.assertTrue(sp["formation_source"] and sp["cp_source"], sp["id"])
            self.assertIn(sp["phase"], "gls")
        with open(os.path.join(ROOT, "docs", "DATA_SOURCES.md"), encoding="utf-8") as fh:
            doc = fh.read()
        for word in ("Table C.1", "Table C.4", "J/mol", "298.15 K", "1 bar", "NIST"):
            self.assertIn(word, doc)


class TestReactions(unittest.TestCase):
    NAMED = ["co2_methanol", "rwgs", "wgs", "methanol_synthesis", "ammonia", "smr"]

    def test_at_least_15_to_20_predefined_reactions_including_the_named_ones(self):
        ids = [r[0] for r in library.REACTIONS]
        self.assertGreaterEqual(len(ids), 20)
        for rid in self.NAMED:
            self.assertIn(rid, ids)

    def test_the_user_can_enter_an_own_balanced_reaction(self):
        res = ok("analyze", {"equation": "2 C2H6 + 7 O2 -> 4 CO2 + 6 H2O(g)", "T": 900})
        self.assertLess(res["at_T"]["dH"], 0.0)

    def test_elemental_balance_is_verified_before_any_calculation(self):
        out = call("analyze", {"equation": "CH4 + O2 -> CO2 + H2O", "T": 500})
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"]["kind"], "unbalanced_reaction")
        self.assertIn("2 O2", out["error"]["details"]["suggestion"])
        self.assertNotIn("result", out)                              # no number is returned


class TestCalculations(unittest.TestCase):
    def setUp(self):
        self.res = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15, "P": 50})

    def test_standard_heat_of_reaction_at_298_and_exothermic_or_endothermic(self):
        e = self.res["at_T"]
        self.assertAlmostEqual(e["dH0"], -48969.0, delta=1.0)
        self.assertEqual(e["thermicity0"], "exothermic")
        self.assertEqual(ok("analyze", {"equation": "CH4 + H2O(g) -> CO + 3 H2"})["at_T"]["thermicity0"], "endothermic")

    def test_cp_expression_and_individual_sensible_enthalpy_changes(self):
        ch4 = SPECIES["CH4(g)"]
        self.assertEqual(ch4.cp[:4], (1.702, 9.081e-3, -2.164e-6, 0.0))      # A, B, C, D of SVN Table C.1
        rows = self.res["species"]
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertIsNotNone(row["sensible_dH"])
        total = sum(r["nu_sensible_dH"] for r in rows)
        self.assertAlmostEqual(total, self.res["at_T"]["dH"] - self.res["at_T"]["dH0"], delta=1e-6)

    def test_entropy_and_gibbs_energy_of_reaction_with_temperature(self):
        e = self.res["at_T"]
        self.assertAlmostEqual(e["dS"], -199.76, delta=0.01)
        self.assertAlmostEqual(e["dG"], e["dH"] - 523.15 * e["dS"], delta=1e-6)
        sweep = self.res["sweep"]
        for key in ("dH", "dS", "dG", "lnK"):
            self.assertGreater(len(sweep[key]), 50)
            self.assertNotEqual(sweep[key][0], sweep[key][-1])           # they do change with temperature

    def test_pressure_effects_and_residual_properties(self):
        res = ok("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 723.15, "P": 200, "model": "pr"})
        self.assertAlmostEqual(res["comparison"]["residual"], -5158.0, delta=1.0)
        self.assertEqual(len(res["sweep"]["P"]), 61)                     # the trend against pressure
        self.assertEqual(len(res["sweep_T"]["T"]), 61)

    def test_plots_against_temperature_and_pressure(self):
        with open(os.path.join(ROOT, "web", "tab-reaction.js"), encoding="utf-8") as fh:
            tab1 = fh.read()
        with open(os.path.join(ROOT, "web", "tab-pressure.js"), encoding="utf-8") as fh:
            tab2 = fh.read()
        # tab 1 had a graph of the equilibrium constant and one of the conversion, until the user
        # asked for both to be left off tab 1 (23 November 2026)
        self.assertEqual(len(set(re.findall(r'TS\.plot\("(rx-plot-[A-Za-z]+)"', tab1))), 3)
        self.assertEqual(len(set(re.findall(r'TS\.plot\("(pr-plot-[A-Za-z]+)"', tab2))), 4)
        self.assertEqual(tab1.count("TS.fig("), 3)                       # each with a line on how to read it
        self.assertEqual(tab2.count("TS.fig("), 4)

    def test_favourability_at_a_certain_temperature(self):
        fav = self.res["at_T"]["favourability"]
        self.assertFalse(fav["spontaneous_standard"])                    # K < 1 at 523 K
        cold = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 250})
        self.assertTrue(cold["at_T"]["favourability"]["spontaneous_standard"])
        self.assertAlmostEqual(self.res["crossover"][0], 276.3, delta=0.3)

    def test_favourability_at_a_certain_pressure(self):
        # K belongs to 1 bar. At a chosen pressure the solver gives how far the reaction goes.
        # Since 23 November 2026 the page shows this on tab 4 (pressure slider of the product
        # slate), not on tab 1; the number is the same, as the check against "network" below shows.
        self.assertEqual(self.res["P"], 50.0)
        low, high = self.res["equilibrium"], self.res["equilibrium_P"]
        self.assertAlmostEqual(low["conversion"], 0.006, delta=0.001)     # 1 bar
        self.assertAlmostEqual(high["conversion"], 0.213, delta=0.001)    # 50 bar
        self.assertEqual(high["limiting_reactant"], "CO2(g)")
        sweep = self.res["sweep"]
        self.assertEqual(len(sweep["conversion_P"]), len(sweep["T"]))
        self.assertTrue(all(b >= a - 1e-12 for a, b in zip(sweep["conversion_1bar"], sweep["conversion_P"])))
        # the definition: K = prod(y_i^nu_i) * (P/P0)^(sum of nu), here sum of nu = -2
        y, K = high["y"], Reaction.parse("CO2 + 3 H2 -> CH3OH + H2O").K(523.15)
        self.assertAlmostEqual(y["CH3OH(g)"] * y["H2O(g)"] / (y["CO2(g)"] * y["H2(g)"] ** 3) / 50.0 ** 2, K, delta=1e-9 * K + 1e-15)
        # the same number as the product slate with only this reaction allowed
        slate = ok("network", {"species": ["CO2", "H2", "CH3OH(g)", "H2O(g)"], "feed": {"CO2": 1, "H2": 3},
                               "T": 523.15, "P": 50, "sweep": "none"})
        self.assertAlmostEqual(slate["conversions"]["CO2(g)"], high["conversion"], places=6)
        # a reaction with no change in gas moles does not care about pressure
        wgs = ok("analyze", {"equation": "CO + H2O(g) -> CO2 + H2", "T": 700, "P": 80})
        self.assertAlmostEqual(wgs["equilibrium"]["conversion"], wgs["equilibrium_P"]["conversion"], places=9)
        # without a pressure the two are the same calculation
        plain = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15})
        self.assertEqual(plain["P"], 1.0)
        self.assertEqual(plain["equilibrium"]["conversion"], plain["equilibrium_P"]["conversion"])
        self.assertEqual(plain["sweep"]["conversion_1bar"], plain["sweep"]["conversion_P"])
        self.assertEqual(call("analyze", {"equation": "CO + 2 H2 -> CH3OH", "P": -5})["error"]["kind"], "input_error")


class TestAIErrorChallenge(unittest.TestCase):
    def setUp(self):
        self.res = ok("challenge", {})

    def test_the_five_stress_tests_are_there(self):
        self.assertFalse(self.res["stoichiometry"][0]["accepted"])                         # 1. unbalanced rejected
        row = next(r for r in self.res["cp_assumption"] if "steam reforming" in r["name"].lower())
        self.assertGreater(abs(row["dH"] - row["dH_const"]), 5000.0)                       # 2. constant against Cp(T) at 1000 K
        self.assertEqual(row["T"], 1000.0)
        state = self.res["physical_state"]
        self.assertAlmostEqual(state["difference_dH"], state["explained"], delta=1e-6)     # 3. H2O(l) against H2O(g)
        self.assertTrue(any(e["warned"] for e in self.res["extrapolation"]))               # 4. extrapolation warned
        lit = ok("literature", {})
        self.assertGreaterEqual(len(json.dumps(lit)), 1000)                                # 5. published values

    def test_extrapolation_examples_still_warn_with_the_extended_data(self):
        by = {(e["equation"], e["T"]): e["warned"] for e in self.res["extrapolation"]}
        self.assertEqual(sum(by.values()), 4)
        self.assertEqual(sum(1 for w in by.values() if not w), 1)       # 1400 K is inside the range


class TestDeliverables(unittest.TestCase):
    def test_report_and_hosted_page_exist(self):
        for name in ("report/Assignment2_Report.docx", "report/report.html", "index.html", "guide.html"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, name)), name)
        with open(os.path.join(ROOT, "report", "report.html"), encoding="utf-8") as fh:
            report = fh.read()
        for section in ("Models", "Important findings", "Errors of the AI-generated solver"):
            self.assertIn(section, report)
        # 23 November 2026: the report says where each calculation of the brief is done
        self.assertIn("What the assignment asks for, and where the solver does it", report)
        for item in ("exo- or endothermic", "C<sub>p</sub>&deg;(T) = A + BT + CT<sup>2</sup> + DT<sup>&minus;2</sup>",
                     "&Delta;S&deg; with temperature", "&Delta;G&deg; of reaction", "Pressure and residual properties",
                     "Plots against T and P", "Favourability at T and P"):
            self.assertIn(item, report)
        # the rest of the brief: the named reactions, what the database documents, and the kinds of error
        for item in ("which include all those named in the assignment", "including all 26 suggested in the assignment",
                     "it lists the phase", "S&deg; at 298.15 K and 1 bar", "each with its unit and source",
                     "eight incorrect, misleading, incomplete or physically unreasonable results", "AI platform used"):
            self.assertIn(item, report)
        self.assertEqual(report.count("<tr><td>") - report.count("<tr><td>1.") - report.count("<tr><td>2.") - report.count("<tr><td>3.")
                         - report.count("<tr><td>4.") - report.count("<tr><td>5."), 6 + 7 + 8)   # models, brief table, errors
        from thermosolver import library
        ids = {e[0] for e in library.REACTIONS}
        for rid in ("co2_methanol", "methanol_synthesis", "rwgs", "wgs", "ammonia", "smr"):   # the reactions the brief names
            self.assertIn(rid, ids)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "report", "Assignment2_Report.pdf")))
        self.assertIn("kirti-1307.github.io/AI-Solver", report)


if __name__ == "__main__":
    unittest.main()
