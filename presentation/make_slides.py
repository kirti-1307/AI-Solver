"""Build presentation/Thermo_Solver_Presentation.pptx (six slides) with python-pptx.

    python presentation/make_slides.py

Every number on the slides is the solver's (see docs/STUDY_GUIDE.md, section 2).
The speaker notes are the words of docs/PRESENTATION_SCRIPT.md, part 1.
The look follows the website: navy and white with one orange accent, and the
square "tile" of the start page as the repeated element.
"""

import os
import re

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Thermo_Solver_Presentation.pptx")

NAVY = RGBColor(0x16, 0x23, 0x3A)
NAVY_SOFT = RGBColor(0x24, 0x34, 0x52)
ORANGE = RGBColor(0xC2, 0x41, 0x0C)
BLUE = RGBColor(0x0B, 0x5C, 0xAD)
INK = RGBColor(0x1F, 0x29, 0x37)
MUTED = RGBColor(0x5B, 0x67, 0x78)
PALE = RGBColor(0xEE, 0xF2, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xC9, 0xD6, 0xE8)
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
TITLE_ONLY = prs.slide_layouts[5]


# ---------------------------------------------------------------- helpers
def runs(paragraph, text, size, color, bold=False, italic=False, font=BODY):
    """Text with _{sub} and ^{sup} marks, written as runs with a raised or lowered baseline."""
    for part in re.split(r"([_^]\{[^}]*\})", text):
        if not part:
            continue
        shift = None
        if part.startswith("_{"):
            part, shift = part[2:-1], "-25000"
        elif part.startswith("^{"):
            part, shift = part[2:-1], "30000"
        r = paragraph.add_run()
        r.text = part
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, font
        f.color.rgb = color
        if shift:
            r._r.get_or_add_rPr().set("baseline", shift)


def text(slide, x, y, w, h, paragraphs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font=BODY, space_after=6, name=None):
    """A text box. paragraphs: a string, or a list of strings or (string, dict of options)."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    items = paragraphs if isinstance(paragraphs, list) else [paragraphs]
    for i, item in enumerate(items):
        body, opts = (item, {}) if isinstance(item, str) else item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opts.get("align", align)
        p.space_after = Pt(opts.get("space_after", space_after))
        runs(p, body, opts.get("size", size), opts.get("color", color), opts.get("bold", bold),
             opts.get("italic", False), opts.get("font", font))
    return box


def tile(slide, x, y, size, symbol, fill=NAVY, color=WHITE, symbol_size=26, label=None, name=None):
    """The square tile of the website's start page: a big symbol, and a small label under it."""
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(size), Inches(size))
    shp.adjustments[0] = 0.12
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    if name:
        shp.name = name
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0.04))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    runs(p, symbol, symbol_size, color, bold=True, font=HEAD)
    if label:
        q = tf.add_paragraph()
        q.alignment = PP_ALIGN.CENTER
        runs(q, label, max(10, int(symbol_size * 0.38)), color)
    return shp


def card(slide, x, y, w, h, fill=PALE, name=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.05
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    if name:
        shp.name = name
    return shp


def new_slide(title, dark=False, notes=""):
    slide = prs.slides.add_slide(TITLE_ONLY)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY if dark else WHITE
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.9)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    runs(p, title, 34, WHITE if dark else NAVY, bold=True, font=HEAD)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def footer(slide, number, dark=False):
    text(slide, 0.6, 7.0, 9.0, 0.3, "Thermodynamic Reaction Energy Solver · Assignment 2", size=10,
         color=ICE if dark else MUTED)
    text(slide, 11.73, 7.0, 1.0, 0.3, str(number), size=10, color=ICE if dark else MUTED, align=PP_ALIGN.RIGHT)


# ---------------------------------------------------------------- slide 1: title
s = new_slide("Thermodynamic Reaction Energy Solver", dark=True, notes=(
    "Good morning. My project is a Thermodynamic Reaction Energy Solver. It is a web page that works out the heat of "
    "reaction, the entropy change and the Gibbs energy change of a chemical reaction at any temperature, and shows what "
    "pressure does to them, using the data and the equations of Smith, Van Ness and Abbott. I built it with Claude as the "
    "AI platform."))
s.shapes.title.top, s.shapes.title.height, s.shapes.title.width = Inches(2.15), Inches(1.5), Inches(7.6)
s.shapes.title.text_frame.paragraphs[0].runs[0].font.size = Pt(42)
text(s, 0.6, 1.6, 7.6, 0.4, "Assignment 2 · Chemical Engineering Thermodynamics", size=14, color=ORANGE, bold=True)
text(s, 0.6, 3.75, 7.4, 1.0, "Heat, entropy and Gibbs energy of any reaction, at any temperature, from the textbook's data, "
     "in the browser", size=18, color=ICE)
