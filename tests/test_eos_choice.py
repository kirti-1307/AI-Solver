"""The solver chooses the equation of state for each gas (the user's request of
23 November 2026): the one whose residual enthalpy is closest to measured data.

These tests recompute the choice independently from the measured rows, pin the
numbers that the page, the guide and the report quote, and check that the
automatic choice keeps the relations between the residual properties.
"""

import json
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from thermosolver import api, data, eoschoice, library  # noqa: E402
from thermosolver.equilibrium import gibbs_minimize  # noqa: E402
from thermosolver.errors import PhaseError  # noqa: E402
from thermosolver.realgas import MODEL_NAMES, mixture_residual, residual  # noqa: E402
from thermosolver.species import SPECIES  # noqa: E402

EQUATIONS = ("virial", "vdw", "rk", "srk", "pr")


def ok(endpoint, payload=None):
    out = json.loads(api.call(endpoint, json.dumps(payload or {})))
    assert out["ok"], out
    return out["result"]


class TestMeasuredData(unittest.TestCase):
    def test_twenty_four_gases_of_the_database(self):
        self.assertEqual(len(data.NIST_FLUID), 24)
        for sid, (webbook_id, rows) in data.NIST_FLUID.items():
            sp = SPECIES[sid]
            self.assertEqual(sp.phase, "g", sid)
            self.assertIsNotNone(sp.critical, sid)
            self.assertTrue(webbook_id.startswith("C"), sid)
            keys = [(T, P) for T, P, _ in rows]
            self.assertEqual(len(keys), len(set(keys)), f"{sid}: a point appears twice")
            temps = {T for T, _, _ in rows}
            self.assertTrue(temps <= {300, 400, 500, 600, 700, 800, 1000}, sid)
            for T in temps:                     # every isotherm has its 0.01 bar row, the ideal-gas reference
                self.assertIn((T, 0.01), keys, f"{sid} at {T} K")
            self.assertTrue(all(P in (0.01, 10.01, 50.01, 100.01, 200.01, 300.01) for _, P, _ in rows), sid)

    def test_a_few_rows_as_read_from_nist(self):
        # H^R = H(T, P) - H(T, 0.01 bar), from rows copied from the WebBook
        pts = {(T, P): hr for T, P, hr in eoschoice.measured_points("CO2(g)")}
        self.assertAlmostEqual(pts[(400, 300.01)], 1000 * (19.594 - 26.307), places=6)
        pts = {(T, P): hr for T, P, hr in eoschoice.measured_points("CH3OH(g)")}
        self.assertAlmostEqual(pts[(600, 300.01)], 1000 * (35.495 - 51.483), places=6)
        self.assertEqual(sum(len(eoschoice.measured_points(s)) for s in data.NIST_FLUID), 380)

    def test_the_source_is_documented(self):
        self.assertIn("Thermophysical Properties of Fluid Systems", data.SOURCES["fluid_webbook"])


