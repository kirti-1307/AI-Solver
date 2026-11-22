"""One regression test for each finding of the independent code review
(docs/CODE_REVIEW.md). The labels C1, C2, S1 ... are the review's own."""

import json
import random
import unittest

from thermosolver import Reaction, SPECIES, api
from thermosolver.equilibrium import gibbs_minimize, reaction_equilibrium
from thermosolver.realgas import CUBIC, cubic_Z_roots, residual


def call(endpoint, payload):
    return json.loads(api.call(endpoint, json.dumps(payload)))


class TestCritical(unittest.TestCase):
    def test_C1_conversion_arrays_stay_aligned_with_the_pressure_axis(self):
        # Water has no vapour root above about 90 bar at 523 K with Peng/Robinson,
        # so the real-gas conversion stops there. The ideal-gas curve must not shift.
        out = call("pressure", {"equation": "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "T": 523.15, "P": 200,
                                "P_max": 300, "model": "pr"})
        sweep = out["result"]["sweep"]
        n = len(sweep["P"])
        self.assertEqual(len(sweep["conversion_ideal"]), n)
        self.assertEqual(len(sweep["conversion_real"]), n)
        self.assertTrue(all(v is not None for v in sweep["conversion_ideal"]))
        self.assertIsNone(sweep["conversion_real"][-1])
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        self.assertAlmostEqual(sweep["conversion_ideal"][-1],
                               reaction_equilibrium(rxn, 523.15, 300.0)["conversion"], places=10)
        self.assertGreater(sweep["conversion_ideal"][-1], 0.5)

    def test_C2_a_single_vapour_root_is_not_called_a_liquid(self):
        # In these states the equation of state has one root and it is vapour-like,
        # although the pressure is above the Lee/Kesler vapour-pressure estimate.
        for sid, T, P, model in [("CH3OH(g)", 487.0, 56.0, "vdw"), ("H2O(g)", 621.0, 169.0, "vdw"),
                                 ("C2H5OH(g)", 503.6, 52.1, "rk")]:
            res = residual(SPECIES[sid], T, P, model)
            self.assertNotEqual(res.state, "liquid_like", f"{sid} {model}")
            self.assertGreater(res.Z, 0.5)
        out = call("equilibrium", {"equation": "CO + 2 H2 -> CH3OH(g)", "T": 487, "P": 56, "model": "vdw"})
        self.assertTrue(out["ok"], out)

    def test_C2_classification_uses_the_equation_of_state_itself(self):
        # liquid-like <=> below Tc, single root, molar volume below the EOS critical volume
        rng = random.Random(7)
        gases = [s for s in SPECIES.values() if s.phase == "g" and s.critical]
        seen = set()
        for _ in range(4000):
            sp = rng.choice(gases)
            model = rng.choice(list(CUBIC))
            c = sp.critical
            T = c.Tc * rng.uniform(0.5, 1.3)
            P = c.Pc * rng.uniform(0.01, 3.0)
            res = residual(sp, T, P, model)
            roots = cubic_Z_roots(model, T / c.Tc, P / c.Pc, c.omega)
            expected = T < c.Tc and len(roots) == 1 and roots[0] * (T / c.Tc) / (P / c.Pc) < CUBIC[model].Zc
            self.assertEqual(res.state == "liquid_like", expected, f"{sp.id} {model} {T:.1f} K {P:.1f} bar")
            seen.add(res.state)
        self.assertEqual(seen, {"vapour", "hypothetical_vapour", "liquid_like"})

    def expect_input_error(self, endpoint, payload):
        out = call(endpoint, payload)
        self.assertFalse(out["ok"], f"{endpoint} {payload}")
        self.assertEqual(out["error"]["kind"], "input_error", f"{endpoint}: {out['error']['message']}")

    def test_C3a_number_of_points(self):
        base = {"equation": "N2 + 3 H2 -> 2 NH3", "T": 500}
        for bad in ("abc", 1e999, [3], -5, 0, 100000):
            for endpoint in ("analyze", "pressure", "heat_balance"):
                self.expect_input_error(endpoint, dict(base, n_points=bad))
        self.expect_input_error("network", {"species": ["N2", "H2", "NH3"], "feed": {"N2": 1, "H2": 3},
                                            "T": 700, "n_points": "abc"})

    def test_C3b_model_must_be_text(self):
        for bad in (["pr"], {"a": 1}, 3, True):
            self.expect_input_error("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": 10, "model": bad})

    def test_C3c_species_must_be_text(self):
        self.expect_input_error("network", {"species": [1, 2], "feed": {"N2": 1}, "T": 700})
        self.expect_input_error("network", {"species": ["N2", None], "feed": {"N2": 1}, "T": 700})

    def test_C3d_temperature_floor(self):
        for T in (1e-200, 1e-9, 0.005, 0.99):
            self.expect_input_error("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": T})
            self.expect_input_error("sensible", {"species": "CH4", "T1": T, "T2": 500})
            self.expect_input_error("species_residual", {"species": "CH4", "T": T, "P": 10})
        out = call("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 0.005})
        self.assertIn("at least 1 K", out["error"]["message"])      # S10: no untrue "above 0 K" message
        self.assertTrue(call("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 1.0})["ok"])

    def test_C3d_booleans_are_not_numbers(self):
        self.expect_input_error("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": True})
        self.expect_input_error("pressure", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": True})

    def test_C3e_absurd_coefficients(self):
        huge = "9" * 320 + " H2 -> H2"
        for endpoint in ("analyze", "balance", "equilibrium"):
            self.expect_input_error(endpoint, {"equation": huge, "T": 500})
        self.expect_input_error("analyze", {"equation": "10000000 H2 + 5000000 O2 -> 10000000 H2O", "T": 500})
        self.expect_input_error("analyze", {"equation": "0.0000000001 CH4 -> 0.0000000001 C(s) + 0.0000000002 H2", "T": 500})
        self.assertTrue(call("analyze", {"equation": "1000 H2 + 500 O2 -> 1000 H2O(g)", "T": 500})["ok"])

    def test_C3f_absurd_feed(self):
        self.expect_input_error("equilibrium", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 700, "P": 10,
                                                "feed": {"N2": 1e308, "H2": 1e308}})
        self.expect_input_error("network", {"species": ["N2", "H2", "NH3"], "feed": {"N2": 1e308, "H2": 3}, "T": 700})


class TestShouldFix(unittest.TestCase):
    # S1 concerned the electrochemical lens, which was later replaced by the heat lab
    # (see docs/CODE_REVIEW.md), so its regression test went with it.

    def test_S2_soave_alpha_fades_out_continuously(self):
        # The Soave term reaches zero at 1027.5 K for N2 with SRK. Nothing may jump there.
        n2 = SPECIES["N2(g)"]
        for P in (100.0, 1000.0):
            below = residual(n2, 1027.0, P, "srk")
            above = residual(n2, 1028.0, P, "srk")
            self.assertFalse(above.treated_ideal)
            self.assertAlmostEqual(below.Z, above.Z, delta=2e-4 * P / 100)
            self.assertAlmostEqual(below.lnphi, above.lnphi, delta=2e-4 * P / 100)
            self.assertAlmostEqual(below.HR, above.HR, delta=0.5 * P / 100)
            self.assertGreater(above.Z, 1.0)               # only the co-volume term is left
        hot = residual(n2, 1500.0, 100.0, "srk")
        self.assertTrue(any(n["kind"] == "alpha_range" for n in hot.notes))
        self.assertAlmostEqual(hot.HR - 1500.0 * hot.SR, 8.314 * 1500.0 * hot.lnphi, delta=1e-6)

    def test_S3_no_carbon_activity_on_a_foreign_reference_scale(self):
        T = 1000.0
        dGf = {"CH4(g)": 19720.0, "H2O(g)": -192420.0, "CO(g)": -200240.0, "CO2(g)": -395790.0, "H2(g)": 0.0}
        res = gibbs_minimize(list(dGf), {"CH4": 2, "H2O(g)": 3}, T, 1.0,
                             g_rt_override={k: v / (8.314 * T) for k, v in dGf.items()})
        self.assertIsNone(res["carbon_activity"])
        own = gibbs_minimize(list(dGf), {"CH4": 2, "H2O(g)": 3}, T, 1.0)
        boud = Reaction.parse("2 CO -> C(s) + CO2")
        self.assertAlmostEqual(own["carbon_activity"],
                               boud.K(T) * own["y"]["CO(g)"] ** 2 / own["y"]["CO2(g)"], places=8)

    def test_S6_constant_cp_lnK_comes_from_the_solver(self):
        ev = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2").evaluate(1000.0)
        self.assertAlmostEqual(ev["constant_cp"]["lnK"], -ev["constant_cp"]["dG"] / (8.314 * 1000.0), places=12)
        self.assertAlmostEqual(ev["no_cp"]["lnK"], -ev["no_cp"]["dG"] / (8.314 * 1000.0), places=12)

    def test_S8_network_sweep_reports_skipped_points(self):
        out = call("network", {"species": ["CO2", "H2", "CH3OH", "CO", "H2O(g)", "CH4"],
                               "feed": {"CO2": 1, "H2": 3}, "T": 650, "P": 50, "model": "pr",
                               "T_min": 400, "T_max": 900, "n_points": 21})
        sweep = out["result"]["sweep"]
        self.assertGreater(len(sweep["skipped"]), 0)
        self.assertLess(max(sweep["skipped"]), 647.1)       # only below the critical temperature of water
        self.assertIn("vapour", sweep["skipped_reason"])
        missing = [x for x, y in zip(sweep["x"], sweep["y"]["CO2(g)"]) if y is None]
        self.assertEqual(missing, sweep["skipped"])

    def test_S9_fully_reversed_reaction_is_labelled_as_such(self):
        rxn = Reaction.parse("CO2 + 2 H2O(g) -> CH4 + 2 O2")
        res = reaction_equilibrium(rxn, 298.15, 1.0, {"CH4": 1, "O2": 2})
        self.assertEqual(res["status"], "complete_reverse")
        self.assertAlmostEqual(res["extent"], -1.0)
        self.assertEqual(reaction_equilibrium(rxn, 298.15, 1.0)["status"], "no_forward_reaction")


class TestStructuredFuzz(unittest.TestCase):
    """S11: random JSON types on every parameter of every endpoint must never
    produce an internal error."""

    VALUES = [None, "", "abc", 0, -1, 1, 3.5, 1e-200, 1e308, 1e999, True, False, [], [1], ["pr"], {}, {"a": 1},
              "pr", "ideal", "T", "P", 298.15, 700, 5000, "CH4", "N2 + 3 H2 -> 2 NH3", "H2O(g)", ["N2", "H2", "NH3"],
              {"N2": 1, "H2": 3}, {"N2": "x"}, {"N2": -1}, [{"equation": "CO + H2O(g) -> CO2 + H2", "multiplier": 1}] * 2,
              "adiabatic", "duty", "predict", "identify", "excess", "conversion", "T_in", "T_out", "none", 0.2, 2.5, 12800,
              "CH4 + 2 O2 -> CO2 + 2 H2O(g)", "O2(g)", "C2H5OH(l)", {"mass": 1.2, "dT": 2.5, "calorific_value": 26440},
              {"mass": "x"}, [{"equation": "CO + H2O(g) -> CO2 + H2", "extent": 0.1}], [{"equation": 3}], {"N2(g)": 4}]
    KEYS = ["equation", "T", "P", "model", "n_points", "T_min", "T_max", "P_min", "P_max", "species", "feed",
            "steps", "sweep", "T1", "T2", "moles", "key_element", "name",
            "T_in", "T_out", "mode", "conversion", "excess", "excess_species", "key", "air", "extra", "side", "Q",
            "target_T", "sweep_min", "sweep_max", "fuel", "mass", "C_cal", "dT", "corrections", "calibration"]

    def test_never_an_internal_error(self):
        rng = random.Random(2026)
        for _ in range(6000):
            endpoint = rng.choice(list(api.ENDPOINTS))
            payload = {k: rng.choice(self.VALUES) for k in rng.sample(self.KEYS, rng.randint(0, 10))}
            try:
                text = json.dumps(payload)
            except ValueError:
                continue
            out = json.loads(api.call(endpoint, text))
            if not out["ok"]:
                self.assertNotEqual(out["error"]["kind"], "internal_error",
                                    f"{endpoint} {payload}: {out['error']['message']}")


if __name__ == "__main__":
    unittest.main()
