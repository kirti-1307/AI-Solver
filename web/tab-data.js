/* Tab 6: the property database and the single-species sensible-heat calculator. */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, int, sig } = TS;
  const PHASE = { g: "gas", l: "liquid", s: "solid" };

  function tableRows(filter) {
    const q = filter.trim().toLowerCase();
    return TS.database.species.filter((s) => !q ||
      [s.id, s.name, s.formula, PHASE[s.phase]].some((t) => t.toLowerCase().includes(q)))
      .map((s) => {
        const c = s.cp;
        const cr = s.critical;
        return `<tr><td class="l mono">${chem(s.id)}</td><td class="l">${esc(s.name)}</td><td class="l">${PHASE[s.phase]}</td>
          <td>${fix(s.molar_mass, 3)}</td><td>${int(s.dHf)}</td><td>${int(s.dGf)}</td><td>${fix(s.dSf, 2)}</td>
          <td>${s.S298_absolute === null ? "–" : fix(s.S298_absolute, 2)}</td>
          <td>${c ? fix(c[0], 3) : "–"}</td><td>${c ? fix(c[1] * 1e3, 3) : "–"}</td><td>${c ? fix(c[2] * 1e6, 3) : "–"}</td><td>${c ? fix(c[3] * 1e-5, 3) : "–"}</td>
          <td>${c && c[4] ? fix(c[4] * 1e9, 3) : "–"}</td>
          <td>${c ? `${fix(s.cp_Tmin, 0)}–${fix(s.cp_Tmax, 0)}` : "298.15 only"}</td>
          <td>${c ? fix(s.cp298_R, 3) : "–"}</td>
          <td>${cr ? fix(cr.Tc, 1) : "–"}</td><td>${cr ? fix(cr.Pc, 2) : "–"}</td><td>${cr ? fix(cr.omega, 3) : "–"}</td>
          <td class="l" title="${esc(s.formation_source + " | " + s.cp_source)}">${s.from_svn ? "SVN" : '<span class="badge neutral">NIST</span>'}</td></tr>`;
      }).join("");
  }

  function drawTable() {
    $("#db-table").innerHTML = `<table><thead><tr>
      <th class="l">Species</th><th class="l">Name</th><th class="l">State</th><th>M (g/mol)</th>
      <th>ΔH°<sub>f,298</sub> (J/mol)</th><th>ΔG°<sub>f,298</sub> (J/mol)</th><th>ΔS°<sub>f,298</sub> (J/mol·K)</th><th>S°<sub>298</sub> (J/mol·K)</th>
      <th>A</th><th>10³B</th><th>10⁶C</th><th>10⁻⁵D</th><th>10⁹E</th><th>C<sub>p</sub> range (K)</th><th>C<sub>p,298</sub>/R</th>
      <th>T<sub>c</sub> (K)</th><th>P<sub>c</sub> (bar)</th><th>ω</th><th class="l">Source</th></tr></thead>
      <tbody>${tableRows($("#db-search").value)}</tbody></table>`;
  }

  function sensible() {
    const out = $("#sh-out");
    return TS.run($("#sh-run"), out, async () => {
      const r = await TS.engine.call("sensible", {
        species: $("#sh-species").value, T1: TS.readNumber("sh-T1"), T2: TS.readNumber("sh-T2"), moles: TS.readNumber("sh-n"),
      });
      const err = r.dH_constant_cp - r.dH_molar;
      out.innerHTML = `${TS.notes(r.warnings)}<div class="cards" style="margin-top:12px">
          <div class="card ${r.Q < 0 ? "exo" : "endo"}"><div class="k">Q = n·∫C<sub>p</sub>dT</div><div class="v">${kJ(r.Q, 3)} <span class="u">kJ</span></div><div class="s">${int(r.dH_molar)} J/mol</div></div>
          <div class="card"><div class="k">Mean heat capacity ⟨C<sub>p</sub>⟩<sub>H</sub></div><div class="v">${fix(r.mean_cp_H, 2)} <span class="u">J/(mol·K)</span></div><div class="s">Q = n⟨C<sub>p</sub>⟩<sub>H</sub>(T<sub>2</sub> − T<sub>1</sub>)</div></div>
          <div class="card"><div class="k">C<sub>p</sub> at T<sub>1</sub> and T<sub>2</sub></div><div class="v">${fix(r.cp_T1, 2)} → ${fix(r.cp_T2, 2)}</div><div class="s">J/(mol·K)</div></div>
          <div class="card"><div class="k">ΔS = n·∫C<sub>p</sub>dT/T</div><div class="v">${fix(r.dS_total, 3)} <span class="u">J/K</span></div><div class="s">at constant pressure</div></div>
          <div class="card"><div class="k">If C<sub>p</sub> were constant at T<sub>1</sub></div><div class="v">${kJ(r.moles * r.dH_constant_cp, 3)} <span class="u">kJ</span></div>
            <div class="s">error ${fix(100 * err / r.dH_molar, 1)} %</div></div>
        </div><div id="sh-plot" class="plot"></div>`;
      TS.plot("sh-plot", [
        { x: r.curve.T, y: r.curve.cp, name: "Cp(T)", mode: "lines", fill: "tozeroy", line: { width: 2.5, color: "#0b5cad" }, fillcolor: "rgba(11,92,173,0.12)" },
      ], TS.layout(`Heat capacity of ${r.species.id}: the shaded area is the sensible heat`, "Temperature (K)", "Cp (J/(mol·K))",
        { showlegend: false, shapes: TS.rangeShapes(r.curve.T, [r.species.cp_Tmin, r.species.cp_Tmax]) }));
    });
  }

  let started = false;
  TS.tabs.push({
    id: "data",
    init() {
      const db = TS.database;
      $("#db-summary").innerHTML = `${db.count} species (${db.phase_counts.g} gases, ${db.phase_counts.l} liquids, ${db.phase_counts.s} solids). ` +
        `${db.svn_count} use Smith, Van Ness &amp; Abbott (SVN) data only. The other ${db.count - db.svn_count}, marked NIST in the last column, ` +
        `cover what SVN does not tabulate (hydrogen peroxide, and acetic acid beyond its liquid formation values) with data from the NIST Chemistry WebBook. ` +
        `Reference temperature ${db.constants.T0} K, standard-state pressure ${db.constants.P0} bar, R = ${db.constants.R} J/(mol·K). ` +
        `C<sub>p</sub>/R = A + BT + CT² + DT⁻² (the SVN form), plus ET³ for the NIST species. ` +
        `ΔS°<sub>f</sub> = (ΔH°<sub>f</sub> − ΔG°<sub>f</sub>)/298.15; the absolute entropy S°<sub>298</sub> adds the CODATA entropies of the elements.`;
      $("#db-notes").innerHTML = `<details><summary>Sources and notes on the data</summary><ul class="explain">` +
        Object.values(db.sources).map((s) => `<li>${esc(s)}</li>`).join("") +
        db.data_notes.map((n) => `<li><strong>${esc(n.species)}:</strong> ${esc(n.reason)}</li>`).join("") + `</ul></details>`;
      $("#db-search").addEventListener("input", drawTable);
      drawTable();

      const withCp = db.species.filter((s) => s.cp);
      $("#sh-species").innerHTML = withCp.map((s) => `<option value="${esc(s.id)}">${esc(s.id)}, ${esc(s.name)}</option>`).join("");
      $("#sh-species").value = "CH4(g)";
      $("#sh-run").addEventListener("click", sensible);
      for (const id of ["sh-T1", "sh-T2", "sh-n"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") sensible(); });
      }
      $("#sh-species").addEventListener("change", sensible);
    },
    onShow() {
      if (!started) { started = true; sensible(); }
    },
  });
})();