class TestTheChoice(unittest.TestCase):
    def test_each_gas_gets_the_equation_with_the_smallest_mean_error(self):
        # recomputed here without the module, straight from realgas.residual
        for sid in data.NIST_FLUID:
            sp = SPECIES[sid]
            errs = {m: [] for m in EQUATIONS}
            for T, P, hr in eoschoice.measured_points(sid):
                vals = {m: residual(sp, T, P, m) for m in EQUATIONS}
                if any(v.state == "liquid_like" for v in vals.values()):
                    continue
                for m in EQUATIONS:
                    errs[m].append(abs(vals[m].HR - hr))
            means = {m: sum(e) / len(e) for m, e in errs.items()}
            best = min(EQUATIONS, key=lambda m: means[m])
            s = eoschoice.scores(sid)
            self.assertEqual(s["best"], best, sid)
            for m in EQUATIONS:
                self.assertAlmostEqual(s["mean"][m], means[m], places=6)
            model, why = eoschoice.choose(sp)
            self.assertEqual((model, why["basis"]), (best, "measured"))

    def test_what_the_data_say(self):
        o = eoschoice.overall()
        self.assertEqual(o["wins"], {"virial": 0, "vdw": 0, "rk": 4, "srk": 14, "pr": 6})
        self.assertEqual(o["best"], "srk")
        self.assertEqual(o["points"], 380)
        self.assertAlmostEqual(o["mean"]["srk"], 137.0, delta=0.5)
        self.assertAlmostEqual(o["mean"]["pr"], 160.0, delta=0.5)
        expected = {"CH3OH(g)": "srk", "NH3(g)": "srk", "H2O(g)": "srk", "CO2(g)": "pr", "N2(g)": "pr",
                    "H2(g)": "rk", "CH4(g)": "rk", "CO(g)": "rk", "O2(g)": "rk"}
        for sid, model in expected.items():
            self.assertEqual(eoschoice.choose(SPECIES[sid])[0], model, sid)

    def test_gases_without_measured_data_or_critical_constants(self):
        model, why = eoschoice.choose(SPECIES["C2H5OH(g)"])                    # no NIST fluid data
        self.assertEqual((model, why["basis"]), ("srk", "overall"))
        self.assertEqual(eoschoice.choose(SPECIES["NO2(g)"]), ("ideal", {"basis": "no_critical"}))
        self.assertEqual(eoschoice.choose(SPECIES["H2O(l)"]), ("ideal", {"basis": "condensed"}))
        res = residual(SPECIES["NO2(g)"], 500.0, 50.0, "auto")
        self.assertTrue(res.treated_ideal)
        self.assertEqual(res.model, "ideal")
        self.assertTrue(any(n["kind"] == "no_critical_data" for n in res.notes))

    def test_auto_is_exactly_the_chosen_equation(self):
        for sid, T, P in (("CH3OH(g)", 523.15, 50.0), ("H2(g)", 723.15, 200.0), ("C2H5OH(g)", 573.15, 70.0)):
            sp = SPECIES[sid]
            chosen, _ = eoschoice.choose(sp)
            a, b = residual(sp, T, P, "auto"), residual(sp, T, P, chosen)
            self.assertEqual(a.model, chosen)
            for key in ("HR", "SR", "lnphi", "Z"):
                self.assertEqual(getattr(a, key), getattr(b, key), f"{sid} {key}")
            self.assertEqual(a.to_dict()["model_name"], MODEL_NAMES[chosen])
            self.assertIn(a.choice["basis"], ("measured", "overall"))

    def test_one_equation_per_gas_keeps_the_residual_relations(self):
        # The choice does not change with T or P, so dH^R/dT and the Gibbs-Helmholtz relation hold.
        for case in library.PRESSURE_CASES:
            _, _, eq, *_ = library.reaction_by_id(case["id"])
            r = ok("pressure", {"equation": eq, "T": case["T"], "P": case["P"]})
            self.assertEqual(r["model"], "auto")
            self.assertTrue(all(a["passed"] for a in r["audit"]), case["id"])