text(s, 0.6, 5.35, 7.6, 1.2, [
    ("Kirti Roshankumar Thakar · Roll No. 25A1CHEB0107", {"size": 16, "color": WHITE, "bold": True}),
    ("Prof. M. Ali Haider · AI platform used: Claude", {"size": 14, "color": ICE}),
    ("Live: kirti-1307.github.io/AI-Solver", {"size": 14, "color": ICE}),
])
for i, (sym, lab) in enumerate((("ΔH°", "heat"), ("ΔS°", "disorder"), ("ΔG°", "which side?"))):
    tile(s, 9.0 + (i % 2) * 1.95 if i < 2 else 9.97, 1.75 + (i // 2) * 1.95, 1.75, sym,
         fill=ORANGE if i == 2 else NAVY_SOFT, symbol_size=34, label=lab, name=f"Tile {sym}")

# ---------------------------------------------------------------- slide 2: the idea
s = new_slide("The idea: the full textbook method, every time", notes=(
    "Let me start with the problem. In our course, the heat of reaction at a temperature other than 298.15 K needs a "
    "heat-capacity integral for every species. By hand, that takes a page of working for one reaction at one temperature, "
    "and a slip in one constant is easy to miss. So people use shortcuts: they take delta Cp as constant, or ignore it. "
    "For the 40 predefined reactions whose data reach 1000 K, a constant delta Cp puts delta H off by 9.0 kJ/mol on "
    "average and by up to 31.5 kJ/mol. And a real reactor adds two more questions that a single delta G cannot answer: "
    "what does high pressure do, and which products actually form when several reactions compete for the same atoms. "
    "My idea was a solver that does the full textbook method every time, in a few seconds, shows every step and every "
    "plot, explains the result in plain words, and checks itself against the textbook."))
text(s, 0.6, 1.5, 6.4, 0.4, "The problem", size=20, color=ORANGE, bold=True, font=HEAD)
problems = (
    ("∫", "Long by hand", "ΔH°(T) needs a C_{p} integral for every species: a page of working for one reaction at one temperature."),
    ("≈", "Shortcuts mislead", "A constant ΔC_{p} is off by 9.0 kJ/mol on average at 1000 K, and by up to 31.5 kJ/mol."),
    ("P", "Real reactors ask more", "What does high pressure do? Which products form when several reactions compete?"),
)
for i, (sym, head, body) in enumerate(problems):
    y = 2.1 + i * 1.5
    tile(s, 0.6, y, 1.1, sym, fill=NAVY, symbol_size=30, name=f"Problem tile {i + 1}")
    text(s, 1.95, y + 0.02, 5.0, 1.3, [(head, {"size": 18, "bold": True, "color": NAVY, "space_after": 3}),
                                       (body, {"size": 15, "color": INK})])
card(s, 7.55, 1.5, 5.2, 4.75, fill=NAVY, name="The solver card")
text(s, 7.95, 1.8, 4.5, 0.5, "The solver", size=22, color=WHITE, bold=True, font=HEAD)
points = ("Checks the element balance first",
          "ΔH°, ΔS°, ΔG° at any temperature, step by step",
          "Real gases at any pressure",
          "Which products form when reactions compete",
          "Explains each result in plain words",
          "Checks itself against the textbook")
text(s, 7.95, 2.5, 4.5, 3.6, [("✓  " + p_, {"size": 17, "color": WHITE, "space_after": 16}) for p_ in points])
footer(s, 2)

# ---------------------------------------------------------------- slide 3: how it works
s = new_slide("How it works", notes=(
    "The user picks one of 45 predefined reactions, or types any reaction. First, the solver checks the balance of every "
    "element. An unbalanced reaction gets no numbers at all, only the balanced form as a suggestion. Then it takes the data "
    "from its database: 57 species, mostly from the textbook's tables, with NIST data only where the textbook has none. It "
    "integrates the heat capacities from 298.15 K to the chosen temperature and gets delta H, delta S and delta G. For "
    "pressure, it adds the residual enthalpy of each gas from an equation of state. Everything runs inside the browser. "
    "There is no server, so the page works anywhere."))
steps = (("1", "Reaction", "45 predefined, or type any reaction"),
         ("2", "Balance check", "every element; unbalanced gets no numbers"),
         ("3", "Data", "57 species: textbook tables, NIST only where needed"),
         ("4", "Calculation", "C_{p} integrals → ΔH°, ΔS°, ΔG°; residual enthalpy for pressure"),
         ("5", "Results", "numbers, plots, every step, plain-word explanation"))
x0, wbox, gap = 0.6, 2.18, 0.3
for i, (num, head, body) in enumerate(steps):
    x = x0 + i * (wbox + gap)
    card(s, x, 1.65, wbox, 2.75, fill=PALE, name=f"Step {num}")
    tile(s, x + 0.2, 1.85, 0.75, num, fill=ORANGE if i == 3 else NAVY, symbol_size=24, name=f"Step tile {num}")
    text(s, x + 0.2, 2.75, wbox - 0.4, 1.6, [(head, {"size": 17, "bold": True, "color": NAVY, "space_after": 4}),
                                             (body, {"size": 14, "color": INK})])
    if i < len(steps) - 1:
        arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + wbox + 0.04), Inches(2.85), Inches(0.22), Inches(0.32))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = MUTED
        arrow.line.fill.background()
        arrow.name = f"Arrow {i + 1}"
