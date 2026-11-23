/* Tab 2: ideal gas against real gas. What pressure does to the heat of reaction,
 * through the residual enthalpy H^R = H(real gas) - H(ideal gas).
 * The user does not pick the equation of state (the user's request of 23 November 2026): the
 * solver uses, for each gas, the one closest to measured data (thermosolver/eoschoice.py). */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, int, signed, coeff } = TS;

  const STATE_LABEL = (s) => {
    if (s.phase !== "g") return "liquid or solid: no pressure correction";
    if (s.treated_ideal) return "treated as ideal gas";
    if (s.state === "liquid_like") return "a liquid at this T and P, not a gas";
    if (s.state === "hypothetical_vapour") return "a liquid on its own at this T and P; taken as a vapour";
    return "gas";
  };

  const heat = (joule) => (joule < 0 ? "releases" : "absorbs");

  /* --------------------------------------------- where does it matter? */
  let overview = null;

  function drawOverview() {
    const box = $("#pr-overview");
    if (!box || !overview) return;
    const top = overview.rows.reduce((m, x) => Math.max(m, Math.abs(x.percent || 0)), 0) || 1;
    const rows = overview.rows.map((x, i) => `
      <div class="lab" style="font-family:inherit"><button type="button" class="link pr-case" data-i="${i}">${esc(x.name)}</button>
        <span class="dim">&nbsp;${fix(x.T, 0)} K, ${fix(x.P, 0)} bar</span></div>
      <div class="track"><div class="fill" style="width:${fix(100 * Math.abs(x.percent || 0) / top, 1)}%;background:var(--accent)"></div></div>
      <div class="num">${x.percent === null ? "–" : `${signed(x.residual / 1000, 2)} kJ/mol · ${signed(x.percent, 1)} %`}
        <span class="dim" style="font-weight:500">${esc(x.size || "")}</span></div>`).join("");
    box.innerHTML = `<details open><summary>Where does the real gas differ from the ideal gas?</summary>
      <p class="hint">Six industrial reactions at their usual conditions. The bar is the residual part of the heat of reaction,
        as a percentage of the ideal-gas value, with the equation of state chosen for each gas. Cold, dense, polar gases such as methanol,
        water and ammonia are far from ideal; hot, light gases are not. Click a name to load that case.</p>
      <div class="bars">${rows}</div></details>`;
    for (const button of box.querySelectorAll(".pr-case")) {
      button.addEventListener("click", () => {
        const x = overview.rows[Number(button.dataset.i)];
        $("#pr-T").value = x.T;
        $("#pr-P").value = x.P;
        $("#pr-Pmax").value = Math.max(50, Math.round(x.P * 1.5));
        TS.pickReaction($("#pr-select"), $("#pr-equation"), x.id);
        calculate();
      });
    }
  }

  /* ------------------------------------------------------ explanation */
  function explain(r) {
    const a = r.at_P;
    const c = r.comparison;
    const lines = [];
    const T = fix(r.T, 0);
    const P = fix(r.P, 1);
    lines.push(`Why the ideal-gas value does not change with pressure: an ideal gas has no forces between its molecules, so its ` +
      `internal energy U depends on temperature only. Also PV = RT, so H = U + PV = U + RT depends on temperature only too. ` +
      `As ideal gases the reaction ${heat(c.dH_ideal)} ${kJ(Math.abs(c.dH_ideal))} kJ/mol at ${T} K, <em>whatever the pressure</em>.`);
    if (!a.gas_phase_valid) {
      const which = a.species.filter((s) => a.no_vapour_species.includes(s.species))
        .map((s) => `${chem(s.species)} (${esc(s.model_name)})`).join(", ");
      lines.push(`At ${T} K and ${P} bar, ${which} is a liquid, not a gas, according to the equation of state used for it. ` +
        `A gas-phase heat of reaction is not defined at this ` +
        `pressure, so no value is reported. Lower the pressure or raise the temperature.`);
      return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
    }
    if (r.model === "ideal") {
      lines.push("The ideal-gas model is selected, so the residual part is zero. Pick a real-gas model to see what pressure does.");
      return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
    }
    lines.push(`Why a real gas is different: its molecules attract each other. Raising the pressure pushes them closer together, ` +
      `so the attraction counts for more and the enthalpy drops below the ideal-gas value. It is the same effect that makes the ` +
      `compressibility factor Z smaller than 1. The residual enthalpy H<sup>R</sup> = H(real gas) − H(ideal gas) measures it for each ` +
      `species at ${T} K and ${P} bar. Added up over the reaction it is Σν<sub>i</sub>H<sub>i</sub><sup>R</sup> = ` +
      `<strong>${signed(c.residual / 1000, 3)} kJ/mol</strong>.`);
    lines.push(`So the real gas ${heat(c.dH_real)} <strong>${kJ(Math.abs(c.dH_real))} kJ/mol</strong>, which is ` +
      `${fix(Math.abs(c.percent), 2)} % ${c.percent < 0 ? "less" : "more"} than the ideal-gas value. The pressure effect is ` +
      `<strong>${esc(c.size)}</strong> here: a heat balance made with the ideal-gas value would be off by ` +
      `${kJ(Math.abs(c.residual))} kJ for every mole that reacts.`);
    const p = c.path;
    // The terms of steps 1 and 3, written out from the table at the bottom of the tab (the sums are the solver's).
    const J = (v) => TS.int(v).replace("-", "−");
    const terms = (products) => a.species.filter((s) => (products ? s.nu > 0 : s.nu < 0))
      .map((s) => `${coeff(s.nu)} × ${s.HR < 0 ? `(${J(s.HR)})` : J(s.HR)}`).join(" + ");
    lines.push(`The three steps above reach the real-gas value by a detour, in the same way as Hess's law. ` +
      `<strong>Step 1</strong>: take the reactants from real gas to ideal gas. That removes their H<sup>R</sup>: ` +
      `−[${terms(false)}] J = ${signed(p.reactants_to_ideal / 1000, 2)} kJ. ` +
      `<strong>Step 2</strong>: let the ideal gases react. That is ΔH° from tab 1, ${signed(p.ideal_reaction / 1000, 2)} kJ. ` +
      `<strong>Step 3</strong>: take the products from ideal gas to real gas. That adds their H<sup>R</sup>: ` +
      `${terms(true)} J = ${signed(p.products_to_real / 1000, 2)} kJ. ` +
      `Each H<sup>R</sup> is in the table at the bottom of this tab, from the equation of state chosen for that gas. H depends only on where you start and where ` +
      `you end, not on the route, so the three steps add up to the real-gas value (${signed(p.total / 1000, 2)} kJ/mol).`);
    lines.push(`The gap between real and ideal grows with pressure (first graph), because the molecules are pushed closer together ` +
      `and attract each other more. It shrinks as the temperature rises (third graph), because hotter molecules move faster and have ` +
      `more energy, so the pull between them matters less and the gas behaves more like an ideal gas (Z closer to 1).`);
    lines.push("Assumptions: each species is taken as the pure species at T and P, and mixing the gases is taken to change no enthalpy; " +
      "the enthalpy of solids and liquids is taken not to change with pressure.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  /* No gas-phase value at this pressure: say why in plain words and offer conditions where there is one. */
  function limitBox(r) {
    const g = r.gas_limit || {};
    const who = r.at_P.no_vapour_species.map(chem).join(", ");
    const t = r.sweep_T ? r.sweep_T.first_valid_T : null;
    const hot = t !== null && t > r.T ? Math.ceil(t / 10) * 10 : null;
    let text = `<strong>No gas-phase value at ${fix(r.P, 0)} bar.</strong> At ${fix(r.T, 0)} K and ${fix(r.P, 0)} bar, ${who} ` +
      `is a liquid, not a gas, so a gas-phase heat of reaction does not exist here. This is a limit of the conditions, not a fault of the solver.`;
    if (g.P_max) text += ` At ${fix(r.T, 0)} K a gas-phase value exists up to about ${fix(g.P_max, 0)} bar.`;
    if (hot) text += ` At ${fix(r.P, 0)} bar it exists above about ${fix(t, 0)} K.`;
    const buttons = [];
    if (g.P_suggest) buttons.push(`<button type="button" class="link pr-fix" data-p="${g.P_suggest}">Use ${fix(g.P_suggest, 0)} bar</button>`);
    if (hot) buttons.push(`<button type="button" class="link pr-fix" data-t="${hot}">Use ${hot} K</button>`);
    return TS.message("info", text + (buttons.length ? `<br>${buttons.join(" &nbsp;·&nbsp; ")}` : ""));
  }

  function leg(title, detail, joule, extra = "") {
    const cls = joule < -0.5 ? "neg" : (joule > 0.5 ? "pos" : "");
    return `<div class="leg ${cls} ${extra}"><div class="t">${title}</div><div class="d">${detail}</div>
      <div class="q">${signed(joule / 1000, 2)} kJ</div></div>`;
  }

  function pathBlock(r) {
    const p = r.comparison.path;
    if (p.total === null || r.model === "ideal") return "";
    return `<h3>The real-gas heat of reaction in three steps</h3><div class="path">
      ${leg("Step 1", "real reactants → ideal gas", p.reactants_to_ideal)}
      ${leg("Step 2", `reaction as ideal gases, ΔH°(${fix(r.T, 0)} K)`, p.ideal_reaction)}
      ${leg("Step 3", "ideal-gas products → real gas", p.products_to_real)}
      ${leg("Sum", `ΔH at ${fix(r.P, 0)} bar, real gas`, p.total, "sum")}</div>`;
  }

  /* ----------------------------------------------------------- tables */
  /* Which equation of state a gas uses, and why (the solver's choice). */
  function equationCell(s) {
    const c = s.choice;
    if (!c || s.phase !== "g") return `<td class="l dim">–</td>`;
    if (c.basis === "no_critical") return `<td class="l dim">ideal gas (no critical constants)</td>`;
    const why = c.basis === "measured"
      ? `closest to NIST data: off by ${fix(c.mean_error / 1000, 2)} kJ/mol on average (${c.points} points)`
      : `no NIST data for this gas: the closest equation over all ${c.gases} measured gases`;
    return `<td class="l"><strong>${esc(s.model_name)}</strong><br><span class="dim">${why}</span></td>`;
  }

  function residualTable(r) {
    const rows = r.at_P.species.map((s) => `<tr>
      <td class="l mono">${chem(s.species)}</td><td>${s.nu > 0 ? "+" : "−"}${coeff(s.nu)}</td>
      ${equationCell(s)}
      <td>${s.Tr === null ? "–" : fix(s.Tr, 3)}</td><td>${s.Pr === null ? "–" : fix(s.Pr, 3)}</td>
      <td>${fix(s.Z, 4)}</td><td>${int(s.HR)}</td><td>${fix(s.SR, 3)}</td>
      <td>${int(s.nu * s.HR)}</td>
      <td class="l ${s.state === "liquid_like" ? "fail" : "dim"}">${STATE_LABEL(s)}</td></tr>`).join("");
    return `<div class="table-scroll"><table><thead><tr><th class="l">Species</th><th>ν</th><th class="l">Equation of state</th><th>T<sub>r</sub></th><th>P<sub>r</sub></th>
      <th>Z</th><th>H<sup>R</sup> (J/mol)</th><th>S<sup>R</sup> (J/mol·K)</th><th>ν·H<sup>R</sup> (J)</th><th class="l">State</th></tr></thead>
      <tbody>${rows}<tr class="sum"><td class="l" colspan="8">Σ ν<sub>i</sub>H<sub>i</sub><sup>R</sup> = ΔH(T,P) − ΔH°(T)</td>
      <td>${r.at_P.gas_phase_valid ? int(r.at_P.sum_HR) : "not defined"}</td><td></td></tr></tbody></table></div>`;
  }

  /* ------------------------------------------------------------ plots */
  function drawPlots(r) {
    const s = r.sweep;
    const c = r.comparison;
    const k = (arr) => arr.map((v) => (v === null ? null : v / 1000));
    const mark = [TS.vline(r.P)];
    const real = r.model !== "ideal";
    const t = r.sweep_T;
    const bars = c.contributions.filter((x) => x.contribution !== null);
    const gas = r.at_P.species.filter((x) => x.phase === "g");

    // All four graphs show residual quantities in kJ/mol, and all four cover exactly the
    // same range of values, so a number can be read across from one graph to another.
    // The value at your pressure in graph 1, the sum of the bars in graph 2 and the dot
    // in graph 3 are the same number.
    const scale = TS.span([k(s.sum_HR), bars.map((x) => x.contribution / 1000), t ? k(t.residual) : [],
      ...gas.map((x) => k(s.species_HR[x.species]))], [0]);
    const residualAxis = scale ? { range: scale } : {};
    // Each x axis covers only the pressures or temperatures at which its graph has a value:
    // where a species would be a liquid there is no gas-phase value, and the axis stops.
    const full = [s.P[0], s.P[s.P.length - 1]];
    const pAxis = TS.axis(TS.xExtent(s.P, [s.sum_HR]) || full);
    const pAxisSpecies = TS.axis(TS.xExtent(s.P, gas.map((x) => s.species_HR[x.species])) || full);

    // 1. Real gas minus ideal gas along the isotherm. The ideal gas is the zero line.
    const traces = [
      { x: s.P, y: s.P.map(() => 0), name: "Ideal gas (no residual part)", mode: "lines",
        line: { width: 2, dash: "dash", color: "#475569" } },
      { x: s.P, y: k(s.sum_HR), name: "Real gas minus ideal gas", mode: "lines", fill: "tonexty",
        fillcolor: "rgba(194,65,12,0.14)", line: { width: 2.5, color: "#c2410c" } },
    ];
    if (c.residual !== null) {
      traces.push({ x: [r.P], y: [c.residual / 1000], mode: "markers", showlegend: false,
        marker: { size: 9, color: "#c2410c", line: { width: 1.5, color: "#fff" } },
        hovertemplate: "%{y:.2f} kJ/mol at %{x:.0f} bar<extra></extra>" });
    }
    TS.plot("pr-plot-dH", traces,
      TS.layout(`How much the real gas differs from the ideal gas at ${fix(r.T, 0)} K`, "Pressure (bar)", "Σ ν Hᴿ (kJ per mol of reaction)",
        { shapes: mark, xaxis: pAxis, yaxis: residualAxis }));

    // 2. Which species the difference comes from, at the chosen state.
    TS.plot("pr-plot-bars", [{
      type: "bar", x: bars.map((x) => x.species), y: bars.map((x) => x.contribution / 1000),
      marker: { color: bars.map((x) => (x.role === "product" ? "#0b5cad" : "#c2410c")) },
      hovertemplate: "%{x}<br>ν·H<sup>R</sup> = %{y:.3f} kJ<extra></extra>",
    }], TS.layout(`Where the difference comes from: ν·Hᴿ of each species at ${fix(r.P, 0)} bar`, "", "kJ per mol of reaction",
      { showlegend: false, hovermode: "closest", shapes: [TS.hline(0)], yaxis: residualAxis }));

    // 3. The same pressure at other temperatures.
    if (t) {
      const tTraces = [{ x: t.T, y: k(t.residual), name: "Σ ν Hᴿ", mode: "lines", line: { width: 2.5, color: "#c2410c" } }];
      if (c.residual !== null) {
        tTraces.push({ x: [r.T], y: [c.residual / 1000], mode: "markers", showlegend: false,
          marker: { size: 9, color: "#c2410c", line: { width: 1.5, color: "#fff" } } });
      }
      TS.plot("pr-plot-T", tTraces,
        TS.layout(`Residual part at ${fix(r.P, 0)} bar: it fades as the gas gets hotter`, "Temperature (K)", "Σ ν Hᴿ (kJ per mol of reaction)",
          { showlegend: false, shapes: [TS.vline(r.T), TS.hline(0)], xaxis: TS.axis(TS.xExtent(t.T, [t.residual])), yaxis: residualAxis }));
    }

    // 4. Residual enthalpy of each pure species along the isotherm.
    const palette = TS.palette();
    TS.plot("pr-plot-HR", gas.map((x, i) => ({
      x: s.P, y: k(s.species_HR[x.species]), name: x.species, mode: "lines", line: { width: 2, color: palette[i % palette.length] },
    })), TS.layout(`Residual enthalpy of each pure species at ${fix(r.T, 0)} K${real ? "" : " (ideal gas: zero)"}`, "Pressure (bar)",
      "Hᴿ (kJ per mol of the species)", { shapes: mark.concat([TS.hline(0)]), xaxis: pAxisSpecies, yaxis: residualAxis }));
  }

  /* ----------------------------------------------------------- render */
  function render(r) {
    const a = r.at_P;
    const c = r.comparison;
    const ok = a.gas_phase_valid;
    const sign = c.dH_real === null ? "" : (c.dH_real < 0 ? "exo" : "endo");
    let html = `<div class="panel"><div class="eqn">${chem(r.equation)} <small>&nbsp; at ${fix(r.T, 2)} K and ${fix(r.P, 2)} bar,
      ${r.model === "auto" ? "each gas with the equation of state chosen for it" : esc(a.model_name)}</small></div>`;
    html += `<div class="verdict">
        <div class="v-item neutral"><div class="v-big">Ideal gas: ${kJ(c.dH_ideal)} kJ/mol</div>
          <div class="v-sub">ΔH°(${fix(r.T, 0)} K), the same at every pressure</div></div>
        <div class="v-item ${sign}"><div class="v-big">Real gas: ${ok ? kJ(c.dH_real) + " kJ/mol" : "not a gas here"}</div>
          <div class="v-sub">ΔH at ${fix(r.P, 0)} bar = ideal value + residual part</div></div>
        <div class="v-item"><div class="v-big">Difference: ${ok ? signed(c.residual / 1000, 2) + " kJ/mol" : "–"}</div>
          <div class="v-sub">${ok && c.percent !== null ? `${fix(Math.abs(c.percent), 2)} %: ${esc(c.effect)} (${esc(c.size)})` : "no gas-phase value at this pressure"}</div></div>
      </div>`;
    // The note about a species that is a liquid here is replaced by a plain box with a way out; a species that would
    // condense on its own gets a note, not a warning.
    html += TS.notes(r.warnings.filter((w) => w.level !== "info")) +
      TS.notes(a.notes.filter((n) => n.level !== "info" && n.kind !== "no_vapour_root"));
    if (!ok) html += limitBox(r);
    html += TS.notes(a.notes.filter((n) => n.kind === "condensation"));
    html += `<div class="cards">
        <div class="card"><div class="k">Residual part, Σ ν H<sup>R</sup></div><div class="v">${ok ? signed(c.residual / 1000, 3) : "–"} <span class="u">kJ/mol</span></div><div class="s">real gas minus ideal gas</div></div>
        <div class="card"><div class="k">Residual entropy part, Σ ν S<sup>R</sup></div><div class="v">${ok ? signed(a.sum_SR, 2) : "–"} <span class="u">J/(mol·K)</span></div><div class="s">real gas minus ideal gas</div></div>
      </div>${pathBlock(r)}<h3>What the numbers mean</h3>${explain(r)}</div>`;
    const hints = [];
    if (r.sweep.first_invalid_P) {
      hints.push(`The real-gas curve stops near ${fix(r.sweep.first_invalid_P, 0)} bar: above that, a species is a liquid at this temperature, so a gas-phase value does not exist.`);
    }
    if (r.sweep_T && r.sweep_T.gas_from) {
      hints.push(`The temperature graph starts at ${fix(r.sweep_T.gas_from, 0)} K: below that, a species is a liquid at ${fix(r.P, 0)} bar, so there is no gas-phase value to plot.`);
    }
    html += `<div class="panel"><div class="grid two">
      ${TS.fig("pr-plot-dH", "how much the real-gas heat of reaction differs from the ideal-gas value, at each pressure. The dashed grey line at zero is the ideal gas: it is flat, because pressure does not change the enthalpy of an ideal gas. The orange line is the residual part, Σ ν Hᴿ, and it grows as the pressure rises. The dot marks your pressure; the real-gas value is the ideal value plus this number.")}
      ${TS.fig("pr-plot-bars", "one bar per species: its residual enthalpy times its stoichiometric number (blue for products, orange for reactants). Added together, the bars are the gap in the first plot. The tallest bar belongs to the gas that is furthest from ideal.")}
      ${r.sweep_T ? TS.fig("pr-plot-T", "the same residual part at your pressure, but at other temperatures. It shrinks towards zero as the gas gets hotter, because a hot gas behaves almost ideally. The dot marks your temperature.") : ""}
      ${TS.fig("pr-plot-HR", "the residual enthalpy of each pure gas against pressure. A line that stays near zero is an almost ideal gas. A line that falls steeply is a gas close to its critical point, where the molecules attract each other strongly.")}</div>
      <p class="hint" style="margin:8px 0 0">All four graphs cover exactly the same range of values (in kJ/mol), so a number can be read
        across from one graph to another. The value at your pressure in the first graph, the sum of the bars and the dot in the third graph
        are the same number.</p>
      ${hints.map((h) => `<p class="hint" style="margin:8px 0 0">${h}</p>`).join("")}</div>`;
    html += `<div class="panel"><h3>Residual properties of each species at ${fix(r.T, 0)} K, ${fix(r.P, 1)} bar</h3>
      ${residualTable(r)}${TS.notes(a.notes.filter((n) => n.level === "info" && n.kind !== "condensation"))}</div>`;
    $("#pr-out").innerHTML = html;
    for (const button of $("#pr-out").querySelectorAll(".pr-fix")) {
      button.addEventListener("click", () => {
        if (button.dataset.p) {
          $("#pr-P").value = button.dataset.p;
          $("#pr-Pmax").value = Math.max(50, Math.round(Number(button.dataset.p) * 1.5));
        }
        if (button.dataset.t) $("#pr-T").value = button.dataset.t;
        calculate();
      });
    }
    drawPlots(r);
  }

  function calculate() {
    const out = $("#pr-out");
    out.dataset.input = "pr-equation";
    return TS.run($("#pr-run"), out, async () => {
      render(await TS.engine.call("pressure", {
        equation: $("#pr-equation").value,
        T: TS.readNumber("pr-T"),
        P: TS.readNumber("pr-P"),
        P_max: TS.readNumber("pr-Pmax"),
        model: "auto",          // the solver chooses the equation of state for each gas
      }));
    });
  }

  let started = false;
  TS.tabs.push({
    id: "pressure",
    init() {
      const select = $("#pr-select");
      const input = $("#pr-equation");
      TS.fillReactionSelect(select, input, {
        filter: (r) => r.valid_range !== null,
        onPick: (rxn) => {
          // A reaction of the overview list opens at its own industrial conditions; any other keeps the pressure.
          const known = overview ? overview.rows.find((x) => x.id === rxn.id) : null;
          if (known) {
            $("#pr-T").value = known.T;
            $("#pr-P").value = known.P;
            $("#pr-Pmax").value = Math.max(50, Math.round(known.P * 1.5));
          } else {
            // at least 350 K, unless the heat capacities of this reaction end below that
            const top = rxn.valid_range ? rxn.valid_range[1] : rxn.T;
            $("#pr-T").value = top < 350 ? rxn.T : Math.max(rxn.T, 350);
          }
          calculate();
        },
      });
      $("#pr-run").addEventListener("click", calculate);
      for (const id of ["pr-equation", "pr-T", "pr-P", "pr-Pmax"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      TS.pickReaction(select, input, "ammonia");
    },
    onShow() {
      if (started) return;
      started = true;
      calculate();
      TS.engine.call("pressure_overview", {}).then((o) => { overview = o; drawOverview(); }).catch(() => {});
    },
  });
})();
