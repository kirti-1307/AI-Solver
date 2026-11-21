/* Tab 3: build a reaction by adding and subtracting other reactions (Hess's law). */
"use strict";
(() => {
  const { $, $$, esc, chem, fix, kJ, int, sig, fmtK, signed } = TS;

  function addStep(equation = "", multiplier = 1) {
    const row = document.createElement("div");
    row.className = "step";
    row.innerHTML = `<input type="number" step="any" value="${esc(multiplier)}" aria-label="Multiplier" title="Multiplier (negative reverses the reaction)">
      <input type="text" spellcheck="false" autocomplete="off" list="cb-reactions" value="${esc(equation)}"
             aria-label="Reaction" placeholder="e.g. CO + H2O(g) -> CO2 + H2">
      <button type="button" title="Remove this reaction" aria-label="Remove">✕</button>`;
    row.querySelector("button").addEventListener("click", () => {
      if ($$("#cb-steps .step").length > 2) row.remove();
    });
    for (const input of row.querySelectorAll("input")) {
      input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
    }
    $("#cb-steps").appendChild(row);
  }

  function loadPreset(id) {
    const preset = TS.library.combinations.find((c) => c.id === id);
    if (!preset) return;
    $("#cb-steps").innerHTML = "";
    for (const step of preset.steps) addStep(step.equation, step.multiplier);
    $("#cb-T").value = preset.T;
  }

  function render(r) {
    const d = r.direct;
    const T = fix(r.T, 0);
    const rows = r.steps.map((s, i) => `<tr>
      <td class="l">${i + 1}</td><td>${signed(s.multiplier, 2).replace(".00", "")}</td>
      <td class="l mono">${chem(s.applied)}</td>
      <td>${kJ(s.m_dH0)}</td><td>${kJ(s.m_dH)}</td><td>${fix(s.m_dS, 2)}</td><td>${kJ(s.m_dG)}</td><td>${fix(s.m_lnK, 3)}</td></tr>`).join("");
    const c = r.check;
    const exo = d.dH < 0 ? "exo" : "endo";

    let html = `<div class="panel"><h3>Net reaction</h3><div class="eqn">${chem(r.net_equation)}</div>`;
    if (r.cancelled_intermediates.length) {
      html += TS.message("info", `Cancelled intermediates: ${r.cancelled_intermediates.map((s) => `<span class="mono">${chem(s)}</span>`).join(", ")}`);
    }
    html += TS.notes(r.warnings.filter((w) => w.level !== "info"));
    html += `<div class="cards">
        <div class="card ${exo}"><div class="k">ΔH°(${T} K)</div><div class="v">${kJ(d.dH)} <span class="u">kJ/mol</span></div><div class="s">${esc(d.thermicity)}</div></div>
        <div class="card"><div class="k">ΔS°(${T} K)</div><div class="v">${fix(d.dS, 2)} <span class="u">J/(mol·K)</span></div></div>
        <div class="card"><div class="k">ΔG°(${T} K)</div><div class="v">${kJ(d.dG)} <span class="u">kJ/mol</span></div><div class="s">${esc(d.favourability.label)}</div></div>
        <div class="card"><div class="k">K = Π K<sub>j</sub><sup>m<sub>j</sub></sup></div><div class="v">${fmtK(d.lnK)}</div><div class="s">ln K = ${fix(d.lnK, 3)}</div></div>
      </div>
      <div class="table-scroll"><table><thead><tr><th class="l">#</th><th>m<sub>j</sub></th><th class="l">Step as applied (m<sub>j</sub> × reaction j)</th>
        <th>m·ΔH°<sub>298</sub> (kJ)</th><th>m·ΔH°(T) (kJ)</th><th>m·ΔS°(T) (J/K)</th><th>m·ΔG°(T) (kJ)</th><th>m·ln K</th></tr></thead>
        <tbody>${rows}
        <tr class="sum"><td class="l" colspan="3">Sum of the steps (Hess's law)</td><td>${kJ(c.dH0.hess)}</td><td>${kJ(c.dH.hess)}</td><td>${fix(c.dS.hess, 2)}</td><td>${kJ(c.dG.hess)}</td><td>${fix(c.lnK.hess, 3)}</td></tr>
        <tr><td class="l" colspan="3">Directly from the net reaction</td><td>${kJ(c.dH0.direct)}</td><td>${kJ(c.dH.direct)}</td><td>${fix(c.dS.direct, 2)}</td><td>${kJ(c.dG.direct)}</td><td>${fix(c.lnK.direct, 3)}</td></tr>
        </tbody></table></div>
      ${TS.message("good", `<strong>Check:</strong> the two routes agree to ${sig(r.max_difference_J, 2)} J/mol. H, S and G are state functions, so the path does not matter.`)}
      <ul class="explain">
        <li>Adding reactions adds their ΔH°, ΔS° and ΔG°. Since ln K = −ΔG°/RT, the logarithms add and the equilibrium constants multiply: K<sub>net</sub> = Π K<sub>j</sub><sup>m<sub>j</sub></sup>.</li>
        <li>Reversing a reaction (m = −1) changes the sign of ΔH°, ΔS°, ΔG° and inverts K.</li>
        <li>This is the same rule that builds any heat of reaction from formation reactions: ΔH° = Σ ν<sub>i</sub> ΔH°<sub>f,i</sub>.</li>
      </ul></div>`;
    if (r.sweep) html += `<div class="panel"><div class="grid two"><div id="cb-plot-G" class="plot"></div><div id="cb-plot-H" class="plot"></div></div></div>`;
    $("#cb-out").innerHTML = html;

    if (r.sweep) {
      const s = r.sweep;
      const palette = TS.palette();
      const k = (arr) => arr.map((v) => (v === null ? null : v / 1000));
      const stepTraces = (series) => series.map((y, i) => ({
        x: s.T, y: k(y), name: `step ${i + 1} × ${r.steps[i].multiplier}`, mode: "lines",
        line: { width: 1.6, dash: "dash", color: palette[(i + 1) % palette.length] } }));
      TS.plot("cb-plot-G", stepTraces(s.steps).concat([
        { x: s.T, y: k(s.net_dG), name: "net reaction", mode: "lines", line: { width: 3, color: palette[0] } },
      ]), TS.layout("ΔG° of the steps add up to the net ΔG°", "Temperature (K)", "kJ/mol", { shapes: [TS.hline(0), TS.vline(r.T)] }));
      TS.plot("cb-plot-H", stepTraces(s.steps_dH).concat([
        { x: s.T, y: k(s.net_dH), name: "net reaction", mode: "lines", line: { width: 3, color: palette[0] } },
      ]), TS.layout("ΔH° of the steps add up to the net ΔH°", "Temperature (K)", "kJ/mol", { shapes: [TS.hline(0), TS.vline(r.T)] }));
    }
  }

  function calculate() {
    const steps = $$("#cb-steps .step").map((row) => {
      const [mult, eq] = row.querySelectorAll("input");
      const m = mult.value.trim() === "" ? 1 : Number(mult.value);
      return { equation: eq.value, multiplier: Number.isFinite(m) ? m : mult.value };
    }).filter((s) => s.equation.trim() !== "");
    return TS.run($("#cb-run"), $("#cb-out"), async () => {
      render(await TS.engine.call("combine", { steps, T: TS.readNumber("cb-T") }));
    });
  }

  let started = false;
  TS.tabs.push({
    id: "combine",
    init() {
      const list = document.createElement("datalist");
      list.id = "cb-reactions";
      list.innerHTML = TS.library.reactions.map((r) => `<option value="${esc(r.equation)}">${esc(r.name)}</option>`).join("");
      document.body.appendChild(list);

      const preset = $("#cb-preset");
      preset.innerHTML = TS.library.combinations.map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join("") +
        `<option value="">Custom (edit the reactions below)</option>`;
      preset.addEventListener("change", () => { if (preset.value) { loadPreset(preset.value); calculate(); } });
      $("#cb-add").addEventListener("click", () => { if ($$("#cb-steps .step").length < 8) addStep("", 1); });
      $("#cb-run").addEventListener("click", calculate);
      $("#cb-T").addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      loadPreset(TS.library.combinations[0].id);
    },
    onShow() {
      if (!started) { started = true; calculate(); }
    },
  });
})();
