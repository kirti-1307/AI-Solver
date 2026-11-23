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
    r'<header class="top">.*?</header>',
    r'<section id="tab-home".*?</section>',
    r"<footer.*?</footer>",
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
        for tab in ("reaction", "pressure", "combine", "network", "heat", "data", "validation"):
            self.assertIn(f'id="tab-{tab}"', html)
        self.assertNotIn('id="tab-home"', html)

    def test_no_untaught_term_in_the_markup_or_the_scripts(self):
        files = {"index.html": tab_sections(read("index.html"))}
        files.update({f"web/{name}": read("web", name) for name in scripts()})
        self.assertGreater(len(files), 9)
        for name, text in files.items():
            lower = text.lower()
            for term in FORBIDDEN:
                self.assertNotIn(term, lower, f"'{term}' in {name}")

    def test_the_guide_uses_the_same_words(self):
        for name in (os.path.join("docs", "LEARNERS_GUIDE.md"), "guide.html"):
            lower = read(name).lower()
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

    def test_tab_4_says_whether_solid_carbon_can_form_without_the_number(self):
        script = read("web", "tab-network.js")
        self.assertIn("Solid carbon (soot)", script)
        self.assertIn("can form", script)
        # the solver's number is only compared with 1; it is never printed or plotted as a value
        self.assertNotRegex(script, r"(sig|fix)\([^)]*carbon_activity")
        self.assertNotRegex(script, r"y: s\.carbon_activity\b")
        self.assertEqual(len(re.findall(r"carbon_activity > 1|v > 1 \? 1 : 0", script)), 3)

    def test_tab_5_names_the_heat_in_plain_words(self):
        html = tab_sections(read("index.html"))
        self.assertIn('data-mode="duty">Find the heat to add or remove</button>', html)      # the mode keeps its name
        self.assertRegex(html, r'id="hb-condense" checked><span>Let the water change phase')
        script = read("web", "tab-heat.js")
        for words in ("Heat added, Q", "Water starts to condense at", "The most work the hot products could deliver",
                      "Carnot engine"):
            self.assertIn(words, script)
        self.assertNotIn("W<sub>ideal</sub>", script)


class TestTextsFromTheSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {
            "analyze": ok("analyze", METHANOL),
            "analyze, stable phase": ok("analyze", dict(METHANOL, auto_phase=True)),
            "pressure": ok("pressure", AMMONIA),
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
        self.assertIn('<option value="virial">Generalized virial correlation</option>', read("index.html"))

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
