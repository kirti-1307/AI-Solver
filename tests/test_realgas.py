"""Real-gas models and residual properties, and the effect of pressure on a
reaction at constant temperature."""

import math
import unittest

from thermosolver import InputError, R, Reaction, SPECIES
from thermosolver.audit import all_passed, audit_residuals
from thermosolver.realgas import (
    CUBIC, cubic_Z_roots, pressure_sweep, psat_estimate, reaction_at_pressure, residual,
)

MODELS = ("virial", "vdw", "rk", "srk", "pr")


def eps_b(eos, b):
    return eos.epsilon * b


class TestTextbookNumbers(unittest.TestCase):
    def test_table_3_1_parameters(self):
        self.assertAlmostEqual(CUBIC["vdw"].Omega, 0.125)
        self.assertAlmostEqual(CUBIC["vdw"].Psi, 0.421875)
        self.assertEqual((CUBIC["rk"].Omega, CUBIC["rk"].Psi), (0.08664, 0.42748))
        self.assertEqual((CUBIC["pr"].Omega, CUBIC["pr"].Psi), (0.07780, 0.45724))
        self.assertAlmostEqual(CUBIC["pr"].sigma, 1 + math.sqrt(2))
        self.assertAlmostEqual(CUBIC["pr"].epsilon, 1 - math.sqrt(2))

    def test_critical_compressibility_of_each_cubic(self):
        # At the critical point each cubic gives its own fixed Zc (SVN Table 3.1).
        # The critical point is a triple root, so the five-digit rounding of
        # Omega and Psi in the table moves the root by roughly the cube root of
        # the rounding error (about 0.01). van der Waals uses exact fractions.
        self.assertAlmostEqual(cubic_Z_roots("vdw", 1.0, 1.0, 0.1)[-1], 0.375, delta=1e-4)
        for model, zc in (("rk", 1 / 3), ("srk", 1 / 3), ("pr", 0.30740)):
            roots = cubic_Z_roots(model, 1.0, 1.0, 0.1)
            self.assertAlmostEqual(roots[-1], zc, delta=0.02, msg=model)

    def test_roots_satisfy_the_pressure_explicit_equation(self):
        # Independent of the Z-polynomial: put V = ZRT/P back into
        # P = RT/(V-b) - a(T)/((V+eps*b)(V+sigma*b)) and recover P.
        Rg = 83.14
        for sid, T, P in [("n-C4H10(g)", 350.0, 9.4573), ("CO2(g)", 283.0, 49.0), ("NH3(g)", 700.0, 200.0),
                          ("H2O(g)", 500.0, 20.0), ("CH4(g)", 150.0, 8.0), ("N2(g)", 300.0, 500.0)]:
            c = SPECIES[sid].critical
            for model, eos in CUBIC.items():
                b = eos.Omega * Rg * c.Tc / c.Pc
                a = eos.Psi * eos.alpha(T / c.Tc, c.omega) * Rg ** 2 * c.Tc ** 2 / c.Pc
                roots = cubic_Z_roots(model, T / c.Tc, P / c.Pc, c.omega)
                self.assertIn(len(roots), (1, 3), f"{sid} {model}")
                for Z in roots:
                    V = Z * Rg * T / P
                    P_back = Rg * T / (V - b) - a / ((V + eps_b(eos, b)) * (V + eos.sigma * b))
                    self.assertAlmostEqual(P_back, P, delta=1e-8 * P, msg=f"{sid} {model} Z={Z}")

    def test_n_butane_500K_50bar(self):
        but = SPECIES["n-C4H10(g)"]
        expected = {"vdw": (0.6608, -3937, -5.424), "rk": (0.6850, -4505, -6.546),
                    "srk": (0.7222, -4824, -7.413), "pr": (0.6907, -4988, -7.426)}
        for model, (z, hr, sr) in expected.items():
            res = residual(but, 500.0, 50.0, model)
            self.assertAlmostEqual(res.Z, z, delta=5e-4, msg=model)
            self.assertAlmostEqual(res.HR, hr, delta=5.0, msg=model)
            self.assertAlmostEqual(res.SR, sr, delta=0.008, msg=model)

    def test_virial_coefficients_n_butane_510K(self):
        Tr = 510.0 / 425.1
        self.assertAlmostEqual(0.083 - 0.422 / Tr ** 1.6, -0.232, delta=5e-4)
        self.assertAlmostEqual(0.139 - 0.172 / Tr ** 4.2, 0.059, delta=5e-4)
        self.assertAlmostEqual(residual(SPECIES["n-C4H10(g)"], 510.0, 25.0, "virial").Z, 0.879, delta=5e-4)

    def test_course_slide_peng_robinson_roots(self):
        c = SPECIES["CO2(g)"].critical
        roots = cubic_Z_roots("pr", 283.0 / c.Tc, 49.0 / c.Pc, 0.225)
        self.assertEqual(len(roots), 3)
        for got, want in zip(roots, (0.1099, 0.2845, 0.5501)):
            self.assertAlmostEqual(got, want, delta=2e-4)


