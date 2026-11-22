"""Tab 4: what each product switch would change.

A switch removes one product from those allowed to form. It only matters when
that product would hold a real share of the atoms, so the solver works out,
for every switch, what flipping it would do. The page fades the switches that
would change nothing. These tests check that classification against separate
equilibrium calculations.
"""

import json
import os
import unittest

from thermosolver import api, library
from thermosolver.species import SPECIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CO2 = {"species": ["CO2(g)", "H2(g)", "CH3OH(g)", "CO(g)", "H2O(g)", "CH4(g)"], "feed": {"CO2(g)": 1, "H2(g)": 3},
       "T": 523.15, "P": 50, "sweep": "none", "switches": True}


def call(endpoint, payload):
    return json.loads(api.call(endpoint, json.dumps(payload)))


def ok(endpoint, payload):
    out = call(endpoint, payload)
    assert out["ok"], out
    return out["result"]


def rows(payload):
    return {r["species"]: r for r in ok("network", payload)["switches"]}


def without(payload, *off):
    """The same system with some products blocked, as the page sends it."""
    return dict(payload, species=[s for s in payload["species"] if s not in off], candidates=list(off))


class TestCO2Hydrogenation(unittest.TestCase):
    def test_everything_allowed_only_methane_matters(self):
        r = rows(CO2)
        self.assertEqual({s: x["effect"] for s, x in r.items()},
                         {"CO2(g)": "feed", "H2(g)": "feed", "CH3OH(g)": "none", "CO(g)": "none",
                          "H2O(g)": "needed", "CH4(g)": "changes"})
        self.assertEqual([s for s, x in r.items() if x["clickable"]], ["CH4(g)"])
        self.assertAlmostEqual(r["CH4(g)"]["share"], 0.748, delta=0.001)
        self.assertLess(r["CH3OH(g)"]["share"], 1e-4)                 # nothing to remove
        self.assertLess(r["CH3OH(g)"]["largest_change"], api.SWITCH_TOLERANCE)
        self.assertAlmostEqual(r["CH4(g)"]["conversion_now"], 0.748, delta=0.001)
        self.assertAlmostEqual(r["CH4(g)"]["conversion_if_flipped"], 0.252, delta=0.001)
        self.assertEqual(r["CH4(g)"]["primary"], "CO2(g)")
        self.assertIsNone(r["H2O(g)"]["share"])                       # no carbon in water: the page shows y
        self.assertGreater(r["H2O(g)"]["y"], 0.5)

    def test_methane_off_wakes_the_other_switches(self):
        r = rows(without(CO2, "CH4(g)"))
        self.assertEqual(r["CH3OH(g)"]["effect"], "changes")
        self.assertEqual(r["CO(g)"]["effect"], "changes")
        self.assertEqual(r["H2O(g)"]["effect"], "needed")
        self.assertAlmostEqual(r["CH3OH(g)"]["share"], 0.173, delta=0.001)
        self.assertAlmostEqual(r["CO(g)"]["share"], 0.079, delta=0.001)
        self.assertAlmostEqual(r["CH3OH(g)"]["conversion_if_flipped"], 0.162, delta=0.001)
        self.assertAlmostEqual(r["CO(g)"]["conversion_if_flipped"], 0.213, delta=0.001)
        # the blocked product: always clickable, and the solver says what allowing it would do
        off = r["CH4(g)"]
        self.assertEqual((off["state"], off["effect"], off["clickable"]), ("off", "changes", True))
        self.assertAlmostEqual(off["conversion_if_flipped"], 0.748, delta=0.001)
        self.assertAlmostEqual(off["share_if_flipped"], 0.748, delta=0.001)
        self.assertIsNone(off["share"])

    def test_the_last_product_left_is_needed(self):
        r = rows(without(CO2, "CH4(g)", "CO(g)"))
        self.assertEqual(r["CH3OH(g)"]["effect"], "needed")
        self.assertFalse(r["CH3OH(g)"]["clickable"])
        self.assertAlmostEqual(r["CH3OH(g)"]["share"], 0.213, delta=0.001)
        self.assertEqual({s for s, x in r.items() if x["state"] == "off"}, {"CH4(g)", "CO(g)"})
        self.assertAlmostEqual(r["CO(g)"]["share_if_flipped"], 0.079, delta=0.001)

    def test_a_switch_can_wake_up_with_temperature(self):
        # at 523 K carbon monoxide holds nothing; at 1100 K it is a real product
        hot = rows(dict(CO2, T=1100, P=1))
        self.assertEqual(hot["CO(g)"]["effect"], "changes")
        self.assertGreater(hot["CO(g)"]["share"], 0.05)
        self.assertEqual(hot["CH3OH(g)"]["effect"], "none")


