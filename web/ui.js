/* Shared helpers: the calculation engine (web worker), formatting and plots.
 * No thermodynamics lives in JavaScript; this file only talks to the Python
 * solver and draws what it returns.
 */
"use strict";

const TS = {};

/* -------------------------------------------------------------- fresh page */
/* GitHub Pages lets a browser keep index.html for up to 10 minutes, so right after an update a visitor
 * can still get the old page. Ask the server for the current index.html, past every cache, and reload
 * once if it names a newer release (the ?v= tag) than the page on screen. */
TS.reloadIfOutdated = async () => {
  const tag = (html) => (html.match(/web\/ui\.js\?v=([\w.]+)/) || [])[1];
  const mine = tag(document.documentElement.innerHTML);
  if (!mine || !window.fetch || location.protocol === "file:") return;
  try {
    const res = await fetch(`${location.pathname}?fresh=${Date.now()}`, { cache: "no-store" });
    const live = res.ok ? tag(await res.text()) : null;
    if (!live || live === mine) return;
    // Reload at most once for each release, so a cache that still answers with the old page cannot loop.
    if (sessionStorage.getItem("ts-reloaded-for") === live) return;
    sessionStorage.setItem("ts-reloaded-for", live);
    location.reload();
  } catch (err) {
    // offline, or storage blocked: keep the page that is on screen
  }
};

/* ------------------------------------------------------------------ engine */
TS.Engine = class {
  constructor(onStatus) {
    this.pending = new Map();
    this.nextId = 1;
    this.onStatus = onStatus;
    this.ready = new Promise((resolve, reject) => {
      this._resolve = resolve;
      this._reject = reject;
    });
    this.ready.catch(() => {});
    try {
      this.worker = new Worker("web/worker.js?v=1.8.12");
    } catch (err) {
      this._fail(`This browser could not start the calculation engine (${err}). ` +
        "Open the page through a web server (http://…), not directly from a file.");
      return;
    }
    this.worker.onmessage = (event) => this._onMessage(event.data);
    this.worker.onerror = (event) => this._fail(event.message || "The calculation engine could not start.");
  }

  _fail(message) {
    this.failed = message;
    this.onStatus("failed", message);
    this._reject(new Error(message));
    for (const { reject } of this.pending.values()) reject(new Error(message));
    this.pending.clear();
  }

  _onMessage(msg) {
    if (msg.type === "status") {
      this.onStatus("loading", msg.message);
    } else if (msg.type === "ready") {
      this.onStatus("ready", "Solver ready");
      this._resolve();
    } else if (msg.type === "failed") {
      this._fail(`The solver could not load: ${msg.message}. Check the internet connection and reload.`);
    } else if (msg.type === "result") {
      const entry = this.pending.get(msg.id);
      if (!entry) return;
      this.pending.delete(msg.id);
      let out;
      try {
        out = JSON.parse(msg.text);
      } catch (err) {
        entry.reject(new Error("The solver returned an unreadable answer."));
        return;
      }
      if (out.ok) {
        entry.resolve(out.result);
      } else {
        const error = new Error(out.error.message);
        error.kind = out.error.kind;
        error.details = out.error.details || {};
        entry.reject(error);
      }
    }
  }

  call(endpoint, payload) {
    if (this.failed) return Promise.reject(new Error(this.failed));
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ id, endpoint, payload: payload || {} });
    });
  }
};

/* -------------------------------------------------------------- formatting */
TS.$ = (selector, root = document) => root.querySelector(selector);
TS.$$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

TS.esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* CH4(g) -> CH<sub>4</sub>(g): subscript the digits that follow an element
 * symbol (capital letter, optional lower-case letter) or a closing bracket.
 * Plain prose such as "1e3" or "at 298 K" is left alone. */
TS.chem = (text) => TS.esc(text).replace(/([A-Z][a-z]?|\))(\d+)/g, "$1<sub>$2</sub>");

TS.fix = (x, digits = 2) => {
  if (x === null || x === undefined || !Number.isFinite(x)) return "–";
  return x.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
};
TS.kJ = (x, digits = 2) => (x === null || x === undefined ? "–" : TS.fix(x / 1000, digits));
TS.int = (x) => (x === null || x === undefined ? "–" : Math.round(x).toLocaleString("en-US"));

