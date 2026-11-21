"""Draw the report figure from the solver itself (needs Pillow only).

    python report/make_figure.py

Left:  where the carbon of a CO2 + 3 H2 feed goes at equilibrium, 50 bar,
       when methane is not allowed to form, and (dashed) the methane share
       when it is allowed.
Right: ideal efficiency of a hydrogen fuel cell against the Carnot limit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from thermosolver import Reaction
from thermosolver.electrochem import electrochemistry_sweep
from thermosolver.equilibrium import atom_distribution, gibbs_minimize

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure.png")
S = 3                       # supersampling factor
W, H = 1560, 470            # final size in pixels

BLUE, ORANGE, GREY, INK, MUTED, PURPLE, LINE = (
    "#0b5cad", "#c2410c", "#cbd5e1", "#17202a", "#5d6b7a", "#7c3aed", "#d5dae1")


def font(size, bold=False):
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size * S)
        except OSError:
            continue
    return ImageFont.load_default()


F_TICK, F_LABEL, F_TITLE, F_LEG = font(15), font(16), font(18, True), font(14)


class Axes:
    def __init__(self, draw, box, xlim, ylim):
        self.d = draw
        self.x0, self.y0, self.x1, self.y1 = [v * S for v in box]
        self.xlim, self.ylim = xlim, ylim

    def px(self, x, y):
        fx = (x - self.xlim[0]) / (self.xlim[1] - self.xlim[0])
        fy = (y - self.ylim[0]) / (self.ylim[1] - self.ylim[0])
        return (self.x0 + fx * (self.x1 - self.x0), self.y1 - fy * (self.y1 - self.y0))

    def frame(self, xticks, yticks, xlabel, ylabel, title):
        d = self.d
        for y in yticks:
            _, py = self.px(self.xlim[0], y)
            d.line([(self.x0, py), (self.x1, py)], fill=LINE, width=S)
            d.text((self.x0 - 8 * S, py), f"{y:g}", font=F_TICK, fill=MUTED, anchor="rm")
        for x in xticks:
            px, _ = self.px(x, self.ylim[0])
            d.line([(px, self.y1), (px, self.y1 + 5 * S)], fill=MUTED, width=S)
            d.text((px, self.y1 + 9 * S), f"{x:g}", font=F_TICK, fill=MUTED, anchor="mt")
        d.line([(self.x0, self.y0), (self.x0, self.y1), (self.x1, self.y1)], fill=MUTED, width=S)
        d.text(((self.x0 + self.x1) / 2, self.y1 + 34 * S), xlabel, font=F_LABEL, fill=INK, anchor="mt")
        d.text((self.x0 - 62 * S, self.y0 - 34 * S), title, font=F_TITLE, fill=INK, anchor="lt")
        # rotated y label
        tmp = Image.new("RGBA", (int(self.y1 - self.y0), 26 * S), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((tmp.width / 2, 13 * S), ylabel, font=F_LABEL, fill=INK, anchor="mm")
        rot = tmp.rotate(90, expand=True)
        d._image.paste(rot, (int(self.x0 - 66 * S), int(self.y0)), rot)

    def line(self, xs, ys, color, width=3, dash=None):
        pts = [self.px(x, y) for x, y in zip(xs, ys)]
        if not dash:
            self.d.line(pts, fill=color, width=width * S, joint="curve")
            return
        on, off = dash
        for i in range(0, len(pts) - 1, on + off):
            self.d.line(pts[i:i + on + 1], fill=color, width=width * S, joint="curve")

    def area(self, xs, lower, upper, color):
        pts = [self.px(x, y) for x, y in zip(xs, upper)] + [self.px(x, y) for x, y in zip(reversed(xs), reversed(lower))]
        self.d.polygon(pts, fill=color)

    def legend(self, items, x, y):
        for i, (label, color, kind) in enumerate(items):
            yy = (y + i * 22) * S
            xx = x * S
            if kind == "box":
                self.d.rectangle([xx, yy - 6 * S, xx + 22 * S, yy + 6 * S], fill=color)
            elif kind == "dash":
                for k in range(3):
                    self.d.line([(xx + k * 9 * S, yy), (xx + (k * 9 + 5) * S, yy)], fill=color, width=3 * S)
            else:
                self.d.line([(xx, yy), (xx + 22 * S, yy)], fill=color, width=3 * S)
            self.d.text((xx + 30 * S, yy), label, font=F_LEG, fill=INK, anchor="lm")


def main():
    img = Image.new("RGB", (W * S, H * S), "white")
    draw = ImageDraw.Draw(img)

    # ---- (a) product slate -------------------------------------------------
    feed = {"CO2": 1, "H2": 3}
    selective = ["CO2", "H2", "CH3OH", "CO", "H2O(g)"]
    Ts = [400 + 5 * i for i in range(61)]
    meoh, co, ch4 = [], [], []
    for T in Ts:
        d = atom_distribution(gibbs_minimize(selective, feed, T, 50.0), "C")
        meoh.append(100 * d["CH3OH(g)"])
        co.append(100 * d["CO(g)"])
        d_all = atom_distribution(gibbs_minimize(selective + ["CH4"], feed, T, 50.0), "C")
        ch4.append(100 * d_all["CH4(g)"])
    a = Axes(draw, (92, 62, 730, 388), (400, 700), (0, 100))
    zero = [0.0] * len(Ts)
    top = [m + c for m, c in zip(meoh, co)]
    a.area(Ts, top, [100.0] * len(Ts), GREY)
    a.area(Ts, meoh, top, ORANGE)
    a.area(Ts, zero, meoh, BLUE)
    a.frame([400, 450, 500, 550, 600, 650, 700], [0, 20, 40, 60, 80, 100], "Temperature (K)",
            "Share of carbon atoms (%)", "(a) Product slate: CO₂ + 3 H₂ at 50 bar")
    a.line(Ts, ch4, INK, 3, dash=(3, 2))
    draw.rectangle([452 * S, 172 * S, 722 * S, 272 * S], fill="white")
    a.legend([("CH₃OH (methane blocked)", BLUE, "box"), ("CO (methane blocked)", ORANGE, "box"),
              ("unreacted CO₂", GREY, "box"), ("CH₄ if methane is allowed", INK, "dash")], 462, 188)

    # ---- (b) electrochemical lens --------------------------------------------
    rxn = Reaction.parse("H2 + 1/2 O2 -> H2O(g)")
    T2 = [400 + 10 * i for i in range(141)]
    sw = electrochemistry_sweep(rxn, T2)
    b = Axes(draw, (880, 62, 1530, 388), (400, 1800), (20, 100))
    b.frame([400, 600, 800, 1000, 1200, 1400, 1600, 1800], [20, 40, 60, 80, 100], "Temperature (K)",
            "Maximum efficiency (%)", "(b) Electrochemical lens: H₂ + ½ O₂ → H₂O(g)")
    Tx = sw["crossover_T"]
    px, _ = b.px(Tx, 20)
    for k in range(int(b.y0), int(b.y1), 9 * S):
        draw.line([(px, k), (px, k + 4 * S)], fill=PURPLE, width=2 * S)
    b.line(T2, [100 * v for v in sw["carnot_efficiency"]], MUTED, 3, dash=(4, 2))
    b.line(T2, [100 * v for v in sw["efficiency"]], BLUE, 4)
    draw.text((px + 10 * S, b.y1 - 96 * S), f"break-even at {Tx:.0f} K", font=F_LEG, fill=PURPLE, anchor="lm")
    b.legend([("Ideal fuel cell, ΔG/ΔH", BLUE, "line"), ("Carnot engine, 1 − 298/T", MUTED, "dash")], 1250, 330)

    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT, dpi=(220, 220))
    print("wrote", OUT, f"(break-even {Tx:.0f} K; methanol share at 523 K = {meoh[Ts.index(525)]:.1f} %)")


if __name__ == "__main__":
    main()
