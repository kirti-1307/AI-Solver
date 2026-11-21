"""Is the transcribed SVN data right?

Three independent checks that do not rely on the solver's own equations:
1. Cp checksum: the heat-capacity tables print Cp/R at 298.15 K next to the
   constants A, B, C, D. Recomputing it catches a mistyped constant.
2. Formula check: the molar mass from the chemical formula must match the
   molar mass printed in SVN Table B.1.
3. Third-law check: dSf = (dHf - dGf)/T0 from Table C.4, plus the CODATA
   entropies of the elements, must reproduce the absolute entropies tabulated
   by CODATA / NIST. This catches a wrong dHf or dGf.
"""

import math
import unittest

from thermosolver import SPECIES, T0, find_species
from thermosolver import data
from thermosolver.formula import molar_mass, parse_formula
from thermosolver.heatcap import cp_over_r

# Absolute entropies at 298.15 K and 1 bar, J/(mol K).
# CODATA Key Values (Cox, Wagman & Medvedev 1989) where available, otherwise
# the NIST Chemistry WebBook gas-phase thermochemistry value.
REFERENCE_S298 = {
    "CO(g)": 197.660, "CO2(g)": 213.785, "H2O(g)": 188.835, "H2O(l)": 69.95,
    "NH3(g)": 192.77, "HCl(g)": 186.902, "SO2(g)": 248.223, "H2S(g)": 205.81,
    "CH4(g)": 186.25, "C2H4(g)": 219.32, "C2H2(g)": 200.93, "C2H6(g)": 229.2,
    "NO(g)": 210.76, "NO2(g)": 240.04, "N2O(g)": 219.96,
}


class TestDatabaseSize(unittest.TestCase):
    def test_assignment_asks_for_at_least_20_to_30_species(self):
        self.assertGreaterEqual(len(SPECIES), 30)

    def test_all_three_phases_present(self):
        phases = {sp.phase for sp in SPECIES.values()}
        self.assertEqual(phases, {"g", "l", "s"})

    def test_suggested_species_available(self):
        # Every one of the 26 species suggested in the assignment
        suggested = ["H2", "O2", "N2", "CO", "CO2", "H2O", "NH3", "CH4", "C2H6", "C2H4",
                     "C2H2", "C3H8", "C3H6", "C4H10", "C4H8", "CH3OH", "C2H5OH", "CH2O",
                     "CH3CHO", "CH3COOH", "H2O2", "NO", "NO2", "N2O", "H2S", "SO2"]
        self.assertEqual(len(suggested), 26)
        for name in suggested:
            sp, _ = find_species(name)
            self.assertIsNotNone(sp.cp, f"{name} must have a heat capacity")


