"""The heat lab: energy balance on a reactor (SVN Chapter 4, heat effects of
industrial reactions) and the bomb calorimeter of the course lab."""

import json
import math
import random
import unittest

from thermosolver import InputError, R, Reaction, SPECIES, T0, api, library
from thermosolver import heatbalance as hb
from thermosolver.heatcap import cp_over_r, simpson

METHANE = "CH4 + 2 O2 -> CO2 + 2 H2O(g)"


def call(endpoint, payload):
    return json.loads(api.call(endpoint, json.dumps(payload)))


def ok(endpoint, payload):
    out = call(endpoint, payload)
    if not out["ok"]:
        raise AssertionError(f"{endpoint} failed: {out['error']}")
    return out["result"]


def flame(equation=METHANE, T_in=T0, **settings):
    return hb.solve(hb.build_case(Reaction.parse(equation), **settings), T_in, "adiabatic")


class TestTextbookExamples(unittest.TestCase):
    def test_flame_temperature_of_methane_with_20_percent_excess_air(self):
        # SVN Ch. 4: methane and air enter at 25 C, 20 % excess air, complete combustion
        case = hb.build_case(Reaction.parse(METHANE), excess=0.2, air=True)
        self.assertEqual(case["key"], "CH4(g)")
        self.assertAlmostEqual(case["feed"]["O2(g)"], 2.4)
        self.assertAlmostEqual(case["feed"]["N2(g)"], 2.4 * 79 / 21)
        self.assertAlmostEqual(case["outlet"]["O2(g)"], 0.4)
        self.assertAlmostEqual(case["outlet"]["CO2(g)"], 1.0)
        self.assertAlmostEqual(case["outlet"]["H2O(g)"], 2.0)
        self.assertNotIn("CH4(g)", hb.Stream(case["outlet"]).moles)

        res = hb.solve(case, T0)
        self.assertAlmostEqual(res["T_out"], 2066.0, delta=1.0)
        self.assertAlmostEqual(res["path"]["dH_298"], -802625.0, delta=1e-6)
        self.assertEqual(res["path"]["dH_R"], 0.0)                 # the feed is already at 298.15 K
        self.assertAlmostEqual(res["Q"], 0.0, delta=1e-9)
        # the relation the book iterates on: T = T0 - dH298 / <Cp>_H
        self.assertAlmostEqual(T0 - res["path"]["dH_298"] / res["mean_cp_products"], res["T_out"], places=6)
        self.assertTrue(all(c["passed"] for c in res["audit"]))

    def test_heat_requirement_of_a_steam_reformer(self):
        # SVN Ch. 4: 2 mol steam per mol CH4 at 600 K, products at 1300 K with 17.4 mol-% CO
        smr = Reaction.parse("CH4 + H2O(g) -> CO + 3 H2")
        wgs = Reaction.parse("CO + H2O(g) -> CO2 + H2")
        case = hb.build_case(smr, excess_species="H2O(g)", excess=1.0, side=[(wgs, 0.13)])
        out = case["outlet"]
        for sid, n in {"CO(g)": 0.87, "H2(g)": 3.13, "CO2(g)": 0.13, "H2O(g)": 0.87}.items():
            self.assertAlmostEqual(out[sid], n, places=12)
        self.assertAlmostEqual(out["CO(g)"] / sum(out.values()), 0.174, places=12)
        res = hb.solve(case, 600.0, "duty", T_out=1300.0)
        self.assertAlmostEqual(res["path"]["dH_R"], -34390.0, delta=5.0)
        self.assertAlmostEqual(res["path"]["dH_298"], 200460.0, delta=2.0)
        self.assertAlmostEqual(res["path"]["dH_P"], 161940.0, delta=5.0)
        self.assertAlmostEqual(res["Q"], 328010.0, delta=5.0)
        self.assertTrue(all(c["passed"] for c in res["audit"]))


