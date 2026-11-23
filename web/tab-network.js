/* Tab 4 (extra feature 1): equilibrium of competing reactions (the mixture with
 * the lowest total Gibbs energy), as a live reactor.
 *
 * Not shown on the page at the user's request (23 November 2026), but still in the
 * solver's answer: the method line, the mixture as a table of numbers, and the
 * solid-carbon test along the plot (sweep.carbon_activity).
 *
 * Two kinds of request go to the solver: a single point (while a slider is
 * being dragged) and the same point with a sweep for the plots (when the user
 * lets go). The page itself calculates nothing.
 */
"use strict";
(() => {
  const { $, $$, esc, chem, fix, sig, pct } = TS;

  let system = [];          // species shown as switches: the preset's, plus any the user ticked
  let ratioPair = null;     // { top, bottom, base } when exactly two species are fed
  let lastSweep = null;     // "T" or "P" of the plots on screen
  let switchInfo = {};      // species id -> what the solver says its switch would change (last result)
  let tour = [];            // guided steps of the example on screen
  let tourStep = null;      // index of the step that is active, or null
  let pending = null;       // what to say once the next result is in: a tour step or a flipped switch

  const chips = () => $$("#nw-species .chip");
  const parts = (chip) => chip.querySelectorAll("input");   // [tick box, feed]

  /* ------------------------------------------------------------ species grid */
  function buildChips() {
    const gases = TS.database.species.filter((s) => s.phase === "g");
    $("#nw-species").innerHTML = gases.map((s, i) => `<div class="chip off" data-id="${esc(s.id)}">
        <input type="checkbox" id="nw-allow-${i}">
        <label for="nw-allow-${i}" title="${esc(s.name)}">${chem(s.id)} <span class="dim">${esc(s.name)}</span></label>
        <input type="number" step="any" min="0" value="" placeholder="feed" aria-label="Feed of ${esc(s.id)} in mol">
      </div>`).join("");
    for (const chip of chips()) {
      const [box, feed] = parts(chip);
      box.addEventListener("change", () => {
        chip.classList.toggle("off", !box.checked);
        if (!box.checked) feed.value = "";
        if (box.checked && !system.includes(chip.dataset.id)) system.push(chip.dataset.id);
        syncControls();
        full();
      });
      feed.addEventListener("change", () => { syncControls(); full(); });
      feed.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { syncControls(); full(); } });
    }
  }

  function readSystem() {
    const species = [];
    const feed = {};
    for (const chip of chips()) {
      const [box, feedInput] = parts(chip);
      if (!box.checked) continue;
      species.push(chip.dataset.id);
      const moles = Number(feedInput.value);
      if (feedInput.value.trim() !== "" && Number.isFinite(moles) && moles !== 0) feed[chip.dataset.id] = moles;
    }
    return { species, feed };
  }

  /* --------------------------------------------- switches and the feed ratio */
  function syncControls() {
    const { species, feed } = readSystem();
    const fed = Object.keys(feed).filter((s) => feed[s] > 0);

    $("#nw-switches").innerHTML = `<span class="cap">The catalyst may form:</span>` + system.map((sid) => {
      if (fed.includes(sid)) {
        return `<button type="button" class="switch locked" disabled title="Fed to the reactor"><span class="dot"></span><span>${chem(sid)} <small>feed</small></span></button>`;
      }
      const on = species.includes(sid);
      return `<button type="button" class="switch ${on ? "on" : "off"}" data-id="${esc(sid)}" aria-pressed="${on}"
        title="${on ? "Click to block this product" : "Click to allow this product"}"><span class="dot"></span><span>${chem(sid)} <small></small></span></button>`;
    }).join("");
    for (const button of $$("#nw-switches .switch[data-id]")) {
      button.addEventListener("click", () => {
        if (button.getAttribute("aria-disabled") === "true") return;      // faded or needed: nothing to flip
        const sid = button.dataset.id;
        const row = switchInfo[sid];
        pending = row ? { kind: "switch", sid, on: row.state === "off" } : null;
        setTourStep(null);
        const chip = chips().find((c) => c.dataset.id === sid);
        const [box] = parts(chip);
        box.checked = !box.checked;
        chip.classList.toggle("off", !box.checked);
        syncControls();
        full();
      });
    }
    paintSwitches();

    // A ratio slider makes sense when exactly two species are fed.
    if (fed.length === 2) {
      const [a, b] = fed;
      const top = feed[a] > feed[b] ? a : b;
      const bottom = top === a ? b : a;
      ratioPair = { top, bottom, base: feed[bottom] };
      $("#nw-ratio-name").innerHTML = `Feed ratio ${chem(top.replace(/\(g\)$/, ""))} : ${chem(bottom.replace(/\(g\)$/, ""))}`;
      TS.setSlider("nw-ratio", Number((feed[top] / feed[bottom]).toPrecision(4)), [0.2, 10, 0.05]);
      $("#nw-ratio-box").hidden = false;
    } else {
      ratioPair = null;
      $("#nw-ratio-box").hidden = true;
    }
  }

  /* What each switch would change, as the solver worked it out for the mixture on screen.
   * A switch that would change nothing is faded and cannot be clicked. */
  function paintSwitches() {
    const el = switchInfo.__element || "";
    for (const button of $$("#nw-switches .switch[data-id]")) {
      const sid = button.dataset.id;
      const row = switchInfo[sid];
      const small = button.querySelector("small");
      const on = button.classList.contains("on");
      button.classList.remove("idle", "locked");
      button.removeAttribute("aria-disabled");
      if (!row || (row.state === "on") !== on) { small.textContent = ""; continue; }   // result not in yet
      const holds = row.share !== null ? `${pct(row.share, 1)} of ${el}` : `y = ${sig(row.y, 3)}`;
      if (row.state === "off") {
        small.textContent = row.effect === "none" ? "off · no effect now" : "off";
        button.title = row.effect === "none" ? `Blocked. Allowing ${sid} would change nothing at these settings.`
          : `Blocked. Click to allow ${sid}.` +
            (row.share_if_flipped !== null ? ` It would take ${pct(row.share_if_flipped, 1)} of the ${el} atoms.` : "");
      } else if (row.effect === "needed") {
        small.textContent = "needed";
        button.classList.add("locked");
        button.setAttribute("aria-disabled", "true");
        button.title = `Without ${sid} nothing can react at these settings: the atoms would have nowhere to go.`;
      } else if (row.effect === "cannot_form") {
        small.textContent = "cannot form";
        button.classList.add("idle");
        button.setAttribute("aria-disabled", "true");
        button.title = `${sid} cannot form: the feed has none of an element it contains.`;
      } else if (row.effect === "none") {
        small.textContent = "no effect now";
        button.classList.add("idle");
        button.setAttribute("aria-disabled", "true");
        button.title = `Blocking ${sid} would change nothing: it holds ${holds} at these settings. The switch wakes up when that changes.`;
      } else {
        small.textContent = holds;
        button.title = `Click to block ${sid}. It holds ${holds} atoms now.`;
      }
    }
  }

  /* ------------------------------------------------------------ guided steps */
  function setTourStep(index) {
    tourStep = index;
    for (const button of $$("#nw-tour button")) button.classList.toggle("on", Number(button.dataset.step) === index);
  }

  function buildTour() {
    const box = $("#nw-tour");
    box.hidden = !tour.length;
    box.innerHTML = tour.length ? `<span class="cap">Try this:</span><div class="seg">` +
      tour.map((step, i) => `<button type="button" data-step="${i}">${i + 1}. ${esc(step.label)}</button>`).join("") + `</div>` : "";
    for (const button of $$("#nw-tour button")) {
      button.addEventListener("click", () => {
        const step = tour[Number(button.dataset.step)];
        const { feed } = readSystem();
        for (const chip of chips()) {
          const sid = chip.dataset.id;
          if (!system.includes(sid) || feed[sid] > 0) continue;
          const [box_] = parts(chip);
          box_.checked = !step.off.includes(sid);
          chip.classList.toggle("off", !box_.checked);
        }
        pending = { kind: "tour", say: step.say };
        setTourStep(Number(button.dataset.step));
        syncControls();
        full();
      });
    }
  }

  function say(html) { $("#nw-say").innerHTML = html; }

  function applyRatio() {
    if (!ratioPair) return;
    const ratio = Number($("#nw-ratio").value);
    if (!Number.isFinite(ratio) || ratio <= 0) return;
    const chip = chips().find((c) => c.dataset.id === ratioPair.top);
    parts(chip)[1].value = Number((ratio * ratioPair.base).toPrecision(6));
  }

  function loadPreset(id) {
    const preset = TS.library.networks.find((n) => n.id === id);
    if (!preset) return;
    for (const chip of chips()) {
      const [box, feed] = parts(chip);
      const sid = chip.dataset.id;
      box.checked = preset.species.includes(sid);
      chip.classList.toggle("off", !box.checked);
      feed.value = preset.feed[sid] !== undefined ? preset.feed[sid] : "";
    }
    system = preset.species.slice();
    switchInfo = {};
    pending = null;
    tour = preset.tour || [];
    buildTour();
    setTourStep(tour.length ? 0 : null);
    say("");
    const [lo, hi] = preset.T_range;
    // An example may name the temperature it opens at; otherwise the middle of its range.
    TS.setSlider("nw-T", preset.T !== undefined ? preset.T : Math.round((lo + hi) / 2), [Math.min(300, lo), Math.max(1500, hi), 1]);
    TS.setSlider("nw-P", preset.P, [1, 300, 1]);
    $("#nw-sweep").value = "T";
    $("#nw-min").value = lo;
    $("#nw-max").value = hi;
    $("#nw-note").textContent = preset.note || "";
    syncControls();
  }

  /* ------------------------------------------------------------- explanation */
  function explain(r) {
    const lines = [];
    const dist = r.atom_distribution;
    const el = r.key_element;
    const fedIds = Object.keys(r.feed).filter((s) => r.feed[s] > 0);
    const products = Object.keys(dist).filter((s) => !fedIds.includes(s)).sort((a, b) => dist[b] - dist[a]);
    if (products.length) {
      const top = products[0];
      lines.push(`At ${fix(r.T, 0)} K and ${fix(r.P, 1)} bar, ${pct(dist[top], 1)} of the ${esc(el)} atoms end up in ` +
        `<strong>${chem(top)}</strong>` + (products[1] ? `, then ${pct(dist[products[1]], 2)} in ${chem(products[1])}.` : "."));
    }
    if (r.carbon_activity !== null && r.carbon_activity !== undefined) {
      // The solver's number is above 1 when solid carbon would lower the total Gibbs energy. Only that yes or no is shown.
      const canForm = r.carbon_activity > 1;
      const blocked = system.filter((s) => !r.species.includes(s));
      lines.push("Solid carbon (soot): " + (canForm
        ? "making it from this gas would lower the total Gibbs energy further, so <strong>solid carbon can form</strong> at these conditions." +
          (blocked.length ? ` With ${blocked.map(chem).join(", ")} switched off the gas is held away from its full equilibrium, which makes this more likely. ` +
            "Solid carbon is then one more product that a selective catalyst has to avoid: the result says it is possible, not that it forms." : "")
        : "making it from this gas would raise the total Gibbs energy, so no solid carbon is expected from thermodynamics."));
      lines.push("How the solver decides: it takes the gas it found and a reaction that would make carbon from it, for example " +
        "2 CO → C(s) + CO<sub>2</sub>. It compares the K<sub>p</sub> of that reaction with the same ratio of partial pressures in the gas, " +
        "p<sub>CO2</sub>/p<sub>CO</sub><sup>2</sup> (solid carbon does not appear in it). If the gas ratio is smaller than K<sub>p</sub>, " +
        "the reaction can still go forward, so carbon can form. Every reaction that makes carbon gives the same answer, because the gas is already at equilibrium. " +
        "The gases here are real gases, so each partial pressure is first multiplied by exp(G<sup>R</sup>/RT) of its gas, the real-gas correction " +
        "from its equation of state (at 1 bar this factor is almost exactly 1).");
    }
    if (r.excluded.length) {
      lines.push(`Left out because the feed has none of their elements: ${r.excluded.map(chem).join(", ")}.`);
    }
    lines.push("This is the composition the system would reach with unlimited time and a catalyst that can make every species that is switched on. " +
      "Switch a product off to model a catalyst that cannot form it; the difference between the two answers is what catalyst selectivity has to fight against.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  /* ---------------------------------------------------------------- live view */
  function ensureLive() {
    if ($("#nw-live-bars")) return;
    $("#nw-live").innerHTML = `<div class="panel">
      <div id="nw-live-notes"></div>
      <div class="cards" id="nw-live-cards"></div>
      <div class="grid two">
        <div><h3 id="nw-live-title"></h3><div id="nw-live-bars"></div>
          <h3 style="margin-top:16px">Mole fractions at equilibrium</h3><div id="nw-live-y"></div>
          <p class="live-note">Bars follow the sliders. The plots below are redrawn when you let go.</p></div>
        <div><h3>What it means</h3><div id="nw-live-explain"></div></div>
      </div></div>`;
  }

  function renderLive(r) {
    ensureLive();
    const el = r.key_element;
    const dist = r.atom_distribution;

    // What each switch would change now, and one line on what the last click did.
    switchInfo = { __element: el };
    for (const row of r.switches || []) switchInfo[row.species] = row;
    paintSwitches();
    if (pending) {
      // Where the atoms of the key element go now, largest share first (the same numbers as the bars).
      const shares = Object.keys(dist).filter((s) => dist[s] >= 0.0005).sort((a, b) => dist[b] - dist[a])
        .map((s) => `${chem(s)} <strong>${pct(dist[s], 1)}</strong>`).join(", ");
      const now = shares ? ` The ${esc(el)} atoms now go to: ${shares}.` : "";
      say(pending.kind === "tour" ? `${esc(pending.say)}${now}`
        : `${chem(pending.sid)} switched ${pending.on ? "on" : "off"}.${now}`);
      pending = null;
    }

    $("#nw-live-notes").innerHTML = TS.notes(r.warnings) +
      TS.notes(r.notes.filter((n) => n.level !== "info" || n.kind === "condensation" || n.kind === "vapour_fallback"));
    $("#nw-live-title").innerHTML = `Where the ${esc(el)} atoms go at ${fix(r.T, 0)} K, ${fix(r.P, 1)} bar`;

    // Rows keep the order of the system so the bars do not jump around while dragging.
    const order = system.filter((s) => dist[s] !== undefined).concat(Object.keys(dist).filter((s) => !system.includes(s)));
    TS.updateBars($("#nw-live-bars"), order.map((sid) => ({
      key: sid, label: chem(sid), percent: 100 * dist[sid], text: pct(dist[sid], 1), color: TS.colorOf(sid),
    })));
    const all = system.filter((s) => r.y[s] !== undefined).concat(r.species.filter((s) => !system.includes(s)));
    TS.updateBars($("#nw-live-y"), all.map((sid) => ({
      key: sid, label: chem(sid), percent: 100 * r.y[sid], text: sig(r.y[sid], 3), color: TS.colorOf(sid),
    })));

    let cards = "";
    if (r.carbon_activity !== null && r.carbon_activity !== undefined) {
      const canForm = r.carbon_activity > 1;
      cards += `<div class="card ${canForm ? "bad" : "good"}"><div class="k">Solid carbon (soot)</div><div class="v">${canForm ? "can form" : "cannot form"}</div>
        <div class="s">making it would ${canForm ? "lower" : "raise"} the total Gibbs energy</div></div>`;
    }
    cards += `<div class="card"><div class="k">Moles of gas</div><div class="v">${sig(r.total_moles, 4)}</div>
      <div class="s">from ${sig(Object.values(r.feed).reduce((a, b) => a + b, 0), 4)} mol of feed</div></div>`;
    $("#nw-live-cards").innerHTML = cards;
    $("#nw-live-explain").innerHTML = explain(r);

    // Move the marker on the plots that are already on screen.
    if (lastSweep && typeof Plotly !== "undefined") {
      const here = lastSweep === "T" ? r.T : r.P;
      for (const plot of $$("#nw-out .js-plotly-plot")) Plotly.relayout(plot, { "shapes[0].x0": here, "shapes[0].x1": here });
    }
  }

  function showError(err) {
    $("#nw-live").innerHTML = `<div class="panel">${TS.errorBox(err)}</div>`;
  }

  /* -------------------------------------------------------------------- plots */
  function renderPlots(r) {
    const s = r.sweep;
    const out = $("#nw-out");
    if (!s) {
      out.innerHTML = `<div class="panel">${TS.message("warning", "<strong>No plots:</strong> the plot range is empty. \"To\" must be above \"From\".")}</div>`;
      lastSweep = null;
      return;
    }
    const el = r.key_element;
    const sk = s.skipped || [];
    const unit = s.variable === "T" ? "K" : "bar";
    out.innerHTML = `<div class="panel"><div class="grid two"><div id="nw-plot-y" class="plot tall"></div><div id="nw-plot-dist" class="plot tall"></div></div>
      ${sk.length ? `<p class="hint" style="margin:8px 0 0">Gaps in the curves: ${sk.length} of ${s.x.length} points
        (${fix(Math.min(...sk), 0)} to ${fix(Math.max(...sk), 0)} ${unit}) could not be calculated with this real-gas model.
        ${esc(s.skipped_reason || "")}</p>` : ""}</div>`;
    lastSweep = s.variable;

    const xTitle = s.variable === "T" ? "Temperature (K)" : "Pressure (bar)";
    const here = s.variable === "T" ? r.T : r.P;
    // Every graph of this panel uses the same horizontal axis, and the fractions run over
    // the whole 0 to 1 (0 to 100 %) on every graph, so curves can be compared from one to the next.
    const xAxis = { range: [s.x[0], s.x[s.x.length - 1]] };
    TS.plot("nw-plot-y", r.species.map((sid) => ({
      x: s.x, y: s.y[sid], name: sid, mode: "lines", line: { width: 2.2, color: TS.colorOf(sid) },
    })), TS.layout("Equilibrium mole fractions", xTitle, "Mole fraction", { shapes: [TS.vline(here)], xaxis: xAxis, yaxis: { range: [0, 1] } }));

    TS.plot("nw-plot-dist", Object.keys(s.distribution).map((sid) => ({
      x: s.x, y: s.distribution[sid].map((v) => (v === null ? null : 100 * v)), name: sid, mode: "lines",
      stackgroup: "one", line: { width: 0.6, color: TS.colorOf(sid) },
    })), TS.layout(`Where the ${el} atoms go`, xTitle, `% of ${el} atoms`, { shapes: [TS.vline(here)], xaxis: xAxis, yaxis: { range: [0, 100] } }));
  }

  /* ------------------------------------------------------------- calculations */
  function payload(withSweep) {
    const { species, feed } = readSystem();
    const sweep = $("#nw-sweep").value;
    // "candidates" are the products that are switched off; the solver reports what allowing them would change.
    // Real gases, each with the equation of state the solver chose for it (closest to measured data)
    const body = { species, feed, T: TS.readNumber("nw-T"), P: TS.readNumber("nw-P"), model: "auto",
      sweep: withSweep ? sweep : "none", switches: true, candidates: system.filter((s) => !species.includes(s)) };
    if (withSweep) {
      body[sweep === "T" ? "T_min" : "P_min"] = TS.readNumber("nw-min");
      body[sweep === "T" ? "T_max" : "P_max"] = TS.readNumber("nw-max");
    }
    return body;
  }

  const point = TS.latest(async () => {
    try {
      renderLive(await TS.engine.call("network", payload(false)));
    } catch (err) {
      showError(err);
    }
  });

  const full = TS.latest(async () => {
    const button = $("#nw-run");
    button.disabled = true;
    try {
      const r = await TS.engine.call("network", payload(true));
      renderLive(r);
      renderPlots(r);
    } catch (err) {
      showError(err);
    } finally {
      button.disabled = false;
    }
  });

  let started = false;
  TS.tabs.push({
    id: "network",
    init() {
      buildChips();
      const preset = $("#nw-preset");
      preset.innerHTML = TS.library.networks.map((n) => `<option value="${esc(n.id)}">${esc(n.name)}</option>`).join("");
      preset.addEventListener("change", () => { loadPreset(preset.value); full(); });
      // The line about the last click belongs to the settings it was made at.
      TS.bindSlider("nw-T", () => { say(""); point(); }, full);
      TS.bindSlider("nw-P", () => { say(""); point(); }, full);
      TS.bindSlider("nw-ratio", () => { say(""); applyRatio(); point(); }, () => { applyRatio(); full(); });
      $("#nw-sweep").addEventListener("change", () => {
        const isT = $("#nw-sweep").value === "T";
        const system_ = TS.library.networks.find((n) => n.id === preset.value);
        $("#nw-min").value = isT ? (system_ ? system_.T_range[0] : 400) : 1;
        $("#nw-max").value = isT ? (system_ ? system_.T_range[1] : 900) : 300;
        full();
      });
      $("#nw-run").addEventListener("click", () => full());
      for (const id of ["nw-min", "nw-max"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") full(); });
      }
      loadPreset(TS.library.networks[0].id);
    },
    onShow() {
      if (!started) { started = true; full(); }
    },
  });
})();
