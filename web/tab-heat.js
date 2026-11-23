/* Tab 5 (extra feature 2): the bomb calorimeter of the course lab.
 *
 * Constant-volume combustion: the calorimeter constant from a calibration run
 * with benzoic acid, then the temperature rise of a known fuel, or the closest
 * fuels of the database for a measured rise.
 *
 * (Until v1.8.3 this tab also had a "Reactor and flame" view, an energy balance
 * around a reactor. The user asked for it to be taken off the page; the solver
 * still has it: thermosolver/heatbalance.py and the "heat_balance" endpoint.)
 *
 * The page only converts units for display (calories, Celsius).
 * Every thermodynamic number comes from the Python solver.
 */
"use strict";
(() => {
  const { $, esc, chem, fix, kJ, signed } = TS;
  const bare = (sid) => sid.replace(/\((g|l|s)\)$/, "");

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
    const top = dT * 1.04;          // the axis ends just above the rise: no empty band over the curve
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
    // A hidden tab gets no animation frames, so it is shown the final state at once.
    if (still || !length || document.hidden) { readout.textContent = fix(dT, 2); return; }
    curve.style.strokeDasharray = `${length}`;
    curve.style.strokeDashoffset = `${length}`;
    const duration = 2400;
    const begin = performance.now();
    // Safety net: whatever happens to the animation, the final value is shown.
    setTimeout(() => {
      if (!document.body.contains(curve)) return;
      curve.style.strokeDashoffset = "0";
      readout.textContent = fix(dT, 2);
    }, duration + 500);
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
    const heat = found ? found.heat_measured : run.heat_released;

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
  let started = false;

  TS.tabs.push({
    id: "heat",
    init() {
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
      if (started || !TS.ready) return;
      started = true;
      ignite();
    },
  });
})();