class TestPredictionsAreRealCalculations(unittest.TestCase):
    def test_what_a_switch_promises_is_what_flipping_it_gives(self):
        checked = 0
        for net in library.NETWORKS:
            T = 523.15 if net["id"] == "co2_hydrogenation" else sum(net["T_range"]) / 2
            base = {"species": net["species"], "feed": net["feed"], "T": T, "P": net["P"], "sweep": "none", "switches": True}
            for sid, row in rows(base).items():
                if row["effect"] not in ("changes", "none"):
                    continue
                after = ok("network", without(base, sid))
                self.assertAlmostEqual(after["conversions"][row["primary"]], row["conversion_if_flipped"], places=9,
                                       msg=f"{net['id']} {sid}")
                moved = max(abs(after["y"].get(k, 0.0) - v) for k, v in ok("network", base)["y"].items())
                if row["effect"] == "none":
                    self.assertLess(moved, api.SWITCH_TOLERANCE, f"{net['id']} {sid}")
                    self.assertFalse(row["clickable"])
                else:
                    self.assertTrue(row["clickable"])
                # and the way back: the blocked product reports the original state
                back = {r["species"]: r for r in after["switches"]}[sid]
                self.assertEqual(back["state"], "off")
                self.assertAlmostEqual(back["conversion_if_flipped"], row["conversion_now"], places=9)
                checked += 1
        self.assertGreaterEqual(checked, 12)

    def test_needed_means_nothing_reacts_without_it(self):
        for net in library.NETWORKS:
            T = sum(net["T_range"]) / 2
            base = {"species": net["species"], "feed": net["feed"], "T": T, "P": net["P"], "sweep": "none", "switches": True}
            for sid, row in rows(base).items():
                if row["effect"] != "needed":
                    continue
                rest = [s for s in net["species"] if s != sid]
                after = ok("network", dict(base, species=rest, switches=False))
                self.assertTrue(all(abs(v) < 1e-9 for v in after["conversions"].values()), f"{net['id']} {sid}")
                self.assertFalse(row["clickable"])


class TestEveryExample(unittest.TestCase):
    EXPECTED = {
        "co2_hydrogenation": {"CH3OH(g)": "none", "CO(g)": "none", "H2O(g)": "needed", "CH4(g)": "changes"},
        "steam_reforming": {"CO(g)": "changes", "CO2(g)": "changes", "H2(g)": "needed"},
        "dry_reforming": {"CO(g)": "needed", "H2(g)": "changes", "H2O(g)": "changes"},
        "ammonia": {"NH3(g)": "needed"},
        "syngas_to_methanol": {"CH3OH(g)": "changes", "H2O(g)": "changes"},
        "h2_o2": {"H2O(g)": "changes", "H2O2(g)": "none"},
        "nox": {"NO(g)": "changes", "NO2(g)": "none", "N2O(g)": "none"},
    }

    def test_classification_at_the_default_settings(self):
        self.assertEqual({n["id"] for n in library.NETWORKS}, set(self.EXPECTED))
        for net in library.NETWORKS:
            # the settings the page opens with: the example's own temperature, or the middle of its range
            T = net.get("T", round(sum(net["T_range"]) / 2))
            r = rows({"species": net["species"], "feed": net["feed"], "T": T, "P": net["P"], "sweep": "none", "switches": True})
            self.assertEqual(list(r), net["species"], net["id"])                    # one row per species, same order
            products = {s: x["effect"] for s, x in r.items() if x["state"] != "feed"}
            self.assertEqual(products, self.EXPECTED[net["id"]], net["id"])
            for x in r.values():
                self.assertEqual(x["clickable"], x["effect"] == "changes", f"{net['id']} {x['species']}")

    def test_guided_steps_use_products_of_their_own_example(self):
        with_tour = 0
        for net in library.NETWORKS:
            tour = net["tour"]
            self.assertIsInstance(tour, list, net["id"])
            if not tour:
                continue
            with_tour += 1
            self.assertEqual(tour[0]["off"], [], net["id"])                         # step 1 is "everything allowed"
            for step in tour:
                self.assertTrue(step["label"] and step["say"], net["id"])
                for sid in step["off"]:
                    self.assertIn(sid, net["species"], net["id"])
                    self.assertNotIn(sid, net["feed"], net["id"])
                # every step can be calculated, and a later step really changes the mixture
                res = ok("network", without({"species": net["species"], "feed": net["feed"], "T": sum(net["T_range"]) / 2,
                                             "P": net["P"], "sweep": "none", "switches": True}, *step["off"]))
                self.assertEqual(len(res["switches"]), len(net["species"]))
        self.assertGreaterEqual(with_tour, 5)
        sent = {n["id"]: n for n in ok("library", {})["networks"]}
        self.assertEqual(len(sent["co2_hydrogenation"]["tour"]), 3)                 # the page receives them
        # the CO2 example opens at the temperature its numbers in the guide and the report are for
        self.assertEqual(sent["co2_hydrogenation"]["T"], 523)
        lo, hi = sent["co2_hydrogenation"]["T_range"]
        self.assertTrue(lo <= 523 <= hi)