class TestTheTabs(unittest.TestCase):
    def test_tab_2_ammonia(self):
        r = ok("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 723.15, "P": 200})
        models = {s["species"]: s["model"] for s in r["at_P"]["species"]}
        self.assertEqual(models, {"N2(g)": "pr", "H2(g)": "rk", "NH3(g)": "srk"})
        hr = {s["species"]: s["HR"] for s in r["at_P"]["species"]}
        c = r["comparison"]
        self.assertAlmostEqual(c["residual"], -hr["N2(g)"] - 3 * hr["H2(g)"] + 2 * hr["NH3(g)"], places=6)
        self.assertAlmostEqual(c["residual"], -5049.5, delta=1.0)
        self.assertAlmostEqual(c["dH_real"], -111553.6, delta=1.0)
        self.assertAlmostEqual(c["percent"], 4.74, delta=0.01)
        self.assertAlmostEqual(c["path"]["reactants_to_ideal"], -1152.1, delta=1.0)    # -(1 x 177 + 3 x 325) J
        self.assertAlmostEqual(c["path"]["products_to_real"], -3897.4, delta=1.0)      # 2 x (-1949) J

    def test_tab_2_still_says_when_a_gas_is_a_liquid(self):
        r = ok("pressure", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15, "P": 200})
        self.assertFalse(r["at_P"]["gas_phase_valid"])
        self.assertEqual(r["at_P"]["no_vapour_species"], ["H2O(g)"])
        self.assertEqual(r["gas_limit"]["P_suggest"], 88.0)

    def test_tab_4_example(self):
        net = next(n for n in library.NETWORKS if n["id"] == "co2_hydrogenation")

        def shares(off, T=523.0, P=50.0):
            r = ok("network", {"species": [s for s in net["species"] if s not in off], "feed": net["feed"],
                               "T": T, "P": P, "model": "auto", "sweep": "none"})
            return {s: round(100 * v, 1) for s, v in r["atom_distribution"].items()}
        self.assertEqual(shares([])["CH4(g)"], 74.9)
        s = shares(["CH4(g)"])
        self.assertEqual((s["CO2(g)"], s["CH3OH(g)"], s["CO(g)"]), (71.9, 20.6, 7.5))
        self.assertEqual(shares(["CH4(g)", "CO(g)"])["CH3OH(g)"], 24.5)
        self.assertEqual(shares(["CH4(g)", "CO(g)"], P=1.0)["CH3OH(g)"], 0.6)
        self.assertEqual(shares(["CH4(g)"], P=100.0)["CH3OH(g)"], 39.4)
        self.assertEqual(shares(["CH4(g)"], T=700.0)["CO(g)"], 41.0)

    def test_every_tab_4_example_works_along_its_plot(self):
        for net in library.NETWORKS:
            T = net.get("T", 0.5 * sum(net["T_range"]))
            r = ok("network", {"species": net["species"], "feed": net["feed"], "T": T, "P": net["P"], "model": "auto",
                               "sweep": "T", "T_min": net["T_range"][0], "T_max": net["T_range"][1]})
            self.assertEqual(r["sweep"].get("skipped") or [], [], net["id"])

    def test_a_gas_with_no_gas_state_of_its_own_in_a_mixture(self):
        # Water at 523 K and 100 bar: SRK has no gas state for pure water. In the mixture it stays a
        # vapour, described by the virial correlation, and the page says so.
        sp = SPECIES["H2O(g)"]
        self.assertEqual(residual(sp, 523.0, 100.0, "auto").state, "liquid_like")
        res = mixture_residual(sp, 523.0, 100.0, "auto")
        self.assertEqual(res.state, "hypothetical_vapour")
        self.assertEqual(res.model, "virial")
        self.assertEqual(res.lnphi, residual(sp, 523.0, 100.0, "virial").lnphi)
        self.assertTrue(any(n["kind"] == "vapour_fallback" for n in res.notes))
        with open(os.path.join(ROOT, "web", "tab-network.js"), encoding="utf-8") as fh:
            self.assertIn("vapour_fallback", fh.read())                   # the page shows that note
        # just below the pressure where SRK loses the gas state, the two differ little
        below = residual(sp, 523.0, 90.0, "auto")
        self.assertEqual(below.model, "srk")
        self.assertLess(abs(below.lnphi - residual(sp, 523.0, 90.0, "virial").lnphi), 0.04)
        # an equation named by the caller is never replaced
        feed = {"CO2(g)": 1, "H2(g)": 3}
        with self.assertRaises(PhaseError):
            gibbs_minimize(["CO2(g)", "H2(g)", "CH3OH(g)", "H2O(g)"], feed, 523.0, 100.0, model="srk")
        gibbs_minimize(["CO2(g)", "H2(g)", "CH3OH(g)", "H2O(g)"], feed, 523.0, 100.0, model="auto")

    def test_the_soot_test_with_real_gases(self):
        # Kp of 2 CO -> C(s) + CO2 over the gas ratio, each partial pressure times exp(G^R/RT) = phi
        from thermosolver.reaction import Reaction
        net = next(n for n in library.NETWORKS if n["id"] == "co2_hydrogenation")
        r = ok("network", {"species": [s for s in net["species"] if s != "CH4(g)"], "feed": net["feed"],
                           "T": 700.0, "P": 50.0, "model": "auto", "sweep": "none"})
        f = {s: r["y"][s] * 50.0 * math.exp(residual(SPECIES[s], 700.0, 50.0, "auto").lnphi) for s in ("CO(g)", "CO2(g)")}
        Kp = Reaction.parse("2 CO -> C(s) + CO2").K(700.0)
        self.assertAlmostEqual(Kp / (f["CO2(g)"] / f["CO(g)"] ** 2), r["carbon_activity"], delta=1e-6 * r["carbon_activity"])

    def test_the_validation_tab_answer(self):
        e = ok("eos_check")
        self.assertEqual(len(e["rows"]), 24)
        self.assertEqual(e["overall"]["best"], "srk")
        self.assertEqual(set(e["names"]), set(EQUATIONS))
        gases = [s for s, sp in SPECIES.items() if sp.phase == "g"]
        self.assertEqual([c["species"] for c in e["choices"]], gases)
        self.assertEqual({c["basis"] for c in e["choices"]}, {"measured", "overall", "no_critical"})


if __name__ == "__main__":
    unittest.main()