card(s, 0.6, 4.75, 12.1, 1.15, fill=NAVY, name="Formula strip")
text(s, 0.9, 4.75, 11.5, 1.15, "ΔH°(T) = ΔH°_{298} + R∫(ΔC_{p}°/R)dT      ΔG° = ΔH° − TΔS°      ΔH(T,P) = ΔH°(T) + Σν_{i}H_{i}^{R}",
     size=20, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=HEAD, space_after=0)
facts = ("Runs in any browser: the Python solver works inside the page", "Seven tabs, from one reaction to a whole reactor",
         "No server: nothing is sent anywhere")
for i, f_ in enumerate(facts):
    text(s, 0.6 + i * 4.1, 6.15, 3.8, 0.7, f_, size=14, color=MUTED)
footer(s, 3)

# ---------------------------------------------------------------- slide 4: what it shows
s = new_slide("What the solver shows", notes=(
    "Three results from the solver. First, temperature decides which side is favoured. CO2 to methanol gives out heat, but "
    "it turns four moles of gas into two, so delta S is negative. At 523 K, delta G is plus 46.6 kJ/mol, so the reactants "
    "are favoured. Steam reforming is the opposite case: its products are favoured above 893 K. Second, pressure matters for "
    "real gases. For ammonia synthesis at 200 bar, the real gas releases 4.7 % more heat than the ideal gas. Third, no "
    "single equation of state is best. I compared the five equations of the course with measured data from NIST for 24 "
    "gases. The chart shows the average error: Soave/Redlich/Kwong and Peng/Robinson are far better than van der Waals and "
    "the virial equation. So the solver, not the user, chooses the equation for each gas."))
text(s, 0.6, 1.55, 5.6, 1.0, "+46.6 kJ/mol", size=48, color=ORANGE, bold=True, font=HEAD)
text(s, 0.6, 2.5, 5.6, 1.2, [("ΔG° of CO_{2} + 3H_{2} → CH_{3}OH + H_{2}O at 523 K", {"size": 16, "bold": True, "color": NAVY}),
                             ("It gives out heat (ΔH° = −57.9 kJ/mol), but 4 moles of gas become 2: the reactants are favoured. "
                              "Steam reforming is favoured above 893 K.", {"size": 14, "color": INK})])
text(s, 0.6, 4.25, 5.6, 1.0, "4.7 %", size=48, color=ORANGE, bold=True, font=HEAD)
text(s, 0.6, 5.2, 5.6, 1.2, [("more heat from real-gas ammonia at 200 bar", {"size": 16, "bold": True, "color": NAVY}),
                             ("−111.55 instead of −106.50 kJ/mol: the residual enthalpy of each gas, from an equation of state.",
                              {"size": 14, "color": INK})])
data = CategoryChartData()
data.categories = ["Virial", "van der Waals", "Redlich/Kwong", "Peng/Robinson", "Soave/Redlich/Kwong"]
data.add_series("Average error (kJ/mol)", (1.349, 1.246, 0.510, 0.160, 0.137))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(6.75), Inches(1.95), Inches(5.95), Inches(3.75), data)
gf.name = "Chart: equations of state against NIST"
chart = gf.chart
chart.has_legend = False
chart.has_title = False
plot = chart.plots[0]
plot.gap_width = 55
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format, dl.number_format_is_linked = "0.000", False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size, dl.font.color.rgb, dl.font.name = Pt(13), INK, BODY
for i, point in enumerate(plot.series[0].points):
    point.format.fill.solid()
    point.format.fill.fore_color.rgb = ORANGE if i == 4 else (BLUE if i == 3 else ICE)
cat = chart.category_axis
cat.tick_labels.font.size, cat.tick_labels.font.color.rgb, cat.tick_labels.font.name = Pt(13), INK, BODY
cat.format.line.color.rgb = ICE
cat.has_major_gridlines = False
val = chart.value_axis
val.visible = False
val.has_major_gridlines = False
val.maximum_scale, val.minimum_scale = 1.6, 0.0
text(s, 6.75, 1.5, 5.95, 0.45, "Average error against NIST measured residual enthalpy (kJ/mol)", size=14, color=NAVY, bold=True)
text(s, 6.75, 5.8, 5.95, 0.9, [("24 gases, 380 measured points. Closest for each gas: Soave/Redlich/Kwong 14, Peng/Robinson 6, "
                                "Redlich/Kwong 4.", {"size": 13, "color": INK}),
                               ("So the solver, not the user, picks the equation for each gas.", {"size": 13, "color": ORANGE, "bold": True})])
