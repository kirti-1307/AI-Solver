"""Command-line use of the solver.

    python -m thermosolver "CO + 2 H2 -> CH3OH(g)" --T 1073.15
    python -m thermosolver "N2 + 3 H2 -> 2 NH3" --T 723.15 --P 200 --model pr
    python -m thermosolver --validate
"""

from __future__ import annotations

import argparse
import sys

from . import benchmarks
from .constants import T0
from .errors import SolverError
from .realgas import MODEL_NAMES, reaction_at_pressure
from .reaction import Reaction


def _print_reaction(args) -> None:
    rxn = Reaction.parse(args.reaction)
    ev = rxn.evaluate(args.T)
    print(f"\n  {rxn.equation}")
    for note in rxn.notes:
        print(f"  note: {note}")
    print(f"\n  At 298.15 K   dH0 = {ev['dH0']:>14,.1f} J/mol   ({ev['thermicity0']})")
    print(f"                dG0 = {ev['dG0']:>14,.1f} J/mol")
    print(f"                dS0 = {ev['dS0']:>14,.3f} J/(mol K)")
    print(f"\n  At {args.T:g} K")
    print(f"                dH  = {ev['dH']:>14,.1f} J/mol   ({ev['thermicity']})")
    print(f"                dS  = {ev['dS']:>14,.3f} J/(mol K)")
    print(f"                dG  = {ev['dG']:>14,.1f} J/mol")
    print(f"                ln K = {ev['lnK']:.4f}   (log10 K = {ev['log10K']:.4f})")
    print(f"                {ev['favourability']['label']}: {ev['favourability']['text']}")
    for w in rxn.range_warnings(args.T):
        print(f"  {w['level']}: {w['message']}")
    if args.P is not None:
        out = reaction_at_pressure(rxn, args.T, args.P, args.model)
        print(f"\n  At {args.T:g} K and {args.P:g} bar ({out['model_name']}), pure species at T and P")
        if out["gas_phase_valid"]:
            print(f"                sum nu*H^R = {out['sum_HR']:>12,.1f} J/mol")
            print(f"                dH(T,P)    = {out['dH_P']:>12,.1f} J/mol")
            print(f"                dG(T,P)    = {out['dG_P']:>12,.1f} J/mol")
        else:
            print(f"                no gas-phase value: {', '.join(out['no_vapour_species'])} "
                  f"has only a liquid root at these conditions")
        for note in out["notes"]:
            if note["level"] != "info":
                print(f"  {note['level']}: {note['message']}")
    print()


def _validate() -> int:
    rows = benchmarks.build()
    for r in rows:
        mark = "PASS" if r["passed"] else "FAIL"
        got = "error" if r["computed"] is None else f"{r['computed']:.6g}"
        print(f"  {mark}  {r['description']:<78} book {r['expected']:<12g} solver {got}")
    s = benchmarks.summary(rows)
    print(f"\n  {s['passed']} of {s['total']} textbook values reproduced.\n")
    return 0 if s["passed"] == s["total"] else 1


def main(argv=None) -> int:
    # Reaction arrows and Greek letters must not crash a console that is not UTF-8.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(prog="python -m thermosolver",
                                     description="Thermodynamic reaction energy solver (SVN data).")
    parser.add_argument("reaction", nargs="?", help='for example "CH4 + 2 O2 -> CO2 + 2 H2O(g)"')
    parser.add_argument("--T", type=float, default=T0, help="temperature in K (default 298.15)")
    parser.add_argument("--P", type=float, default=None, help="pressure in bar: adds the real-gas pressure effect")
    parser.add_argument("--model", default="pr", choices=list(MODEL_NAMES), help="real-gas model (default pr)")
    parser.add_argument("--validate", action="store_true", help="run the textbook benchmarks")
    args = parser.parse_args(argv)
    if args.validate:
        return _validate()
    if not args.reaction:
        parser.print_help()
        return 2
    try:
        _print_reaction(args)
    except SolverError as exc:
        print(f"\n  {exc.kind}: {exc.message}\n", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
