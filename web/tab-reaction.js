/* Tab 1: standard heat of reaction, entropy, Gibbs energy and K versus temperature. */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, int, sig, fmtK, signed, pct, coeff } = TS;

  function explain(r) {
    const e = r.at_T;
    const T = r.T;
    const lines = [];
    const dn = e.delta_n_gas;

    lines.push(`At ${fix(T, 2)} K the reaction is <strong>${e.thermicity}</strong>: it ` +
      `${e.dH < 0 ? "releases" : "absorbs"} ${kJ(Math.abs(e.dH))} kJ of heat per mole of reaction as written ` +
      `(${kJ(Math.abs(e.dH0))} kJ at 298.15 K).`);

    if (Math.abs(dn) > 1e-9) {
      const agrees = (dn > 0) === (e.dS > 0);
      lines.push(`The number of gas moles ${dn > 0 ? "rises" : "falls"} by ${coeff(dn)}, ` +
        `${agrees ? "which is why" : "yet"} ΔS° is ${e.dS > 0 ? "positive" : "negative"} ` +
        `(${signed(e.dS, 2)} J/(mol·K)).`);
    } else {
      lines.push(`The number of gas moles does not change, so ΔS° is small (${signed(e.dS, 2)} J/(mol·K)).`);
    }

    let drive = null;
    if (e.dH < 0 && e.dS > 0) drive = "At this temperature both enthalpy and entropy favour the products, so ΔG° is negative. As long as ΔH° and ΔS° keep these signs, that holds at any temperature.";
    else if (e.dH < 0 && e.dS < 0) drive = "The reaction is enthalpy-driven: heat release favours it, but the entropy loss works against it more and more as T rises, so it is favoured at low temperature.";
    else if (e.dH > 0 && e.dS > 0) drive = "The reaction is entropy-driven: it must absorb heat, and only the T·ΔS° term can pay for that, so it is favoured at high temperature.";
    else if (e.dH > 0 && e.dS < 0) drive = "At this temperature both enthalpy and entropy oppose the products, so ΔG° is positive. As long as ΔH° and ΔS° keep these signs, no temperature makes it favourable.";
    if (drive) lines.push(drive);

    lines.push(`ΔG° = ΔH° − TΔS° = ${kJ(e.dG)} kJ/mol, so K = ${fmtK(e.lnK)}. ${esc(e.favourability.text)}`);
    if (e.dG > 0) {
      lines.push(`A positive ΔG° does not take anything away from ΔH°. ΔH° is the enthalpy of the products minus that of the ` +
        `reactants, so it exists for any balanced reaction. K &lt; 1 means less product than reactant at equilibrium, not none, ` +
        `and every mole that does react ${e.dH < 0 ? "releases" : "absorbs"} ${kJ(Math.abs(e.dH))} kJ. ` +
        `The reverse reaction has the same ΔH° with the opposite sign.`);
    }
    if (e.low_T_species && e.low_T_species.length) {
      lines.push(`The standard state fixes the pressure at 1 bar, not the temperature, so ΔH°, ΔS° and ΔG° are defined at ${fix(T, 2)} K as well. ` +
        `SVN's heat-capacity tables start at 298 K; below that the solver uses tabulated values from NIST (200 to 298.15 K).`);
    }

    if (r.crossover && r.crossover.length) {
      const Tx = r.crossover[0];
      lines.push(`ΔG° changes sign at <strong>${fix(Tx, 0)} K</strong> (K = 1). ` +
        `Products are favoured ${e.dH < 0 ? "below" : "above"} this temperature.`);
    }
    lines.push(`van 't Hoff: d ln K/dT = ΔH°/(RT²). Because ΔH° is ${e.dH < 0 ? "negative" : "positive"}, ` +
      `K ${e.dH < 0 ? "falls" : "rises"} as the temperature goes up.`);

    if (Math.abs(dn) > 1e-9) {
      lines.push(`Pressure: K itself does not depend on pressure, but the equilibrium composition does. ` +
        `With Δν(gas) = ${signed(dn, 2).replace(".00", "")}, raising the pressure shifts the equilibrium towards the ` +
        `${dn < 0 ? "products" : "reactants"} (tab 4, Product slate, shows the composition at any pressure).`);
    } else {
      lines.push("Pressure: with no change in gas moles, pressure has almost no effect on the ideal-gas equilibrium.");
    }
    const eq = r.equilibrium;
    if (eq && eq.conversion !== null && eq.conversion !== undefined && eq.limiting_reactant) {
      const what = (x) => (x.status === "complete" ? "goes to completion"
        : x.status === "no_forward_reaction" ? "does not proceed"
        : `reaches ${pct(x.conversion)} conversion of ${chem(x.limiting_reactant)}`) + condensedNote(x);
      const eqP = r.equilibrium_P;
      const other = r.P !== 1 && eqP && eqP.conversion !== null && eqP.conversion !== undefined;
      lines.push(`Favourability at a given pressure: with a stoichiometric feed at ${fix(T, 0)} K (ideal-gas mixture), the reaction ` +
        `${what(eq)} at 1 bar` + (other ? `, and ${what(eqP)} at <strong>${fix(r.P, 1)} bar</strong>.` : ".") +
        (other ? "" : " Type another pressure in the form to see what it does."));
      if (r.phase && r.phase.auto && r.phase.transitions.length) {
        lines.push("Standard state and real mixture are two things. Below its boiling point the standard state of a species is the liquid, " +
          "and ΔH°, ΔS°, ΔG° and K above use it. In the gas mixture the species still stays a vapour until its partial pressure reaches " +
          "its vapour pressure. The conversion is calculated that way: a product leaves as liquid only once the gas is saturated with it.");
      }
    }
    lines.push("Thermodynamics fixes where the equilibrium lies, not how fast it is reached. A favourable ΔG° can still need a catalyst.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  /* What the choice of phase did, or would do. Every number is the solver's. */
  function phaseBlock(r) {
    const ph = r.phase;
    if (!ph) return "";
    let html = "";
    const boil = (t) => `${esc(t.compound.toLowerCase())} boils at ${fix(t.T_boil, 1)} K at 1 bar` +
      (t.T_boil_table ? ` (SVN Table B.1: ${fix(t.T_boil_table, 1)} K)` : "");
    if (ph.auto && ph.transitions.length) {
      const swapped = ph.swaps.map((s) => `${chem(s.typed)} → ${chem(s.used)}`).join(", ");
      const lines = ph.transitions.map((t) => `<li>${boil(t).replace(/^./, (c) => c.toUpperCase())}. Above that temperature ` +
        `${chem(t.gas)} is used, below it ${chem(t.liquid)}. There ΔH° of this reaction jumps by ` +
        `<strong>${signed(t.dH_jump / 1000, 2)} kJ/mol</strong> (ν × latent heat = ${signed(t.nu, 2).replace(".00", "")} × ${kJ(t.dH_vap)} kJ/mol) ` +
        `and ΔS° by ${signed(t.dS_jump, 1)} J/(mol·K), while ΔG° does not jump.</li>`).join("");
      html += TS.message("info", `<strong>Phase chosen by the solver.</strong> At ${fix(r.T, 2)} K and 1 bar ` +
        (swapped ? `the stable phase is not the one typed, so the calculation uses ${swapped}.`
          : "every species is already in its stable phase, so nothing is changed.") +
        ` The stable phase is the one with the lower Gibbs energy; where the two are equal, the liquid boils.` +
        `<ul class="explain" style="margin:8px 0 0">${lines}</ul>`);
    } else if (!ph.auto && ph.swaps.length) {
      const names = ph.swaps.map((s) => `${chem(s.typed)} (${boil(ph.transitions.find((t) => t.liquid === s.typed || t.gas === s.typed))})`).join("; ");
      html += `<div class="msg info"><strong>Phase:</strong> at ${fix(r.T, 2)} K and 1 bar this is not the stable phase of ${names}. ` +
        `The numbers below are for the phase that is typed. <button type="button" class="link" id="rx-use-stable">Pick the stable phase</button></div>`;
    }
    for (const s of ph.skipped) {
      if (ph.auto || s.why === "data") html += TS.message("info", `<strong>Phase:</strong> ${chem(s.message)}`);
    }
    return html;
  }

  /* The sentence about a species that leaves the gas as a liquid at equilibrium. */
  function condensedNote(x) {
    if (!x || !x.condensed || !x.condensed.length) return "";
    return ` (${x.condensed.map(chem).join(" and ")} ${x.condensed.length > 1 ? "leave" : "leaves"} as liquid` +
      `${x.extrapolated ? "; approximate, because the data of the liquid are stretched beyond their range" : ""})`;
  }

  function speciesTable(r) {
    const rows = r.species.map((s) => `<tr>
      <td class="l mono">${chem(s.id)}</td><td class="l">${esc(s.name)}</td>
      <td>${s.nu > 0 ? "+" : "−"}${coeff(s.nu)}</td>
      <td>${int(s.dHf)}</td><td>${int(s.dGf)}</td>
      <td>${fix(s.cp_T, 2)}</td><td>${int(s.sensible_dH)}</td><td>${int(s.nu_sensible_dH)}</td>
      <td class="${s.in_cp_range ? "" : "fail"}">${s.cp_Tmin === null ? "298.15 only" : `${fix(s.cp_Tmin, 0)}–${fix(s.cp_Tmax, 0)}`}${s.in_cp_range ? "" : " ⚠"}${s.cp_from_low_T_table ? ' <span class="badge neutral" title="Below 298.15 K the heat capacity is from NIST tables">NIST</span>' : ""}${s.cp_from_high_T_equation ? ' <span class="badge neutral" title="Above the SVN range the heat capacity is from the NIST Shomate equation">NIST</span>' : ""}</td>
    </tr>`).join("");
    const total = r.species.reduce((a, s) => a + (s.nu_sensible_dH || 0), 0);
    return `<div class="table-scroll"><table><thead><tr>
      <th class="l">Species</th><th class="l">Name</th><th>ν</th><th>ΔH°<sub>f,298</sub> (J/mol)</th>
      <th>ΔG°<sub>f,298</sub> (J/mol)</th><th>C<sub>p</sub>(T) (J/mol·K)</th>
      <th>∫C<sub>p</sub>dT, 298→T (J/mol)</th><th>ν·∫C<sub>p</sub>dT (J)</th><th>C<sub>p</sub> valid (K)</th>
      </tr></thead><tbody>${rows}
      <tr class="sum"><td class="l" colspan="7">Sum = ΔH°(T) − ΔH°<sub>298</sub></td><td>${int(total)}</td><td></td></tr>
      </tbody></table></div>`;
  }

  function stepsBlock(r) {
    const rows = r.steps.map((s, i) => `<div class="step-row">
      <div><div class="t">${i + 1}. ${esc(s.title)}</div>
        <div class="f">${esc(s.formula)}</div><div class="f">= ${esc(s.work)}</div></div>
      <div class="val">${sig(s.value, 7)} <span class="dim">${esc(s.unit)}</span></div></div>`).join("");
    return `<details open><summary>Step-by-step calculation</summary>${rows}</details>`;
  }

  function comparisonBlock(r) {
    const e = r.at_T;
    if (!e.constant_cp) return "";
    const lnKc = e.constant_cp.lnK;
    const lnKn = e.no_cp.lnK;
    const p = e.path;
    return `<details><summary>How much does the heat-capacity treatment matter at ${fix(r.T, 0)} K?</summary>
      <div class="table-scroll"><table><thead><tr><th class="l">Treatment of ΔC<sub>p</sub></th><th>ΔH° (kJ/mol)</th>
        <th>error</th><th>ΔG° (kJ/mol)</th><th>error</th><th>K</th></tr></thead><tbody>
      <tr><td class="l"><strong>C<sub>p</sub>(T) = A + BT + CT² + DT⁻²</strong> (used)</td><td>${kJ(e.dH)}</td><td>–</td><td>${kJ(e.dG)}</td><td>–</td><td>${fmtK(e.lnK)}</td></tr>
      <tr><td class="l">Constant ΔC<sub>p</sub> frozen at 298.15 K</td><td>${kJ(e.constant_cp.dH)}</td><td>${signed((e.constant_cp.dH - e.dH) / 1000)}</td><td>${kJ(e.constant_cp.dG)}</td><td>${signed((e.constant_cp.dG - e.dG) / 1000)}</td><td>${fmtK(lnKc)}</td></tr>
      <tr><td class="l">ΔC<sub>p</sub> ignored (ΔH°, ΔS° frozen at 298.15 K)</td><td>${kJ(e.no_cp.dH)}</td><td>${signed((e.no_cp.dH - e.dH) / 1000)}</td><td>${kJ(e.no_cp.dG)}</td><td>${signed((e.no_cp.dG - e.dG) / 1000)}</td><td>${fmtK(lnKn)}</td></tr>
      </tbody></table></div>
      <p class="hint" style="margin-top:10px">Hess path behind the temperature correction: cool the reactants from T to 298.15 K
        (${signed(p.cool_reactants / 1000)} kJ), react at 298.15 K (${signed(p.react_at_T0 / 1000)} kJ), heat the products back
        to T (${signed(p.heat_products / 1000)} kJ). Sum = ${kJ(e.dH)} kJ/mol.</p></details>`;
  }

  function formationBlock(r) {
    const rows = r.formation.map((f) => `<tr><td class="l mono">${chem(f.species)}</td>
      <td>${f.nu > 0 ? "+" : "−"}${coeff(f.nu)}</td>
      <td class="l mono">${f.is_element ? "element in its standard state" : (f.equation ? chem(f.equation) : "formation reaction not available (no SVN data for an element)")}</td>
      <td>${int(f.dHf)}</td><td>${int(f.nu * f.dHf)}</td></tr>`).join("");
    return `<details><summary>The reaction as a sum of formation reactions</summary>
      <p class="hint">ΔH°<sub>298</sub> = Σ ν<sub>i</sub> ΔH°<sub>f,i</sub> is Hess's law: each compound's formation reaction is
        added ν<sub>i</sub> times (negative ν reverses it) and the elements cancel.</p>
      <div class="table-scroll"><table><thead><tr><th class="l">Species</th><th>ν</th><th class="l">Formation reaction</th>
        <th>ΔH°<sub>f,298</sub> (J/mol)</th><th>ν·ΔH°<sub>f</sub> (J)</th></tr></thead><tbody>${rows}
        <tr class="sum"><td class="l" colspan="4">ΔH°<sub>298</sub></td><td>${int(r.at_T.dH0)}</td></tr></tbody></table></div></details>`;
  }

  function drawPlots(r) {
    const s = r.sweep;
    const e = r.at_T;
    if (!s) return;
    const k = (arr) => arr.map((v) => (v === null ? null : v / 1000));
    // Grey bands where a heat capacity is outside its range. With the stable-phase
    // choice each stretch between two boiling points has its own range, so the
    // solver lists the bands; otherwise they follow from the one valid range.
    const band = ([x0, x1]) => ({ type: "rect", xref: "x", yref: "paper", x0, x1, y0: 0, y1: 1,
      fillcolor: "rgba(160,120,0,0.13)", line: { width: 0 }, layer: "below" });
    const outside = s.out_of_range ? s.out_of_range.map(band) : TS.rangeShapes(s.T, r.valid_range);
    // A line at each boiling point that the solver used
    const first = s.T[0], last = s.T[s.T.length - 1];
    const boiling = (r.phase && r.phase.auto ? r.phase.transitions : []).filter((t) => t.T_boil > first && t.T_boil < last);
    const boilLines = boiling.map((t) => TS.vline(t.T_boil, "#c2410c"));
    const boilNotes = boiling.map((t, i) => ({ x: t.T_boil, y: 1 - 0.07 * (i % 3), yref: "paper", xanchor: "left", yanchor: "top",
      text: ` ${t.compound.toLowerCase()} boils`, showarrow: false, font: { size: 10.5, color: "#c2410c" } }));
    const shapes = outside.concat(boilLines, [TS.vline(r.T)]);
    TS.plot("rx-plot-energy", [
      { x: s.T, y: k(s.dH), name: "ΔH°", mode: "lines", line: { width: 2.5, color: "#c2410c" } },
      { x: s.T, y: k(s.dG), name: "ΔG°", mode: "lines", line: { width: 2.5, color: "#0b5cad" } },
      { x: s.T, y: k(s.TdS), name: "T·ΔS°", mode: "lines", line: { width: 1.8, color: "#11734b" } },
      { x: s.T, y: k(s.dH_const_cp), name: "ΔH°, constant ΔCp", mode: "lines", line: { width: 1.3, dash: "dash", color: "#c2410c" } },
      { x: s.T, y: k(s.dG_no_cp), name: "ΔG°, ΔCp ignored", mode: "lines", line: { width: 1.3, dash: "dot", color: "#0b5cad" } },
      { x: [r.T, r.T], y: [e.dH / 1000, e.dG / 1000], name: `at ${fix(r.T, 0)} K`, mode: "markers",
        marker: { size: 9, color: ["#c2410c", "#0b5cad"], line: { width: 1.5, color: "#fff" } }, showlegend: false },
    ], TS.layout("Energy changes versus temperature", "Temperature (K)", "kJ per mol of reaction", { shapes, annotations: boilNotes }));

    // Equilibrium conversion against temperature, at 1 bar and at the chosen pressure.
    if (s.conversion_1bar && s.conversion_1bar.some((v) => v !== null)) {
      const percent = (arr) => arr.map((v) => (v === null ? null : 100 * v));
      const traces = [{ x: s.T, y: percent(s.conversion_1bar), name: "1 bar", mode: "lines", line: { width: 2, dash: "dash", color: "#475569" } }];
      if (r.P !== 1) traces.push({ x: s.T, y: percent(s.conversion_P), name: `${fix(r.P, 1)} bar`, mode: "lines", line: { width: 2.5, color: "#0b5cad" } });
      TS.plot("rx-plot-X", traces, TS.layout("Equilibrium conversion (stoichiometric feed, ideal-gas mixture)", "Temperature (K)",
        "Conversion of the limiting reactant (%)", { shapes: outside.concat([TS.vline(r.T)]), yaxis: { range: [0, 100] } }));
    }

    const kShapes = outside.concat(boilLines, [TS.vline(r.T), TS.hline(0)]);
    const annotations = (r.crossover || []).filter((x) => x >= s.T[0] && x <= s.T[s.T.length - 1]).map((x) => ({
      x, y: 0, text: `K = 1 at ${fix(x, 0)} K`, showarrow: true, arrowhead: 2, ax: 40, ay: -34, font: { size: 11 } }));
    TS.plot("rx-plot-K", [
      { x: s.T, y: s.log10K, name: "log₁₀ K", mode: "lines", line: { width: 2.5, color: "#7c3aed" } },
      { x: [r.T], y: [e.log10K], mode: "markers", marker: { size: 9, color: "#7c3aed", line: { width: 1.5, color: "#fff" } }, showlegend: false },
    ], TS.layout("Equilibrium constant: products favoured above the dotted line", "Temperature (K)", "log₁₀ K",
      { shapes: kShapes, annotations, showlegend: false }));

    const sp = r.species.filter((x) => x.nu_sensible_dH !== null);
    TS.plot("rx-plot-sensible", [{
      type: "bar", x: sp.map((x) => x.id), y: sp.map((x) => x.nu_sensible_dH / 1000),
      marker: { color: sp.map((x) => (x.nu > 0 ? "#0b5cad" : "#c2410c")) },
      hovertemplate: "%{x}<br>ν·∫Cp dT = %{y:.2f} kJ<extra></extra>",
    }], TS.layout(`Sensible heat of each species, 298.15 K → ${fix(r.T, 0)} K (ν·∫Cp dT)`, "", "kJ per mol of reaction",
      { showlegend: false, hovermode: "closest" }));

    TS.plot("rx-plot-cp", [
      { x: s.T, y: s.dCp, name: "ΔCp°(T)", mode: "lines", line: { width: 2.5, color: "#0e7490" } },
      { x: [s.T[0], s.T[s.T.length - 1]], y: [e.dCp0, e.dCp0], name: "ΔCp° at 298.15 K (constant-Cp assumption)", mode: "lines",
        line: { width: 1.3, dash: "dash", color: "#0e7490" } },
    ], TS.layout("Heat-capacity change of reaction", "Temperature (K)", "J/(mol·K)", { shapes: outside.concat(boilLines, [TS.hline(0)]) }));
  }

  function render(r) {
    const out = $("#rx-out");
    const e = r.at_T;
    const exo = e.dH < 0 ? "exo" : "endo";
    const fav = e.favourability;
    const eq = r.equilibrium || {};
    const eqP = r.equilibrium_P || eq;
    let html = `<div class="panel">
      <div class="eqn">${chem(r.equation)}</div>
      <div class="verdict">
        <div class="v-item ${exo}"><div class="v-big">${e.dH < 0 ? "Gives out heat" : "Takes in heat"}</div>
          <div class="v-sub">${esc(e.thermicity)} at ${fix(r.T, 0)} K: ΔH° = ${kJ(e.dH)} kJ/mol</div></div>
        <div class="v-item ${fav.spontaneous_standard ? "good" : "bad"}"><div class="v-big">${fav.spontaneous_standard ? "Products favoured" : "Reactants favoured"}</div>
          <div class="v-sub">K = ${fmtK(e.lnK)} at ${fix(r.T, 0)} K and 1 bar: ΔG° = ${signed(e.dG / 1000, 2)} kJ/mol${fav.spontaneous_standard ? "" : ". Some product still forms"}</div></div>
        <div class="v-item neutral"><div class="v-big">Balanced</div>
          <div class="v-sub">every element checked; gas moles change by ${signed(e.delta_n_gas, 2).replace(".00", "")}</div></div>
      </div>`;
    html += (r.notes || []).map((n) => TS.message("info", `<strong>Note:</strong> ${chem(n)}`)).join("");
    html += phaseBlock(r);
    // With the hint and its button on the page, the plain hint about the same species would say it twice.
    const hinted = r.phase && !r.phase.auto ? r.phase.swaps.map((s) => s.typed) : [];
    html += TS.notes(r.warnings.filter((w) => !(w.kind === "phase" && hinted.includes(w.species))));
    html += `<div class="cards">
        <div class="card ${e.dH0 < 0 ? "exo" : "endo"}"><div class="k">ΔH°<sub>298</sub></div><div class="v">${kJ(e.dH0)} <span class="u">kJ/mol</span></div><div class="s">${esc(e.thermicity0)} at 298.15 K</div></div>
        <div class="card ${exo}"><div class="k">ΔH°(${fix(r.T, 0)} K)</div><div class="v">${kJ(e.dH)} <span class="u">kJ/mol</span></div><div class="s">${signed((e.dH - e.dH0) / 1000)} kJ from sensible heat</div></div>
        <div class="card"><div class="k">ΔS°(${fix(r.T, 0)} K)</div><div class="v">${fix(e.dS, 2)} <span class="u">J/(mol·K)</span></div><div class="s">${fix(e.dS0, 2)} at 298.15 K</div></div>
        <div class="card"><div class="k">ΔG°(${fix(r.T, 0)} K)</div><div class="v">${kJ(e.dG)} <span class="u">kJ/mol</span></div><div class="s">${kJ(e.dG0)} at 298.15 K</div></div>
        <div class="card"><div class="k">Equilibrium constant K</div><div class="v">${fmtK(e.lnK)}</div><div class="s">ln K = ${fix(e.lnK, 3)}</div></div>
        <div class="card"><div class="k">Equilibrium conversion at ${fix(r.P, 1)} bar</div><div class="v">${eqP.conversion === null || eqP.conversion === undefined ? "–" : pct(eqP.conversion)}</div><div class="s">${eqP.limiting_reactant ? "of " + chem(eqP.limiting_reactant) + ", stoichiometric feed" : ""}${condensedNote(eqP)}${r.P !== 1 && eq.conversion !== null && eq.conversion !== undefined ? ` (${pct(eq.conversion)} at 1 bar)` : ""}</div></div>
      </div>
      <h3>What the numbers mean</h3>${explain(r)}
    </div>`;

    if (r.sweep) {
      const hasX = r.sweep.conversion_1bar && r.sweep.conversion_1bar.some((v) => v !== null);
      html += `<div class="panel"><div class="grid two">
        ${TS.fig("rx-plot-energy", "orange is ΔH° (the heat of reaction), blue is ΔG° (which side is favoured), green is T·ΔS°. At every temperature blue = orange − green. Where the blue line crosses zero, K = 1. The thin dashed and dotted lines are what the shortcuts on C<sub>p</sub> would give. The dots mark your temperature.")}
        ${TS.fig("rx-plot-K", "the higher the line, the more the products are favoured. Above the dotted line K is larger than 1, below it smaller. A line that falls to the right belongs to a reaction that gives out heat; one that rises, to a reaction that takes in heat.")}
        ${hasX ? TS.fig("rx-plot-X", "how much of the limiting reactant has reacted when the reaction comes to rest. The dashed grey line is at 1 bar, the blue line at the pressure you typed. If the reaction makes fewer gas molecules, the blue line lies above the grey one: pressure helps.") : ""}
        ${TS.fig("rx-plot-cp", "ΔC<sub>p</sub>° is the heat capacity of the products minus that of the reactants. It is the slope of the ΔH° line: where it is negative, ΔH° falls as the temperature rises. The dashed line is its value at 298.15 K, which the constant-C<sub>p</sub> shortcut uses everywhere.")}
        ${TS.fig("rx-plot-sensible", "one bar per species: the heat it takes up between 298.15 K and your temperature, times its stoichiometric number (blue for products, orange for reactants). Added together, the bars are the difference between ΔH° at your temperature and ΔH° at 298.15 K.")}</div>
        <p class="hint" style="margin:8px 0 0">Shaded bands mark temperatures outside the validity range of at least one
          heat-capacity correlation (valid ${r.valid_range ? `${fix(r.valid_range[0], 0)} to ${fix(r.valid_range[1], 0)} K` : "at 298.15 K only"} for this reaction).
          The dotted vertical line is the selected temperature.${r.phase && r.phase.auto && r.phase.transitions.length ? ` Each orange dotted line is a boiling point.
          There the orange ΔH° line has a step, which is the latent heat, and the ΔC<sub>p</sub>° line has one too, because liquid and vapour have
          different heat capacities. The blue ΔG° line and the K line only bend.` : ""}${r.valid_range && r.valid_range[0] < 298 ? ` Below 298.15 K the heat capacities
          come from NIST tables and above it from SVN. The two do not give exactly the same C<sub>p</sub> at 298.15 K, which is the small step in the
          ΔC<sub>p</sub> plot; ΔH°, ΔG° and K stay continuous.` : ""}</p></div>`;
    } else {
      html += `<div class="panel">${TS.message("info", "SVN gives no heat capacity for at least one species of this reaction, so only the 298.15 K values are available and no temperature plot is drawn.")}</div>`;
    }

    html += `<div class="panel"><h3>Species data and individual sensible heats</h3>${speciesTable(r)}
      ${stepsBlock(r)}${comparisonBlock(r)}${formationBlock(r)}${TS.auditTable(r.audit)}</div>`;
    out.innerHTML = html;
    const useStable = $("#rx-use-stable");
    if (useStable) useStable.addEventListener("click", () => { $("#rx-auto-phase").checked = true; calculate(); });
    drawPlots(r);
  }

  function calculate() {
    const out = $("#rx-out");
    out.dataset.input = "rx-equation";
    return TS.run($("#rx-run"), out, async () => {
      const result = await TS.engine.call("analyze", {
        equation: $("#rx-equation").value,
        T: TS.readNumber("rx-T"),
        P: TS.readNumber("rx-P"),
        T_min: TS.readNumber("rx-Tmin"),
        T_max: TS.readNumber("rx-Tmax"),
        auto_phase: $("#rx-auto-phase").checked,
      });
      render(result);
    });
  }

  function showCelsius() {
    const T = Number($("#rx-T").value);
    $("#rx-TC").textContent = Number.isFinite(T) && $("#rx-T").value !== "" ? `= ${fix(T - 273.15, 2)} °C` : "";
  }

  TS.tabs.push({
    id: "reaction",
    init() {
      const select = $("#rx-select");
      const input = $("#rx-equation");
      TS.fillReactionSelect(select, input, {
        onPick: (rxn) => { $("#rx-T").value = rxn.T; $("#rx-Tmin").value = ""; $("#rx-Tmax").value = ""; showCelsius(); calculate(); },
      });
      $("#rx-T").addEventListener("input", showCelsius);
      $("#rx-run").addEventListener("click", calculate);
      $("#rx-auto-phase").addEventListener("change", calculate);
      for (const id of ["rx-equation", "rx-T", "rx-P", "rx-Tmin", "rx-Tmax"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      TS.pickReaction(select, input, "co2_methanol", (rxn) => { $("#rx-T").value = rxn.T; });
      showCelsius();
      calculate();
    },
  });
})();
