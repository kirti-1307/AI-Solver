/* Tab 5 (extra feature 2): the heat lab.
 *
 * View 1, "Reactor and flame": an energy balance around a reactor. The solver
 * returns the outlet temperature (adiabatic or with a given heat input) or the
 * heat duty for a given outlet temperature, with the three-step path, the
 * enthalpy lines of the two mixtures and a sweep of one setting.
 *
 * View 2, "Bomb calorimeter": constant-volume combustion as in the course lab.
 *
 * The page only converts units for display (percent, kJ, calories, Celsius).
 * Every thermodynamic number comes from the Python solver.
 */
"use strict";
(() => {
  const { $, $$, esc, chem, fix, kJ, sig, signed, pct } = TS;
  const T_FREEZE = 273.15;                    // kelvin to degrees Celsius, display only
  const bare = (sid) => sid.replace(/\((g|l|s)\)$/, "");
  /* a temperature the user set: whole numbers plainly, anything else with its decimals */
  const kelvin = (T) => (Math.abs(T - Math.round(T)) < 0.005 ? fix(T, 0) : fix(T, 2));

  /* Several species outside their heat-capacity range become one message. */
  function rangeNotes(warnings) {
    const list = warnings.filter((w) => w.kind === "cp_extrapolation");
    const rest = warnings.filter((w) => w.kind !== "cp_extrapolation");
    if (list.length < 2) return TS.notes(warnings);
    const groups = new Map();
    for (const w of list) {
      const key = `${w.where}|${w.T}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(w);
    }
    let html = "";
    for (const group of groups.values()) {
      const first = group[0];
      const names = group.map((w) => `${chem(w.species)} (${fix(w.cp_Tmin, 0)} to ${fix(w.cp_Tmax, 0)} K)`).join(", ");
      html += TS.message("warning", `<strong>Warning:</strong> the ${esc(first.where)} temperature of ${fix(first.T, 0)} K is outside the range ` +
        `of the heat-capacity correlation of ${names}. The correlations are extrapolated.` +
        (group.some((w) => w.condensed) ? " A liquid or solid may not exist at this temperature; no phase change is applied." : ""));
    }
    return html + TS.notes(rest);
  }

  /* =================================================================== reactor */
  let mode = "adiabatic";
  let builtFor = null;          // reaction text for which the key/excess selects were filled
  let modeSeg = null;

  function reactorPayload() {
    const equation = $("#hb-equation").value;
    const same = builtFor !== null && builtFor === equation.trim();
    const body = {
      equation, mode,
      T_in: TS.readNumber("hb-Tin"),
      conversion: Number($("#hb-conv").value) / 100,
      excess: $("#hb-excess-box").hidden ? 0 : Number($("#hb-excess").value) / 100,
      air: !$("#hb-air-box").hidden && $("#hb-air").checked,
      key: same ? ($("#hb-key").value || null) : null,
      excess_species: same ? ($("#hb-excess-species").value || null) : null,
      sweep: same ? ($("#hb-sweep").value || null) : null,
      side: [], extra: {},
    };
    if (mode === "duty") {
      body.T_out = TS.readNumber("hb-Tout");
      if (body.sweep === null) body.sweep = "T_out";
    } else {
      const q = TS.readNumber("hb-Q");
      body.Q = typeof q === "number" ? 1000 * q : q;
      body.target_T = TS.readNumber("hb-target");
      if (body.sweep === "T_out") body.sweep = null;
    }
    const sideEq = $("#hb-side-eq").value.trim();
    if (sideEq) body.side = [{ equation: sideEq, extent: TS.readNumber("hb-side-extent") ?? 0 }];
    const extra = $("#hb-extra-species").value;
    const extraN = TS.readNumber("hb-extra-n");
    if (extra && extraN) body.extra = { [extra]: extraN };
    return body;
  }

  function fillSelects(r) {
    builtFor = $("#hb-equation").value.trim();
    $("#hb-key").innerHTML = r.reactants.map((s) => `<option value="${esc(s)}"${s === r.key ? " selected" : ""}>${esc(s)}</option>`).join("");
    const others = r.reactants.filter((s) => s !== r.key);
    $("#hb-excess-species").innerHTML = others.length
      ? others.map((s) => `<option value="${esc(s)}"${s === r.excess_species ? " selected" : ""}>${esc(s)}</option>`).join("")
      : `<option value="">none (single reactant)</option>`;
    $("#hb-excess-box").hidden = !r.excess_species;
    const usesAir = r.settings.air && r.excess_species === "O2(g)";
    $("#hb-excess-name").innerHTML = r.excess_species ? (usesAir ? "Excess air" : `Excess ${chem(bare(r.excess_species))}`) : "Excess";
    $("#hb-air-box").hidden = !r.reactants.includes("O2(g)");
    $("#hb-conv-name").innerHTML = `Conversion of ${chem(bare(r.key))}`;

    const options = [];
    if (r.excess_species) options.push(["excess", usesAir ? "Excess air" : "Excess reactant"]);
    options.push(["T_in", "Inlet temperature"], ["conversion", "Conversion"]);
    if (r.mode === "duty") options.push(["T_out", "Outlet temperature"]);
    const chosen = r.sweep ? r.sweep.variable : options[0][0];
    $("#hb-sweep").innerHTML = options.map(([v, label]) => `<option value="${v}"${v === chosen ? " selected" : ""}>${label}</option>`).join("");
  }

  function ensureReactor() {
    if ($("#hb-cards")) return;
    $("#hb-out").innerHTML = `<div class="panel">
        <div class="eqn" id="hb-eqn"></div>
        <div id="hb-notes"></div>
        <div class="cards" id="hb-cards"></div>
        <h3>The path of the calculation, per mole of <span id="hb-basis"></span> fed</h3>
        <div class="path" id="hb-path"></div>
        <h3>What the numbers mean</h3><div id="hb-explain"></div>
      </div>
      <div class="panel"><div class="grid two"><div id="hb-plot-H" class="plot tall"></div><div id="hb-plot-sweep" class="plot tall"></div></div></div>
      <div class="panel" id="hb-more"></div>`;
  }

  function leg(title, detail, joule, extra = "") {
    const cls = joule < -0.5 ? "neg" : (joule > 0.5 ? "pos" : "");
    return `<div class="leg ${cls} ${extra}"><div class="t">${title}</div><div class="d">${detail}</div>
      <div class="q">${signed(joule / 1000, 2)} kJ</div></div>`;
  }

  function explainReactor(r) {
    const p = r.point;
    const key = chem(bare(r.key));
    const lines = [];
    const feedMoles = sig(p.feed_total, 4);
    const outMoles = sig(p.outlet_total, 4);
    if (Math.abs(p.path.dH_R) > 0.5) {
      lines.push(`The feed (${feedMoles} mol per mol of ${key}) enters at ${kelvin(p.T_in)} K. Taking it to 298.15 K ` +
        `${p.path.dH_R < 0 ? "gives up" : "needs"} ${kJ(Math.abs(p.path.dH_R))} kJ of sensible heat.`);
    } else {
      lines.push(`The feed (${feedMoles} mol per mol of ${key}) enters at 298.15 K, so the first step of the path is zero.`);
    }
    lines.push(`At 298.15 K the reaction${r.settings.side.length ? "s" : ""} ${p.path.dH_298 < 0 ? "release" : "absorb"}${r.settings.side.length ? "" : "s"} ` +
      `${kJ(Math.abs(p.path.dH_298))} kJ (extent × ΔH°<sub>298</sub>).`);
    if (r.mode === "adiabatic") {
      lines.push(`${Math.abs(p.Q) < 0.5 ? "No heat crosses the wall, so" : `With ${signed(p.Q / 1000, 1)} kJ exchanged,`} the remaining ` +
        `${kJ(p.path.dH_P)} kJ ${p.path.dH_P >= 0 ? "heats" : "is taken from"} the ${outMoles} mol of products. Their mean heat capacity between 298.15 K and the outlet is ` +
        `${fix(p.mean_cp_products, 1)} J/K, which puts the outlet at <strong>${fix(p.T_out, 0)} K (${fix(p.T_out - T_FREEZE, 0)} °C)</strong>.`);
    } else {
      lines.push(`Taking the ${outMoles} mol of products from 298.15 K to ${kelvin(p.T_out)} K needs ${signed(p.path.dH_P / 1000, 2)} kJ. ` +
        `The sum of the three steps is the heat duty: <strong>${signed(p.Q / 1000, 2)} kJ per mol of ${key}</strong>, ` +
        `${p.Q > 0 ? "which the furnace must supply" : "which must be removed by cooling"}.`);
    }
    const inert = p.inert;
    if (inert.length) {
      lines.push(`${inert.map(chem).join(", ")} pass${inert.length === 1 ? "es" : ""} through unchanged but still ${inert.length === 1 ? "has" : "have"} to be heated: ` +
        `more of ${inert.length === 1 ? "it" : "them"} means a cooler outlet for the same heat of reaction.`);
    }
    if (r.target) {
      lines.push(r.target.excess !== null
        ? `To hold the outlet at ${fix(r.target.target_T, 0)} K the feed needs <strong>${pct(r.target.excess, 1)} excess</strong> of ${chem(bare(r.excess_species))}.`
        : `Temperature limit of ${fix(r.target.target_T, 0)} K: ${esc(r.target.reason)}`);
    }
    if (r.work) {
      lines.push(`Second-law view: cooled reversibly to 298.15 K, the hot products could deliver at most ${kJ(-r.work.W_ideal)} kJ of work ` +
        `(W<sub>ideal</sub> = ΔH − T<sub>σ</sub>ΔS), ${pct(r.work.fraction, 1)} of their heat. A Carnot engine supplied at a constant ` +
        `${fix(p.T_out, 0)} K would convert ${pct(r.work.carnot_at_T_out, 1)}; the stream does less because its temperature falls as it gives up heat.`);
    }
    if (r.mode === "adiabatic" && p.T_out > 1800) {
      lines.push("The reaction is taken to go to the stated conversion. Above about 2000 K real flames are cooler than this, because CO<sub>2</sub> and H<sub>2</sub>O partly dissociate.");
    }
    lines.push("Assumptions: every species stays in the phase written, the gases are ideal, and nothing limits the conversion you set.");
    return `<ul class="explain">${lines.map((l) => `<li>${l}</li>`).join("")}</ul>`;
  }

  function fuelBlock(f) {
    if (!f) return "";
    return `<details open><summary>Fuel facts for ${chem(f.fuel)}</summary>
      <div class="table-scroll"><table><thead><tr><th class="l">Quantity</th><th>per mol of fuel</th><th>per kg of fuel</th><th class="l">How</th></tr></thead><tbody>
      <tr><td class="l">Lower heating value (water as vapour)</td><td>${kJ(f.LHV)} kJ</td><td>${fix(f.LHV_mass, 2)} MJ</td><td class="l mono">${chem(f.equation_lhv)}</td></tr>
      <tr><td class="l">Higher heating value (water as liquid)</td><td>${kJ(f.HHV)} kJ</td><td>${fix(f.HHV_mass, 2)} MJ</td><td class="l mono">${chem(f.equation_hhv)}</td></tr>
      <tr><td class="l">What a bomb calorimeter reads, −ΔU</td><td>${kJ(-f.dU_bomb)} kJ</td><td>${fix(-f.dU_bomb / f.molar_mass / 1000, 2)} MJ</td>
        <td class="l">ΔU = ΔH − Δn<sub>gas</sub>RT, Δn<sub>gas</sub> = ${signed(f.dn_gas_bomb, 2)}</td></tr>
      <tr><td class="l">Oxygen needed</td><td>${fix(f.o2_stoich, 3)} mol</td><td></td><td class="l">from the balanced reaction</td></tr>
      <tr><td class="l">Air needed (21 % O<sub>2</sub>)</td><td>${fix(f.air_stoich, 3)} mol</td><td>${fix(f.air_fuel_mass, 2)} kg</td><td class="l">stoichiometric air</td></tr>
      <tr><td class="l">CO<sub>2</sub> formed</td><td>${fix(f.co2_per_mol, 2)} mol</td><td>${f.co2_per_MJ === null ? "–" : `${fix(f.co2_per_MJ, 1)} g per MJ`}</td><td class="l">per MJ of lower heating value</td></tr>
      </tbody></table></div></details>`;
  }

  function streamTable(r) {
    const p = r.point;
    const rows = p.species.map((s) => `<tr><td class="l mono">${chem(s.id)}</td><td class="l">${esc(s.name)}</td>
      <td>${sig(s.n_in, 5)}</td><td>${sig(s.n_out, 5)}</td><td>${s.y_out === null ? "–" : sig(s.y_out, 4)}</td>
      <td>${TS.int(s.sensible_in)}</td><td>${TS.int(s.sensible_out)}</td>
      <td>${s.cp_Tmin === null ? "298.15 only" : `${fix(s.cp_Tmin, 0)}–${fix(s.cp_Tmax, 0)}`}</td></tr>`).join("");
    return `<details><summary>Stream table and sensible heat of each species</summary>
      <div class="table-scroll"><table><thead><tr><th class="l">Species</th><th class="l">Name</th><th>In (mol)</th><th>Out (mol)</th>
        <th>y out</th><th>n·∫C<sub>p</sub>dT, T<sub>in</sub>→298 (J)</th><th>n·∫C<sub>p</sub>dT, 298→T<sub>out</sub> (J)</th><th>C<sub>p</sub> valid (K)</th></tr></thead>
      <tbody>${rows}<tr class="sum"><td class="l" colspan="2">Total</td><td>${sig(p.feed_total, 5)}</td><td>${sig(p.outlet_total, 5)}</td><td>1</td>
        <td>${TS.int(p.path.dH_R)}</td><td>${TS.int(p.path.dH_P)}</td><td></td></tr></tbody></table></div></details>`;
  }

  function renderReactor(r) {
    ensureReactor();
    fillSelects(r);
    const p = r.point;
    const key = chem(bare(r.key));
    const adiabatic = r.mode === "adiabatic";

    $("#hb-eqn").innerHTML = chem(r.equation) + r.settings.side.map((s) => `<br><small>side reaction:</small> ${chem(s.equation)}`).join("");
    $("#hb-notes").innerHTML = TS.notes(r.notes.map((m) => ({ level: "info", message: m }))) + rangeNotes(p.warnings);
    $("#hb-basis").innerHTML = key;

    const exo = p.path.dH_298 < 0;
    let cards = adiabatic
      ? `<div class="card hero"><div class="k">Outlet temperature${Math.abs(p.Q) < 0.5 ? " (adiabatic)" : ""}</div>
           <div class="v">${fix(p.T_out, 0)} <span class="u">K</span></div><div class="s">${fix(p.T_out - T_FREEZE, 0)} °C, from ${kelvin(p.T_in)} K at the inlet</div></div>`
      : `<div class="card hero"><div class="k">Heat duty</div>
           <div class="v">${signed(p.Q / 1000, 1)} <span class="u">kJ per mol ${key}</span></div>
           <div class="s">${p.Q > 0 ? "heat must be supplied" : "heat must be removed"}, ${signed(p.Q_per_kg / 1e6, 2)} MJ per kg</div></div>`;
    cards += `<div class="card ${exo ? "exo" : "endo"}"><div class="k">Heat of reaction at 298.15 K</div>
        <div class="v">${signed(p.path.dH_298 / 1000, 1)} <span class="u">kJ</span></div><div class="s">${exo ? "exothermic" : "endothermic"}, extent × ΔH°<sub>298</sub></div></div>
      <div class="card"><div class="k">Mean C<sub>p</sub> of the products</div><div class="v">${fix(p.mean_cp_products, 1)} <span class="u">J/K</span></div>
        <div class="s">${sig(p.outlet_total, 4)} mol, 298.15 K to outlet</div></div>`;
    if (r.target && r.target.excess !== null) {
      cards += `<div class="card good"><div class="k">Excess for ${fix(r.target.target_T, 0)} K</div><div class="v">${pct(r.target.excess, 0)}</div>
        <div class="s">to hold the temperature limit</div></div>`;
    }
    if (r.fuel) {
      cards += `<div class="card"><div class="k">Heating value of ${chem(bare(r.fuel.fuel))}</div><div class="v">${fix(r.fuel.LHV_mass, 1)} <span class="u">MJ/kg</span></div>
        <div class="s">lower; higher is ${fix(r.fuel.HHV_mass, 1)} MJ/kg</div></div>`;
    }
    $("#hb-cards").innerHTML = cards;

    $("#hb-path").innerHTML =
      leg("Step 1", `feed, ${kelvin(p.T_in)} K → 298.15 K`, p.path.dH_R) +
      leg("Step 2", "reaction at 298.15 K", p.path.dH_298) +
      leg("Step 3", `products, 298.15 K → ${adiabatic ? fix(p.T_out, 0) : kelvin(p.T_out)} K`, p.path.dH_P) +
      leg("Sum", adiabatic && Math.abs(p.Q) < 0.5 ? "Q = 0, adiabatic" : "Q, heat added", p.path.total, "sum");
    $("#hb-explain").innerHTML = explainReactor(r);
    $("#hb-more").innerHTML = fuelBlock(r.fuel) + streamTable(r) + TS.auditTable(p.audit);

    // Enthalpy of the two mixtures against temperature, with the process as an arrow
    const c = r.curves;
    const k = (arr) => arr.map((v) => (v === null ? null : v / 1000));
    const T0 = TS.database.constants.T0;
    TS.plot("hb-plot-H", [
      { x: c.T, y: k(c.H_feed), name: "Feed mixture", mode: "lines", line: { width: 2.5, color: "#0b5cad" } },
      { x: c.T, y: k(c.H_out), name: "Product mixture", mode: "lines", line: { width: 2.5, color: "#c2410c" } },
      { x: [p.T_in], y: [p.H_in / 1000], name: "Feed in", mode: "markers", marker: { size: 11, color: "#0b5cad", line: { width: 2, color: TS.css("--panel") } } },
      { x: [p.T_out], y: [p.H_out / 1000], name: "Products out", mode: "markers", marker: { size: 11, color: "#c2410c", line: { width: 2, color: TS.css("--panel") } } },
    ], TS.layout("Enthalpy of the feed and of the products", "Temperature (K)", "H relative to the elements at 298.15 K (kJ)", {
      shapes: [TS.vline(T0)], hovermode: "closest",
      annotations: [{ x: p.T_out, y: p.H_out / 1000, ax: p.T_in, ay: p.H_in / 1000, xref: "x", yref: "y", axref: "x", ayref: "y",
        showarrow: true, arrowhead: 3, arrowsize: 1.1, arrowwidth: 2, arrowcolor: TS.css("--muted"), standoff: 8, startstandoff: 8, text: "" },
      { x: T0, y: 1, yref: "paper", text: "298.15 K", showarrow: false, yanchor: "bottom", font: { size: 11 } }],
    }));

    const s = r.sweep;
    if (s) {
      const percent = s.variable === "excess" || s.variable === "conversion";
      const xs = percent ? s.x.map((v) => 100 * v) : s.x;
      const label = { excess: r.settings.air && r.excess_species === "O2(g)" ? "Excess air (%)" : `Excess of ${bare(r.excess_species || "")} (%)`,
        T_in: "Inlet temperature (K)",
        conversion: `Conversion of ${bare(r.key)} (%)`, T_out: "Outlet temperature (K)" }[s.variable];
      const here = { excess: 100 * r.settings.excess, T_in: p.T_in, conversion: 100 * r.settings.conversion, T_out: p.T_out }[s.variable];
      const ys = adiabatic ? s.T_out : k(s.Q);
      const hereY = adiabatic ? p.T_out : p.Q / 1000;
      const shapes = [TS.vline(here)];
      if (adiabatic && r.target) shapes.push(TS.hline(r.target.target_T, "#11734b"));
      if (!adiabatic) shapes.push(TS.hline(0));
      TS.plot("hb-plot-sweep", [
        { x: xs, y: ys, name: adiabatic ? "Outlet temperature" : "Heat duty", mode: "lines", line: { width: 2.8, color: "#c2410c" } },
        { x: [here], y: [hereY], name: "now", mode: "markers", marker: { size: 11, color: "#c2410c", line: { width: 2, color: TS.css("--panel") } } },
      ], TS.layout(adiabatic ? "Outlet temperature as the setting changes" : "Heat duty as the setting changes", label,
        adiabatic ? "Outlet temperature (K)" : "Heat duty (kJ per mol)", { shapes, showlegend: false }));
    }
  }

  function showReactorError(err) {
    const out = $("#hb-out");
    out.innerHTML = `<div class="panel">${TS.errorBox(err)}<div id="hb-fix"></div></div>`;
    const fixText = err.details && err.details.suggestion;
    if (fixText) {
      const box = $("#hb-fix");
      box.className = "msg info";
      box.innerHTML = `Balanced form: <span class="mono">${chem(fixText)}</span> &nbsp;`;
      const use = document.createElement("button");
      use.className = "link";
      use.textContent = "Use this";
      use.addEventListener("click", () => { $("#hb-equation").value = fixText; $("#hb-select").value = ""; calculate(); });
      box.appendChild(use);
    }
  }

  const calculate = TS.latest(async () => {
    try {
      renderReactor(await TS.engine.call("heat_balance", reactorPayload()));
    } catch (err) {
      showReactorError(err);
    }
  });

  function setMode(next) {
    mode = next;
    modeSeg.set(next);
    $("#hb-Tout-box").hidden = next !== "duty";
    $("#hb-Q-box").hidden = next !== "adiabatic";
    $("#hb-target-box").hidden = next !== "adiabatic";
  }

  function loadExample(id) {
    const ex = TS.library.heat_examples.find((e) => e.id === id);
    if (!ex) return;
    builtFor = null;
    $("#hb-equation").value = ex.equation;
    $("#hb-note").textContent = ex.note || "";
    setMode(ex.mode);
    TS.setSlider("hb-Tin", ex.T_in, [250, 1500, 1]);
    TS.setSlider("hb-conv", Number((100 * ex.conversion).toPrecision(6)), [0, 100, 1]);
    TS.setSlider("hb-excess", Number((100 * ex.excess).toPrecision(6)), [0, 400, 1]);
    if (ex.T_out) TS.setSlider("hb-Tout", ex.T_out, [300, 2500, 1]);
    $("#hb-air").checked = !!ex.air;
    $("#hb-excess-box").hidden = false;
    $("#hb-air-box").hidden = false;
    const side = (ex.side || [])[0];
    $("#hb-side-eq").value = side ? side.equation : "";
    $("#hb-side-extent").value = side ? side.extent : "";
    $("#hb-extra-species").value = "";
    $("#hb-extra-n").value = "";
    $("#hb-Q").value = 0;
    $("#hb-target").value = "";
    // The selects are refilled from the answer; until then send the example's own choice.
    $("#hb-key").innerHTML = "";
    $("#hb-excess-species").innerHTML = ex.excess_species ? `<option value="${esc(ex.excess_species)}" selected>${esc(ex.excess_species)}</option>` : "";
    $("#hb-sweep").innerHTML = "";
    builtFor = ex.equation.trim();
  }

  /* =============================================================== calorimeter */
  let calMode = "calibrate";
  let runMode = "predict";

  const jPerCal = () => TS.library.joule_per_cal;

  function calorimeterPayload() {
    const J = jPerCal();
    const inCal = (id) => { const v = TS.readNumber(id); return typeof v === "number" ? v * J : v; };
    const body = { mode: runMode, mass: TS.readNumber("bc-mass"), corrections: inCal("bc-corr") ?? 0 };
    if (calMode === "calibrate") {
      body.calibration = { mass: TS.readNumber("bc-std-mass"), dT: TS.readNumber("bc-std-dT"),
        calorific_value: inCal("bc-std-cv"), corrections: inCal("bc-std-corr") ?? 0 };
    } else {
      body.C_cal = inCal("bc-C");
    }
    if (runMode === "predict") body.fuel = $("#bc-fuel").value;
    else { body.dT = TS.readNumber("bc-dT"); body.include_gases = $("#bc-gases").checked; }
    return body;
  }

  /* Temperature against time. Only the size of the rise is calculated; the
   * shape of the curve (flat, fast rise, flat) is an illustration. */
  const RISE_START = 0.16;
  const riseShape = (t) => (t <= RISE_START ? 0 : 1 - Math.exp(-(t - RISE_START) / 0.11));

  function thermogram(dT) {
    const W = 420, H = 210, L = 46, R = 12, T = 12, B = 32;
    const top = dT * 1.15;
    const x = (t) => L + t * (W - L - R);
    const y = (v) => H - B - (v / top) * (H - T - B);
    const pts = [];
    for (let i = 0; i <= 120; i++) { const t = i / 120; pts.push(`${x(t).toFixed(1)},${y(dT * riseShape(t)).toFixed(1)}`); }
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * dT);
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Temperature rise of the calorimeter against time">
      ${ticks.map((v) => `<line class="gridline" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"></line>
        <text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${fix(v, 2)}</text>`).join("")}
      <line class="axis" x1="${L}" x2="${L}" y1="${T}" y2="${H - B}"></line>
      <line class="axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"></line>
      <text x="${x(RISE_START)}" y="${H - B + 14}" text-anchor="middle">ignition</text>
      <text x="${W - R}" y="${H - 6}" text-anchor="end">time</text>
      <text x="${L}" y="${T - 2}" text-anchor="start">rise (°C)</text>
      <polyline class="curve" id="bc-curve" points="${pts.join(" ")}"></polyline></svg>`;
  }

  function animateRise(dT) {
    const curve = $("#bc-curve");
    const readout = $("#bc-readout");
    if (!curve || !readout) return;
    const still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    const length = curve.getTotalLength ? curve.getTotalLength() : 0;
    if (still || !length) { readout.textContent = fix(dT, 2); return; }
    curve.style.strokeDasharray = `${length}`;
    curve.style.strokeDashoffset = `${length}`;
    const duration = 2400;
    const begin = performance.now();
    const frame = (now) => {
      if (!document.body.contains(curve)) return;
      const t = Math.min(1, (now - begin) / duration);
      curve.style.strokeDashoffset = `${length * (1 - t)}`;
      readout.textContent = fix(dT * riseShape(t), 2);
      if (t < 1) requestAnimationFrame(frame);
      else readout.textContent = fix(dT, 2);
    };
    requestAnimationFrame(frame);
  }

  function renderCalorimeter(r) {
    const J = r.joule_per_cal;
    const run = r.run;
    const found = r.identify;
    const dT = found ? found.dT : run.dT;
    const cv = found ? found.measured_calorific_value : run.calorific_value;      // J/g
    const heat = found ? found.C_cal * found.dT : run.heat_released;

    let html = `<div class="panel">${TS.notes(r.warnings)}<div class="calo">
      <div class="thermo">
        <div class="readout"><span class="dim">${found ? "Measured temperature rise" : "Predicted temperature rise"}</span>
          <span><span class="big" id="bc-readout">0.00</span> <span class="dim">°C</span></span></div>
        ${thermogram(dT)}
        <p class="live-note">The shape of the curve is an illustration. Only the size of the rise is ${found ? "used" : "calculated"}.</p>
      </div>
      <div>
        <div class="cards">
          <div class="card"><div class="k">Calorimeter constant</div><div class="v">${fix(r.C_cal_cal, 1)} <span class="u">cal/°C</span></div>
            <div class="s">${fix(r.C_cal / 1000, 2)} kJ/K${r.calibration ? ", from the calibration run" : ", as entered"}</div></div>
          <div class="card"><div class="k">Heat taken up by the calorimeter</div><div class="v">${fix(heat / J, 0)} <span class="u">cal</span></div>
            <div class="s">${fix(heat / 1000, 2)} kJ = C<sub>cal</sub> × ΔT</div></div>
          <div class="card hero"><div class="k">${found ? "Calorific value of the sample" : `Calorific value of ${chem(bare(run.fuel))}`}</div>
            <div class="v">${fix(cv / 1000, 2)} <span class="u">MJ/kg</span></div><div class="s">${fix(cv / J, 0)} cal/g, at constant volume with liquid water</div></div>
        </div>`;

    if (found) {
      const rows = found.candidates.map((c, i) => `<span class="${i === 0 ? "first" : ""}">${i + 1}.</span>
        <span class="${i === 0 ? "first" : ""}"><span class="mono">${chem(c.fuel)}</span> ${esc(c.name)}</span>
        <span>${fix(c.calorific_value / 1000, 2)} MJ/kg</span><span class="${i === 0 ? "first" : "dim"}">${signed(100 * c.difference, 1)} %</span>`).join("");
      html += `<h3>Closest of the ${found.compared} ${found.include_gases ? "fuels" : "liquid and solid fuels"} in the database</h3><div class="rank">${rows}</div>
        <p class="live-note">A match within about 1 % is as good as a student calorimeter can tell. Fuels with nearly equal
          calorific values cannot be told apart by this measurement alone.</p>`;
    }
    html += `</div></div></div>`;

    const liquidWater = run.equation;
    html += `<div class="panel"><h3>${found ? `Thermodynamic reading for the best match, ${chem(run.fuel)}` : "From the reaction to the temperature rise"}</h3>
      <div class="step-row"><div><div class="t">1. Complete combustion, water formed as liquid</div><div class="f">${chem(liquidWater)}</div></div>
        <div class="val">M = ${fix(run.molar_mass, 2)} <span class="dim">g/mol</span></div></div>
      <div class="step-row"><div><div class="t">2. Heat of combustion at constant pressure</div><div class="f">ΔH<sub>c</sub> = Σ ν<sub>i</sub> ΔH°<sub>f,i</sub> at 298.15 K</div></div>
        <div class="val">${kJ(run.dH_c)} <span class="dim">kJ/mol</span></div></div>
      <div class="step-row"><div><div class="t">3. The bomb has a fixed volume, so it measures ΔU</div>
        <div class="f">ΔU<sub>c</sub> = ΔH<sub>c</sub> − Δn<sub>gas</sub>RT, Δn<sub>gas</sub> = ${signed(run.dn_gas, 2)}, Δn<sub>gas</sub>RT = ${signed(run.dn_RT / 1000, 3)} kJ/mol</div></div>
        <div class="val">${kJ(run.dU_c)} <span class="dim">kJ/mol</span></div></div>
      <div class="step-row"><div><div class="t">4. Calorific value</div><div class="f">−ΔU<sub>c</sub> / M</div></div>
        <div class="val">${fix(run.calorific_value / 1000, 3)} <span class="dim">MJ/kg</span></div></div>
      ${found ? "" : `<div class="step-row"><div><div class="t">5. Heat released by the sample</div>
        <div class="f">m × calorific value + thread and wire = ${fix(run.mass, 4)} g × ${fix(run.calorific_value / J, 0)} cal/g + ${fix(run.corrections / J, 1)} cal</div></div>
        <div class="val">${fix(run.heat_released / J, 0)} <span class="dim">cal</span></div></div>
      <div class="step-row"><div><div class="t">6. Temperature rise</div><div class="f">ΔT = heat released / C<sub>cal</sub></div></div>
        <div class="val">${fix(run.dT, 3)} <span class="dim">°C</span></div></div>`}
      <div class="step-row"><div><div class="t">${found ? "5" : "7"}. Heating values at constant pressure</div>
        <div class="f">higher: −ΔH<sub>c</sub>/M with liquid water; lower: the same with water vapour (${fix(run.water_per_gram, 3)} g of water per g of fuel)</div></div>
        <div class="val">${fix(run.HHV / 1000, 2)} / ${fix(run.LHV / 1000, 2)} <span class="dim">MJ/kg</span></div></div>
      <p class="hint" style="margin:10px 0 0">The lab handout takes the lower heating value as HHV − m<sub>w</sub>·h<sub>fg</sub>, starting from the bomb value. Here that gives
        ${fix(run.LHV_shortcut / 1000, 2)} MJ/kg with h<sub>fg</sub> = ${fix(run.h_fg_water, 0)} J/g at 298.15 K, against ${fix(run.LHV / 1000, 2)} MJ/kg from the
        formation data. The small difference is the Δn<sub>gas</sub>RT term.</p></div>`;

    $("#bc-out").innerHTML = html;
    animateRise(dT);
  }

  const ignite = TS.latest(async () => {
    const button = $("#bc-run");
    button.disabled = true;
    try {
      renderCalorimeter(await TS.engine.call("calorimeter", calorimeterPayload()));
    } catch (err) {
      $("#bc-out").innerHTML = `<div class="panel">${TS.errorBox(err)}</div>`;
    } finally {
      button.disabled = false;
    }
  });

  /* ====================================================================== tab */
  let view = "reactor";
  let viewSeg = null;
  const started = { reactor: false, calorimeter: false };

  function showView(next) {
    view = next;
    viewSeg.set(next);
    $("#hl-reactor").hidden = next !== "reactor";
    $("#hl-calorimeter").hidden = next !== "calorimeter";
    if (!TS.ready) return;
    if (!started[next]) {
      started[next] = true;
      if (next === "reactor") calculate(); else ignite();
    }
    if (typeof Plotly !== "undefined") {
      requestAnimationFrame(() => { for (const plot of $$("#tab-heat .js-plotly-plot")) Plotly.Plots.resize(plot); });
    }
  }

  TS.heatView = (next) => showView(next);
  TS.heatExample = (id) => { $("#hb-select").value = id; loadExample(id); started.reactor = true; calculate(); };

  TS.tabs.push({
    id: "heat",
    init() {
      viewSeg = TS.bindSeg("hl-view", "view", showView);

      // ---- reactor
      const select = $("#hb-select");
      select.innerHTML = TS.library.heat_examples.map((e) => `<option value="${esc(e.id)}">${esc(e.name)}</option>`).join("") +
        `<option value="">Custom reaction</option>`;
      select.addEventListener("change", () => { if (select.value) { loadExample(select.value); calculate(); } });
      $("#hb-equation").addEventListener("input", () => { select.value = ""; $("#hb-note").textContent = ""; });
      $("#hb-equation").addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      $("#hb-run").addEventListener("click", () => calculate());
      modeSeg = TS.bindSeg("hb-mode", "mode", (m) => { setMode(m); calculate(); });
      for (const id of ["hb-Tin", "hb-conv", "hb-excess", "hb-Tout"]) TS.bindSlider(id, calculate, calculate);
      $("#hb-air").addEventListener("change", () => calculate());
      for (const id of ["hb-key", "hb-excess-species", "hb-sweep", "hb-extra-species"]) {
        $("#" + id).addEventListener("change", () => calculate());
      }
      for (const id of ["hb-target", "hb-Q", "hb-side-eq", "hb-side-extent", "hb-extra-n"]) {
        $("#" + id).addEventListener("change", () => calculate());
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") calculate(); });
      }
      $("#hb-extra-species").innerHTML = `<option value="">none</option>` +
        TS.database.species.filter((s) => s.phase === "g").map((s) => `<option value="${esc(s.id)}">${esc(s.id)} ${esc(s.name)}</option>`).join("");
      loadExample(TS.library.heat_examples[0].id);

      // ---- calorimeter
      const h = TS.library.calorimeter_handout;
      $("#bc-std-mass").value = h.mass_g;
      $("#bc-std-cv").value = h.calorific_value_cal_per_g;
      $("#bc-std-dT").value = h.dT;
      $("#bc-std-corr").value = h.corrections_cal;
      $("#bc-C").value = h.C_cal_cal_per_K;
      const fuels = TS.library.fuels;
      const group = (label, list) => (list.length ? `<optgroup label="${label}">` +
        list.map((f) => `<option value="${esc(f.id)}">${esc(f.name)}, ${esc(f.id)}</option>`).join("") + "</optgroup>" : "");
      $("#bc-fuel").innerHTML = group("Liquids and solids", fuels.filter((f) => f.phase !== "g")) + group("Gases", fuels.filter((f) => f.phase === "g"));
      if (fuels.some((f) => f.id === "C2H5OH(l)")) $("#bc-fuel").value = "C2H5OH(l)";
      TS.bindSeg("bc-cal-mode", "cal", (m) => {
        calMode = m;
        $("#bc-calibrate").hidden = m !== "calibrate";
        $("#bc-known").hidden = m !== "known";
      });
      TS.bindSeg("bc-mode", "mode", (m) => {
        runMode = m;
        $("#bc-fuel-box").hidden = m !== "predict";
        $("#bc-dT-box").hidden = m !== "identify";
        $("#bc-gases-box").hidden = m !== "identify";
        $("#bc-run").textContent = m === "predict" ? "Ignite" : "Identify";
      });
      $("#bc-run").addEventListener("click", () => ignite());
      $("#bc-fuel").addEventListener("change", () => ignite());
      $("#bc-gases").addEventListener("change", () => ignite());
      for (const id of ["bc-mass", "bc-dT", "bc-corr", "bc-std-mass", "bc-std-cv", "bc-std-dT", "bc-std-corr", "bc-C"]) {
        $("#" + id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") ignite(); });
      }
    },
    onShow() {
      showView(view);
    },
  });
})();