class TestOtherSources(unittest.TestCase):
    """Species that SVN does not cover, taken from the NIST Chemistry WebBook.
    The numbers below were read from the NIST species pages."""

    def test_only_three_species_use_outside_data_and_they_say_so(self):
        outside = {sp.id for sp in SPECIES.values() if not sp.from_svn}
        self.assertEqual(outside, {"H2O2(g)", "CH3COOH(g)", "CH3COOH(l)"})
        for sid in outside:
            self.assertIn("NIST", SPECIES[sid].remark)
            self.assertIn("NIST", SPECIES[sid].cp_source)
        for sp in SPECIES.values():
            if sp.from_svn:
                self.assertIsNone(sp.remark, sp.id)
                self.assertIn("SVN", sp.formation_source)

    def test_hydrogen_peroxide_gas(self):
        sp = SPECIES["H2O2(g)"]
        self.assertEqual(sp.dHf, -136110.0)                       # NIST: -136.11 kJ/mol
        self.assertAlmostEqual(sp.S298_absolute, 232.95, places=9)  # NIST: 232.95 J/(mol K)
        # dGf = dHf - T0 (S - S_H2 - S_O2); handbooks list about -105.6 kJ/mol
        expected = -136110.0 - T0 * (232.95 - 130.680 - 205.152)
        self.assertAlmostEqual(sp.dGf, expected, places=6)
        self.assertAlmostEqual(sp.dGf / 1000.0, -105.6, delta=0.3)
        # the Shomate equation must be reproduced exactly at every temperature
        a, b, c, d, e = data.NIST_GASES_SHOMATE[0][5]
        for T in (298.15, 500.0, 1000.0, 1500.0):
            t = T / 1000.0
            shomate = a + b * t + c * t * t + d * t ** 3 + e / (t * t)
            self.assertAlmostEqual(sp.cp_J(T), shomate, places=9)
        self.assertEqual((sp.cp_Tmin, sp.cp_Tmax), (298.0, 1500.0))
        self.assertIsNone(sp.critical)                             # not in SVN Table B.1

    def test_shomate_integrals_match_the_nist_enthalpy_and_entropy_functions(self):
        # NIST also gives H(T) - H(298.15) and S(T) in Shomate form with constants
        # F, G, H. They are an independent check of the solver's own integrals.
        a, b, c, d, e = data.NIST_GASES_SHOMATE[0][5]
        F, G, H = -149.9098, 257.0604, -136.1064

        def h_nist(T):          # H - H(298.15), kJ/mol
            t = T / 1000.0
            return a * t + b * t ** 2 / 2 + c * t ** 3 / 3 + d * t ** 4 / 4 - e / t + F - H

        def s_nist(T):          # S, J/(mol K)
            t = T / 1000.0
            return a * math.log(t) + b * t + c * t ** 2 / 2 + d * t ** 3 / 3 - e / (2 * t * t) + G

        sp = SPECIES["H2O2(g)"]
        # NIST's rounded F, G, H leave small offsets at 298.15 K (0.014 kJ/mol and
        # 0.01 J/(mol K)); they cancel in a difference between two temperatures.
        self.assertAlmostEqual(h_nist(T0), 0.0, delta=0.02)
        self.assertAlmostEqual(s_nist(T0), 232.95, delta=0.02)
        for T in (400.0, 800.0, 1500.0):
            self.assertAlmostEqual(sp.sensible_dH(T0, T) / 1000.0, h_nist(T) - h_nist(T0), places=9)
            self.assertAlmostEqual(sp.sensible_dS(T0, T), s_nist(T) - s_nist(T0), places=9)

    def test_acetic_acid_gas(self):
        sp = SPECIES["CH3COOH(g)"]
        self.assertEqual(sp.dHf, -432900.0)                        # NIST: -432.9 kJ/mol
        self.assertAlmostEqual(sp.S298_absolute, 282.84, places=9)
        self.assertAlmostEqual(sp.dGf / 1000.0, -374.5, delta=0.5)  # handbook value for the monomer
        # consistent with the SVN liquid: the difference is the 51.6 kJ/mol to the monomer
        self.assertAlmostEqual(sp.dHf - SPECIES["CH3COOH(l)"].dHf, 51600.0, delta=1e-6)
        # the fitted polynomial against every point of the NIST table
        worst = max(abs(sp.cp_J(T) - cp) / cp for T, cp in data.ACETIC_ACID_GAS_CP_TABLE)
        self.assertLess(worst, 0.0025)
        self.assertEqual(len(data.ACETIC_ACID_GAS_CP_TABLE), 14)
        self.assertIsNotNone(sp.critical)                          # acetic acid is in SVN Table B.1

    def test_acetic_acid_liquid(self):
        sp = SPECIES["CH3COOH(l)"]
        self.assertEqual((sp.dHf, sp.dGf), (-484500.0, -389900.0))  # SVN Table C.4, unchanged
        for T in (290.0, 298.15, 320.0):
            self.assertAlmostEqual(sp.cp_J(T), 123.1, places=9)     # NIST, constant
        self.assertEqual((sp.cp_Tmin, sp.cp_Tmax), (290.0, 320.0))


