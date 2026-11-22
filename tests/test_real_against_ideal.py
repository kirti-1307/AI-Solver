"""Tab 2: the heat of reaction of the real gas next to the ideal-gas value.

The tab shows how much the residual enthalpy changes the heat of reaction at
pressure. These tests check the numbers behind it, the three-step path, the
overview of industrial cases, and that the tab does not use fugacity.
"""

import json
import os
import re
import unittest

from thermosolver import api, library
from thermosolver.reaction import Reaction
from thermosolver.realgas import reaction_at_pressure, residual
from thermosolver.species import SPECIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMMONIA = {"equation": "N2 + 3 H2 -> 2 NH3", "T": 723.15, "P": 200, "model": "pr"}


def ok(endpoint, payload):
    out = json.loads(api.call(endpoint, json.dumps(payload)))
    assert out["ok"], out
    return out["result"]


class TestComparison(unittest.TestCase):
    def test_ammonia_at_200_bar(self):
        res = ok("pressure", AMMONIA)
        c = res["comparison"]
        self.assertAlmostEqual(c["dH_ideal"], -106504.0, delta=1.0)
        self.assertAlmostEqual(c["residual"], -5158.0, delta=1.0)
        self.assertAlmostEqual(c["dH_real"], c["dH_ideal"] + c["residual"], places=6)
        self.assertAlmostEqual(c["dH_real"], res["at_P"]["dH_P"], places=9)
        self.assertAlmostEqual(c["percent"], 4.84, delta=0.01)
        self.assertEqual(c["effect"], "more heat released")
        self.assertEqual(c["size"], "significant")
        self.assertEqual(c["largest"]["species"], "NH3(g)")
        self.assertAlmostEqual(c["largest"]["contribution"], -4395.0, delta=1.0)

    def test_the_three_step_path_adds_up(self):
        res = ok("pressure", AMMONIA)
        c = res["comparison"]
        p = c["path"]
        self.assertAlmostEqual(p["reactants_to_ideal"] + p["ideal_reaction"] + p["products_to_real"], p["total"], places=9)
        self.assertAlmostEqual(p["total"], c["dH_real"], places=9)
        self.assertEqual(p["ideal_reaction"], c["dH_ideal"])
        # step 1 undoes the residual enthalpy of the reactants, step 3 adds that of the products
        n2 = residual(SPECIES["N2(g)"], 723.15, 200.0, "pr").HR
        h2 = residual(SPECIES["H2(g)"], 723.15, 200.0, "pr").HR
        nh3 = residual(SPECIES["NH3(g)"], 723.15, 200.0, "pr").HR
        self.assertAlmostEqual(p["reactants_to_ideal"], -(n2 + 3 * h2), places=9)
        self.assertAlmostEqual(p["products_to_real"], 2 * nh3, places=9)
        # the bars of the plot are the same terms, species by species
        self.assertAlmostEqual(sum(x["contribution"] for x in c["contributions"]), c["residual"], places=9)
        self.assertEqual([x["role"] for x in c["contributions"]], ["reactant", "reactant", "product"])

    def test_ideal_gas_model_gives_no_difference(self):
        c = ok("pressure", dict(AMMONIA, model="ideal"))["comparison"]
        self.assertEqual(c["residual"], 0.0)
        self.assertEqual(c["percent"], 0.0)
        self.assertEqual(c["effect"], "no change")
        self.assertEqual(c["size"], "negligible")
        self.assertIsNone(c["largest"])

    def test_endothermic_reaction_and_wording(self):
        c = ok("pressure", {"equation": "CH4 + H2O(g) -> CO + 3 H2", "T": 1100, "P": 30, "model": "pr"})["comparison"]
        self.assertGreater(c["dH_ideal"], 0.0)
        self.assertGreater(c["residual"], 0.0)
        self.assertEqual(c["effect"], "more heat absorbed")
        self.assertEqual(c["size"], "negligible")
        self.assertLess(c["percent"], 0.5)

    def test_no_value_when_a_species_is_a_liquid(self):
        # water has only a liquid root at 523 K and 100 bar
        res = ok("pressure", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15, "P": 100, "model": "pr"})
        self.assertFalse(res["at_P"]["gas_phase_valid"])
        c = res["comparison"]
        for key in ("residual", "dH_real", "percent", "effect", "size", "largest"):
            self.assertIsNone(c[key], key)
        self.assertTrue(all(v is None for k, v in c["path"].items() if k != "ideal_reaction"))
        self.assertIsNotNone(c["dH_ideal"])

    def test_percent_follows_its_definition(self):
        for payload in (AMMONIA, {"equation": "CO + 2 H2 -> CH3OH", "T": 523.15, "P": 80, "model": "srk"},
                        {"equation": "C2H6 -> C2H4 + H2", "T": 1100, "P": 20, "model": "rk"}):
            c = ok("pressure", payload)["comparison"]
            expected = 100.0 * (abs(c["dH_real"]) - abs(c["dH_ideal"])) / abs(c["dH_ideal"])
            self.assertAlmostEqual(c["percent"], expected, places=9)

    def test_every_model_reports_its_difference(self):
        res = ok("pressure", AMMONIA)
        by = {m["model"]: m for m in res["models"]}
        self.assertEqual(by["ideal"]["percent"], 0.0)
        self.assertAlmostEqual(by["pr"]["percent"], res["comparison"]["percent"], places=9)
        for key in ("virial", "vdw", "rk", "srk", "pr"):
            self.assertTrue(4.0 < by[key]["percent"] < 6.0, key)