class TestEnergyBalance(unittest.TestCase):
    def test_every_library_reaction_closes_and_inverts(self):
        # Heat duty for a small temperature step, then the adiabatic solver with
        # that duty must find the same outlet temperature again.
        for row in library.REACTIONS:
            rxn = Reaction.parse(row[2])
            case = hb.build_case(rxn, conversion=0.5)
            duty = hb.solve(case, 320.0, "duty", T_out=360.0)
            self.assertTrue(all(c["passed"] for c in duty["audit"]), row[0])
            back = hb.solve(case, 320.0, "adiabatic", Q=duty["Q"])
            self.assertAlmostEqual(back["T_out"], 360.0, places=6, msg=row[0])
            self.assertTrue(all(c["passed"] for c in back["audit"]), row[0])

    def test_isothermal_duty_is_the_heat_of_reaction_at_that_temperature(self):
        # Stoichiometric feed, complete conversion, T_in = T_out = T: Q = dH(T)
        for eq, T in (("CO + 2 H2 -> CH3OH(g)", 1073.15), ("N2 + 3 H2 -> 2 NH3", 723.15),
                      ("CH4 + H2O(g) -> CO + 3 H2", 1000.0), (METHANE, 1500.0)):
            rxn = Reaction.parse(eq)
            case = hb.build_case(rxn)
            res = hb.solve(case, T, "duty", T_out=T)
            nu_key = -rxn.stoich[case["key"]]
            self.assertAlmostEqual(res["Q"], rxn.dH(T) / nu_key, delta=1e-6 * abs(rxn.dH(T)), msg=eq)

    def test_no_reaction_means_no_temperature_change(self):
        res = flame(T_in=450.0, conversion=0.0, excess=0.5, air=True)
        self.assertAlmostEqual(res["T_out"], 450.0, places=8)
        self.assertEqual(res["path"]["dH_298"], 0.0)

    def test_excess_air_cools_the_flame_and_preheat_heats_it(self):
        temps = [flame(excess=e, air=True)["T_out"] for e in (0.0, 0.2, 0.5, 1.0, 2.0, 4.0)]
        self.assertTrue(all(b < a for a, b in zip(temps, temps[1:])), temps)
        self.assertGreater(flame(T_in=600.0, excess=0.2, air=True)["T_out"], flame(excess=0.2, air=True)["T_out"])

    def test_oxygen_enrichment_gives_a_hotter_flame(self):
        self.assertGreater(flame(excess=0.2)["T_out"], flame(excess=0.2, air=True)["T_out"] + 1000.0)

    def test_inert_only_changes_the_sensible_heat(self):
        dry = flame(excess=0.2, air=True)
        wet = flame(excess=0.2, air=True, extra={"H2O(g)": 2.0})
        self.assertLess(wet["T_out"], dry["T_out"])
        self.assertAlmostEqual(wet["path"]["dH_298"], dry["path"]["dH_298"], places=6)
        self.assertAlmostEqual(wet["outlet"]["H2O(g)"], 4.0)

    def test_endothermic_reaction_cools_an_adiabatic_reactor(self):
        case = hb.build_case(Reaction.parse("CH4 + H2O(g) -> CO + 3 H2"), conversion=0.3,
                             excess_species="H2O(g)", excess=2.0)
        res = hb.solve(case, 1100.0)
        self.assertLess(res["T_out"], 1100.0)
        self.assertGreater(res["path"]["dH_298"], 0.0)

    def test_removing_heat_lowers_the_outlet_temperature(self):
        case = hb.build_case(Reaction.parse(METHANE), excess=0.2, air=True)
        adiabatic = hb.solve(case, T0)
        cooled = hb.solve(case, T0, Q=-200000.0)
        self.assertLess(cooled["T_out"], adiabatic["T_out"])
        self.assertAlmostEqual(cooled["H_out"] - cooled["H_in"], -200000.0, delta=1e-4)

    def test_partial_conversion_and_other_key(self):
        rxn = Reaction.parse("N2 + 3 H2 -> 2 NH3")
        case = hb.build_case(rxn, key="H2(g)", conversion=0.3, excess_species="N2(g)", excess=0.5)
        self.assertAlmostEqual(case["feed"]["H2(g)"], 1.0)
        self.assertAlmostEqual(case["feed"]["N2(g)"], 0.5)
        self.assertAlmostEqual(case["outlet"]["H2(g)"], 0.7)
        self.assertAlmostEqual(case["outlet"]["NH3(g)"], 0.2)
        self.assertAlmostEqual(case["outlet"]["N2(g)"], 0.4)

    def test_infeasible_settings_are_rejected(self):
        rxn = Reaction.parse(METHANE)
        with self.assertRaises(InputError) as ctx:
            hb.build_case(rxn, conversion=1.0, excess=-0.5)        # half the oxygen, full conversion
        self.assertIn("O2(g)", ctx.exception.message)
        hb.build_case(rxn, conversion=0.5, excess=-0.5)            # exactly enough: allowed
        for bad in (dict(key="CO2(g)"), dict(excess_species="CH4(g)"), dict(excess_species="CO2(g)"),
                    dict(conversion=1.2), dict(conversion=-0.1), dict(excess=-1.0), dict(excess=1e6),
                    dict(extra={"N2(g)": -1.0}), dict(side=[(Reaction.parse("CO + H2O(g) -> CO2 + H2"), -0.1)])):
            with self.assertRaises(InputError, msg=str(bad)):
                hb.build_case(rxn, **bad)
        with self.assertRaises(InputError):
            hb.build_case(Reaction.parse("C2H6 -> C2H4 + H2"), excess=0.2)       # nothing to put in excess
        with self.assertRaises(InputError):
            hb.solve(hb.build_case(rxn), T0, "duty")                            # no outlet temperature
        with self.assertRaises(InputError):
            hb.solve(hb.build_case(rxn), T0, "sideways", T_out=500.0)

    def test_flames_hotter_than_the_correlations_are_refused_with_advice(self):
        rxn = Reaction.parse("C2H2 + 5/2 O2 -> 2 CO2 + H2O(g)")
        with self.assertRaises(InputError) as ctx:
            hb.solve(hb.build_case(rxn), T0)
        self.assertIn("excess air", ctx.exception.message)
        self.assertLess(hb.solve(hb.build_case(rxn, excess=0.2, air=True), T0)["T_out"], 3000.0)

    def test_search_stays_where_the_heat_capacity_is_positive(self):
        # The Cp polynomial of methane turns negative above about 4400 K
        stream = hb.Stream({"CH4(g)": 1.0})
        lo, hi = stream.window()
        self.assertLess(hi, 4500.0)
        self.assertGreater(stream.cp(hi), 0.0)
        self.assertLessEqual(lo, T0)
        with self.assertRaises(InputError):
            hb.outlet_temperature(stream, stream, T0, Q=1e9)

    def test_extrapolation_is_reported(self):
        res = flame(excess=0.2, air=True)                          # 2066 K, correlations end at 2000 K
        flagged = {w["species"] for w in res["warnings"]}
        self.assertEqual(flagged, {"O2(g)", "N2(g)", "CO2(g)", "H2O(g)"})
        self.assertEqual(flame(excess=2.0, air=True)["warnings"], [])
        liquid = hb.solve(hb.build_case(Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)"), excess=3.0, air=True), T0)
        self.assertTrue(any("no phase change" in w["message"] for w in liquid["warnings"]))

    def test_goal_seek_finds_the_excess_for_a_target_temperature(self):
        rxn = Reaction.parse(METHANE)
        goal = hb.excess_for_outlet_temperature(rxn, 1500.0, T0, air=True)
        self.assertIsNone(goal["reason"])
        self.assertAlmostEqual(flame(excess=goal["excess"], air=True)["T_out"], 1500.0, delta=1e-4)
        self.assertIsNone(hb.excess_for_outlet_temperature(rxn, 2500.0, T0, air=True)["excess"])   # already cooler
        self.assertIsNone(hb.excess_for_outlet_temperature(rxn, 250.0, T0, air=True)["excess"])    # below the feed

    def test_work_potential_of_the_hot_products(self):
        case = hb.build_case(Reaction.parse(METHANE), excess=1.0, air=True)
        res = hb.solve(case, T0)
        work = hb.work_potential(case, res["T_out"])
        self.assertLess(work["W_ideal"], 0.0)                      # the stream can deliver work
        self.assertLess(abs(work["W_ideal"]), abs(work["dH"]))
        # heat is given up over a falling temperature, so less than a Carnot engine at T_out
        self.assertLess(work["fraction"], work["carnot_at_T_out"])
        self.assertGreater(work["fraction"], 0.0)
        # independent route: integral of (1 - T0/T) * Cp dT
        outlet = hb.Stream(case["outlet"])
        numeric = R * simpson(lambda t: (1.0 - T0 / t) * cp_over_r(outlet.coeffs, t), T0, res["T_out"])
        self.assertAlmostEqual(-work["W_ideal"], numeric, delta=1e-6 * numeric)
        self.assertIsNone(hb.work_potential(case, T0))


class TestFuelFacts(unittest.TestCase):
    def test_methane(self):
        facts = hb.fuel_facts(Reaction.parse(METHANE))
        self.assertAlmostEqual(facts["LHV"], 802625.0, delta=1e-6)
        self.assertAlmostEqual(facts["HHV"], 890649.0, delta=1e-6)
        self.assertAlmostEqual(facts["o2_stoich"], 2.0)
        self.assertAlmostEqual(facts["air_stoich"], 2.0 / 0.21)
        self.assertAlmostEqual(facts["dn_gas_bomb"], -2.0)
        self.assertAlmostEqual(facts["dU_bomb"], -890649.0 + 2.0 * R * T0, delta=1e-6)
        self.assertAlmostEqual(facts["co2_per_MJ"], 44.01 / 0.802625, delta=0.05)
        # the same answer whichever phase of water the user typed
        typed_liquid = hb.fuel_facts(Reaction.parse("CH4 + 2 O2 -> CO2 + 2 H2O(l)"))
        self.assertAlmostEqual(typed_liquid["LHV"], facts["LHV"], delta=1e-6)
        self.assertAlmostEqual(typed_liquid["HHV"], facts["HHV"], delta=1e-6)

    def test_difference_of_the_heating_values_is_the_latent_heat_of_the_water(self):
        vap = Reaction.parse("H2O(l) -> H2O(g)").dH0
        for eq in (METHANE, "H2 + 1/2 O2 -> H2O(g)", "C3H8 + 5 O2 -> 3 CO2 + 4 H2O(g)", "CO + 1/2 O2 -> CO2"):
            facts = hb.fuel_facts(Reaction.parse(eq))
            self.assertAlmostEqual(facts["HHV"] - facts["LHV"], facts["water_formed"] * vap, delta=1e-6, msg=eq)

    def test_only_complete_combustion_counts(self):
        self.assertIsNone(hb.fuel_facts(Reaction.parse("N2 + 3 H2 -> 2 NH3")))
        self.assertIsNone(hb.fuel_facts(Reaction.parse("CH4 + 1/2 O2 -> CO + 2 H2")))      # partial oxidation
        self.assertIsNone(hb.fuel_facts(Reaction.parse("4 NH3 + 5 O2 -> 4 NO + 6 H2O(g)")))
        self.assertIsNotNone(hb.fuel_facts(Reaction.parse("2 H2S + 3 O2 -> 2 SO2 + 2 H2O(g)")))


class TestBombCalorimeter(unittest.TestCase):
    CAL = hb.JOULE_PER_CAL

    def test_calibration_of_the_course_handout(self):
        h = library.CALORIMETER_HANDOUT
        C = hb.calorimeter_constant(h["mass_g"], h["dT"], h["calorific_value_cal_per_g"] * self.CAL,
                                    h["corrections_cal"] * self.CAL)
        self.assertAlmostEqual(C / self.CAL, h["C_cal_cal_per_K"], delta=0.01)
        with self.assertRaises(InputError):
            hb.calorimeter_constant(1.0, 0.0, 26000.0)

    def test_handout_relation_between_dU_and_dH(self):
        # benzoic acid in the handout: dU = -3228.7 kJ/mol, dn(gas) = -0.5, T = 303.15 K -> dH = -3230.0
        self.assertAlmostEqual(-3228.7 + (-0.5) * R * 303.15 / 1000.0, -3230.0, delta=0.05)

    def test_combustion_reaction_is_built_from_the_formula(self):
        self.assertEqual(hb.combustion_reaction("C2H5OH(l)").equation,
                         "C2H5OH(l) + 3 O2(g) → 2 CO2(g) + 3 H2O(l)")
        self.assertEqual(hb.combustion_reaction("NH3(g)", "g").equation,
                         "NH3(g) + 3/4 O2(g) → 3/2 H2O(g) + 1/2 N2(g)")
        self.assertEqual(hb.combustion_reaction("H2S(g)").equation,
                         "H2S(g) + 3/2 O2(g) → H2O(l) + SO2(g)")
        self.assertEqual(hb.combustion_reaction("C(s)").equation, "C(s) + O2(g) → CO2(g)")
        for sid in ("O2(g)", "CO2(g)", "H2O(g)", "N2(g)", "SO3(g)", "H2O2(g)", "CaCO3(s)", "HCl(g)", "Fe(s)"):
            with self.assertRaises(InputError, msg=sid):
                hb.combustion_reaction(sid)

    def test_heating_values_of_ethanol(self):
        v = hb.heating_values("C2H5OH(l)")
        typed = Reaction.parse("C2H5OH(l) + 3 O2 -> 2 CO2 + 3 H2O(l)")
        self.assertAlmostEqual(v["dH_c"], typed.dH0, delta=1e-6)
        self.assertAlmostEqual(v["dn_gas"], -1.0)                  # 2 CO2 formed, 3 O2 consumed
        self.assertAlmostEqual(v["dU_c"], typed.dH0 + R * T0, delta=1e-6)
        self.assertAlmostEqual(v["calorific_value"], -v["dU_c"] / v["molar_mass"])
        self.assertGreater(v["HHV"], v["LHV"])
        # the handout's shortcut LHV = HHV - m_w * h_fg agrees with the rigorous value within 0.5 %
        self.assertAlmostEqual(v["LHV_shortcut"], v["LHV"], delta=0.005 * v["LHV"])

    def test_every_combustible_species_releases_heat(self):
        fuels = hb.combustible_species()
        self.assertGreaterEqual(len(fuels), 25)
        for sid in fuels:
            v = hb.heating_values(sid)
            self.assertGreater(v["calorific_value"], 0.0, sid)
            self.assertGreaterEqual(v["HHV"], v["LHV"] - 1e-9, sid)

    def test_predicted_rise_and_identification_are_consistent(self):
        C = 3059.33 * self.CAL
        run = hb.calorimeter_run("C2H5OH(l)", 1.0, C, corrections=41.0 * self.CAL)
        self.assertAlmostEqual(run["dT"], (run["calorific_value"] + 41.0 * self.CAL) / C, places=12)
        self.assertTrue(1.5 < run["dT"] < 3.5, run["dT"])
        found = hb.identify_fuel(1.0, run["dT"], C, corrections=41.0 * self.CAL)
        self.assertEqual(found["candidates"][0]["fuel"], "C2H5OH(l)")
        self.assertTrue(all(SPECIES[c["fuel"]].phase != "g" for c in found["candidates"]))    # a crucible sample
        wider = hb.identify_fuel(1.0, run["dT"], C, corrections=41.0 * self.CAL, include_gases=True)
        self.assertGreater(wider["compared"], found["compared"])
        self.assertEqual(wider["candidates"][0]["fuel"], "C2H5OH(l)")
        self.assertAlmostEqual(found["candidates"][0]["difference"], 0.0, places=10)
        self.assertAlmostEqual(found["measured_calorific_value"], run["calorific_value"], delta=1e-6)
        for bad in (dict(mass=0.0, dT=2.0, C_cal=C), dict(mass=1.0, dT=2.0, C_cal=C, corrections=1e9)):
            with self.assertRaises(InputError):
                hb.identify_fuel(**bad)


class TestApi(unittest.TestCase):
    def test_heat_balance_point_sweep_and_goal(self):
        res = ok("heat_balance", {"equation": METHANE, "excess": 0.2, "air": True, "target_T": 1500})
        self.assertAlmostEqual(res["point"]["T_out"], 2066.0, delta=1.0)
        self.assertEqual(res["key"], "CH4(g)")
        self.assertEqual(res["excess_species"], "O2(g)")
        self.assertTrue(res["has_o2"])
        self.assertEqual(res["sweep"]["variable"], "excess")
        self.assertEqual(len(res["sweep"]["T_out"]), 41)
        self.assertTrue(all(b < a for a, b in zip(res["sweep"]["T_out"], res["sweep"]["T_out"][1:])))
        self.assertAlmostEqual(res["target"]["excess"], 0.9725, delta=0.001)
        self.assertAlmostEqual(res["fuel"]["LHV"], 802625.0, delta=1e-6)
        self.assertEqual(len(res["curves"]["T"]), 61)
        self.assertLess(res["work"]["W_ideal"], 0.0)

    def test_heat_balance_modes_and_sweeps(self):
        base = {"equation": "CH4 + H2O(g) -> CO + 3 H2", "excess_species": "H2O(g)", "excess": 1.0,
                "side": [{"equation": "CO + H2O(g) -> CO2 + H2", "extent": 0.13}], "T_in": 600}
        duty = ok("heat_balance", dict(base, mode="duty", T_out=1300))
        self.assertAlmostEqual(duty["point"]["Q"], 328010.0, delta=5.0)
        self.assertEqual(duty["sweep"]["variable"], "T_out")
        self.assertIsNone(duty["fuel"])
        for variable in ("excess", "T_in", "conversion", "T_out", "none"):
            res = ok("heat_balance", dict(base, mode="duty", T_out=1300, sweep=variable, n_points=5))
            if variable == "none":
                self.assertIsNone(res["sweep"])
            else:
                self.assertEqual(len(res["sweep"]["Q"]), 5)
        single = ok("heat_balance", {"equation": "C2H6 -> C2H4 + H2", "T_in": 1000, "conversion": 0.2, "excess": 3})
        self.assertIsNone(single["excess_species"])                # the excess is ignored, not an error
        self.assertEqual(single["sweep"]["variable"], "T_in")
        self.assertTrue(700.0 < single["point"]["T_out"] < 850.0, single["point"]["T_out"])
        # Half of the ethane cannot crack adiabatically from 1000 K: the reaction would need more
        # heat than the feed carries, and the solver says so instead of extrapolating far below 298 K.
        out = call("heat_balance", {"equation": "C2H6 -> C2H4 + H2", "T_in": 1000, "conversion": 0.5})
        self.assertEqual(out["error"]["kind"], "input_error")
        self.assertIn("preheat", out["error"]["message"])

    def test_heat_balance_errors_are_input_errors(self):
        for payload in ({"equation": METHANE, "mode": "x"},
                        {"equation": METHANE, "sweep": "T_out"},                  # only in heat-duty mode
                        {"equation": METHANE, "sweep": "zzz"},
                        {"equation": METHANE, "key": "CO2"},
                        {"equation": METHANE, "excess": -0.5},
                        {"equation": METHANE, "air": "yes"},
                        {"equation": METHANE, "extra": [1]},
                        {"equation": METHANE, "side": [{"equation": "CO + O2 -> CO2", "extent": 1}]},
                        {"equation": "C2H6 -> C2H4 + H2", "sweep": "excess"},
                        {"equation": "C2H2 + 5/2 O2 -> 2 CO2 + H2O(g)"},
                        {"equation": "CH4 + O2 -> CO2 + H2O"}):
            out = call("heat_balance", payload)
            self.assertFalse(out["ok"], payload)
            self.assertIn(out["error"]["kind"], ("input_error", "unbalanced_reaction"), out["error"]["message"])
        out = call("heat_balance", {"equation": METHANE, "side": [{"equation": "CO + O2 -> CO2", "extent": 1}]})
        self.assertIn("Side reaction 1", out["error"]["message"])

    def test_calorimeter_endpoint(self):
        cal = hb.JOULE_PER_CAL
        h = library.CALORIMETER_HANDOUT
        calibration = {"mass": h["mass_g"], "dT": h["dT"], "calorific_value": h["calorific_value_cal_per_g"] * cal,
                       "corrections": h["corrections_cal"] * cal}
        res = ok("calorimeter", {"mode": "predict", "fuel": "C2H5OH(l)", "mass": 1.0, "calibration": calibration})
        self.assertAlmostEqual(res["C_cal_cal"], 3059.33, delta=0.01)
        self.assertEqual(res["run"]["fuel"], "C2H5OH(l)")
        back = ok("calorimeter", {"mode": "identify", "mass": 1.0, "dT": res["run"]["dT"], "C_cal": res["C_cal"]})
        self.assertEqual(back["identify"]["candidates"][0]["fuel"], "C2H5OH(l)")
        for payload in ({"mode": "predict", "fuel": "C2H5OH(l)", "mass": 1.0},              # no constant
                        {"mode": "predict", "fuel": "CO2", "mass": 1.0, "C_cal": 12800},
                        {"mode": "predict", "fuel": "C2H5OH(l)", "C_cal": 12800},           # no mass
                        {"mode": "identify", "mass": 1.0, "C_cal": 12800},                  # no rise
                        {"mode": "spin", "mass": 1.0, "C_cal": 12800},
                        {"mode": "predict", "fuel": "C2H5OH(l)", "mass": 1.0, "calibration": {"mass": 1}}):
            out = call("calorimeter", payload)
            self.assertFalse(out["ok"], payload)
            self.assertEqual(out["error"]["kind"], "input_error", out["error"]["message"])

    def test_library_lists_the_fuels(self):
        lib = ok("library", {})
        ids = {f["id"] for f in lib["fuels"]}
        self.assertTrue({"CH4(g)", "H2(g)", "C2H5OH(l)", "C(s)", "CO(g)", "NH3(g)"} <= ids)
        self.assertFalse({"O2(g)", "CO2(g)", "H2O(l)", "CaCO3(s)"} & ids)
        self.assertEqual(lib["calorimeter_handout"]["C_cal_cal_per_K"], 3059.33)

    def test_random_settings_never_break_the_balance(self):
        rng = random.Random(4)
        rows = [r for r in library.REACTIONS]
        solved = 0
        for _ in range(400):
            row = rng.choice(rows)
            payload = {"equation": row[2], "T_in": rng.uniform(250, 1500), "conversion": rng.random(),
                       "excess": rng.choice([0, 0, 0.2, 1.0, 5.0]), "air": rng.random() < 0.5,
                       "mode": rng.choice(["adiabatic", "duty"]), "T_out": rng.uniform(250, 2500),
                       "sweep": "none"}
            out = call("heat_balance", payload)
            if out["ok"]:
                solved += 1
                point = out["result"]["point"]
                self.assertTrue(all(c["passed"] for c in point["audit"]), f"{payload}")
                self.assertTrue(math.isfinite(point["T_out"]) and math.isfinite(point["Q"]))
            else:
                self.assertEqual(out["error"]["kind"], "input_error", f"{payload}: {out['error']['message']}")
        self.assertGreater(solved, 300)


if __name__ == "__main__":
    unittest.main()
