"""Build guide.html (the hosted beginner's guide) from docs/LEARNERS_GUIDE.md.

    python docs/build_guide.py

The Markdown file is the single source. Only the small subset of Markdown that
the guide uses is understood: headings (#, ##, ###), paragraphs, bullet and
numbered lists, tables, indented formula blocks, **bold**, `code` and links.
A test rebuilds the page and compares it with the committed file, so the two
cannot drift apart.
"""

from __future__ import annotations

import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "docs", "LEARNERS_GUIDE.md")
TARGET = os.path.join(ROOT, "guide.html")


def site_version() -> str:
    """The ?v= tag the page uses, so the guide loads the same stylesheet."""
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as fh:
        return re.search(r'href="web/styles\.css\?v=([^"]+)"', fh.read()).group(1)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def cells(line: str):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def body(markdown: str):
    """Return (title, html of the article, [(id, text) of every section])."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    out, sections, title = [], [], ""
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("# "):
            title = line[2:].strip()
            i += 1
        elif line.startswith("## "):
            text = line[3:].strip()
            sections.append((slug(text), text))
            out.append(f'<h2 id="{slug(text)}">{inline(text)}</h2>')
            i += 1
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
            i += 1
        elif line.startswith("    "):
            block = []
            while i < n and lines[i].startswith("    "):
                block.append(html.escape(lines[i][4:], quote=False))
                i += 1
            out.append('<pre class="formula">' + "\n".join(block) + "</pre>")
        elif line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            head, rest = rows[0], rows[2:]                  # rows[1] is the |---|---| line
            out.append('<div class="table-scroll"><table><thead><tr>'
                       + "".join(f'<th class="l">{inline(c)}</th>' for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f'<td class="l wrapcell">{inline(c)}</td>' for c in row) + "</tr>"
                                 for row in rest) + "</tbody></table></div>")
        elif line.startswith("- ") or re.match(r"\d+\. ", line):
            ordered = not line.startswith("- ")
            pattern = r"\d+\. " if ordered else r"- "
            items = []
            while i < n and re.match(pattern, lines[i]):
                items.append(re.sub("^" + pattern, "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in items) + f"</{tag}>")
        else:
            para = []
            while i < n and lines[i].strip() and not re.match(r"(#{1,3} |\||- |\d+\. |    )", lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
    return title, "\n".join(out), sections


def render(markdown: str, version: str) -> str:
    title, article, sections = body(markdown)
    toc = "\n".join(f'        <li><a href="#{sid}">{inline(text)}</a></li>' for sid, text in sections)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · Thermodynamic Reaction Energy Solver</title>
  <meta name="description" content="The Thermodynamic Reaction Energy Solver explained in plain words: the ideas behind it, each tab, why the numbers can be trusted, and questions to check yourself.">
  <!-- Built from docs/LEARNERS_GUIDE.md by docs/build_guide.py. Edit the Markdown, not this file. -->
  <script>
    try {{ const t = localStorage.getItem("ts-theme"); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; }} catch (e) {{}}
  </script>
  <link rel="stylesheet" href="web/styles.css?v={version}">
</head>
<body>
<header class="top">
  <div class="wrap top-row">
    <div class="brand">
      <div class="mark" aria-hidden="true">ΔH</div>
      <div>
        <h1>{html.escape(title)}</h1>
        <p class="sub">Thermodynamic Reaction Energy Solver, explained in plain words.</p>
      </div>
    </div>
    <div class="top-tools">
      <button id="theme" class="icon-btn" type="button" aria-label="Switch between light and dark">Dark</button>
      <a class="icon-btn solid" href="index.html">Open the solver</a>
    </div>
  </div>
</header>

<main class="wrap guide">
  <nav class="toc" aria-label="Sections of the guide">
    <div class="toc-title">In this guide</div>
    <ol>
{toc}
    </ol>
  </nav>
  <article class="panel prose">
{article}
  </article>
</main>

<footer class="wrap foot">
  <p>Data and equations: Smith, Van Ness &amp; Abbott, <em>Introduction to Chemical Engineering Thermodynamics</em>.
    <a href="index.html">Back to the solver</a>.</p>
</footer>
<script>
  (() => {{
    const root = document.documentElement;
    const button = document.getElementById("theme");
    const current = () => root.dataset.theme || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const label = () => {{ button.textContent = current() === "dark" ? "Light" : "Dark"; }};
    button.addEventListener("click", () => {{
      const next = current() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {{ localStorage.setItem("ts-theme", next); }} catch (e) {{}}
      label();
    }});
    label();
  }})();
</script>
</body>
</html>
"""


def main() -> None:
    with open(SOURCE, encoding="utf-8") as fh:
        page = render(fh.read(), site_version())
    with open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print("wrote", TARGET)


if __name__ == "__main__":
    main()
