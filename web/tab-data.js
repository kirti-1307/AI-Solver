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
          <td class="l" title="${esc(s.formation_source + " | " + s.cp_source + (s.cp_low_source ? " | " + s.cp_low_source : ""))}">${s.from_svn ? "SVN" : '<span class="badge neutral">NIST</span>'}${s.cp_low ? ' <span class="dim">+ NIST below 298 K</span>' : ""}${s.cp_high ? ` <span class="dim">and above ${fix(s.cp_main_Tmax, 0)} K</span>` : ""}</td></tr>`;
      }).join("");
  }

  /* Heat capacities from 200 K to 298.15 K: the constants computed from the NIST rows. */
  function lowTemperatureBlock(db) {
    const rows = db.species.filter((s) => s.cp_low).map((s) => {
      const c = s.cp_low;
      return `<tr><td class="l mono">${chem(s.id)}</td><td class="l">${esc(s.name)}</td>
        <td>${fix(c[0], 4)}</td><td>${fix(c[1] * 1e3, 4)}</td><td>${fix(c[2] * 1e6, 4)}</td>
        <td>${fix(s.cp_low_at_Tmin_J, 3)}</td><td>${fix(s.cp298_low_J, 3)}</td><td>${fix(s.cp298_main_J, 3)}</td>
        <td>${TS.signed(s.cp298_step_percent, 2)} %</td>
        <td class="l">${esc(s.cp_low_source.replace(/^Heat capacities from 200 K to 298\.15 K: /, ""))}</td></tr>`;
    }).join("");
    const left = Object.entries(db.low_T.not_covered).map(([id, why]) => `<li><strong>${chem(id)}:</strong> ${esc(why)}.</li>`).join("");
    return `<details><summary>Heat capacities below 298.15 K (${db.low_T.covered} species, ${fix(db.low_T.T_min, 0)} to 298.15 K, from NIST)</summary>
      <p class="hint">SVN's tables start at 298 K, so between ${fix(db.low_T.T_min, 0)} K and 298.15 K the solver uses
        C<sub>p</sub>/R = A + BT + CT² with constants computed from tabulated NIST values. Formation data and everything above 298.15 K are unchanged.
        The last number column is how far the SVN correlation is from the NIST value at 298.15 K.</p>
      <div class="table-scroll"><table><thead><tr><th class="l">Species</th><th class="l">Name</th><th>A</th><th>10³B</th><th>10⁶C</th>
        <th>C<sub>p</sub> at ${fix(db.low_T.T_min, 0)} K</th><th>C<sub>p</sub> at 298.15 K, NIST</th><th>C<sub>p</sub> at 298.15 K, SVN</th>
        <th>SVN − NIST</th><th class="l">Source</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="hint" style="margin-top:8px">C<sub>p</sub> in J/(mol·K). Not covered below 298.15 K:</p><ul class="explain">${left}</ul></details>`;
  }

  /* Heat capacities above the SVN range: the NIST equations, and how the two sources compare where they meet. */
  function highTemperatureBlock(db) {
    const rows = db.species.filter((s) => s.cp_high).map((s) => `<tr><td class="l mono">${chem(s.id)}</td><td class="l">${esc(s.name)}</td>
        <td>${fix(s.cp_main_Tmax, 0)}–${fix(s.cp_Tmax, 0)}</td>
        <td>${fix(s.cp_join_high_J, 3)}</td><td>${fix(s.cp_join_main_J, 3)}</td><td>${TS.signed(s.cp_join_step_percent, 2)} %</td>
        <td>${fix(s.cp_high_at_Tmax_J, 3)}</td>
        <td class="l">${esc(s.cp_high_source.replace(/^Heat capacities above the SVN range, up to 6000 K: /, ""))}</td></tr>`).join("");
    return `<details><summary>Heat capacities above the SVN range (${db.high_T.covered} gases, up to ${fix(db.high_T.T_max, 0)} K, from NIST)</summary>
      <p class="hint">SVN's formula for the gases of a flame ends at 2000 K (2500 K for CO, 3000 K for H<sub>2</sub>). Above that the solver uses
        the heat-capacity equations of the NIST Chemistry WebBook, as published. Inside the SVN range nothing is changed. The step column is how far
        SVN's formula is from the NIST value at the temperature where the NIST equation takes over: SVN's formula runs a little high at its upper end.</p>
      <div class="table-scroll"><table><thead><tr><th class="l">Species</th><th class="l">Name</th><th>NIST used (K)</th>
        <th>C<sub>p</sub> at the join, NIST</th><th>C<sub>p</sub> at the join, SVN</th><th>SVN − NIST</th>
        <th>C<sub>p</sub> at ${fix(db.high_T.T_max, 0)} K</th><th class="l">Source</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="hint" style="margin-top:8px">C<sub>p</sub> in J/(mol·K). Every other species keeps its SVN limit; beyond it the solver extrapolates and warns.</p></details>`;
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
        `From 298.15 K upwards ${db.svn_count} use Smith, Van Ness &amp; Abbott (SVN) data only. The other ${db.count - db.svn_count}, marked NIST in the last column, ` +
        `cover what SVN does not tabulate (hydrogen peroxide, and acetic acid beyond its liquid formation values) with data from the NIST Chemistry WebBook. ` +
        `Standard state: the pure species at ${db.constants.P0} bar, at any temperature. The formation data are listed at the reference temperature ${db.constants.T0} K. R = ${db.constants.R} J/(mol·K). ` +
        `C<sub>p</sub>/R = A + BT + CT² + DT⁻² (the SVN form), plus ET³ for the NIST species. ` +
        `SVN's constants hold from 298 K to the upper limit in the table. From ${fix(db.low_T.T_min, 0)} K to 298.15 K the heat capacities of ${db.low_T.covered} species come from NIST tables, ` +
        `and above the SVN limit, up to ${fix(db.high_T.T_max, 0)} K, those of ${db.high_T.covered} flame gases come from NIST equations (both listed below the table). ` +
        `ΔS°<sub>f</sub> = (ΔH°<sub>f</sub> − ΔG°<sub>f</sub>)/298.15; the standard molar entropy S°<sub>298</sub> adds the entropies of the elements (CODATA values).`;
      $("#db-notes").innerHTML = `<details><summary>Sources and notes on the data</summary><ul class="explain">` +
        Object.values(db.sources).map((s) => `<li>${esc(s)}</li>`).join("") +
        db.data_notes.map((n) => `<li><strong>${esc(n.species)}:</strong> ${esc(n.reason)}</li>`).join("") + `</ul></details>` +
        lowTemperatureBlock(db) + highTemperatureBlock(db);
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
