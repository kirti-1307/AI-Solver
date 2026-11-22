"""The JSON API the web page talks to, the textbook benchmarks, and the five
stress tests of the assignment's AI Error Challenge."""

import json
import math
import os
import random
import re
import unittest

from thermosolver import api, benchmarks, library


def call(endpoint, payload=None):
    text = api.call(endpoint, json.dumps(payload or {}))
    return json.loads(text)


def ok(endpoint, payload=None):
    out = call(endpoint, payload)
    if not out["ok"]:
        raise AssertionError(f"{endpoint} failed: {out['error']}")
    return out["result"]


def assert_json_safe(testcase, obj, path="result"):
    if isinstance(obj, float):
        testcase.assertTrue(math.isfinite(obj), f"non-finite number at {path}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            assert_json_safe(testcase, v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_json_safe(testcase, v, f"{path}[{i}]")


class TestBenchmarks(unittest.TestCase):
    def test_every_textbook_benchmark_passes(self):
        rows = benchmarks.build()
        self.assertGreaterEqual(len(rows), 40)
        failed = [(r["description"], r["expected"], r["computed"], r["error"]) for r in rows if not r["passed"]]
        self.assertEqual(failed, [])

    def test_validate_endpoint(self):
        res = ok("validate")
        self.assertEqual(res["summary"]["passed"], res["summary"]["total"])


class TestDeployment(unittest.TestCase):
    """Things that only break on the hosted page, checked before they can."""

    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_browser_worker_loads_every_solver_module(self):
        # web/worker.js copies a fixed list of files into the in-browser Python.
        # A new module that is missing from that list works locally and fails online.
        with open(os.path.join(self.ROOT, "web", "worker.js"), encoding="utf-8") as fh:
            source = fh.read()
        block = re.search(r"const FILES = \[(.*?)\];", source, re.S).group(1)
        listed = set(re.findall(r'"([\w.]+\.py)"', block))
        on_disk = {f for f in os.listdir(os.path.join(self.ROOT, "thermosolver")) if f.endswith(".py")}
        self.assertEqual(listed, on_disk - {"__main__.py"})

    def test_github_pages_will_serve_underscore_files(self):
        # Without .nojekyll GitHub Pages drops thermosolver/__init__.py
        self.assertTrue(os.path.exists(os.path.join(self.ROOT, ".nojekyll")))

    def test_page_loads_every_script_it_needs(self):
        with open(os.path.join(self.ROOT, "index.html"), encoding="utf-8") as fh:
            html = fh.read()
        # Every local file carries the same ?v= tag, so that a browser never mixes
        # files of two releases from its cache.
        tagged = re.findall(r'(?:src|href)="(web/[^"?]+)\?v=([^"]+)"', html)
        for src, _ in tagged:
            self.assertTrue(os.path.exists(os.path.join(self.ROOT, src)), src)
        self.assertEqual(len({version for _, version in tagged}), 1)
        self.assertNotRegex(html, r'(?:src|href)="web/[^"?]+"')            # nothing left untagged
        scripts = {src[len("web/"):] for src, _ in tagged if src.endswith(".js")}
        on_disk = {f for f in os.listdir(os.path.join(self.ROOT, "web")) if f.endswith(".js")}
        self.assertEqual(scripts, on_disk - {"worker.js"})
        with open(os.path.join(self.ROOT, "web", "ui.js"), encoding="utf-8") as fh:
            worker = re.search(r'new Worker\("web/worker\.js\?v=([^"]+)"\)', fh.read())
        self.assertIsNotNone(worker)
        self.assertEqual(worker.group(1), tagged[0][1])

    def test_no_thermodynamic_constants_in_the_front_end(self):
        # The page must not carry its own copy of R or of any correlation constant.
        for name in os.listdir(os.path.join(self.ROOT, "web")):
            if not name.endswith(".js"):
                continue
            with open(os.path.join(self.ROOT, "web", name), encoding="utf-8") as fh:
                text = fh.read()
            for constant in ("8.314", "83.14", "96485", "0.08664", "0.42748", "0.07780", "0.45724", "0.422", "0.172"):
                self.assertNotIn(constant, text, f"{constant} found in web/{name}")


class TestPublishedValues(unittest.TestCase):
    """Assignment stress test 5: check against published research."""

    @classmethod
    def setUpClass(cls):
        cls.lit = ok("literature")

    def test_heats_of_reaction_within_half_a_kJ(self):
        self.assertGreaterEqual(len(self.lit["enthalpies"]), 8)
        for row in self.lit["enthalpies"]:
            self.assertAlmostEqual(row["solver"] / 1000.0, row["published"], delta=0.5, msg=row["name"])

    def test_equilibrium_constants_within_1p2_kJ_of_published_correlations(self):
        self.assertGreaterEqual(len(self.lit["equilibrium"]), 12)
        for row in self.lit["equilibrium"]:
            self.assertLess(abs(row["dG_equivalent"]), 1200.0, f"{row['name']} at {row['T']} K")
            self.assertLess(abs(row["solver"] / row["published"] - 1.0), 0.25, f"{row['name']} at {row['T']} K")

    def test_janaf_values(self):
        rows = {r["name"]: r for r in self.lit["other"]}
        g = rows["H2 + 1/2 O2 -> H2O(g): standard Gibbs energy change at 1000 K"]
        self.assertAlmostEqual(g["solver"], g["published"], delta=0.05)          # kJ/mol
        h = rows["H2 + 1/2 O2 -> H2O(g): standard heat of reaction at 1000 K"]
        self.assertAlmostEqual(h["solver"], h["published"], delta=0.1)

    def test_pressure_effect_against_nist_reference_equations(self):
        rows = {r["name"]: r for r in self.lit["other"]}
        total = rows["Ammonia synthesis: change of the heat of reaction from 1 to 200 bar at 700 K, per mol NH3"]
        self.assertAlmostEqual(total["solver"], total["published"], delta=0.15)   # kJ/mol
        nh3 = rows["NH3(g): enthalpy change from 1 to 200 bar at 700 K (Peng/Robinson residual)"]
        self.assertAlmostEqual(nh3["solver"], nh3["published"], delta=0.35)


class TestEndpoints(unittest.TestCase):
    def test_database(self):
        db = ok("database")
        self.assertGreaterEqual(db["count"], 30)
        self.assertEqual(db["constants"], {"R": 8.314, "T0": 298.15, "P0": 1.0})
        water = next(s for s in db["species"] if s["id"] == "H2O(g)")
        self.assertEqual(water["dHf"], -241818.0)
        self.assertEqual(water["critical"]["Tc"], 647.1)
        assert_json_safe(self, db)

    def test_library(self):
        lib = ok("library")
        self.assertGreaterEqual(len(lib["reactions"]), 20)      # assignment asks for 15-20
        self.assertGreaterEqual(len(lib["combinations"]), 3)
        self.assertGreaterEqual(len(lib["networks"]), 3)
        assert_json_safe(self, lib)

    def test_analyze_every_library_reaction(self):
        for row in library.REACTIONS:
            res = ok("analyze", {"equation": row[2], "T": row[4]})
            self.assertIn("at_T", res)
            self.assertTrue(all(c["passed"] for c in res["audit"]), row[0])
            self.assertGreaterEqual(len(res["steps"]), 3)
            assert_json_safe(self, res)
            if res["has_cp"]:
                self.assertEqual(len(res["sweep"]["T"]), 81)

    def test_pressure_every_gas_reaction(self):
        for row in library.REACTIONS:
            for model in ("virial", "pr"):
                res = ok("pressure", {"equation": row[2], "T": max(row[4], 400.0), "P": 100, "model": model,
                                      "n_points": 9})
                self.assertTrue(all(c["passed"] for c in res["audit"]), f"{row[0]} {model}")
                self.assertEqual(len(res["sweep"]["dH_P"]), 9)
                assert_json_safe(self, res)

    def test_combine_every_library_combination(self):
        for combo in library.COMBINATIONS:
            res = ok("combine", {"T": combo["T"],
                                 "steps": [{"equation": eq, "multiplier": m} for eq, m in combo["steps"]]})
            self.assertLess(res["max_difference_J"], 1e-6)
            assert_json_safe(self, res)

    def test_network_every_library_example(self):
        for net in library.NETWORKS:
            res = ok("network", {"species": net["species"], "feed": net["feed"],
                                 "T": sum(net["T_range"]) / 2, "P": net["P"],
                                 "T_min": net["T_range"][0], "T_max": net["T_range"][1], "n_points": 11})
            self.assertAlmostEqual(sum(res["y"].values()), 1.0, places=9)
            self.assertEqual(len(res["sweep"]["x"]), 11)
            for series in res["sweep"]["y"].values():
                self.assertTrue(all(v is not None for v in series), net["id"])
            assert_json_safe(self, res)

    def test_network_pressure_sweep(self):
        res = ok("network", {"species": ["N2", "H2", "NH3"], "feed": {"N2": 1, "H2": 3}, "T": 700, "P": 100,
                             "sweep": "P", "P_min": 1, "P_max": 300, "n_points": 7, "model": "pr"})
        nh3 = res["sweep"]["y"]["NH3(g)"]
        self.assertTrue(all(b > a for a, b in zip(nh3, nh3[1:])))

    def test_heat_balance_every_example(self):
        self.assertGreaterEqual(len(library.HEAT_EXAMPLES), 6)
        for ex in library.HEAT_EXAMPLES:
            payload = {k: v for k, v in ex.items() if k not in ("id", "name", "note")}
            res = ok("heat_balance", dict(payload, n_points=9))
            self.assertTrue(all(c["passed"] for c in res["point"]["audit"]), ex["id"])
            self.assertEqual(len(res["sweep"]["x"]), 9)
            self.assertEqual(res["mode"], ex["mode"])
            assert_json_safe(self, res)

    def test_the_removed_endpoint_is_gone(self):
        out = call("electro", {"equation": "H2 + 1/2 O2 -> H2O(g)"})
        self.assertEqual(out["error"]["kind"], "input_error")

    def test_sensible(self):
        res = ok("sensible", {"species": "CH4", "T1": 533.15, "T2": 873.15, "moles": 1})
        self.assertAlmostEqual(res["Q"], 19778.0, delta=1.0)
        self.assertEqual(res["warnings"], [])
        res = ok("sensible", {"species": "CH4", "T1": 300, "T2": 1800})
        self.assertEqual(len(res["warnings"]), 1)

    def test_balance_and_formation(self):
        res = ok("balance", {"equation": "Fe2O3 + H2 -> Fe + H2O"})
        self.assertFalse(res["balanced"])
        self.assertEqual(res["suggestion"], "Fe2O3(s) + 3 H2(g) → 2 Fe(s) + 3 H2O(g)")
        res = ok("formation", {"species": "NH3", "T": 700})
        self.assertEqual(res["equation"], "1/2 N2(g) + 3/2 H2(g) → NH3(g)")

    def test_species_residual_and_equilibrium(self):
        res = ok("species_residual", {"species": "n-C4H10", "T": 500, "P": 50})
        self.assertEqual([m["model"] for m in res["models"]], ["virial", "vdw", "rk", "srk", "pr"])
        res = ok("equilibrium", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": 200, "model": "pr",
                                 "feed": {"N2": 1, "H2": 3, "CH4": 0.2}})
        self.assertTrue(0 < res["conversion"] < 1)


