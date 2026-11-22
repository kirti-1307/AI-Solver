"""The textbook data against an outside source.

The SVN tables were typed in by hand, and the heat-capacity checksum (Cp at
298.15 K) only tests the constants at one temperature. Here the formation
data and the heat capacities over the whole SVN range are compared with rows
of the NIST-JANAF tables (tests/janaf_reference.py). The two sources are not
identical, so the tolerances are those of honest source differences; a
mistyped constant would be far outside them.
"""

import unittest

from thermosolver.constants import R, T0
from thermosolver.heatcap import cp_over_r, icph
from thermosolver.species import SPECIES

from tests import janaf_reference as janaf


class TestFormationData(unittest.TestCase):
    def test_enthalpy_and_gibbs_energy_of_formation(self):
        for sid, (dH, dG) in janaf.FORMATION.items():
            sp = SPECIES[sid]
            if sid in janaf.FORMATION_NOTES:
                continue
            self.assertAlmostEqual(sp.dHf / 1000.0, dH, delta=1.0, msg=f"{sid} dHf")
            self.assertAlmostEqual(sp.dGf / 1000.0, dG, delta=1.0, msg=f"{sid} dGf")
        self.assertGreaterEqual(len(janaf.FORMATION) - len(janaf.FORMATION_NOTES), 19)

    def test_the_known_differences_are_what_the_notes_say(self):
        self.assertEqual(set(janaf.FORMATION_NOTES), {"CH2O(g)", "Fe2O3(s)", "Fe3O4(s)"})
        expected = {"CH2O(g)": 7.3, "Fe2O3(s)": 1.3, "Fe3O4(s)": 2.5}       # SVN minus JANAF, kJ/mol
        for sid, gap in expected.items():
            sp = SPECIES[sid]
            dH, dG = janaf.FORMATION[sid]
            self.assertAlmostEqual(sp.dHf / 1000.0 - dH, gap, delta=0.1, msg=sid)
            # the Gibbs energy carries the same shift, so the entropy of formation agrees
            self.assertAlmostEqual((sp.dHf / 1000.0 - dH) - (sp.dGf / 1000.0 - dG), 0.0, delta=0.5, msg=sid)

    def test_ammonia_gibbs_energy_supports_the_eighth_edition_value(self):
        # -16,400 J/mol (8th edition) against -16,450 (6th): JANAF has -16,367
        self.assertEqual(SPECIES["NH3(g)"].dGf, -16400.0)
        self.assertLess(abs(-16.400 - janaf.FORMATION["NH3(g)"][1]), abs(-16.450 - janaf.FORMATION["NH3(g)"][1]))


class TestHeatCapacitiesOverTheWholeRange(unittest.TestCase):
    def rows(self):
        for sid, (table, rows) in janaf.ROWS.items():
            sp = SPECIES[sid]
            for T, cp, S, H in rows:
                if sp.cp_main_Tmin < T <= sp.cp_main_Tmax:
                    yield sp, T, cp, H

    def test_heat_capacity_of_the_svn_formula(self):
        checked = 0
        for sp, T, cp, _ in self.rows():
            ratio = R * cp_over_r(sp.cp, T) / cp
            limit = 0.10 if T >= 2000 or sp.phase == "s" else 0.05
            self.assertAlmostEqual(ratio, 1.0, delta=limit, msg=f"{sp.id} at {T} K: {100 * (ratio - 1):+.1f} %")
            checked += 1
        self.assertGreaterEqual(checked, 70)

    def test_enthalpy_increment_of_the_svn_formula(self):
        # H(T) - H(298.15 K): what a heat of reaction at T is built from
        for sp, T, _, H in self.rows():
            ratio = R * icph(T0, T, sp.cp) / (H * 1000.0)
            limit = 0.065 if sp.phase == "s" else 0.035
            self.assertAlmostEqual(ratio, 1.0, delta=limit, msg=f"{sp.id} at {T} K: {100 * (ratio - 1):+.1f} %")

    def test_svn_was_fitted_to_reproduce_enthalpies(self):
        # For the gases of a flame the SVN formula gives the enthalpy at 2000 K
        # within 0.3 % of JANAF, although its heat capacity there is 2 to 4 % off.
        # A formula with a mistyped constant could not do that.
        for sid in ("N2(g)", "O2(g)", "CO2(g)", "H2O(g)", "SO2(g)", "SO3(g)"):
            sp = SPECIES[sid]
            rows = {T: (cp, H) for T, cp, S, H in janaf.ROWS[sid][1]}
            cp, H = rows[2000]
            self.assertAlmostEqual(R * icph(T0, 2000.0, sp.cp) / (H * 1000.0), 1.0, delta=0.003, msg=sid)
            self.assertGreater(R * cp_over_r(sp.cp, 2000.0) / cp, 1.02, msg=sid)

    def test_a_planted_typo_would_be_caught(self):
        # methane with B = 9.801e-3 instead of 9.081e-3 (two digits swapped)
        sp = SPECIES["CH4(g)"]
        wrong = (sp.cp[0], 9.801e-3, sp.cp[2], sp.cp[3], sp.cp[4])
        rows = {T: (cp, H) for T, cp, S, H in janaf.ROWS["CH4(g)"][1]}
        cp, H = rows[1000]
        self.assertGreater(abs(R * cp_over_r(wrong, 1000.0) / cp - 1.0), 0.05)
        self.assertGreater(abs(R * icph(T0, 1000.0, wrong) / (H * 1000.0) - 1.0), 0.035)


if __name__ == "__main__":
    unittest.main()
