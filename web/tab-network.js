/* Tab 4 (extra feature 1): equilibrium of competing reactions by Gibbs-energy minimisation. */
"use strict";
(() => {
  const { $, $$, esc, chem, fix, sig, pct } = TS;

  function buildChips() {
    const gases = TS.database.species.filter((s) => s.phase === "g");
    $("#nw-species").innerHTML = gases.map((s, i) => `<div class="chip off" data-id="${esc(s.id)}">
        <input type="checkbox" id="nw-allow-${i}">
        <label for="nw-allow-${i}" title="${esc(s.name)}">${chem(s.id)} <span class="dim">${esc(s.name)}</span></label>
        <input type="number" step="any" min="0" value="" placeholder="feed" aria-label="Feed of ${esc(s.id)} in mol">
      </div>`).join("");
    for (const chip of $$("#nw-species .chip")) {
      const [box, feed] = chip.querySelectorAll("input");
      box.addEventListener("change", () => { chip.classList.toggle("off", !box.checked); if (!box.checked) feed.value = ""; });
      feed.addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
    }
  }

  function loadPreset(id) {
    const preset = TS.library.networks.find((n) => n.id === id);
    if (!preset) return;
    for (const chip of $$("#nw-species .chip")) {
      const [box, feed] = chip.querySelectorAll("input");
      const sid = chip.dataset.id;
      box.checked = preset.species.includes(sid);
      chip.classList.toggle("off", !box.checked);
      feed.value = preset.feed[sid] !== undefined ? preset.feed[sid] : "";
    }
    $("#nw-P").value = preset.P;
    $("#nw-T").value = Math.round((preset.T_range[0] + preset.T_range[1]) / 2);
    $("#nw-sweep").value = "T";
    $("#nw-min").value = preset.T_range[0];
    $("#nw-max").value = preset.T_range[1];
    $("#nw-note").textContent = preset.note || "";
  }

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
    for (const sid of fedIds) {
      lines.push(`Equilibrium conversion of ${chem(sid)}: <strong>${pct(r.conversions[sid], 2)}</strong>.`);
    }
    if (r.carbon_activity !== null && r.carbon_activity !== undefined) {
      const a = r.carbon_activity;
      lines.push(`Carbon activity a<sub>C</sub> = ${sig(a, 3)}. ` + (a > 1
        ? "It is above 1, so solid carbon (graphite) would lower the Gibbs energy further: <strong>coke formation is thermodynamically favoured</strong> at these conditions."
        : "It is below 1, so the gas is not saturated with carbon: no coke is expected from thermodynamics."));
    }
    if (r.excluded.length) {
      lines.push(`Left out because the feed has none of their elements: ${r.excluded.map(chem).join(", ")}.`);
    }
    lines.push("This is the composition the system would reach with unlimited time and a non-selective catalyst. " +
      "Untick a species to model a catalyst that cannot form it; the difference between the two answers is what catalyst selectivity has to fight against.");
    lines.push(`Method: minimise G/RT = Σ n<sub>i</sub>[G<sub>i</sub>°/RT + ln(y<sub>i</sub>φ<sub>i</sub>P/P°)] subject to the element balances ` +
      `(Lagrange multipliers). Converged in ${r.iterations} Newton iterations; largest residual of the equilibrium conditions ${sig(r.kkt_residual, 2)}.`);
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  function render(r) {
    const el = r.key_element;
    const ids = r.species.slice().sort((a, b) => r.y[b] - r.y[a]);
    const rows = ids.map((s) => `<tr><td class="l mono">${chem(s)}</td><td>${fix(r.feed[s], 4)}</td>
      <td>${sig(r.moles[s], 5)}</td><td>${sig(r.y[s], 5)}</td>
      <td>${r.atom_distribution[s] === undefined ? "–" : pct(r.atom_distribution[s], 2)}</td></tr>`).join("");
    let html = `<div class="panel">${TS.notes(r.warnings)}${TS.notes(r.notes.filter((n) => n.level !== "info"))}
      <div class="grid two"><div>
        <h3>Equilibrium mixture at ${fix(r.T, 0)} K, ${fix(r.P, 1)} bar</h3>
        <div class="table-scroll"><table><thead><tr><th class="l">Species</th><th>Feed (mol)</th><th>Equilibrium (mol)</th>
          <th>Mole fraction y</th><th>Share of ${esc(el)} atoms</th></tr></thead><tbody>${rows}
          <tr class="sum"><td class="l">Total</td><td>${fix(Object.values(r.feed).reduce((a, b) => a + b, 0), 4)}</td><td>${sig(r.total_moles, 6)}</td><td>1</td><td></td></tr>
          </tbody></table></div></div>
        <div><h3>What it means</h3>${explain(r)}</div></div></div>`;
    if (r.sweep) {
      const sk = r.sweep.skipped || [];
      const unit = r.sweep.variable === "T" ? "K" : "bar";
      html += `<div class="panel"><div class="grid two"><div id="nw-plot-y" class="plot tall"></div><div id="nw-plot-dist" class="plot tall"></div>
        ${r.sweep.carbon_activity.some((v) => v !== null) ? '<div id="nw-plot-aC" class="plot"></div>' : ""}
        <div id="nw-plot-conv" class="plot"></div></div>
        ${sk.length ? `<p class="hint" style="margin:8px 0 0">Gaps in the curves: ${sk.length} of ${r.sweep.x.length} points
          (${fix(Math.min(...sk), 0)} to ${fix(Math.max(...sk), 0)} ${unit}) could not be calculated with this real-gas model.
          ${esc(r.sweep.skipped_reason || "")}</p>` : ""}</div>`;
    }
    $("#nw-out").innerHTML = html;
    if (!r.sweep) return;

    const s = r.sweep;
    const xTitle = s.variable === "T" ? "Temperature (K)" : "Pressure (bar)";
    const here = s.variable === "T" ? r.T : r.P;
    const palette = TS.palette();
    const colour = {};
    r.species.forEach((sid, i) => { colour[sid] = palette[i % palette.length]; });

    TS.plot("nw-plot-y", r.species.map((sid) => ({
      x: s.x, y: s.y[sid], name: sid, mode: "lines", line: { width: 2.2, color: colour[sid] },
    })), TS.layout("Equilibrium mole fractions", xTitle, "Mole fraction", { shapes: [TS.vline(here)] }));

    TS.plot("nw-plot-dist", Object.keys(s.distribution).map((sid) => ({
      x: s.x, y: s.distribution[sid].map((v) => (v === null ? null : 100 * v)), name: sid, mode: "lines",
      stackgroup: "one", line: { width: 0.6, color: colour[sid] },
    })), TS.layout(`Where the ${el} atoms go`, xTitle, `% of ${el} atoms`, { shapes: [TS.vline(here)], yaxis: { range: [0, 100] } }));

    if (s.carbon_activity.some((v) => v !== null)) {
      TS.plot("nw-plot-aC", [{ x: s.x, y: s.carbon_activity, name: "carbon activity", mode: "lines", line: { width: 2.5, color: "#475569" } }],
        TS.layout("Carbon activity: coke is favoured above the dotted line", xTitle, "a_C",
          { shapes: [TS.vline(here), TS.hline(1)], yaxis: { type: "log" }, showlegend: false }));
    }
    TS.plot("nw-plot-conv", Object.keys(s.conversion).map((sid) => ({
      x: s.x, y: s.conversion[sid].map((v) => (v === null ? null : 100 * v)), name: sid, mode: "lines", line: { width: 2.2, color: colour[sid] },
    })), TS.layout("Equilibrium conversion of the feed species", xTitle, "Conversion (%)", { shapes: [TS.vline(here)] }));
  }

  function calculate() {
    const species = [];
    const feed = {};
    for (const chip of $$("#nw-species .chip")) {
      const [box, feedInput] = chip.querySelectorAll("input");
      if (!box.checked) continue;
      species.push(chip.dataset.id);
      const moles = Number(feedInput.value);
      if (feedInput.value.trim() !== "" && Number.isFinite(moles) && moles !== 0) feed[chip.dataset.id] = moles;
    }
    const sweep = $("#nw-sweep").value;
    const payload = { species, feed, T: TS.readNumber("nw-T"), P: TS.readNumber("nw-P"), model: $("#nw-model").value, sweep };
    payload[sweep === "T" ? "T_min" : "P_min"] = TS.readNumber("nw-min");
    payload[sweep === "T" ? "T_max" : "P_max"] = TS.readNumber("nw-max");
    return TS.run($("#nw-run"), $("#nw-out"), async () => {
      render(await TS.engine.call("network", payload));
    });
  }

  let started = false;
  TS.tabs.push({
    id: "network",
    init() {
      buildChips();
      const preset = $("#nw-preset");
      preset.innerHTML = TS.library.networks.map((n) => `<option value="${esc(n.id)}">${esc(n.name)}</option>`).join("");
      preset.addEventListener("change", () => { loadPreset(preset.value); calculate(); });
      $("#nw-sweep").addEventListener("change", () => {
        const isT = $("#nw-sweep").value === "T";
        $("#nw-min").value = isT ? 400 : 1;
        $("#nw-max").value = isT ? 900 : 300;
      });
      $("#nw-run").addEventListener("click", calculate);
      for (const id of ["nw-T", "nw-P", "nw-min", "nw-max"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      $("#nw-model").addEventListener("change", calculate);
      loadPreset(TS.library.networks[0].id);
    },
    onShow() {
      if (!started) { started = true; calculate(); }
    },
  });
})();
