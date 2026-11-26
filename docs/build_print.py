"""Print the study guide and the presentation script as PDF files.

    python docs/build_print.py

Writes docs/STUDY_GUIDE.pdf and docs/PRESENTATION_SCRIPT.pdf from the Markdown
files next to them. The Markdown is turned into HTML with the same reader as
the guide page (build_guide.body), then Microsoft Edge prints it to PDF, so
this needs Windows with Edge installed. Run it again after editing either file.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_guide import body  # noqa: E402

DOCS = Path(__file__).resolve().parent
FILES = ("STUDY_GUIDE", "PRESENTATION_SCRIPT")
EDGE = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: Calibri, "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.42; color: #1f2937; }
h1 { font-family: Cambria, Georgia, serif; font-size: 20pt; color: #16233a; margin: 0 0 10pt; }
h2 { font-family: Cambria, Georgia, serif; font-size: 14pt; color: #16233a; margin: 16pt 0 6pt;
     padding-bottom: 3pt; border-bottom: 1.5pt solid #c2410c; break-after: avoid; }
h3 { font-size: 11.5pt; color: #16233a; margin: 11pt 0 4pt; break-after: avoid; }
p { margin: 0 0 6pt; }
ul, ol { margin: 0 0 6pt; padding-left: 18pt; }
li { margin-bottom: 2pt; }
em { color: #0b5cad; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; background: #eef2f7; padding: 0 2pt; }
pre.formula { font-family: Cambria, "Cambria Math", serif; font-size: 11pt; background: #eef2f7;
              border-left: 3pt solid #16233a; padding: 5pt 9pt; margin: 4pt 0 8pt; white-space: pre-wrap;
              break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 9pt; font-size: 9.5pt; break-inside: auto; }
tr { break-inside: avoid; }
th { background: #16233a; color: #fff; text-align: left; padding: 3pt 5pt; }
td { border-bottom: 0.6pt solid #c9d6e8; padding: 3pt 5pt; vertical-align: top; }
hr { border: 0; border-top: 0.8pt solid #c9d6e8; margin: 12pt 0; }
a { color: #0b5cad; text-decoration: none; }
"""


def italics(html: str) -> str:
    """*text* to <em>text</em>, outside the formula blocks (where * never appears anyway)."""
    parts = re.split(r"(<pre.*?</pre>)", html, flags=re.DOTALL)
    for k in range(0, len(parts), 2):
        parts[k] = re.sub(r"(?<![\w*])\*([^\s*][^*\n]*?)\*(?![\w*])", r"<em>\1</em>", parts[k])
    return "".join(parts)


def page(markdown: str) -> str:
    title, article, _ = body(markdown)
    article = article.replace("<p>---</p>", "<hr>")
    article = italics(article)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
            f"<style>{CSS}</style></head><body><h1>{title}</h1>\n{article}\n</body></html>")


def edge() -> str:
    for path in EDGE:
        if os.path.exists(path):
            return path
    sys.exit("Microsoft Edge not found; open the .md files instead.")


def main() -> None:
    exe = edge()
    with tempfile.TemporaryDirectory() as tmp:
        for name in FILES:
            markdown = (DOCS / f"{name}.md").read_text(encoding="utf-8")
            source = Path(tmp) / f"{name}.html"
            source.write_text(page(markdown), encoding="utf-8")
            target = DOCS / f"{name}.pdf"
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            f"--user-data-dir={Path(tmp) / 'edge'}", f"--print-to-pdf={target}", source.as_uri()],
                           check=True, timeout=120, capture_output=True)
            print("wrote", target)


if __name__ == "__main__":
    main()