footer(s, 4)

# ---------------------------------------------------------------- slide 5: two extra features
s = new_slide("Two extra features", notes=(
    "On top of what the assignment asks, I added two features. The product slate is a live reactor. I only choose which "
    "species may exist, and the solver finds the mixture with the lowest total Gibbs energy. For CO2 and hydrogen at 523 K "
    "and 50 bar, methane takes 74.9 % of the carbon. If I switch methane off, like a selective catalyst would, methanol "
    "takes 20.6 %. So thermodynamics favours methane, and it is the catalyst that makes methanol possible. The second "
    "feature repeats our bomb calorimeter lab. The bomb is a closed vessel, so it measures delta U and not delta H. After a "
    "calibration with the benzoic acid run of the handout, it predicts the temperature rise of any fuel, 2.31 degrees C for "
    "1 g of ethanol, and it can work backwards to name an unknown sample."))
cols = (
    ("G", "Product slate", "figure_slate.png",
     ["The lowest total Gibbs energy of the allowed species.",
      "Methane 74.9 % of the carbon; switched off: methanol 20.6 %.",
      ("The catalyst decides what forms.", {"bold": True, "color": ORANGE})]),
    ("ΔU", "Bomb calorimeter", "figure_calorimeter.png",
     ["A closed vessel gives ΔU, not ΔH: ΔH = ΔU + Δn_{gas}RT.",
      "Calibrated with benzoic acid: 3059.3 cal/°C.",
      ("1 g of ethanol: 2.31 °C; it also names an unknown sample.", {"bold": True, "color": ORANGE})]),
)
for i, (sym, head, img, lines) in enumerate(cols):
    x = 0.6 + i * 6.25
    card(s, x, 1.5, 5.85, 5.3, fill=PALE, name=f"{head} card")
    tile(s, x + 0.3, 1.75, 0.8, sym, fill=NAVY, symbol_size=22 if len(sym) > 1 else 26, name=f"{head} tile")
    text(s, x + 1.3, 1.8, 4.3, 0.7, head, size=22, color=NAVY, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    pic = s.shapes.add_picture(os.path.join(HERE, img), Inches(x + 0.3), Inches(2.7), height=Inches(2.85))
    pic.left = Inches(x) + (Inches(5.85) - pic.width) // 2          # centred in the card
    pic.name = f"{head} figure"
    text(s, x + 0.3, 5.7, 5.25, 1.0,
         [(l_, {"size": 14, "color": INK, "space_after": 5}) if isinstance(l_, str) else (l_[0], dict({"size": 14, "space_after": 5}, **l_[1]))
          for l_ in lines])
footer(s, 5)

# ---------------------------------------------------------------- slide 6: checked
s = new_slide("Checked, and ready to try", dark=True, notes=(
    "Finally, why the numbers can be trusted. The solver reproduces 67 of 67 reference values from the textbook, the "
    "course material and NIST. It passes all five stress tests of the assignment. I found and corrected eight errors of "
    "the AI-generated solver. And 441 automated tests run every time the code changes. Let me show you the solver live."))
stats = (("67/67", "reference values from the textbook, the course and NIST"),
         ("5/5", "stress tests of the assignment passed"),
         ("8", "errors of the AI-generated solver found and corrected"),
         ("441", "automated tests run on every change"))
for i, (num, lab) in enumerate(stats):
    x = 0.6 + i * 3.1
    card(s, x, 1.75, 2.8, 2.7, fill=NAVY_SOFT, name=f"Stat {num}")
    text(s, x + 0.25, 1.95, 2.3, 1.2, num, size=50, color=ORANGE if i == 0 else WHITE, bold=True, font=HEAD, align=PP_ALIGN.CENTER)
    text(s, x + 0.25, 3.25, 2.3, 1.4, lab, size=15, color=ICE, align=PP_ALIGN.CENTER)
text(s, 0.6, 5.0, 12.1, 0.6, "Live demo now", size=26, color=WHITE, bold=True, font=HEAD)
text(s, 0.6, 5.65, 12.1, 0.8, [("kirti-1307.github.io/AI-Solver      ·      ai-solver-seven.vercel.app      ·      "
                                "github.com/kirti-1307/AI-Solver", {"size": 16, "color": ICE})])
footer(s, 6, dark=True)

prs.save(OUT)
print("wrote", OUT, "with", len(prs.slides), "slides")
