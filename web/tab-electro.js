/* Tab 5 (extra feature 2): the electrochemical lens.
 *
 * Display convention: the solver returns E_rev = -dG/(nF) and E_tn = -dH/(nF),
 * which are positive for a spontaneous, exothermic reaction. For an
 * electrolyser the page shows the positive voltage that has to be applied,
 * dG/(nF). `sign` converts between the two and is applied to every voltage,
 * slope and shift that is printed, so the text always matches the cards.
 */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, signed, pct } = TS;
  const nText = (n) => fix(n, 2).replace(".00", "");

  function explain(r) {
    const p = r.point;
    const T = fix(p.T, 0);
    const galvanic = p.mode === "galvanic";
    const sign = galvanic ? 1 : -1;
    const lines = [];
    lines.push(`Electrons through the external circuit per mole of reaction: n = ${nText(p.n_electrons)} (${esc(p.n_basis)}). ` +
      `The automatic count takes 4 electrons for each O<sub>2</sub>; if there is no O<sub>2</sub>, 2 for each H<sub>2</sub> or Cl<sub>2</sub>. ` +
      `With hydrogen peroxide, whose oxygen is at −1, it is 2 per H<sub>2</sub> or per O<sub>2</sub>.`);

    if (galvanic) {
      lines.push(`ΔG < 0, so the reaction is spontaneous: this is a <strong>fuel cell</strong>. The most electrical work it can deliver is ` +
        `−ΔG = ${kJ(-p.dG)} kJ/mol, which corresponds to a reversible voltage of <strong>${fix(p.E_rev, 3)} V</strong>.`);
      if (p.dH < 0) {
        lines.push(`Burning the same fuel releases −ΔH = ${kJ(-p.dH)} kJ/mol as heat. The cell can turn at most ΔG/ΔH = ` +
          `<strong>${pct(p.efficiency, 1)}</strong> of that into electricity; the remaining T·ΔS = ${kJ(p.reversible_heat)} kJ/mol ` +
          `${p.reversible_heat < 0 ? "must be rejected as heat even by a perfect cell" : "is absorbed from the surroundings, which is why this ratio is above 100 %"}.`);
        lines.push(`A Carnot engine working between ${T} K and ${fix(p.T_cold, 0)} K is limited to ${pct(p.carnot_efficiency, 1)}. ` +
          (p.efficiency > p.carnot_efficiency
            ? "The fuel cell wins here because it is not a heat engine and is not bound by the Carnot limit."
            : "At this temperature the heat engine has the higher ceiling: the fuel cell's advantage shrinks as T rises because |ΔG| shrinks."));
      } else {
        lines.push(`The reaction is endothermic (ΔH = ${kJ(p.dH)} kJ/mol) and still spontaneous, so it is driven by entropy: ` +
          `a reversible cell would deliver ${kJ(-p.dG)} kJ/mol of electricity while absorbing T·ΔS = ${kJ(p.reversible_heat)} kJ/mol of heat. ` +
          `An efficiency based on ΔH has no meaning here.`);
      }
    } else {
      lines.push(`ΔG > 0, so the reaction has to be driven: this is an <strong>electrolyser</strong>. The least electrical work is ` +
        `ΔG = ${kJ(p.dG)} kJ/mol, a minimum cell voltage of <strong>${fix(-p.E_rev, 3)} V</strong>.`);
      if (p.dH > 0) {
        lines.push(`The total energy demand is ΔH = ${kJ(p.dH)} kJ/mol. The difference T·ΔS = ${kJ(p.reversible_heat)} kJ/mol ` +
          `${p.reversible_heat > 0 ? "can be supplied as heat instead of electricity" : "is released as heat"}. ` +
          `At the thermoneutral voltage of ${fix(-p.E_tn, 3)} V the cell neither heats up nor cools down.`);
        if (p.efficiency !== null) {
          lines.push(`Only ${pct(p.efficiency, 1)} of the energy has to be electricity. This share falls as the temperature rises, ` +
            `which is the thermodynamic case for high-temperature (solid-oxide) electrolysis.`);
        }
      } else {
        lines.push(`The reaction is exothermic (ΔH = ${kJ(p.dH)} kJ/mol) but not spontaneous at this temperature, because its entropy change is ` +
          `strongly negative. All of ΔG must be supplied as electricity, and the cell gives off ΔG − ΔH = ${kJ(p.dG - p.dH)} kJ/mol as heat. ` +
          `There is no thermoneutral voltage in this case.`);
      }
    }
    lines.push(`Temperature coefficient of the ${galvanic ? "reversible" : "minimum"} voltage: ${signed(1000 * sign * p.dE_dT, 3)} mV/K ` +
      `(from ΔS/(nF)).`);
    if (Math.abs(p.nernst_shift) > 1e-6) {
      lines.push(`Pressure (Nernst) shift of that voltage relative to 1 bar: ${signed(1000 * sign * p.nernst_shift, 1)} mV at ${fix(p.P, 1)} bar.`);
    }
    lines.push("These are thermodynamic limits. A real cell loses voltage to activation, ohmic and mass-transport overpotentials.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  function render(r) {
    const p = r.point;
    const galvanic = p.mode === "galvanic";
    const sign = galvanic ? 1 : -1;
    const sameSign = (p.dH < 0) === (p.dG < 0);
    let html = `<div class="panel"><div class="eqn">${chem(r.equation)}</div>
      <p><span class="badge ${galvanic ? "good" : "neutral"}">${galvanic ? "Fuel cell (galvanic)" : "Electrolyser (electrolytic)"}</span>
         <span class="badge neutral">n = ${nText(p.n_electrons)} electrons</span></p>
      ${TS.notes(r.warnings.filter((w) => w.level !== "info"))}${TS.notes(p.notes.filter((n) => n.level !== "info"))}
      <div class="cards">
        <div class="card"><div class="k">${galvanic ? "Reversible voltage" : "Minimum cell voltage"}</div><div class="v">${fix(sign * p.E_rev, 3)} <span class="u">V</span></div><div class="s">|ΔG|/(nF)</div></div>
        <div class="card"><div class="k">Thermoneutral voltage</div><div class="v">${sameSign ? fix(sign * p.E_tn, 3) : "–"} <span class="u">V</span></div>
          <div class="s">${sameSign ? "|ΔH|/(nF)" : "not defined: ΔH and ΔG have opposite signs"}</div></div>
        <div class="card"><div class="k">ΔG = electrical work</div><div class="v">${kJ(p.dG)} <span class="u">kJ/mol</span></div></div>
        <div class="card"><div class="k">ΔH</div><div class="v">${kJ(p.dH)} <span class="u">kJ/mol</span></div></div>
        <div class="card"><div class="k">T·ΔS = reversible heat</div><div class="v">${kJ(p.reversible_heat)} <span class="u">kJ/mol</span></div></div>
        <div class="card"><div class="k">${galvanic ? "Ideal efficiency ΔG/ΔH" : "Electricity share ΔG/ΔH"}</div><div class="v">${p.efficiency === null ? "–" : pct(p.efficiency, 1)}</div>
          <div class="s">${galvanic && p.efficiency !== null ? `Carnot limit ${pct(p.carnot_efficiency, 1)}` : ""}</div></div>
      </div><h3>What the numbers mean</h3>${explain(r)}</div>`;

    const s = r.sweep;
    // The work/heat split is only meaningful where dH and dG share a sign and |dG| <= |dH|.
    const splitOk = s && s.dG.every((g, i) => g !== null && s.dH[i] !== null &&
      (g < 0) === (s.dH[i] < 0) && Math.abs(g) <= Math.abs(s.dH[i]));
    const effOk = s && s.efficiency.some((x) => x !== null);
    if (s) {
      html += `<div class="panel"><div class="grid two"><div id="el-plot-E" class="plot"></div>
        ${effOk ? '<div id="el-plot-eff" class="plot"></div>' : ""}
        ${splitOk ? '<div id="el-plot-split" class="plot"></div>' : ""}</div>
        <p class="hint" style="margin:8px 0 0">Voltages are plotted for the mode at the selected temperature
          (${galvanic ? "fuel cell" : "electrolyser"}). Where a curve crosses zero, the reaction changes direction.</p></div>`;
    }
    $("#el-out").innerHTML = html;
    if (!s) return;

    const mark = [TS.vline(p.T), TS.hline(0)];
    const volts = (arr) => arr.map((x) => (x === null ? null : sign * x));
    const traces = [{ x: s.T, y: volts(s.E_rev), name: galvanic ? "Reversible voltage" : "Minimum voltage", mode: "lines", line: { width: 2.5, color: "#0b5cad" } }];
    if (sameSign) traces.push({ x: s.T, y: volts(s.E_tn), name: "Thermoneutral voltage", mode: "lines", line: { width: 2.5, color: "#c2410c" } });
    TS.plot("el-plot-E", traces, TS.layout("Cell voltages versus temperature", "Temperature (K)", "Volts", { shapes: mark }));

    const percent = (arr) => arr.map((x) => (x === null ? null : 100 * x));
    if (effOk && galvanic) {
      const shapes = [TS.vline(p.T)];
      const annotations = [];
      if (s.crossover_T) {
        shapes.push(TS.vline(s.crossover_T, "#7c3aed"));
        annotations.push({ x: s.crossover_T, y: 1, yref: "paper", text: `break-even ${fix(s.crossover_T, 0)} K`, showarrow: false, yanchor: "bottom", font: { size: 11 } });
      }
      TS.plot("el-plot-eff", [
        { x: s.T, y: percent(s.efficiency), name: "Ideal fuel cell, ΔG/ΔH", mode: "lines", line: { width: 2.5, color: "#0b5cad" } },
        { x: s.T, y: percent(s.carnot_efficiency), name: `Carnot engine, 1 − ${fix(p.T_cold, 0)}/T`, mode: "lines", line: { width: 2.5, dash: "dash", color: "#475569" } },
      ], TS.layout("Fuel cell versus heat engine", "Temperature (K)", "Maximum efficiency (%)", { shapes, annotations }));
    } else if (effOk) {
      TS.plot("el-plot-eff", [
        { x: s.T, y: percent(s.efficiency), name: "Electricity share ΔG/ΔH", mode: "lines", line: { width: 2.5, color: "#0b5cad" } },
      ], TS.layout("Share of the energy that must be electricity", "Temperature (K)", "ΔG/ΔH (%)", { shapes: [TS.vline(p.T)], showlegend: false }));
    }

    if (splitOk) {
      TS.plot("el-plot-split", [
        { x: s.T, y: s.dG.map((g) => Math.abs(g) / 1000), name: galvanic ? "electricity available, |ΔG|" : "electricity needed, ΔG", mode: "lines", stackgroup: "one", line: { width: 0.8, color: "#0b5cad" } },
        { x: s.T, y: s.dG.map((g, i) => (Math.abs(s.dH[i]) - Math.abs(g)) / 1000), name: galvanic ? "unavoidable heat, |ΔH| − |ΔG|" : "heat that can replace electricity, ΔH − ΔG",
          mode: "lines", stackgroup: "one", line: { width: 0.8, color: "#c2410c" } },
      ], TS.layout("How |ΔH| splits into work and heat", "Temperature (K)", "kJ per mol of reaction", { shapes: [TS.vline(p.T)] }));
    }
  }

  function calculate() {
    const out = $("#el-out");
    out.dataset.input = "el-equation";
    return TS.run($("#el-run"), out, async () => {
      render(await TS.engine.call("electro", {
        equation: $("#el-equation").value,
        T: TS.readNumber("el-T"),
        P: TS.readNumber("el-P"),
        n_electrons: TS.readNumber("el-n"),
      }));
    });
  }

  let started = false;
  TS.tabs.push({
    id: "electro",
    init() {
      const select = $("#el-select");
      const input = $("#el-equation");
      const reverse = (eq) => { const [l, r] = eq.split("->"); return `${r.trim()} -> ${l.trim()}`; };
      const options = [];
      for (const ex of TS.library.electro_examples) {
        options.push({ label: ex.label, equation: ex.equation, id: ex.id });
      }
      options.splice(1, 0, { label: "Steam electrolysis (reverse of the hydrogen fuel cell)", equation: reverse("H2 + 1/2 O2 -> H2O(g)"), id: "steam_electrolysis", T: 1073.15 });
      options.push({ label: "CO2 electrolysis to CO", equation: reverse("CO + 1/2 O2 -> CO2"), id: "co2_electrolysis", T: 1073.15 });
      select.innerHTML = options.map((o, i) => `<option value="${i}">${esc(o.label)}</option>`).join("") +
        `<option value="">Custom reaction</option>`;
      select.addEventListener("change", () => {
        const o = options[Number(select.value)];
        if (!o || select.value === "") return;
        input.value = o.equation;
        const lib = TS.library.reactions.find((x) => x.id === o.id);
        $("#el-T").value = o.T || (lib ? lib.T : 298.15);
        $("#el-n").value = "";
        calculate();
      });
      input.addEventListener("input", () => { select.value = ""; });
      $("#el-run").addEventListener("click", calculate);
      for (const id of ["el-equation", "el-T", "el-P", "el-n"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      select.value = "0";
      input.value = options[0].equation;
    },
    onShow() {
      if (!started) { started = true; calculate(); }
    },
  });
})();
