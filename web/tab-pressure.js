/* Tab 2: effect of pressure at constant temperature (residual properties). */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, int, sig, signed, pct, coeff } = TS;

  const STATE_LABEL = (s) => {
    if (s.phase !== "g") return "condensed phase, no correction";
    if (s.treated_ideal) return "treated as ideal gas";
    if (s.state === "liquid_like") return "liquid root only: not a gas";
    if (s.state === "hypothetical_vapour") return "above vapour pressure: hypothetical vapour";
    return "gas";
  };

  function explain(r) {
    const a = r.at_P;
    const lines = [];
    const T = fix(r.T, 0);
    lines.push(`For ideal gases ΔH would be ${kJ(a.dH_std)} kJ/mol at ${T} K <em>at any pressure</em>, because the ` +
      `enthalpy of an ideal gas depends on temperature only.`);
    if (!a.gas_phase_valid) {
      lines.push(`At ${T} K and ${fix(r.P, 1)} bar, ${a.no_vapour_species.map(chem).join(", ")} has no vapour-like state with the ` +
        `${esc(a.model_name)} equation: the pure species is a liquid there. A gas-phase heat of reaction is not defined at this ` +
        `pressure, so no value is reported. Lower the pressure or raise the temperature.`);
      return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
    }
    if (r.model === "ideal") {
      lines.push("The ideal-gas model is selected, so no pressure effect on ΔH is calculated. Pick a real-gas model to see it.");
    } else {
      const shift = a.sum_HR;
      lines.push(`At ${fix(r.P, 1)} bar the residual enthalpies add Σν<sub>i</sub>H<sub>i</sub><sup>R</sup> = ` +
        `<strong>${signed(shift / 1000, 3)} kJ/mol</strong>, so ΔH(T,P) = ${kJ(a.dH_P, 3)} kJ/mol ` +
        `(${fix(100 * Math.abs(shift / a.dH_std), 2)} % ${shift * a.dH_std > 0 ? "larger" : "smaller"} in magnitude).`);
      const worst = a.species.filter((s) => s.phase === "g" && !s.treated_ideal)
        .sort((x, y) => Math.abs(y.nu * y.HR) - Math.abs(x.nu * x.HR))[0];
      if (worst) {
        lines.push(`The largest contribution comes from ${chem(worst.species)} (T<sub>r</sub> = ${fix(worst.Tr, 2)}, ` +
          `P<sub>r</sub> = ${fix(worst.Pr, 2)}, Z = ${fix(worst.Z, 3)}): the closer a gas is to its critical point, ` +
          `the more its molecules attract each other and the more negative its H<sup>R</sup>.`);
      }
      lines.push(`Fugacity coefficients change the equilibrium too: K<sub>φ</sub> = Π φ<sub>i</sub><sup>ν<sub>i</sub></sup> = ` +
        `${sig(a.K_phi, 4)}. The mole-fraction quotient at equilibrium is K·(P/P°)<sup>−Δν</sup>/K<sub>φ</sub>.`);
    }
    const turned = (a.dG_std > 0) !== (a.dG_P > 0);
    lines.push(`Favourability at these conditions: with every species pure at ${T} K and ${fix(r.P, 1)} bar, ` +
      `ΔG(T,P) = ${kJ(a.dG_P, 2)} kJ/mol, so the reaction is <strong>${a.dG_P < 0 ? "favourable" : "unfavourable"}</strong> here` +
      (turned ? ` even though ΔG° at 1 bar is ${kJ(a.dG_std, 2)} kJ/mol. Pressure alone has changed the verdict, because Δν(gas) = ${signed(a.delta_n_gas, 2).replace(".00", "")}.`
        : ` (ΔG° at 1 bar is ${kJ(a.dG_std, 2)} kJ/mol).`));
    const ei = r.equilibrium_ideal;
    const er = r.equilibrium_real;
    if (ei && er && ei.conversion !== null && er.conversion !== null && ei.limiting_reactant) {
      lines.push(`Equilibrium conversion of ${chem(ei.limiting_reactant)} at ${fix(r.P, 1)} bar (stoichiometric feed): ` +
        `${pct(ei.conversion, 2)} as an ideal gas, ${pct(er.conversion, 2)} with ${esc(a.model_name)}.`);
    }
    lines.push("Assumptions: each species is the pure component at T and P (ideal-solution mixing, so no heat of mixing); " +
      "solids and liquids are incompressible with unit activity.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  function residualTable(r) {
    const rows = r.at_P.species.map((s) => `<tr>
      <td class="l mono">${chem(s.species)}</td><td>${s.nu > 0 ? "+" : "−"}${coeff(s.nu)}</td>
      <td>${s.Tr === null ? "–" : fix(s.Tr, 3)}</td><td>${s.Pr === null ? "–" : fix(s.Pr, 3)}</td>
      <td>${fix(s.Z, 4)}</td><td>${int(s.HR)}</td><td>${fix(s.SR, 3)}</td><td>${fix(s.phi, 4)}</td>
      <td>${int(s.nu * s.HR)}</td>
      <td class="l ${s.state === "liquid_like" ? "fail" : "dim"}">${STATE_LABEL(s)}</td></tr>`).join("");
    return `<div class="table-scroll"><table><thead><tr><th class="l">Species</th><th>ν</th><th>T<sub>r</sub></th><th>P<sub>r</sub></th>
      <th>Z</th><th>H<sup>R</sup> (J/mol)</th><th>S<sup>R</sup> (J/mol·K)</th><th>φ</th><th>ν·H<sup>R</sup> (J)</th><th class="l">State</th></tr></thead>
      <tbody>${rows}<tr class="sum"><td class="l" colspan="8">Σ ν<sub>i</sub>H<sub>i</sub><sup>R</sup> = ΔH(T,P) − ΔH°(T)</td>
      <td>${r.at_P.gas_phase_valid ? int(r.at_P.sum_HR) : "not defined"}</td><td></td></tr></tbody></table></div>`;
  }

  function modelTable(r) {
    const rows = r.models.map((m) => `<tr><td class="l">${m.model === r.model ? "<strong>" + esc(m.name) + "</strong> (selected)" : esc(m.name)}</td>
      <td>${int(m.sum_HR)}</td><td>${kJ(m.dH_P, 3)}</td><td>${fix(m.sum_SR, 3)}</td><td>${kJ(m.dG_P, 3)}</td><td>${sig(m.K_phi, 4)}</td></tr>`).join("");
    return `<details open><summary>Same state, every model</summary>
      <div class="table-scroll"><table><thead><tr><th class="l">Model</th><th>Σν H<sup>R</sup> (J/mol)</th><th>ΔH(T,P) (kJ/mol)</th>
      <th>Σν S<sup>R</sup> (J/mol·K)</th><th>ΔG(T,P) (kJ/mol)</th><th>K<sub>φ</sub></th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="hint" style="margin-top:8px">The spread between the cubic equations is a fair measure of the model uncertainty.
        The virial equation truncated after B is only for low to moderate pressure.</p></details>`;
  }

  function drawPlots(r) {
    const s = r.sweep;
    const k = (arr) => arr.map((v) => (v === null ? null : v / 1000));
    const mark = [TS.vline(r.P)];
    TS.plot("pr-plot-dH", [
      { x: s.P, y: k(s.dH_P), name: `ΔH(T,P), ${r.at_P.model_name}`, mode: "lines", line: { width: 2.5, color: "#c2410c" } },
      { x: [s.P[0], s.P[s.P.length - 1]], y: [s.dH_std / 1000, s.dH_std / 1000], name: "ΔH°(T), ideal gas", mode: "lines",
        line: { width: 1.5, dash: "dash", color: "#475569" } },
    ], TS.layout(`Heat of reaction versus pressure at ${fix(r.T, 0)} K`, "Pressure (bar)", "kJ per mol of reaction", { shapes: mark }));

    const palette = TS.palette();
    const gas = r.at_P.species.filter((x) => x.phase === "g");
    TS.plot("pr-plot-HR", gas.map((x, i) => ({
      x: s.P, y: k(s.species_HR[x.species]), name: x.species, mode: "lines", line: { width: 2, color: palette[i % palette.length] },
    })), TS.layout("Residual enthalpy of each pure species", "Pressure (bar)", "H^R (kJ/mol)", { shapes: mark }));

    TS.plot("pr-plot-Z", gas.map((x, i) => ({
      x: s.P, y: s.species_Z[x.species], name: x.species, mode: "lines", line: { width: 2, color: palette[i % palette.length] },
    })), TS.layout("Compressibility factor Z = PV/RT", "Pressure (bar)", "Z", { shapes: mark.concat([TS.hline(1)]) }));

    const hasConv = s.conversion_ideal.some((v) => v !== null);
    if (hasConv) {
      TS.plot("pr-plot-X", [
        { x: s.P, y: s.conversion_real.map((v) => (v === null ? null : 100 * v)), name: r.at_P.model_name, mode: "lines", line: { width: 2.5, color: "#0b5cad" } },
        { x: s.P, y: s.conversion_ideal.map((v) => (v === null ? null : 100 * v)), name: "Ideal gas", mode: "lines", line: { width: 1.5, dash: "dash", color: "#475569" } },
      ], TS.layout("Equilibrium conversion (stoichiometric feed)", "Pressure (bar)", "Conversion of limiting reactant (%)", { shapes: mark }));
    }
  }

  function render(r) {
    const a = r.at_P;
    const ok = a.gas_phase_valid;
    const v = (x) => (ok ? x : null);
    let html = `<div class="panel"><div class="eqn">${chem(r.equation)} <small>&nbsp; at ${fix(r.T, 2)} K and ${fix(r.P, 2)} bar, ${esc(a.model_name)}</small></div>`;
    html += TS.notes(r.warnings.filter((w) => w.level !== "info")) + TS.notes(a.notes.filter((n) => n.level !== "info"));
    html += `<div class="cards">
        <div class="card"><div class="k">ΔH°(T), ideal gas</div><div class="v">${kJ(a.dH_std, 3)} <span class="u">kJ/mol</span></div><div class="s">independent of pressure</div></div>
        <div class="card"><div class="k">Σ ν H<sup>R</sup></div><div class="v">${ok ? signed(a.sum_HR / 1000, 3) : "–"} <span class="u">kJ/mol</span></div><div class="s">the pressure effect</div></div>
        <div class="card ${ok ? (a.dH_P < 0 ? "exo" : "endo") : ""}"><div class="k">ΔH(T,P), real gas</div><div class="v">${kJ(v(a.dH_P), 3)} <span class="u">kJ/mol</span></div><div class="s">ΔH° + Σ ν H<sup>R</sup></div></div>
        <div class="card"><div class="k">ΔS(T,P)</div><div class="v">${fix(v(a.dS_P), 2)} <span class="u">J/(mol·K)</span></div><div class="s">ideal-gas part ${fix(a.dS_ig_P, 2)}</div></div>
        <div class="card"><div class="k">ΔG(T,P)</div><div class="v">${kJ(v(a.dG_P), 3)} <span class="u">kJ/mol</span></div><div class="s">ideal-gas value ${kJ(a.dG_ig_P, 3)}</div></div>
        <div class="card"><div class="k">K<sub>φ</sub> = Π φ<sub>i</sub><sup>ν</sup></div><div class="v">${sig(v(a.K_phi), 4)}</div><div class="s">1 for ideal gases</div></div>
      </div><h3>What the numbers mean</h3>${explain(r)}</div>`;
    const hasConv = r.sweep.conversion_ideal.some((x) => x !== null);
    html += `<div class="panel"><div class="grid two"><div id="pr-plot-dH" class="plot"></div><div id="pr-plot-HR" class="plot"></div>
      <div id="pr-plot-Z" class="plot"></div>${hasConv ? '<div id="pr-plot-X" class="plot"></div>' : ""}</div>
      ${r.sweep.first_invalid_P ? `<p class="hint" style="margin:8px 0 0">The real-gas curves stop near ${fix(r.sweep.first_invalid_P, 0)} bar: above that, a species has no vapour-like state at this temperature, so a gas-phase value does not exist.</p>` : ""}</div>`;
    html += `<div class="panel"><h3>Residual properties of each species at ${fix(r.T, 0)} K, ${fix(r.P, 1)} bar</h3>
      ${residualTable(r)}${TS.notes(a.notes.filter((n) => n.level === "info"))}${modelTable(r)}${TS.auditTable(r.audit)}</div>`;
    $("#pr-out").innerHTML = html;
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
        model: $("#pr-model").value,
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
        onPick: (rxn) => { $("#pr-T").value = Math.max(rxn.T, 350); calculate(); },
      });
      $("#pr-run").addEventListener("click", calculate);
      $("#pr-model").addEventListener("change", calculate);
      for (const id of ["pr-equation", "pr-T", "pr-P", "pr-Pmax"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      TS.pickReaction(select, input, "ammonia");
    },
    onShow() {
      if (!started) { started = true; calculate(); }
    },
  });
})();
