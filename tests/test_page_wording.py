"""The words on the page.

Every technical term a visitor can read has to be one the course has taught
(slides, tutorials, problem sets, lab handout), one the assignment brief uses,
or plain school-level wording. Terms outside that were reworded in plain words
or taken off the page; the solver still calculates everything it did before.

These tests keep it that way. They look at the two places a visible text can
come from: the page files (index.html and web/*.js) and the texts the solver
sends to the page (names of checks, notes, warnings, example names ...).
"""

import json
import os
import re
import unittest
import zipfile

from thermosolver import api, library

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Not taught, so not shown. Lower case; the texts are compared in lower case.
FORBIDDEN = ("dew point", "heat duty", "kirchhoff", "gibbs-helmholtz", "simpson", "lagrange", "boudouard",
             "carbon activity", "shomate", "pitzer", "dissociat", "ideal work", "fugacity")

# Full names of the NIST sources. They belong where the data are documented
# (tab 6, the source columns of tab 7, the footer); everywhere else the page
# says "NIST data".
SOURCE_NAMES = ("nist-janaf", "webbook")

# Blocks of index.html that are not covered here: the <head> (not shown on the
# page), the header, the start page and the footer. Remove an entry to bring
# that block under the test.
BLOCKS_NOT_CHECKED = (
    r"<head>.*?</head>",
)

METHANOL = {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523}
AMMONIA = {"equation": "N2 + 3 H2 -> 2 NH3", "T": 723.15, "P": 200, "model": "pr"}


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def tab_sections(html):
    """index.html without the blocks listed in BLOCKS_NOT_CHECKED."""
    for pattern in BLOCKS_NOT_CHECKED:
        html, found = re.subn(pattern, "", html, count=1, flags=re.DOTALL)
        assert found == 1, pattern
    return html


def scripts():
    return sorted(f for f in os.listdir(os.path.join(ROOT, "web")) if f.endswith(".js"))


def ok(endpoint, payload):
    out = json.loads(api.call(endpoint, json.dumps(payload)))
    assert out["ok"], out
    return out["result"]


def shown(obj, internal=("kind",)):
    """A result without the values of its internal names. The page compares
    them (a note of kind "dissociation" keeps that name) but never prints them."""
    if isinstance(obj, dict):
        return {k: shown(v, internal) for k, v in obj.items() if k not in internal}
    if isinstance(obj, list):
        return [shown(v, internal) for v in obj]
    return obj


def text_of(result, internal=("kind",)):
    return json.dumps(shown(result, internal), ensure_ascii=False).lower()


def network_payload(net_id, model):
    net = next(n for n in library.NETWORKS if n["id"] == net_id)
    lo, hi = net["T_range"]
    # the temperature the example opens at (the page uses it too), else the middle of its range
    T = net.get("T", 0.5 * (lo + hi))
    return {"species": net["species"], "feed": net["feed"], "T": T, "P": net["P"], "model": model,
            "sweep": "T", "T_min": lo, "T_max": hi, "n_points": 9, "switches": True, "candidates": []}


def heat_payload(example_id):
    ex = next(e for e in library.HEAT_EXAMPLES if e["id"] == example_id)
    body = {k: ex[k] for k in ("equation", "mode", "T_in", "conversion", "excess_species", "excess", "air", "side")}
    body["condense"] = ex.get("condense", True)
    if "T_out" in ex:
        body["T_out"] = ex["T_out"]
    return body


