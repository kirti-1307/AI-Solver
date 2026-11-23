/* Tab 7: live validation against the textbook, the AI Error Challenge and published research. */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, sig, signed } = TS;

  function benchmarks(res) {
    const groups = new Map();
    for (const row of res.rows) {
      if (!groups.has(row.group)) groups.set(row.group, []);
      groups.get(row.group).push(row);
    }
    let body = "";
    for (const [group, rows] of groups) {
      body += `<tr><td class="l" colspan="7"><strong>${esc(group)}</strong></td></tr>`;
      body += rows.map((r) => `<tr><td class="l wrapcell">${chem(r.description)}</td>
        <td>${sig(r.expected, 6)}</td><td>${r.computed === null ? esc(r.error || "–") : sig(r.computed, 6)}</td>
        <td class="l">${esc(r.unit)}</td><td>${r.rel_error === null ? "–" : fix(100 * r.rel_error, 3) + " %"}</td>
        <td class="${r.passed ? "pass" : "fail"}">${r.passed ? "pass" : "FAIL"}</td>
        <td class="l wrapcell dim">${esc(r.source)}</td></tr>`).join("");
    }
    const s = res.summary;
    $("#vl-bench").innerHTML = TS.message(s.passed === s.total ? "good" : "error",
      `<strong>${s.passed} of ${s.total}</strong> reference values reproduced.`) +
      `<div class="table-scroll"><table><thead><tr><th class="l">Quantity</th><th>Reference</th><th>Solver</th><th class="l">Unit</th>
        <th>Difference</th><th>Result</th><th class="l">Where the reference value comes from</th></tr></thead><tbody>${body}</tbody></table></div>
      <p class="hint" style="margin-top:8px">Small differences (below 0.1 %) come from the rounding of intermediate values in the printed solutions.</p>`;
  }

  function challenge(c) {
    const st = c.stoichiometry.map((x) => `<tr><td class="l mono">${chem(x.input)}</td>
      <td class="${x.accepted ? "pass" : "fail"}">${x.accepted ? "accepted" : "rejected"}</td>
      <td class="l mono">${x.suggestion ? chem(x.suggestion) : "–"}</td></tr>`).join("");
    // Every predefined reaction. One whose heat-capacity data stop below 1000 K is listed without numbers.
    const cp = c.cp_assumption.map((x) => (x.in_range ? `<tr><td class="l">${esc(x.name)}</td>
      <td>${kJ(x.dH)}</td><td>${kJ(x.dH_const)}</td><td>${signed((x.dH_const - x.dH) / 1000)}</td>
      <td>${kJ(x.dH_none)}</td><td>${signed((x.dH_none - x.dH) / 1000)}</td></tr>`
      : `<tr><td class="l">${esc(x.name)}</td><td class="l dim" colspan="5">no comparison: the C<sub>p</sub> data of this reaction hold only from
        ${x.valid_range ? `${fix(x.valid_range[0], 0)} to ${fix(x.valid_range[1], 0)} K` : "298.15 K"}, not at ${fix(x.T, 0)} K</td></tr>`)).join("");
    const cs = c.cp_summary;
    const cpSummary = `For the <strong>${cs.in_range} of ${cs.total}</strong> predefined reactions whose heat-capacity data reach ${fix(cs.T, 0)} K:
      a constant ΔC<sub>p</sub> (its value at 298.15 K) puts ΔH° off by ${kJ(cs.constant.mean)} kJ/mol on average and by up to
      <strong>${kJ(cs.constant.max)} kJ/mol</strong> (${esc(cs.constant.worst)}). Ignoring ΔC<sub>p</sub> puts it off by ${kJ(cs.ignored.mean)} kJ/mol
      on average and by up to <strong>${kJ(cs.ignored.max)} kJ/mol</strong> (${esc(cs.ignored.worst)}).`;
    const ps = c.physical_state;
    const ex = c.extrapolation.map((x) => `<tr><td class="l mono">${chem(x.equation)}</td><td>${fix(x.T, 0)}</td>
      <td>${x.valid_range ? `${fix(x.valid_range[0], 0)}–${fix(x.valid_range[1], 0)}` : "–"}</td>
      <td class="pass">${x.warned ? "outside range: warning shown" : "inside range: no warning"}</td>
      <td class="l wrapcell dim">${x.warnings.length ? esc(x.warnings.length + " species extrapolated: " + x.warnings.map((w) => w.split(":")[0]).join(", ")) : ""}</td></tr>`).join("");

    $("#vl-challenge").innerHTML = `
      <h3>1. Stoichiometry: is an unbalanced reaction rejected?</h3>
      <div class="table-scroll"><table><thead><tr><th class="l">Typed</th><th>Result</th><th class="l">Balanced form offered</th></tr></thead><tbody>${st}</tbody></table></div>
      <p class="hint">The element balance is checked before any property is looked up. A rejected reaction returns no numbers at all.</p>

      <h3>2. C<sub>p</sub> assumptions at 1000 K, for every predefined reaction</h3>
      ${TS.message("info", cpSummary)}
      <div class="table-scroll"><table><thead><tr><th class="l">Reaction</th><th>ΔH° with C<sub>p</sub>(T) (kJ/mol)</th><th>constant ΔC<sub>p</sub></th><th>error</th>
        <th>ΔC<sub>p</sub> ignored</th><th>error</th></tr></thead><tbody>${cp}</tbody></table></div>
      <p class="hint">A constant ΔC<sub>p</sub> taken at 298.15 K misses how C<sub>p</sub> changes with temperature, and ignoring ΔC<sub>p</sub>
        keeps ΔH° at its 298.15 K value. Any reaction can be checked the same way at any temperature on tab 1, under
        "How much does the heat-capacity treatment matter".</p>

      <h3>3. Physical state: methane combustion with H<sub>2</sub>O(l) or H<sub>2</sub>O(g)</h3>
      <div class="table-scroll"><table><thead><tr><th class="l">Reaction</th><th>ΔH°<sub>298</sub> (kJ/mol)</th><th>ΔG°<sub>298</sub> (kJ/mol)</th><th>ΔS°<sub>298</sub> (J/mol·K)</th></tr></thead><tbody>
        <tr><td class="l mono">${chem(ps.liquid.equation)}</td><td>${kJ(ps.liquid.dH0, 3)}</td><td>${kJ(ps.liquid.dG0, 3)}</td><td>${fix(ps.liquid.dS0, 2)}</td></tr>
        <tr><td class="l mono">${chem(ps.vapour.equation)}</td><td>${kJ(ps.vapour.dH0, 3)}</td><td>${kJ(ps.vapour.dG0, 3)}</td><td>${fix(ps.vapour.dS0, 2)}</td></tr>
        <tr class="sum"><td class="l">Difference = 2 × heat of vaporisation of water (2 × ${kJ(ps.vaporisation_dH0, 3)})</td><td>${kJ(ps.difference_dH, 3)}</td><td></td><td></td></tr>
      </tbody></table></div>
      <p class="hint">The higher and lower heating values differ by exactly the latent heat of the water formed. The solver never guesses silently:
        if no phase is typed it assumes gas and says so in a note.</p>

      <h3>4. Correlation validity: is extrapolation flagged?</h3>
      <div class="table-scroll"><table><thead><tr><th class="l">Reaction</th><th>T (K)</th><th>Valid range (K)</th><th>Result</th><th class="l"></th></tr></thead><tbody>${ex}</tbody></table></div>
      <p class="hint">Each species carries the temperature range of its heat-capacity data: the textbook's correlation, extended with NIST data
        below 298.15 K and, for eight gases, above the textbook's limit. Outside that range the result is still shown, with a warning and a
        shaded band on the plots. Every one of the 45 predefined reactions was checked 1 K inside and 1 K outside each end of its range.</p>

      <h3>5. Check against published work</h3>
      <p class="hint">See the next panel.</p>`;
  }

  function literature(lit) {
    const dh = lit.enthalpies.map((x) => `<tr><td class="l">${esc(x.name)}</td><td class="l mono">${chem(x.equation)}</td>
      <td>${kJ(x.solver, 2)}</td><td>${sig(x.published, 5)}</td><td>${signed(x.solver / 1000 - x.published, 2)}</td>
      <td class="l wrapcell dim">${esc(x.source)}</td></tr>`).join("");
    const kk = lit.equilibrium.map((x) => `<tr><td class="l">${esc(x.name)}</td><td>${fix(x.T, 0)}</td>
      <td>${sig(x.solver, 4)}</td><td>${sig(x.published, 4)}</td><td>${signed(100 * (x.solver / x.published - 1), 1)} %</td>
      <td>${signed(x.dG_equivalent / 1000, 2)}</td><td class="l wrapcell dim">${esc(x.source)}</td></tr>`).join("");
    const extra = (lit.other || []).map((x) => `<tr><td class="l wrapcell">${esc(x.name)}</td><td>${sig(x.solver, 4)}</td><td>${sig(x.published, 4)}</td>
      <td class="l">${esc(x.unit)}</td><td class="l wrapcell dim">${esc(x.source)}</td></tr>`).join("");
    $("#vl-literature").innerHTML = `
      <h3>Standard heats of reaction at 298 K</h3>
      <div class="table-scroll"><table><thead><tr><th class="l">Reaction</th><th class="l">Equation</th><th>Solver (kJ/mol)</th><th>Published (kJ/mol)</th>
        <th>Difference</th><th class="l">Source</th></tr></thead><tbody>${dh}</tbody></table></div>
      <h3 style="margin-top:14px">Equilibrium constants from published correlations</h3>
      <div class="table-scroll"><table><thead><tr><th class="l">Reaction</th><th>T (K)</th><th>K, solver</th><th>K, published</th><th>Difference</th>
        <th>as ΔG° (kJ/mol)</th><th class="l">Source</th></tr></thead><tbody>${kk}</tbody></table></div>
      ${extra ? `<h3 style="margin-top:14px">Other published values</h3><div class="table-scroll"><table><thead><tr><th class="l">Quantity</th><th>Solver</th><th>Published</th><th class="l">Unit</th><th class="l">Source</th></tr></thead><tbody>${extra}</tbody></table></div>` : ""}
      <p class="hint" style="margin-top:8px">${esc(lit.comment)}</p>`;
  }

  /* The five equations of state against measured data, and the equation each gas therefore uses. */
  function eos(e) {
    const eqs = e.equations;
    const cell = (mean, best, m) => `<td class="${m === best ? "pass" : ""}">${fix(mean[m] / 1000, 3)}</td>`;
    const rows = e.rows.map((x) => `<tr><td class="l">${esc(x.name)}</td><td>${x.points}</td>
      ${eqs.map((m) => cell(x.mean, x.best, m)).join("")}<td class="l"><strong>${esc(e.names[x.best])}</strong></td></tr>`).join("");
    const o = e.overall;
    const total = `<tr class="sum"><td class="l">All ${o.gases} gases together</td><td>${o.points}</td>
      ${eqs.map((m) => cell(o.mean, o.best, m)).join("")}<td class="l"><strong>${esc(e.names[o.best])}</strong></td></tr>`;
    const wins = eqs.filter((m) => o.wins[m] > 0).sort((a, b) => o.wins[b] - o.wins[a])
      .map((m) => `${esc(e.names[m])} for ${o.wins[m]}`).join(", ");
    const never = eqs.filter((m) => !o.wins[m]).map((m) => esc(e.names[m])).join(" and ");
    const others = e.choices.filter((c) => c.basis === "overall").map((c) => esc(c.name));
    const ideal = e.choices.filter((c) => c.basis === "no_critical").map((c) => esc(c.name));
    $("#vl-eos").innerHTML = TS.message("info", `Closest equation: ${wins} of the ${o.gases} measured gases; ${never} never.
        Over all ${o.points} measured points ${esc(e.names[o.best])} is closest on average, so the ${others.length} gases without
        measured data use it (${others.join(", ")}).${ideal.length ? ` ${ideal.join(", ")} ${ideal.length > 1 ? "have" : "has"} no critical
        constants in the textbook and ${ideal.length > 1 ? "stay ideal gases" : "stays an ideal gas"}.` : ""}`) +
      `<div class="table-scroll"><table><thead><tr><th class="l">Gas</th><th>Measured points</th>
        ${eqs.map((m) => `<th>${esc(e.names[m])}</th>`).join("")}<th class="l">Used by the solver</th></tr></thead>
        <tbody>${rows}${total}</tbody></table></div>
      <p class="hint" style="margin-top:8px">Each number is the average of |H<sup>R</sup>(equation) − H<sup>R</sup>(measured)| in kJ/mol;
        the smallest in each row is green. Points: 300 to 1000 K and 10 to 300 bar, as far as NIST covers each gas, gas states only.
        Measured data: ${esc(e.source)}.</p>`;
  }

  let started = false;
  TS.tabs.push({
    id: "validation",
    init() {},
    async onShow() {
      if (started) return;
      started = true;
      $("#vl-bench").innerHTML = TS.message("info", "Running the benchmarks…");
      try {
        const [b, c, l, e] = await Promise.all([TS.engine.call("validate"), TS.engine.call("challenge"),
          TS.engine.call("literature"), TS.engine.call("eos_check")]);
        benchmarks(b);
        challenge(c);
        literature(l);
        eos(e);
      } catch (err) {
        $("#vl-bench").innerHTML = TS.errorBox(err);
        started = false;
      }
    },
  });
})();