class TestHeatCapacityChecksum(unittest.TestCase):
    def test_cp298_matches_printed_column(self):
        checked = 0
        for sp in SPECIES.values():
            # only the SVN tables print a Cp298/R column to check against
            if sp.cp is None or sp.cp298_tab is None or sp.id in data.CP_CHECKSUM_EXCEPTIONS:
                continue
            computed = cp_over_r(sp.cp, T0)
            # the table prints three decimals; allow rounding of the constants
            self.assertAlmostEqual(
                computed, sp.cp298_tab, delta=0.0025,
                msg=f"{sp.id}: Cp298/R from A,B,C,D = {computed:.4f}, table prints {sp.cp298_tab}")
            checked += 1
        self.assertGreaterEqual(checked, 50)

    def test_the_only_checksum_exception_is_a_misprint_in_the_book(self):
        # 1,3-butadiene: the transcription was checked against the printed
        # table and matches it; the printed Cp298/R (10.720) is what disagrees
        # with the printed A, B, C (9.931). The measured value is about 9.6,
        # so the constants are the trustworthy part.
        self.assertEqual(set(data.CP_CHECKSUM_EXCEPTIONS), {"C4H6(g)"})
        sp = SPECIES["C4H6(g)"]
        self.assertAlmostEqual(cp_over_r(sp.cp, T0), 9.931, delta=0.001)
        self.assertAlmostEqual(cp_over_r(sp.cp, T0), 79.5 / 8.314, delta=0.45)

    def test_heat_capacity_is_positive_over_the_valid_range(self):
        for sp in SPECIES.values():
            if sp.cp is None:
                continue
            for i in range(21):
                T = sp.cp_Tmin + (sp.cp_Tmax - sp.cp_Tmin) * i / 20
                self.assertGreater(sp.cp_R(T), 0.0, f"{sp.id} at {T} K")

    def test_validity_ranges(self):
        for sp in SPECIES.values():
            if sp.cp is None:
                continue
            self.assertLess(sp.cp_Tmin, sp.cp_Tmax, sp.id)
            self.assertTrue(sp.in_cp_range(T0), f"{sp.id} must be valid at 298.15 K")
            if sp.phase == "l" and sp.from_svn:
                self.assertEqual((sp.cp_Tmin, sp.cp_Tmax), (273.15, 373.15))


class TestFormulas(unittest.TestCase):
    def test_parse_formula(self):
        self.assertEqual(parse_formula("Ca(OH)2"), {"Ca": 1, "O": 2, "H": 2})
        self.assertEqual(parse_formula("(CH2)2O"), {"C": 2, "H": 4, "O": 1})
        self.assertEqual(parse_formula("C2H5OH"), {"C": 2, "H": 6, "O": 1})
        self.assertEqual(parse_formula("Fe3O4"), {"Fe": 3, "O": 4})
        self.assertEqual(parse_formula("CH₄"), {"C": 1, "H": 4})

    def test_molar_mass_matches_table_b1(self):
        for sp in SPECIES.values():
            if sp.critical is None:
                continue
            self.assertAlmostEqual(
                molar_mass(sp.formula), sp.critical.molar_mass, delta=0.02,
                msg=f"{sp.id}: formula gives {molar_mass(sp.formula):.3f}, Table B.1 prints {sp.critical.molar_mass}")

    def test_same_compound_same_formula_in_every_phase(self):
        by_name = {}
        for sp in SPECIES.values():
            by_name.setdefault(sp.name, set()).add(tuple(sorted(sp.elements.items())))
        for name, formulas in by_name.items():
            self.assertEqual(len(formulas), 1, name)