class TestThermodynamicConsistency(unittest.TestCase):
    STATES = [("N2(g)", 300.0, 100.0), ("CO2(g)", 350.0, 60.0), ("NH3(g)", 700.0, 200.0),
              ("CH4(g)", 250.0, 40.0), ("H2O(g)", 800.0, 150.0), ("H2(g)", 400.0, 300.0),
              ("CH3OH(g)", 550.0, 50.0), ("n-C4H10(g)", 500.0, 50.0)]

    def test_ideal_gas_limit(self):
        for sid, T, _ in self.STATES:
            for model in MODELS:
                res = residual(SPECIES[sid], T, 1e-6, model)
                self.assertAlmostEqual(res.Z, 1.0, delta=1e-6, msg=f"{sid} {model}")
                self.assertAlmostEqual(res.HR, 0.0, delta=1e-2, msg=f"{sid} {model}")
                self.assertAlmostEqual(res.SR, 0.0, delta=1e-5, msg=f"{sid} {model}")
                self.assertAlmostEqual(res.lnphi, 0.0, delta=1e-6, msg=f"{sid} {model}")

    def test_gibbs_identity(self):
        for sid, T, P in self.STATES:
            for model in MODELS:
                res = residual(SPECIES[sid], T, P, model)
                self.assertAlmostEqual(res.HR - T * res.SR, R * T * res.lnphi, delta=1e-6,
                                       msg=f"{sid} {model}")

    def test_gibbs_helmholtz_and_volume_relations(self):
        # d(ln phi)/dT|P = -H^R/(R T^2)  and  d(ln phi)/dP|T = (Z-1)/P, by finite differences
        for sid, T, P in self.STATES:
            sp = SPECIES[sid]
            for model in MODELS:
                res = residual(sp, T, P, model)
                h = 1e-4 * T
                dT = (residual(sp, T + h, P, model).lnphi - residual(sp, T - h, P, model).lnphi) / (2 * h)
                self.assertAlmostEqual(dT, -res.HR / (R * T * T), delta=2e-5 * abs(dT) + 1e-10,
                                       msg=f"{sid} {model} Gibbs-Helmholtz")
                h = 1e-4 * P
                dP = (residual(sp, T, P + h, model).lnphi - residual(sp, T, P - h, model).lnphi) / (2 * h)
                self.assertAlmostEqual(dP, (res.Z - 1) / P, delta=2e-5 * abs(dP) + 1e-10,
                                       msg=f"{sid} {model} volume relation")

    def test_audit_function(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for model in MODELS:
            checks = audit_residuals(rxn, 700.0, 200.0, model)
            self.assertEqual(len(checks), 9)
            self.assertTrue(all_passed(checks), [c for c in checks if not c["passed"]])

    def test_models_agree_at_low_pressure(self):
        # The second virial coefficient is the common low-pressure limit
        sp = SPECIES["CO2(g)"]
        ref = residual(sp, 400.0, 2.0, "virial")
        for model in ("rk", "srk", "pr"):
            res = residual(sp, 400.0, 2.0, model)
            self.assertAlmostEqual(res.Z, ref.Z, delta=2e-3, msg=model)
            self.assertAlmostEqual(res.HR, ref.HR, delta=12.0, msg=model)

    def test_attractive_forces_lower_the_enthalpy(self):
        # Below the Boyle/inversion region the residual enthalpy is negative
        for sid, T, P in [("CO2(g)", 350.0, 60.0), ("NH3(g)", 700.0, 200.0), ("CH4(g)", 250.0, 40.0)]:
            for model in MODELS:
                self.assertLess(residual(SPECIES[sid], T, P, model).HR, 0.0, f"{sid} {model}")


class TestSpecialCases(unittest.TestCase):
    def test_hydrogen_uses_effective_critical_constants(self):
        res = residual(SPECIES["H2(g)"], 300.0, 100.0, "virial")
        # Experimental second virial coefficient of H2 at 300 K is about +15 cm3/mol:
        # Z > 1 and it warms on throttling (H^R > 0 would need B - T dB/dT > 0)
        self.assertTrue(1.03 < res.Z < 1.08, res.Z)
        self.assertTrue(any(n["kind"] == "quantum_gas" for n in res.notes))

    def test_condensed_phases_have_no_pressure_correction(self):
        for sid in ("H2O(l)", "C(s)", "CaCO3(s)"):
            res = residual(SPECIES[sid], 350.0, 100.0, "pr")
            self.assertEqual((res.Z, res.HR, res.SR, res.lnphi), (1.0, 0.0, 0.0, 0.0))
            self.assertTrue(res.treated_ideal)

    def test_species_without_critical_constants_are_flagged(self):
        res = residual(SPECIES["NO2(g)"], 400.0, 50.0, "pr")
        self.assertTrue(res.treated_ideal)
        self.assertEqual(res.notes[0]["kind"], "no_critical_data")

    def test_condensation_warning(self):
        # Water at 400 K has a vapour pressure of about 2.5 bar: at 50 bar it is a liquid
        for model in MODELS:
            res = residual(SPECIES["H2O(g)"], 400.0, 50.0, model)
            kinds = {n["kind"] for n in res.notes}
            self.assertTrue(kinds & {"condensation", "no_vapour_root"}, model)
            self.assertNotEqual(res.state, "vapour", model)
        res = residual(SPECIES["H2O(g)"], 400.0, 1.0, "pr")
        self.assertEqual(res.state, "vapour")
        self.assertFalse(any(n["kind"] in ("condensation", "no_vapour_root") for n in res.notes))

    def test_a_liquid_root_is_never_passed_off_as_a_gas(self):
        # Water at 523.15 K has a vapour pressure of about 40 bar.
        water = SPECIES["H2O(g)"]
        self.assertEqual(residual(water, 523.15, 10.0, "pr").state, "vapour")
        self.assertEqual(residual(water, 523.15, 50.0, "pr").state, "hypothetical_vapour")
        liquid = residual(water, 523.15, 100.0, "pr")
        self.assertEqual(liquid.state, "liquid_like")
        self.assertLess(liquid.Z, 0.2)
        self.assertEqual(liquid.notes[0]["level"], "error")
        # Above the critical temperature there is no such distinction
        self.assertEqual(residual(water, 700.0, 300.0, "pr").state, "vapour")

        from thermosolver.equilibrium import gibbs_minimize, reaction_equilibrium
        from thermosolver.errors import PhaseError
        rxn = Reaction.parse("CO2 + 3 H2 -> CH3OH(g) + H2O(g)")
        self.assertTrue(reaction_at_pressure(rxn, 523.15, 50.0, "pr")["gas_phase_valid"])
        bad = reaction_at_pressure(rxn, 523.15, 100.0, "pr")
        self.assertFalse(bad["gas_phase_valid"])
        self.assertEqual(bad["no_vapour_species"], ["H2O(g)"])
        with self.assertRaises(PhaseError):
            reaction_equilibrium(rxn, 523.15, 100.0, model="pr")
        with self.assertRaises(PhaseError):
            gibbs_minimize(["CO2", "H2", "CH3OH", "H2O(g)"], {"CO2": 1, "H2": 3}, 523.15, 100.0, "pr")
        # the ideal-gas and virial models still answer, and agree on the trend
        ideal = reaction_equilibrium(rxn, 523.15, 100.0, model="ideal")["conversion"]
        virial = reaction_equilibrium(rxn, 523.15, 100.0, model="virial")["conversion"]
        self.assertTrue(0.25 < ideal < virial < 0.5)
        # the isotherm stops reporting values where the gas phase ends
        sweep = pressure_sweep(rxn, 523.15, [10.0, 50.0, 100.0, 150.0], "pr")
        self.assertEqual(sweep["gas_phase_valid"], [True, True, False, False])
        self.assertEqual(sweep["dH_P"][2:], [None, None])
        self.assertEqual(sweep["first_invalid_P"], 100.0)

    def test_virial_range_warning_at_high_density(self):
        res = residual(SPECIES["CO2(g)"], 320.0, 150.0, "virial")
        self.assertTrue(any(n["kind"] == "virial_range" for n in res.notes))
        res = residual(SPECIES["CO2(g)"], 600.0, 10.0, "virial")
        self.assertFalse(any(n["kind"] == "virial_range" for n in res.notes))

    def test_vapour_pressure_estimate(self):
        self.assertAlmostEqual(psat_estimate(SPECIES["H2O(g)"], 373.15), 1.013, delta=0.12)
        self.assertAlmostEqual(psat_estimate(SPECIES["n-C4H10(g)"], 350.0), 9.4573, delta=0.3)  # SVN example
        self.assertIsNone(psat_estimate(SPECIES["N2(g)"], 300.0))

    def test_bad_inputs(self):
        sp = SPECIES["CO2(g)"]
        for T, P in ((0.0, 10.0), (-5.0, 10.0), (300.0, 0.0), (300.0, -1.0), (float("nan"), 1.0)):
            with self.assertRaises(InputError):
                residual(sp, T, P, "pr")
        with self.assertRaises(InputError):
            residual(sp, 300.0, 10.0, "magic")


class TestPressureEffectOnReaction(unittest.TestCase):
    def test_ideal_gas_enthalpy_does_not_depend_on_pressure(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        for P in (1.0, 50.0, 300.0):
            self.assertAlmostEqual(reaction_at_pressure(rxn, 700.0, P, "ideal")["dH_P"], rxn.dH(700.0), places=6)

    def test_real_gas_reduces_to_standard_state_at_1_bar(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        # A real gas at 1 bar is not exactly the ideal-gas standard state, but
        # the difference is tiny (tens of J/mol against a dH of -105 kJ/mol).
        out = reaction_at_pressure(rxn, 700.0, 1.0, "pr")
        self.assertAlmostEqual(out["dH_P"], rxn.dH(700.0), delta=40.0)
        self.assertAlmostEqual(out["dG_P"], rxn.dG(700.0), delta=25.0)
        tiny = reaction_at_pressure(rxn, 700.0, 1e-4, "pr")
        self.assertAlmostEqual(tiny["dH_P"], rxn.dH(700.0), delta=0.01)

    def test_definitions(self):
        rxn = Reaction.parse("CO + 2 H2 -> CH3OH(g)")
        T, P = 550.0, 80.0
        out = reaction_at_pressure(rxn, T, P, "srk")
        self.assertAlmostEqual(out["dH_P"], out["dH_std"] + out["sum_HR"], places=6)
        self.assertAlmostEqual(out["dS_ig_P"], out["dS_std"] - R * (-2) * math.log(P), places=8)
        self.assertAlmostEqual(out["dG_P"], out["dH_P"] - T * out["dS_P"], places=6)
        # dG(T,P) = dG0 + RT sum nu ln(phi P/P0)
        expected = out["dG_std"] + R * T * (-2 * math.log(P) + out["sum_lnphi"])
        self.assertAlmostEqual(out["dG_P"], expected, delta=1e-6)

    def test_ammonia_heat_of_reaction_grows_with_pressure(self):
        # Well-known experimental trend: more exothermic at high pressure
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        sweep = pressure_sweep(rxn, 723.15, [1.0, 100.0, 200.0, 300.0], "pr")
        dH = sweep["dH_P"]
        self.assertTrue(dH[0] > dH[1] > dH[2] > dH[3])
        self.assertTrue(-8000 < dH[2] - dH[0] < -3000)      # a few kJ at 200 bar

    def test_mole_neutral_reaction_ideal_gas_dG_is_pressure_independent(self):
        rxn = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        a = reaction_at_pressure(rxn, 700.0, 1.0, "ideal")["dG_P"]
        b = reaction_at_pressure(rxn, 700.0, 50.0, "ideal")["dG_P"]
        self.assertAlmostEqual(a, b, places=6)

    def test_gas_solid_reaction(self):
        rxn = Reaction.parse("CaCO3 -> CaO + CO2")
        out = reaction_at_pressure(rxn, 1100.0, 5.0, "pr")
        rows = {r["species"]: r for r in out["species"]}
        self.assertEqual(rows["CaO(s)"]["HR"], 0.0)
        self.assertNotEqual(rows["CO2(g)"]["HR"], 0.0)
        self.assertEqual(out["delta_n_gas"], 1.0)


if __name__ == "__main__":
    unittest.main()