class TestPageFiles(unittest.TestCase):
    def test_the_tab_sections_are_what_is_checked(self):
        html = tab_sections(read("index.html"))
        for tab in ("home", "reaction", "pressure", "combine", "network", "heat", "data", "validation"):
            self.assertIn(f'id="tab-{tab}"', html)
        self.assertNotIn("<head>", html)

    def test_no_untaught_term_in_the_markup_or_the_scripts(self):
        files = {"index.html": tab_sections(read("index.html"))}
        files.update({f"web/{name}": read("web", name) for name in scripts()})
        self.assertGreater(len(files), 9)
        for name, text in files.items():
            lower = text.lower()
            for term in FORBIDDEN:
                self.assertNotIn(term, lower, f"'{term}' in {name}")

    def test_the_guide_uses_the_same_words(self):
        for name in (os.path.join("docs", "LEARNERS_GUIDE.md"), "guide.html", os.path.join("docs", "PRESENTATION_SCRIPT.md"),
                     os.path.join("docs", "STUDY_GUIDE.md"), os.path.join("presentation", "PITCH_DECK.md")):
            lower = read(name).lower()
            for term in FORBIDDEN:
                self.assertNotIn(term, lower, f"'{term}' in {name}")
        # The six slides and their speaker notes, read straight from the .pptx.
        path = os.path.join(ROOT, "presentation", "Thermo_Solver_Presentation.pptx")
        with zipfile.ZipFile(path) as deck:
            slides = [n for n in deck.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
            notes = [n for n in deck.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
            self.assertEqual(len(slides), 6)
            self.assertEqual(len(notes), 6)
            for name in slides + notes:
                lower = "".join(re.findall(r"<a:t>([^<]*)</a:t>", deck.read(name).decode("utf-8"))).lower()
                self.assertTrue(lower.strip(), name)
                for term in FORBIDDEN:
                    self.assertNotIn(term, lower, f"'{term}' in {name}")

    def test_full_source_names_only_where_the_data_are_documented(self):
        allowed = {"tab-data.js", "tab-validation.js"}
        for name in scripts():
            if name in allowed:
                continue
            lower = read("web", name).lower()
            for term in SOURCE_NAMES:
                self.assertNotIn(term, lower, f"'{term}' in web/{name}")
        html = tab_sections(read("index.html")).lower()
        start, end = html.index('id="tab-reaction"'), html.index('id="tab-data"')
        for term in SOURCE_NAMES:
            self.assertNotIn(term, html[start:end])

    def test_tab_4_says_nothing_about_solid_carbon(self):
        # 23 November 2026: "in tab 4, remove all details about carbon soot". The solver still works
        # carbon_activity out (tests/test_equilibrium.py); the page no longer uses it.
        script = read("web", "tab-network.js")
        for gone in ("Solid carbon (soot)", "can form", "How the solver decides", "r.carbon_activity", "soot", "nw-plot-aC"):
            self.assertNotIn(gone, script)
        self.assertNotIn("Solid carbon", read("web", "ui.js"))                       # no glossary entry either
        html = tab_sections(read("index.html"))
        start, end = html.index('id="tab-network"'), html.index('id="tab-heat"')
        self.assertNotIn("soot", html[start:end].lower())
        self.assertNotIn("solid carbon", html[start:end].lower())
        for net in library.NETWORKS:                                                 # the notes shown on tab 4
            self.assertNotIn("soot", net["note"].lower(), net["id"])
            self.assertNotIn("solid-carbon", net["note"].lower(), net["id"])

    def test_tab_5_is_the_bomb_calorimeter_only(self):
        # 23 November 2026: "can u remove the reactor and flame part in tab 5? i know nothing about it."
        # The energy balance stays in the solver (heat_balance endpoint, tests/test_heatbalance.py).
        html = read("index.html")
        for gone in ('id="hl-reactor"', 'id="hl-view"', 'data-demo="flame"', "Reactor and flame", "flame temperature", "hb-"):
            self.assertNotIn(gone, html)
        self.assertIn('<span class="n">5</span>Bomb calorimeter', html)
        self.assertIn('<div id="hl-calorimeter">', html)                  # shown, not hidden
        script = read("web", "tab-heat.js")
        self.assertNotIn('call("heat_balance"', script)
        self.assertIn('TS.engine.call("calorimeter"', script)
        self.assertNotIn("heatExample", read("web", "main.js"))


class TestRequestsOfTheTwentyThirdOfNovember(unittest.TestCase):
    """What the user asked for on tabs 1 and 2 on 23 November 2026, kept in place."""

    def test_tab_1_has_no_van_t_hoff_line_and_no_consistency_checks(self):
        script = read("web", "tab-reaction.js")
        self.assertNotIn("van 't Hoff", script)
        self.assertNotIn("d ln K/dT", script)
        self.assertNotIn("falls to the right", script)
        self.assertNotIn("auditTable", script)

    def test_tab_1_shows_no_equilibrium_constant(self):
        # 23 November 2026: "in tab 1, no need to mention about eqm constant". The solver still
        # works K out (the conversion and tab 4 use it); tab 1 only does not show it.
        script = read("web", "tab-reaction.js")
        hide = '!s.title.startsWith("Equilibrium constant")'
        self.assertIn(hide, script)                                                  # the step is left out of the list
        shown = script.replace(hide, "")
        for gone in ("K<sub>p</sub>", "fmtK", "lnK", "log10K", "rx-plot-K", "Equilibrium constant", "K = 1", "K &lt;"):
            self.assertNotIn(gone, shown)
        steps = ok("analyze", METHANOL)["steps"]
        self.assertIn("Kp", steps[-1]["title"])                                      # the solver still has it
        html = tab_sections(read("index.html"))
        start, end = html.index('id="tab-reaction"'), html.index('id="tab-pressure"')
        self.assertNotIn(" and K ", html[start:end])

    def test_tab_2_has_no_largest_contribution(self):
        script = read("web", "tab-pressure.js")
        self.assertNotIn("Largest contribution", script)
        self.assertNotIn("c.largest", script)

    def test_tab_2_says_why_the_ideal_gas_value_is_flat_and_how_the_equation_is_chosen(self):
        script = read("web", "tab-pressure.js")
        self.assertIn("H = U + PV = U + RT", script)
        html = read("index.html")
        # 23 November 2026: the paragraph on how the equation is chosen was taken off tab 2 at the user's
        # request; the table at the bottom still names each gas's equation, and the Validation tab the comparison
        self.assertNotIn("You do not pick the equation of state", html)
        self.assertIn("equationCell(s)", script)

    def test_graphs_that_are_compared_share_their_scales(self):
        pressure = read("web", "tab-pressure.js")
        self.assertEqual(pressure.count("yaxis: residualAxis"), 4)            # all four graphs: the same range of values
        self.assertNotIn("totalAxis", pressure)
        self.assertIn("y: k(s.sum_HR)", pressure)                              # graph 1 shows the residual part
        self.assertEqual(read("web", "tab-reaction.js").count("xaxis: tAxis"), 2)   # energy and ΔCp graphs
        self.assertEqual(read("web", "tab-combine.js").count("...same"), 2)
        self.assertEqual(read("web", "tab-network.js").count("xaxis: xAxis"), 2)    # mole fractions and atom shares

    def test_tab_2_has_no_checks_no_percent_card_and_no_model_table(self):
        script = read("web", "tab-pressure.js")
        for gone in ("auditTable", "Change caused by pressure", "Same state, every model", "modelTable", "r.models"):
            self.assertNotIn(gone, script)
        self.assertNotIn("The table under", read("index.html"))

    def test_tab_2_explains_the_three_steps_and_the_pressure_effect_in_plain_words(self):
        script = read("web", "tab-pressure.js")
        self.assertIn("in the same way as Hess's law", script)
        self.assertIn("p.reactants_to_ideal", script)                      # the step values are quoted
        self.assertIn("hotter molecules move faster", script)
        self.assertIn("Why a real gas is different", script)

    def test_tab_3_has_no_equilibrium_constant(self):
        script = read("web", "tab-combine.js")
        for gone in ("fmtK", "lnK", "ln K", "K<sub>", "equilibrium constant"):
            self.assertNotIn(gone, script)
        html = tab_sections(read("index.html"))
        start, end = html.index('id="tab-combine"'), html.index('id="tab-network"')
        self.assertNotIn(" and K of the net", html[start:end])

    def test_tab_4_names_the_products_that_hardly_form(self):
        # 23 November 2026: "Equilibrium mole fraction of CH3OH isn't seen in tab 4". With methane allowed
        # it is about 1e-10, so its bar and line lie on zero; the page now names it with its number.
        script = read("web", "tab-network.js")
        self.assertIn('id="nw-live-tiny"', script)
        self.assertIn("r.y[s] < 1e-3", script)
        self.assertIn("with methane switched off, methanol appears", script)
        net = next(n for n in library.NETWORKS if n["id"] == "co2_hydrogenation")
        everything = ok("network", {"species": net["species"], "feed": net["feed"], "T": 523.0, "P": 50.0, "model": "auto", "sweep": "none"})
        self.assertLess(everything["y"]["CH3OH(g)"], 1e-3)
        no_methane = ok("network", {"species": [s for s in net["species"] if s != "CH4(g)"], "feed": net["feed"], "T": 523.0,
                                    "P": 50.0, "model": "auto", "sweep": "none"})
        self.assertGreater(no_methane["y"]["CH3OH(g)"], 0.05)

    def test_tab_4_shows_no_conversion(self):
        script = read("web", "tab-network.js")
        self.assertNotIn("conversion", script.lower())
        self.assertNotIn("nw-plot-conv", script)
        html = tab_sections(read("index.html"))
        start, end = html.index('id="tab-network"'), html.index('id="tab-heat"')
        self.assertNotIn("conversion", html[start:end].lower())

    def test_the_soot_test_on_tab_4_is_what_the_solver_does(self):
        # Kp of 2 CO -> C(s) + CO2 divided by the same pressure ratio of the gas is the
        # solver's number; carbon can form when it is above 1, as the page says.
        from thermosolver.reaction import Reaction
        net = next(n for n in library.NETWORKS if n["id"] == "co2_hydrogenation")
        for T, off in ((700.0, ["CH4(g)"]), (523.0, [])):
            r = ok("network", {"species": [s for s in net["species"] if s not in off], "feed": net["feed"],
                               "T": T, "P": 50.0, "model": "ideal"})
            p = {s: y * 50.0 for s, y in r["y"].items()}
            ratio = p["CO2(g)"] / p["CO(g)"] ** 2
            Kp = Reaction.parse("2 CO -> C(s) + CO2").K(T)
            self.assertAlmostEqual(Kp / ratio, r["carbon_activity"], delta=1e-6 * r["carbon_activity"])
            self.assertEqual(ratio < Kp, r["carbon_activity"] > 1)


class TestSecondRoundOfTheTwentyThirdOfNovember(unittest.TestCase):
    """The second list of 23 November 2026 for tabs 1, 2 and 4. What left the page stays in the solver."""

    def test_tab_1_shows_no_conversion_and_no_notes_on_pressure(self):
        script = read("web", "tab-reaction.js")
        for gone in ("Favourability at a given pressure", "Standard state and real mixture", "Pressure: ΔG° belongs",
                     "Pressure: with no change in gas moles", "rx-plot-X", "Equilibrium conversion", "conversion_1bar",
                     "equilibrium_P", "condensedNote", 'readNumber("rx-P")', "Type another pressure"):
            self.assertNotIn(gone, script)
        html = tab_sections(read("index.html"))
        start, end = html.index('id="tab-reaction"'), html.index('id="tab-pressure"')
        self.assertNotIn('id="rx-P"', html)
        self.assertNotIn("conversion", html[start:end].lower())
        # the solver still works the conversion out (at 1 bar when no pressure is sent)
        r = ok("analyze", {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15})
        self.assertEqual(r["P"], 1.0)
        self.assertAlmostEqual(r["equilibrium"]["conversion"], 0.006, delta=0.001)

    def test_tab_2_no_longer_points_to_tab_4(self):
        self.assertNotIn("Pressure also moves the equilibrium composition", read("web", "tab-pressure.js"))

    def test_tab_2_writes_out_steps_1_and_3_from_the_table(self):
        script = read("web", "tab-pressure.js")
        self.assertIn("That removes their H<sup>R</sup>", script)
        self.assertIn("That adds their H<sup>R</sup>", script)
        self.assertIn("terms(false)", script)
        self.assertIn("terms(true)", script)
        self.assertIn("table at the bottom of this tab", script)
        # the sums written out on the page are the solver's step values
        r = ok("pressure", AMMONIA)
        species, path = r["at_P"]["species"], r["comparison"]["path"]
        self.assertAlmostEqual(-sum(-s["nu"] * s["HR"] for s in species if s["nu"] < 0), path["reactants_to_ideal"], places=6)
        self.assertAlmostEqual(sum(s["nu"] * s["HR"] for s in species if s["nu"] > 0), path["products_to_real"], places=6)

    def test_tab_4_has_no_method_line_no_table_of_numbers_and_no_soot_graph(self):
        script = read("web", "tab-network.js")
        for gone in ("Method: the solver", "r.iterations", "nw-live-table", "Equilibrium mixture as numbers",
                     "nw-plot-aC", "Can solid carbon (soot) form?"):
            self.assertNotIn(gone, script)

    def test_bars_are_drawn(self):
        # The fill of a bar is a <span>. Without display: block it is an inline box, which ignores
        # width and height, so the bars of tab 4 looked empty (found by the user on 23 November 2026).
        css = read("web", "styles.css")
        rule = re.search(r"\.bars \.fill \{([^}]*)\}", css).group(1)
        self.assertIn("display: block", rule)


class TestRangesOfTheGraphs(unittest.TestCase):
    """23 November 2026: tab 1 starts at 298.15 K, and every graph's axes cover only where it has data."""

    METHANOL = {"equation": "CO2 + 3 H2 -> CH3OH + H2O", "T": 523.15}

    def test_tab_1_starts_at_298_15_K(self):
        self.assertIn("from_reference_T: true", read("web", "tab-reaction.js"))
        html = read("index.html")
        self.assertIn('<input id="rx-T" type="number" step="any" min="298.15"', html)
        self.assertIn('<input id="rx-Tmin" type="number" step="any" min="298.15"', html)
        self.assertNotIn("200 K upwards", html)
        for gone in ("low_T_species", "Below 298.15 K the heat capacities", "cp_from_low_T_table"):
            self.assertNotIn(gone, read("web", "tab-reaction.js"))
        r = ok("analyze", dict(self.METHANOL, from_reference_T=True))
        self.assertEqual(r["sweep"]["T"][0], 298.15)
        self.assertEqual(r["valid_range"][0], 298.15)
        self.assertEqual(r["crossover"], [])                     # dG changes sign at 276 K, below the range
        rows = {x["id"]: x for x in r["species"]}
        self.assertEqual(rows["CO2(g)"]["cp_Tmin"], 298.0)       # the textbook's own range
        for payload, words in ((dict(self.METHANOL, T=250, from_reference_T=True), "298.15 K or more"),
                               (dict(self.METHANOL, T_min=200, from_reference_T=True), "starts at 298.15 K")):
            out = json.loads(api.call("analyze", json.dumps(payload)))
            self.assertFalse(out["ok"])
            self.assertIn(words, out["error"]["message"])
        # without the flag (other callers, the tests of the data below 298.15 K) nothing changed
        plain = ok("analyze", self.METHANOL)
        self.assertEqual(plain["sweep"]["T"][0], 200.0)
        self.assertAlmostEqual(plain["crossover"][0], 276.3, delta=0.3)

    def test_every_graph_covers_only_its_data(self):
        uses = {"tab-reaction.js": 1, "tab-pressure.js": 3, "tab-network.js": 1, "tab-combine.js": 1, "tab-data.js": 1}
        for name, count in uses.items():
            self.assertEqual(read("web", name).count("TS.xExtent("), count, name)
        self.assertNotIn("yaxis: { range: [0, 1] }", read("web", "tab-network.js"))
        self.assertNotIn(".map(k), [0])", read("web", "tab-combine.js"))
        self.assertIn("dT * 1.04", read("web", "tab-heat.js"))

    def test_tab_2_temperature_graph_starts_where_the_gas_phase_values_begin(self):
        # methanol synthesis at 80 bar: methanol has no gas state of its own below about 525 K
        r = ok("pressure", {"equation": "CO + 2 H2 -> CH3OH", "T": 523.15, "P": 80})
        t = r["sweep_T"]
        self.assertTrue(500.0 < t["gas_from"] < 530.0)
        self.assertEqual(t["T"][0], t["gas_from"])
        self.assertTrue(all(v is not None for v in t["residual"]))
        self.assertIn("The temperature graph starts at", read("web", "tab-pressure.js"))


class TestTextsFromTheSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {
            "analyze": ok("analyze", METHANOL),
            "analyze, stable phase": ok("analyze", dict(METHANOL, auto_phase=True)),
            "pressure": ok("pressure", AMMONIA),
            # what the page asks for since the solver chooses the equation of state itself
            "pressure, automatic": ok("pressure", {k: v for k, v in AMMONIA.items() if k != "model"}),
            "network, automatic, 100 bar": ok("network", {"species": ["CO2(g)", "H2(g)", "CH3OH(g)", "CO(g)", "H2O(g)"],
                                                          "feed": {"CO2(g)": 1, "H2(g)": 3}, "T": 523.0, "P": 100.0,
                                                          "model": "auto", "sweep": "none"}),
            "eos_check": ok("eos_check", {}),
            "network, ideal gas": ok("network", network_payload("dry_reforming", "ideal")),
            "network, real gas": ok("network", network_payload("co2_hydrogenation", "pr")),
            "heat balance, flame": ok("heat_balance", heat_payload("methane_burner")),
            "heat balance, condensing": ok("heat_balance", heat_payload("condensing_boiler")),
            "challenge": ok("challenge", {}),
            "validate": ok("validate", {}),
            "database": ok("database", {}),
            "literature": ok("literature", {}),
        }
        # the ids of the library entries are internal names as well ("boudouard" is one)
        cls.library = ok("library", {})

    def test_no_untaught_term_reaches_the_page(self):
        texts = {name: text_of(res) for name, res in self.results.items()}
        texts["library"] = text_of(self.library, internal=("kind", "id"))
        # stress test 2 lists every library reaction with its id, which the page does not print
        texts["challenge"] = text_of(self.results["challenge"], internal=("kind", "id"))
        self.assertNotIn("x.id", read("web", "tab-validation.js"))
        for name, text in texts.items():
            self.assertGreater(len(text), 500, name)
            for term in FORBIDDEN:
                self.assertNotIn(term, text, f"'{term}' in the answer of: {name}")

    def test_the_cases_cover_the_texts_they_are_meant_to(self):
        flame, boiler = self.results["heat balance, flame"], self.results["heat balance, condensing"]
        self.assertEqual(flame["mode"], "adiabatic")
        self.assertGreater(flame["point"]["T_out"], 2000.0)                 # hot enough for both notes
        self.assertEqual([n["kind"] for n in flame["point"]["notes"]], ["high_T_data", "dissociation"])
        self.assertIn("partly break apart", flame["point"]["notes"][1]["message"])
        self.assertGreater(boiler["point"]["water"]["n_liquid"], 1.0)       # water does condense
        note = next(n for n in boiler["point"]["notes"] if n["kind"] == "condensation")
        self.assertIn("the temperature at which its water vapour becomes saturated", note["message"])
        self.assertIsNotNone(flame["work"])
        self.assertIsNotNone(self.results["network, ideal gas"]["carbon_activity"])      # still calculated
        self.assertTrue(self.results["network, real gas"]["notes"])                      # a real-gas note is there
        self.assertTrue(self.results["analyze, stable phase"]["phase"]["auto"])

    def test_full_source_names_stay_on_the_data_and_validation_tabs(self):
        for name in ("analyze", "analyze, stable phase", "pressure", "network, ideal gas", "network, real gas",
                     "heat balance, flame", "heat balance, condensing", "challenge"):
            text = text_of(self.results[name])
            for term in SOURCE_NAMES:
                self.assertNotIn(term, text, f"'{term}' in the answer of: {name}")
        # where the data are documented they are named in full
        self.assertIn("nist-janaf", text_of(self.results["database"]))
        self.assertIn("nist-janaf", " ".join(r["source"].lower() for r in self.results["validate"]["rows"]))
        # below 200 K and above the SVN range the notes of tab 1 say "NIST data" and "NIST equations"
        cold = ok("analyze", {"equation": "N2 + 3 H2 -> 2 NH3", "T": 150})
        hot = ok("analyze", {"equation": "CO + 1/2 O2 -> CO2", "T": 2600})
        for res in (cold, hot):
            text = text_of(res)
            self.assertIn("nist", text)
            for term in SOURCE_NAMES + FORBIDDEN:
                self.assertNotIn(term, text)

    def test_names_of_the_consistency_checks(self):
        names = [c["name"] for c in self.results["analyze"]["audit"]]
        self.assertEqual(names, ["Elemental balance", "Two routes to dG(T)", "Slope of ΔH° with temperature",
                                 "van 't Hoff equation", "Slope of ΔG° with temperature",
                                 "Enthalpy integral", "Entropy integral"])
        relations = " | ".join(c["relation"] for c in self.results["analyze"]["audit"])
        self.assertIn("d(dH)/dT = dCp", relations)                          # the formulas stay
        self.assertIn("d(dG)/dT = -dS", relations)
        self.assertEqual(relations.count("numerical integration"), 2)
        residual = [c["name"] for c in self.results["pressure"]["audit"]]
        self.assertEqual(len(residual), 9)                                  # three checks for each of the three gases
        for sid in ("N2(g)", "H2(g)", "NH3(g)"):
            for check in ("residual enthalpy, entropy and Gibbs energy fit together",
                          "residual enthalpy from the temperature slope",
                          "compressibility factor from the pressure slope"):
                self.assertIn(f"{sid}: {check}", residual)
        boiling = [c["name"] for c in self.results["analyze, stable phase"]["audit"]]
        self.assertTrue(any("Clausius/Clapeyron" in name for name in boiling))          # taught, so it stays
        for res in self.results.values():
            for check in res.get("audit", []) + res.get("point", {}).get("audit", []):
                self.assertTrue(check["passed"], check["name"])

    def test_benchmark_groups_and_real_gas_models(self):
        groups = {r["group"] for r in self.results["validate"]["rows"]}
        self.assertIn("Equilibrium mixture", groups)
        self.assertEqual(sum(1 for r in self.results["validate"]["rows"] if r["group"] == "Equilibrium mixture"), 5)
        self.assertEqual(self.results["database"]["models"]["virial"], "Generalized virial correlation")
        # 23 November 2026: the user no longer picks the equation of state, on tab 2 or on tab 4
        html = read("index.html")
        for gone in ('id="pr-model"', 'id="nw-model"', "<option value=\"pr\">", "Real-gas model", "Gas model"):
            self.assertNotIn(gone, html)
        for name in ("tab-pressure.js", "tab-network.js"):
            script = read("web", name)
            self.assertNotIn("-model", script)
            self.assertIn('model: "auto"', script)

    def test_a_species_that_is_a_liquid_is_called_a_liquid(self):
        # water at 523 K and 100 bar: no gas-phase value, and the texts say why in plain words
        res = ok("pressure", {"equation": "CO2 + 3 H2 -> CH3OH(g) + H2O(g)", "T": 523.15, "P": 100, "model": "pr"})
        self.assertFalse(res["at_P"]["gas_phase_valid"])
        text = text_of(res)
        self.assertIn("describes a liquid, not a gas", text)
        for words in ("liquid root", "vapour-like", "hypothetical vapour", "ideal-solution", "activity = 1"):
            self.assertNotIn(words, text)
        script = read("web", "tab-pressure.js")
        for words in ("liquid root", "vapour-like", "hypothetical vapour", "ideal-solution", "incompressible"):
            self.assertNotIn(words, script)


if __name__ == "__main__":
    unittest.main()