TS.sig = (x, digits = 4) => {
  if (x === null || x === undefined || !Number.isFinite(x)) return "–";
  if (x === 0) return "0";
  const a = Math.abs(x);
  if (a >= 1e-3 && a < 1e5) return String(Number(x.toPrecision(digits)));
  const [m, e] = x.toExponential(digits - 1).split("e");
  return `${m} × 10<sup>${Number(e)}</sup>`;
};

/* K from ln K, also when K itself overflows a double */
TS.fmtK = (lnK) => {
  if (lnK === null || lnK === undefined) return "–";
  const log10 = lnK / Math.LN10;
  if (Math.abs(log10) < 300) return TS.sig(Math.exp(lnK), 4);
  return `10<sup>${log10.toFixed(0)}</sup>`;
};

TS.signed = (x, digits = 2) => (x > 0 ? "+" : "") + TS.fix(x, digits);
TS.pct = (x, digits = 1) => (x === null || x === undefined ? "–" : TS.fix(100 * x, digits) + " %");
TS.coeff = (x) => {
  const a = Math.abs(x);
  if (Math.abs(a - Math.round(a)) < 1e-9) return String(Math.round(a));
  for (const d of [2, 3, 4, 5, 6, 8]) {
    if (Math.abs(a * d - Math.round(a * d)) < 1e-9) return `${Math.round(a * d)}/${d}`;
  }
  return String(Number(a.toPrecision(4)));
};