class TestFormationData(unittest.TestCase):
    def test_elements_have_zero_formation_properties(self):
        for el, (sid, _) in data.ELEMENT_REFERENCE.items():
            sp = SPECIES[sid]
            self.assertEqual((sp.dHf, sp.dGf), (0.0, 0.0), sid)
            self.assertTrue(sp.is_element)

    def test_third_law_entropy_cross_check(self):
        for sid, s_ref in REFERENCE_S298.items():
            s_calc = SPECIES[sid].S298_absolute
            self.assertAlmostEqual(
                s_calc, s_ref, delta=1.0,
                msg=f"{sid}: (dHf-dGf)/T0 + elements = {s_calc:.2f}, reference {s_ref}")

    def test_entropy_of_every_species_is_physical(self):
        for sp in SPECIES.values():
            s = sp.S298_absolute
            if s is None:        # contains sulfur etc. with no reference loaded
                continue
            self.assertGreater(s, 0.0, sp.id)
            if sp.phase == "g":
                self.assertGreater(s, 100.0, sp.id)

    def test_liquid_is_more_stable_than_vapour_at_298K_for_condensables(self):
        # dGf(l) < dGf(g) for a substance that is liquid at 25 C and 1 bar
        for liq, gas in [("H2O(l)", "H2O(g)"), ("CH3OH(l)", "CH3OH(g)"), ("C2H5OH(l)", "C2H5OH(g)"),
                         ("C6H6(l)", "C6H6(g)"), ("C6H12(l)", "C6H12(g)"), ("C7H8(l)", "C7H8(g)")]:
            self.assertLess(SPECIES[liq].dGf, SPECIES[gas].dGf, liq)
            self.assertLess(SPECIES[liq].dHf, SPECIES[gas].dHf, liq)   # vaporisation is endothermic

    def test_heat_of_vaporisation_of_water_at_25C(self):
        self.assertAlmostEqual(SPECIES["H2O(g)"].dHf - SPECIES["H2O(l)"].dHf, 44012.0, delta=0.5)


class TestCriticalData(unittest.TestCase):
    def test_critical_constants_are_physical(self):
        for sp in SPECIES.values():
            c = sp.critical
            if c is None:
                continue
            self.assertGreater(c.Tc, 0, sp.id)
            self.assertGreater(c.Pc, 0, sp.id)
            self.assertTrue(0.15 < c.Zc < 0.35, sp.id)
            self.assertTrue(-0.3 < c.omega < 0.8, sp.id)
            if c.Tn is not None:
                self.assertLess(c.Tn, c.Tc, sp.id)
            # Zc must be consistent with Pc Vc / (R Tc). The printed table is
            # itself slightly inconsistent for chlorine (0.265 printed, 0.276
            # from Pc, Vc, Tc) and carbon monoxide (0.299 vs 0.296). Zc is
            # shown in the database but never used in a calculation.
            zc = c.Pc * c.Vc / (83.14 * c.Tc)
            self.assertAlmostEqual(zc, c.Zc, delta=0.012, msg=f"{sp.id}: PcVc/RTc = {zc:.4f} vs Zc {c.Zc}")

    def test_acentric_factor_consistent_with_boiling_point(self):
        # omega = -1 - log10(Pr_sat at Tr = 0.7). The Lee/Kesler vapour-pressure
        # correlation is built on that definition, so it must return about
        # 1 atm at the tabulated normal boiling point of non-polar species.
        from thermosolver.realgas import psat_estimate
        for sid in ["CH4(g)", "C2H6(g)", "C3H8(g)", "n-C4H10(g)", "C2H4(g)", "N2(g)", "O2(g)", "CO(g)", "C6H6(g)"]:
            sp = SPECIES[sid]
            psat = psat_estimate(sp, sp.critical.Tn)
            self.assertAlmostEqual(psat, 1.01325, delta=0.06, msg=f"{sid}: Psat(Tn) = {psat:.3f} bar")


class TestLookup(unittest.TestCase):
    def test_every_alias_resolves(self):
        for sid, aliases in data.ALIASES.items():
            self.assertIn(sid, SPECIES)
            for alias in aliases:
                phase = SPECIES[sid].phase
                sp, _ = find_species(f"{alias}({phase})")
                self.assertEqual(sp.id, sid, alias)

    def test_default_phase_is_reported(self):
        sp, note = find_species("H2O")
        self.assertEqual(sp.id, "H2O(g)")
        self.assertIn("assumed", note)

    def test_formula_is_case_sensitive(self):
        from thermosolver import UnknownSpeciesError
        with self.assertRaises(UnknownSpeciesError):
            find_species("Co")
        with self.assertRaises(UnknownSpeciesError):
            find_species("CS2")

    def test_isomers_are_not_guessed(self):
        from thermosolver import InputError
        with self.assertRaises(InputError):
            find_species("C2H4O")
        self.assertEqual(find_species("CH3CHO")[0].name, "Acetaldehyde")
        self.assertEqual(find_species("(CH2)2O")[0].name, "Ethylene oxide")


if __name__ == "__main__":
    unittest.main()