class TestRequest(unittest.TestCase):
    def test_switches_are_only_worked_out_on_request(self):
        plain = ok("network", dict(CO2, switches=False))
        self.assertIsNone(plain["switches"])
        self.assertIsNone(ok("network", {k: v for k, v in CO2.items() if k != "switches"})["switches"])
        # asking for them does not change the mixture
        asked = ok("network", CO2)
        self.assertEqual(asked["y"], plain["y"])
        self.assertEqual(asked["conversions"], plain["conversions"])

    def test_blocked_products_may_be_given_by_name_and_duplicates_are_ignored(self):
        r = rows(dict(without(CO2, "CH4(g)"), candidates=["methane", "CH4", "CO2"]))
        self.assertEqual([s for s, x in r.items() if x["state"] == "off"], ["CH4(g)"])

    def test_a_product_whose_elements_are_not_in_the_feed_cannot_form(self):
        r = rows(dict(CO2, species=CO2["species"] + ["NH3(g)"]))
        self.assertEqual(r["NH3(g)"]["effect"], "cannot_form")
        self.assertFalse(r["NH3(g)"]["clickable"])
        off = rows(dict(CO2, candidates=["NH3"]))
        self.assertEqual((off["NH3(g)"]["state"], off["NH3(g)"]["effect"]), ("off", "cannot_form"))

    def test_bad_requests_are_input_errors(self):
        for extra in ({"switches": "yes"}, {"switches": 1}, {"candidates": "CH4"}, {"candidates": [1]},
                      {"candidates": ["CH4"] * 21}):
            out = call("network", dict(CO2, **extra))
            self.assertFalse(out["ok"], extra)
            self.assertEqual(out["error"]["kind"], "input_error", extra)
        out = call("network", dict(CO2, candidates=["unobtainium"]))
        self.assertEqual(out["error"]["kind"], "unknown_species")

    def test_real_gas_model_and_a_system_where_nothing_reacts(self):
        r = rows(dict(CO2, model="pr", T=600))
        self.assertEqual(r["CH4(g)"]["effect"], "changes")
        # cold air: no NO forms at all, so no switch can change anything and none is "needed"
        cold = rows({"species": ["N2(g)", "O2(g)", "NO(g)", "NO2(g)"], "feed": {"N2(g)": 0.79, "O2(g)": 0.21},
                     "T": 400, "P": 1, "sweep": "none", "switches": True})
        self.assertEqual({cold["NO(g)"]["effect"], cold["NO2(g)"]["effect"]}, {"none"})


class TestThePage(unittest.TestCase):
    def test_the_tab_asks_for_the_switch_effects_and_has_its_places(self):
        with open(os.path.join(ROOT, "web", "tab-network.js"), encoding="utf-8") as fh:
            script = fh.read()
        for word in ("switches: true", "candidates", "aria-disabled", "no effect now", "needed"):
            self.assertIn(word, script)
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as fh:
            page = fh.read()
        for element in ('id="nw-switches"', 'id="nw-tour"', 'id="nw-say"'):
            self.assertIn(element, page)
        for net in library.NETWORKS:
            for sid in net["species"]:
                self.assertEqual(SPECIES[sid].phase, "g")


if __name__ == "__main__":
    unittest.main()
