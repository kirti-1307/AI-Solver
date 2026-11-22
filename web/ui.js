/* Shared helpers: the calculation engine (web worker), formatting and plots.
 * No thermodynamics lives in JavaScript; this file only talks to the Python
 * solver and draws what it returns.
 */
"use strict";

const TS = {};

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
      this.worker = new Worker("web/worker.js?v=1.1.2");
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
  convergence_error: "No convergence.",
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
    title: { text: title, font: { size: 14, color: ink }, x: 0.02, xanchor: "left" },
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

/* ------------------------------------------------------- shared UI pieces */
TS.tabs = [];          // each tab file registers { id, init, onShow }

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
  return `<details><summary>Consistency audit: ${passed} of ${checks.length} identities satisfied</summary>
    <p class="hint">Each result is re-derived by an independent route (numerical derivative or quadrature).
      A wrong formula, sign or unit would break at least one of these.</p>
    <div class="table-scroll"><table><thead><tr><th class="l">Check</th><th class="l">Identity</th><th>Left side</th>
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

window.TS = TS;