class TestErrorHandling(unittest.TestCase):
    def expect(self, endpoint, payload, kind):
        out = call(endpoint, payload)
        self.assertFalse(out["ok"], f"{endpoint} {payload} should fail")
        self.assertEqual(out["error"]["kind"], kind, out["error"]["message"])
        self.assertTrue(out["error"]["message"])

    def test_expected_errors_have_the_right_kind(self):
        self.expect("analyze", {"equation": "CH4 + O2 -> CO2 + H2O"}, "unbalanced_reaction")
        self.expect("analyze", {"equation": "CS2 + 3 O2 -> CO2 + 2 SO2"}, "unknown_species")
        self.expect("analyze", {"equation": "CH4 + 2 O2 -> CO2 + 2 H2O", "T": 25 - 273.15 - 100}, "input_error")
        self.expect("analyze", {"equation": "CH4 + 2 O2 -> CO2 + 2 H2O", "T": "hot"}, "input_error")
        self.expect("analyze", {}, "input_error")
        self.expect("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": 0}, "input_error")
        self.expect("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": 10, "model": "x"}, "input_error")
        self.expect("combine", {"steps": [{"equation": "CO + H2O(g) -> CO2 + H2", "multiplier": 1}]}, "input_error")
        self.expect("network", {"species": ["N2", "H2", "NH3"], "feed": {}}, "input_error")
        self.expect("heat_balance", {"equation": "CH4 + 2 O2 -> CO2 + 2 H2O(g)", "mode": "x"}, "input_error")
        self.expect("calorimeter", {"fuel": "CO2", "mass": 1, "C_cal": 10000}, "input_error")
        self.expect("nonsense", {}, "input_error")

    def test_nist_species_through_the_api(self):
        res = ok("analyze", {"equation": "2 H2O2 -> 2 H2O + O2", "T": 400})
        self.assertTrue(any(w["kind"] == "data_source" for w in res["warnings"]))
        self.assertTrue(all(c["passed"] for c in res["audit"]))
        self.assertIn("ΔE", res["steps"][3]["work"])               # the cubic term is shown when used
        plain = ok("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 400})
        self.assertNotIn("ΔE", plain["steps"][3]["work"])
        db = ok("database")
        self.assertEqual(db["count"], 57)
        self.assertEqual(db["svn_count"], 54)
        h2o2 = next(s for s in db["species"] if s["id"] == "H2O2(g)")
        self.assertFalse(h2o2["from_svn"])
        self.assertEqual(len(h2o2["cp"]), 5)
        # sensible heat of acetic acid vapour against a hand integration of the NIST table
        res = ok("sensible", {"species": "CH3COOH(g)", "T1": 400, "T2": 800})
        table = {400: 79.66, 500: 93.93, 600: 106.18, 700: 116.63, 800: 125.50}
        trapezoid = sum(100.0 * (table[t] + table[t + 100]) / 2 for t in (400, 500, 600, 700))
        self.assertAlmostEqual(res["dH_molar"], trapezoid, delta=0.004 * trapezoid)

    def test_combine_error_names_the_step(self):
        out = call("combine", {"steps": [{"equation": "CO + H2O(g) -> CO2 + H2", "multiplier": 1},
                                         {"equation": "CH4 + O2 -> CO2", "multiplier": 1}]})
        self.assertIn("Step 2", out["error"]["message"])

    def test_invalid_json(self):
        out = json.loads(api.call("analyze", "{not json"))
        self.assertEqual(out["error"]["kind"], "input_error")
        out = json.loads(api.call("analyze", "[1, 2]"))
        self.assertEqual(out["error"]["kind"], "input_error")

    def test_garbage_never_causes_an_internal_error(self):
        rng = random.Random(1307)
        pieces = ["CH4", "O2", "CO2", "H2O", "H2", "N2", "NH3", "->", "+", "=", "2", "1/2", "0", "-1", "(g)",
                  "(l)", "(s)", "(", ")", "xyz", "", " ", "→", "1e400", "C(s)", "CaCO3", "CH3COOH", "3.5", "/0",
                  "*", "💥", "<script>", "'; DROP", "H2O(l)", "Fe", "1-butene", ",", "..", "++"]
        endpoints = ("analyze", "pressure", "heat_balance", "balance", "equilibrium")
        for _ in range(1500):
            text = " ".join(rng.choice(pieces) for _ in range(rng.randint(1, 9)))
            payload = {"equation": text, "T": rng.choice([300, 700, 2500, 0, -1, "a", None, 1e9]),
                       "P": rng.choice([1, 100, 0, -5, "b", None, 1e9]),
                       "model": rng.choice(["pr", "virial", "ideal", "srk", "zzz", None])}
            for ep in endpoints:
                out = call(ep, payload)
                if not out["ok"]:
                    self.assertNotEqual(out["error"]["kind"], "internal_error",
                                        f"{ep} {payload}: {out['error']['message']}")

    def test_extreme_but_legal_conditions(self):
        for T in (1.0, 50.0, 298.15, 3000.0, 6000.0):
            for P in (1e-6, 1.0, 5000.0):
                for model in ("ideal", "virial", "vdw", "rk", "srk", "pr"):
                    out = call("pressure", {"equation": "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "T": T, "P": P,
                                            "model": model, "n_points": 3})
                    if not out["ok"]:
                        self.assertNotEqual(out["error"]["kind"], "internal_error",
                                            f"T={T} P={P} {model}: {out['error']['message']}")


class TestAIErrorChallenge(unittest.TestCase):
    """The five stress tests listed in the assignment."""

    @classmethod
    def setUpClass(cls):
        cls.res = ok("challenge")

    def test_1_stoichiometry_unbalanced_reactions_are_rejected(self):
        cases = {c["input"]: c for c in self.res["stoichiometry"]}
        self.assertFalse(cases["CH4 + O2 -> CO2 + H2O"]["accepted"])
        self.assertEqual(cases["CH4 + O2 -> CO2 + H2O"]["suggestion"], "CH4(g) + 2 O2(g) → CO2(g) + 2 H2O(g)")
        self.assertFalse(cases["N2 + H2 -> NH3"]["accepted"])
        self.assertTrue(cases["CO + 2 H2 -> CH3OH"]["accepted"])

    def test_2_constant_versus_temperature_dependent_cp_at_1000K(self):
        smr = self.res["cp_assumption"][0]
        self.assertEqual(smr["T"], 1000.0)
        self.assertAlmostEqual(smr["dH"], 225255.0, delta=5.0)
        self.assertGreater(abs(smr["dH_const"] - smr["dH"]), 10000.0)   # 13.6 kJ/mol error
        self.assertGreater(abs(smr["dH_none"] - smr["dH"]), 15000.0)    # 19.4 kJ/mol error

    def test_3_physical_state_of_water_in_methane_combustion(self):
        ps = self.res["physical_state"]
        self.assertAlmostEqual(ps["liquid"]["dH0"], -890649.0)
        self.assertAlmostEqual(ps["vapour"]["dH0"], -802625.0)
        self.assertAlmostEqual(ps["difference_dH"], 2 * 44012.0)
        self.assertAlmostEqual(ps["difference_dH"], ps["explained"])

    def test_4_extrapolation_warnings(self):
        by_T = {(e["equation"], e["T"]): e for e in self.res["extrapolation"]}
        smr = "CH4(g) + H2O(g) → CO(g) + 3 H2(g)"
        self.assertFalse(by_T[(smr, 1400.0)]["warned"])
        self.assertTrue(by_T[(smr, 2200.0)]["warned"])
        self.assertTrue(all(e["warned"] for e in self.res["extrapolation"] if e["T"] != 1400.0))


if __name__ == "__main__":
    unittest.main()