class TestTemperatureSweep(unittest.TestCase):
    def test_residual_part_along_the_isobar(self):
        res = ok("pressure", AMMONIA)
        t = res["sweep_T"]
        self.assertEqual(len(t["T"]), 61)
        self.assertEqual(t["P"], 200.0)
        self.assertEqual((t["T"][0], t["T"][-1]), (200.0, 1800.0))
        for key in ("dH_ideal", "dH_real", "residual", "percent"):
            self.assertEqual(len(t[key]), 61, key)
        # below about 410 K ammonia is a liquid at 200 bar: no gas-phase value there
        self.assertIsNone(t["residual"][0])
        self.assertTrue(400.0 < t["first_valid_T"] < 430.0)
        usable = [(T, v) for T, v in zip(t["T"], t["residual"]) if v is not None]
        self.assertGreater(len(usable), 40)
        # the effect fades as the gas gets hotter
        sizes = [abs(v) for _, v in usable]
        self.assertTrue(all(a > b for a, b in zip(sizes, sizes[1:])))
        self.assertGreater(sizes[0], 5 * sizes[-1])
        # each point is the single-point calculation at that temperature
        T, value = usable[10]
        point = reaction_at_pressure(Reaction.parse("N2 + 3 H2 -> 2 NH3"), T, 200.0, "pr")
        self.assertAlmostEqual(value, point["sum_HR"], places=9)

    def test_the_sweep_covers_the_range_of_the_heat_capacities(self):
        # acetic acid liquid limits this one to 290 to 320 K
        res = ok("pressure", {"equation": "CH3CHO + 1/2 O2 -> CH3COOH(l)", "T": 300, "P": 5, "model": "pr"})
        t = res["sweep_T"]
        self.assertEqual((t["T"][0], t["T"][-1]), (290.0, 320.0))
        self.assertEqual(len(t["T"]), 61)


class TestOverview(unittest.TestCase):
    def test_six_industrial_cases_largest_effect_first(self):
        rows = ok("pressure_overview", {})["rows"]
        self.assertEqual(len(rows), len(library.PRESSURE_CASES))
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r["gas_phase_valid"] for r in rows))
        sizes = [abs(r["percent"]) for r in rows]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        by = {r["id"]: r for r in rows}
        self.assertEqual(rows[0]["id"], "co2_methanol")
        self.assertAlmostEqual(by["co2_methanol"]["percent"], 10.56, delta=0.05)
        self.assertEqual(by["co2_methanol"]["size"], "large")
        self.assertAlmostEqual(by["ammonia"]["residual"], -5158.0, delta=1.0)
        self.assertEqual(by["ammonia"]["size"], "significant")
        self.assertEqual(by["smr"]["size"], "negligible")
        self.assertEqual(by["so2_oxidation"]["size"], "negligible")
        for r in rows:
            self.assertAlmostEqual(r["dH_real"], r["dH_ideal"] + r["residual"], places=6)
            self.assertIsNotNone(library.reaction_by_id(r["id"]))        # the page loads the case by this id

    def test_overview_row_equals_the_tab_result(self):
        row = next(r for r in ok("pressure_overview", {})["rows"] if r["id"] == "ammonia")
        c = ok("pressure", AMMONIA)["comparison"]
        for key in ("dH_ideal", "residual", "dH_real", "percent", "effect", "size"):
            self.assertEqual(row[key], c[key], key)


class TestNoFugacityOnTab2(unittest.TestCase):
    WORDS = re.compile(r"fugacity|φ|\bphi\b|K_phi|lnphi", re.IGNORECASE)

    def test_script_of_the_tab(self):
        with open(os.path.join(ROOT, "web", "tab-pressure.js"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIsNone(self.WORDS.search(text))
        # the equilibrium conversion needed fugacity coefficients; it is no longer shown here
        self.assertNotIn("conversion", text)
        self.assertNotIn("dG_P", text)
        self.assertIn("comparison", text)

    def test_markup_of_the_tab(self):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as fh:
            page = fh.read()
        start, end = page.index('id="tab-pressure"'), page.index('id="tab-combine"')
        self.assertIsNone(self.WORDS.search(page[start:end]))
        self.assertIn('id="pr-overview"', page[start:end])

    def test_texts_the_tab_receives(self):
        res = ok("pressure", AMMONIA)
        texts = [c["relation"] + c["name"] for c in res["audit"]]
        # a state where the pure species would condense, which adds notes
        wet = ok("pressure", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15, "P": 45, "model": "pr"})
        texts += [n["message"] for n in wet["at_P"]["notes"]] + [w["message"] for w in wet["warnings"]]
        self.assertGreater(len(texts), 9)
        for text in texts:
            self.assertIsNone(self.WORDS.search(text), text)

    def test_the_audit_still_checks_the_residual_enthalpy(self):
        res = ok("pressure", AMMONIA)
        self.assertEqual(len(res["audit"]), 9)
        self.assertTrue(all(c["passed"] for c in res["audit"]))
        relations = {c["relation"] for c in res["audit"]}
        self.assertIn("d(G^R/RT)/dT at constant P = -H^R/(R T^2)", relations)


if __name__ == "__main__":
    unittest.main()