TS.readNumber = (id) => {
  const raw = TS.$("#" + id).value.trim();
  if (raw === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : raw;   // let the solver report bad text
};

/* ---------------------------------------------------------------- messages */
TS.message = (level, html) => `<div class="msg ${level}">${html}</div>`;

TS.errorBox = (err) => {
  let html = `<strong>${TS.esc(TS.errorTitle(err.kind))}</strong> ${TS.esc(err.message)}`;
  const suggestions = err.details && err.details.suggestions;
  if (Array.isArray(suggestions) && suggestions.length) {
    html += `<br>Closest species in the database: ${suggestions.map((s) => `<code>${TS.esc(s)}</code>`).join(" ")}`;
  }
  return TS.message("error", html);
};

TS.errorTitle = (kind) => ({
  unbalanced_reaction: "Reaction rejected.",
  unknown_species: "Unknown species.",
  input_error: "Check the input.",
  data_unavailable: "Data not available in SVN.",
  phase_error: "Not a gas at these conditions.",
  convergence_error: "No answer found.",
  internal_error: "Solver error.",
  engine_error: "Engine error.",
}[kind] || "Error.");

TS.notes = (list) => (list || []).map((n) => {
  const level = n.level === "info" ? "info" : (n.level === "error" ? "error" : "warning");
  const label = level === "info" ? "Note" : (level === "error" ? "Error" : "Warning");
  return TS.message(level, `<strong>${label}:</strong> ${TS.chem(n.message)}`);
}).join("");

/* ------------------------------------------------------------------- plots */
TS.css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

TS.palette = () => ["#0b5cad", "#c2410c", "#11734b", "#7c3aed", "#b45309", "#0e7490", "#be185d", "#4d7c0f",
  "#475569", "#b91c1c", "#1d4ed8", "#a16207"];

TS.layout = (title, xTitle, yTitle, extra = {}) => {
  const ink = TS.css("--ink");
  const line = TS.css("--line");
  const base = {
    title: { text: title, font: { family: TS.css("--display") || "system-ui", size: 17, color: ink }, x: 0.02, xanchor: "left" },
    margin: { l: 64, r: 18, t: 44, b: 48 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: TS.css("--sans") || "system-ui", size: 12, color: ink },
    xaxis: { title: { text: xTitle }, gridcolor: line, zerolinecolor: line, linecolor: line, automargin: true },
    yaxis: { title: { text: yTitle }, gridcolor: line, zerolinecolor: TS.css("--muted"), linecolor: line, automargin: true },
    legend: { orientation: "h", y: -0.22, x: 0, font: { size: 11 } },
    hovermode: "x unified",
    colorway: TS.palette(),
  };
  return Object.assign(base, extra, {
    xaxis: Object.assign(base.xaxis, extra.xaxis || {}),
    yaxis: Object.assign(base.yaxis, extra.yaxis || {}),
  });
};

TS.plot = (id, traces, layout) => {
  const el = document.getElementById(id);
  if (!el || typeof Plotly === "undefined") {
    if (el) el.innerHTML = TS.message("warning", "The plotting library could not be loaded (no internet?). Numbers above are unaffected.");
    return;
  }
  Plotly.react(el, traces, layout, { responsive: true, displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"] });
};

/* grey band over the part of a temperature axis outside the Cp validity range */
TS.rangeShapes = (xs, range) => {
  if (!range || !xs.length) return [];
  const shapes = [];
  const lo = xs[0];
  const hi = xs[xs.length - 1];
  const band = (x0, x1) => ({ type: "rect", xref: "x", yref: "paper", x0, x1, y0: 0, y1: 1,
    fillcolor: "rgba(160,120,0,0.13)", line: { width: 0 }, layer: "below" });
  if (lo < range[0]) shapes.push(band(lo, Math.min(range[0], hi)));
  if (hi > range[1]) shapes.push(band(Math.max(range[1], lo), hi));
  return shapes;
};

TS.vline = (x, color) => ({ type: "line", xref: "x", yref: "paper", x0: x, x1: x, y0: 0, y1: 1,
  line: { color: color || TS.css("--muted"), width: 1, dash: "dot" } });

TS.hline = (y, color) => ({ type: "line", xref: "paper", yref: "y", x0: 0, x1: 1, y0: y, y1: y,
  line: { color: color || TS.css("--muted"), width: 1, dash: "dot" } });

/* One axis range for several graphs, so that their values can be compared at a glance:
 * the smallest range that holds every number of every list (and the extra values,
 * such as 0), with a small margin. Display only; it changes no result. */
TS.span = (lists, extra = [], margin = 0.06) => {
  let lo = Infinity;
  let hi = -Infinity;
  for (const list of lists) {
    for (const v of list) {
      if (v === null || !Number.isFinite(v)) continue;
      lo = Math.min(lo, v);
      hi = Math.max(hi, v);
    }
  }
  if (!Number.isFinite(lo)) return null;
  for (const v of extra) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const width = hi - lo || Math.abs(hi) || 1;
  return [lo - margin * width, hi + margin * width];
};

/* The x axis of a graph covers only where it has data (the user's request of 23 November 2026):
 * from the first to the last x at which at least one of the series has a value. Null when
 * no series has two points, so the caller can fall back to the plot's own range. */
TS.xExtent = (x, series) => {
  let lo = Infinity;
  let hi = -Infinity;
  x.forEach((v, i) => {
    if (series.some((ys) => ys && ys[i] !== null && ys[i] !== undefined && Number.isFinite(ys[i]))) {
      lo = Math.min(lo, v);
      hi = Math.max(hi, v);
    }
  });
  return Number.isFinite(lo) && hi > lo ? [lo, hi] : null;
};

/* An axis object for Plotly from a range, or nothing when there is none. */
TS.axis = (range) => (range ? { range } : {});

/* A plot with one line underneath that says how to read it. */
TS.fig = (id, caption, cls = "") => `<figure class="fig"><div id="${id}" class="plot ${cls}"></div>
  <figcaption><strong>How to read it:</strong> ${caption}</figcaption></figure>`;

/* ------------------------------------------------------- shared UI pieces */
TS.tabs = [{ id: "home", init() {}, onShow() {} }];   // each tab file registers { id, init, onShow }

/* Fill a <select> with the predefined reactions, grouped by category, and keep
 * it in sync with a free-text input. */
TS.fillReactionSelect = (select, input, options = {}) => {
  const groups = new Map();
  for (const rxn of TS.library.reactions) {
    if (options.filter && !options.filter(rxn)) continue;
    if (!groups.has(rxn.category)) groups.set(rxn.category, []);
    groups.get(rxn.category).push(rxn);
  }
  let html = `<option value="">Custom reaction (type it on the right)</option>`;
  for (const [category, list] of groups) {
    html += `<optgroup label="${TS.esc(category)}">` +
      list.map((r) => `<option value="${TS.esc(r.id)}">${TS.esc(r.name)}</option>`).join("") + "</optgroup>";
  }
  select.innerHTML = html;
  select.addEventListener("change", () => {
    const rxn = TS.library.reactions.find((r) => r.id === select.value);
    if (!rxn) return;
    input.value = rxn.equation;
    if (options.onPick) options.onPick(rxn);
  });
  input.addEventListener("input", () => { select.value = ""; });
};

TS.pickReaction = (select, input, id, onPick) => {
  const rxn = TS.library.reactions.find((r) => r.id === id);
  if (!rxn) return;
  select.value = id;
  input.value = rxn.equation;
  if (onPick) onPick(rxn);
};

/* Run an async calculation with a busy button and uniform error display. */
TS.run = async (button, out, task) => {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "Calculating…";
  try {
    await task();
  } catch (err) {
    out.innerHTML = TS.errorBox(err);
    const fix = err.details && err.details.suggestion;
    if (fix && out.dataset.input) {
      const box = document.createElement("div");
      box.className = "msg info";
      box.innerHTML = `Balanced form: <span class="mono">${TS.chem(fix)}</span> &nbsp;`;
      const use = document.createElement("button");
      use.className = "link";
      use.textContent = "Use this";
      use.addEventListener("click", () => {
        const input = document.getElementById(out.dataset.input);
        input.value = fix;
        input.dispatchEvent(new Event("input"));
        button.click();
      });
      box.appendChild(use);
      out.appendChild(box);
    }
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
};

TS.auditTable = (checks) => {
  if (!checks || !checks.length) return "";
  const passed = checks.filter((c) => c.passed).length;
  const rows = checks.map((c) => `<tr>
      <td class="l">${TS.chem(c.name)}</td><td class="l mono">${TS.esc(c.relation)}</td>
      <td>${TS.sig(c.lhs, 7)}</td><td>${TS.sig(c.rhs, 7)}</td><td>${TS.sig(c.rel_error, 2)}</td>
      <td class="${c.passed ? "pass" : "fail"}">${c.passed ? "pass" : "FAIL"}</td></tr>`).join("");
  return `<details><summary>Consistency checks: ${passed} of ${checks.length} passed</summary>
    <p class="hint">Each result is worked out a second time by an independent route (a numerical slope or a numerical integration).
      A wrong formula, sign or unit would make at least one of these checks fail.</p>
    <div class="table-scroll"><table><thead><tr><th class="l">Check</th><th class="l">What must be equal</th><th>Left side</th>
      <th>Right side</th><th>Relative error</th><th>Result</th></tr></thead><tbody>${rows}</tbody></table></div></details>`;
};

/* ---------------------------------------------------------- live controls */
/* A slider is a number box (id) and a range input (id + "-r") that mirror each
 * other. The number box is the value that is sent to the solver, so a typed
 * value may lie outside the track. onInput fires while dragging, onChange
 * when the user lets go or finishes typing. */
TS.bindSlider = (id, onInput, onChange) => {
  const box = TS.$("#" + id);
  const range = TS.$("#" + id + "-r");
  range.addEventListener("input", () => { box.value = range.value; onInput(); });
  range.addEventListener("change", () => onChange());
  box.addEventListener("input", () => {
    const value = Number(box.value);
    if (box.value !== "" && Number.isFinite(value)) range.value = value;
  });
  box.addEventListener("change", () => onChange());
  box.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); onChange(); } });
};

TS.setSlider = (id, value, limits) => {
  const range = TS.$("#" + id + "-r");
  if (limits) { range.min = limits[0]; range.max = limits[1]; range.step = limits[2] || 1; }
  if (Number(value) > Number(range.max)) range.max = value;      // widen the track for a preset outside it
  if (Number(value) < Number(range.min)) range.min = value;
  TS.$("#" + id).value = value;
  range.value = value;
};

/* Only one call in flight; while it runs, the newest request is remembered and
 * run next. Dragging a slider therefore never queues stale calculations. */
TS.latest = (task) => {
  let busy = false;
  let waiting = null;
  const run = async (arg) => {
    if (busy) { waiting = { arg }; return; }
    busy = true;
    try {
      await task(arg);
    } finally {
      busy = false;
      if (waiting) { const next = waiting.arg; waiting = null; run(next); }
    }
  };
  return run;
};

/* Segmented control: buttons with a data attribute, one of them "on". */
TS.bindSeg = (id, attribute, onPick) => {
  const root = TS.$("#" + id);
  const set = (value) => {
    for (const b of TS.$$("button", root)) {
      const on = b.dataset[attribute] === value;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    }
  };
  for (const b of TS.$$("button", root)) {
    b.addEventListener("click", () => { set(b.dataset[attribute]); onPick(b.dataset[attribute]); });
  }
  const current = TS.$("button.on", root);
  if (current) set(current.dataset[attribute]);
  return { set, get: () => (TS.$("button.on", root) || {}).dataset?.[attribute] };
};

/* The same species keeps the same colour in every bar and plot. */
TS.colorOf = (() => {
  const seen = new Map();
  return (key) => {
    if (!seen.has(key)) seen.set(key, TS.palette()[seen.size % TS.palette().length]);
    return seen.get(key);
  };
})();

/* Horizontal bars that are updated in place (so the widths glide) as long as
 * the same rows are shown. rows: [{ key, label (html), percent, text, color }] */
TS.updateBars = (container, rows) => {
  const width = (p) => `${Math.max(0, Math.min(100, p)).toFixed(2)}%`;
  const keys = rows.map((r) => r.key).join("|");
  if (container.dataset.keys === keys) {
    const fills = TS.$$(".fill", container);
    const nums = TS.$$(".num", container);
    rows.forEach((r, i) => { fills[i].style.width = width(r.percent); nums[i].innerHTML = r.text; });
    return;
  }
  container.dataset.keys = keys;
  container.innerHTML = `<div class="bars">${rows.map((r) => `<span class="lab">${r.label}</span>
    <span class="track"><span class="fill" style="width:${width(r.percent)};background:${r.color}"></span></span>
    <span class="num">${r.text}</span>`).join("")}</div>`;
};

/* ------------------------------------------------------------------- theme */
TS.theme = {
  current() {
    return document.documentElement.dataset.theme ||
      (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  },
  set(mode) {
    document.documentElement.dataset.theme = mode;
    try { localStorage.setItem("ts-theme", mode); } catch (err) { /* private mode: not remembered */ }
    TS.theme.repaint();
  },
  /* Plots take their colours from the page when they are drawn; restyle the ones on screen. */
  repaint() {
    if (typeof Plotly === "undefined") return;
    const ink = TS.css("--ink");
    const line = TS.css("--line");
    const muted = TS.css("--muted");
    for (const el of TS.$$(".js-plotly-plot")) {
      Plotly.relayout(el, {
        "font.color": ink, "title.font.color": ink,
        "xaxis.gridcolor": line, "yaxis.gridcolor": line, "xaxis.linecolor": line, "yaxis.linecolor": line,
        "xaxis.zerolinecolor": line, "yaxis.zerolinecolor": muted,
      });
    }
  },
};

/* ------------------------------------------------------------- glossary */
/* A small "i" next to the label of a result card opens a one-line explanation
 * in plain words. The first entry whose pattern matches the label is used. */
TS.GLOSSARY = [
  [/^Residual part|^Σ ν H/, "Residual part of the heat of reaction",
    "At high pressure gas molecules attract each other, so a real gas holds a little less enthalpy than an ideal gas. This is that difference, added up over the reaction."],
  [/^Residual entropy/, "Residual part of the entropy change",
    "The entropy of the real gas minus the entropy of the ideal gas at the same temperature and pressure, added up over the reaction. Attraction between molecules orders a gas a little, so it is usually negative for a dense gas."],
  [/^ΔH\(T,P\)/, "Heat of reaction of the real gas",
    "The ideal-gas heat of reaction plus the residual part. This is the value that holds at your pressure."],
  [/^ΔH°298|Heat of reaction at 298/, "Heat of reaction at 298.15 K",
    "Heat the reaction gives out (negative) or takes in (positive) at 25 °C and 1 bar. It comes straight from the heats of formation in the textbook table. 298.15 K is the reference temperature of that table; the standard state (the ° sign) only fixes the pressure at 1 bar."],
  [/^ΔH°/, "Standard heat of reaction at your temperature",
    "The heat of reaction at 298.15 K, corrected to your temperature with the heat capacities of all the species. It is still a standard value: the standard state fixes the pressure at 1 bar, and the temperature can be any."],
  [/^ΔS/, "Entropy change",
    "The change in disorder. It is positive when the reaction makes more gas molecules and negative when it makes fewer."],
  [/^ΔG/, "Gibbs energy change",
    "ΔG = ΔH − T·ΔS. A negative value means the products are favoured. A positive value means the reactants are favoured; some product still forms, only less."],
  [/^Heating value/, "Heating value",
    "Heat released by burning 1 kg of the fuel. Lower: the water leaves as vapour. Higher: the water is condensed, so its latent heat is collected too."],
  [/^Calorific value/, "Calorific value",
    "Heat released per kilogram when the sample burns in the closed bomb. The volume is fixed, so this is −ΔU with the water formed as liquid."],
  [/^Calorimeter constant/, "Calorimeter constant",
    "The heat that warms the whole calorimeter by 1 °C. It is found by burning a standard whose calorific value is known."],
  [/^Heat taken up/, "Heat taken up by the calorimeter",
    "Calorimeter constant times the temperature rise. It equals the heat released by the sample plus the thread and wire."],
  [/^Moles of gas/, "Moles of gas",
    "Total amount of gas at equilibrium. It is smaller than the feed when the reactions make fewer molecules."],
];

TS.glossarize = (root) => {
  for (const label of TS.$$(".card .k", root)) {
    if (label.querySelector(".term-btn")) continue;
    const text = label.textContent.trim();
    const index = TS.GLOSSARY.findIndex(([pattern]) => pattern.test(text));
    if (index < 0) continue;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "term-btn";
    button.textContent = "i";
    button.dataset.term = String(index);
    button.setAttribute("aria-label", `What does "${TS.GLOSSARY[index][1]}" mean?`);
    label.appendChild(button);
  }
};

/* One shared pop-up, placed under the button that opened it. */
TS.watchTerms = () => {
  const pop = document.createElement("div");
  pop.className = "term-pop";
  pop.hidden = true;
  pop.setAttribute("role", "tooltip");
  document.body.appendChild(pop);
  let opener = null;
  const close = () => { pop.hidden = true; opener = null; };
  document.addEventListener("click", (event) => {
    const button = event.target.closest ? event.target.closest(".term-btn[data-term]") : null;
    if (!button) { if (!pop.contains(event.target)) close(); return; }
    if (opener === button) { close(); return; }
    const [, title, text] = TS.GLOSSARY[Number(button.dataset.term)];
    pop.innerHTML = `<strong>${TS.esc(title)}</strong><span>${TS.esc(text)}</span>`;
    pop.hidden = false;
    const box = button.getBoundingClientRect();
    const width = Math.min(320, window.innerWidth - 24);
    pop.style.width = `${width}px`;
    pop.style.left = `${Math.max(12, Math.min(box.left + window.scrollX - 12, window.scrollX + window.innerWidth - width - 12))}px`;
    pop.style.top = `${box.bottom + window.scrollY + 8}px`;
    opener = button;
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(); });
  window.addEventListener("resize", close);

  // Result cards are redrawn all the time; add the buttons whenever they appear.
  const main = TS.$("main");
  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    setTimeout(() => { queued = false; TS.glossarize(main); }, 0);     // a timer: hidden tabs get no animation frames
  }).observe(main, { childList: true, subtree: true });
  TS.glossarize(main);
};

window.TS = TS;
