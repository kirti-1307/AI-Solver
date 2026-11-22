/* Start-up: boot the Python engine, load the library and database, wire the
 * tabs, the start page and the light/dark switch. */
"use strict";
(() => {
  const { $, $$ } = TS;

  function setEngine(state, text) {
    const el = $("#engine");
    el.className = `engine ${state}`;
    $("#engine-text").textContent = text;
    // The loading card on the page says the same thing in more words.
    const boot = $("#boot");
    if (!boot) return;
    if (state === "ready") {
      boot.hidden = true;
    } else if (state === "failed") {
      boot.classList.add("failed");
      $("#boot-title").textContent = "The solver could not start";
      $("#boot-text").textContent = text;
    } else {
      $("#boot-title").textContent = text;
    }
  }

  function showTab(id, push = true) {
    const tab = TS.tabs.find((t) => t.id === id) || TS.tabs[0];
    for (const button of $$(".tabs button")) {
      const active = button.dataset.tab === tab.id;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
      if (active && button.scrollIntoView) button.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
    for (const section of $$("main .tab")) section.classList.toggle("active", section.id === `tab-${tab.id}`);
    if (push && location.hash !== `#${tab.id}`) history.replaceState(null, "", `#${tab.id}`);
    if (TS.ready && tab.onShow) tab.onShow();
    // Plots drawn while their tab was hidden need a resize once visible.
    if (typeof Plotly !== "undefined") {
      requestAnimationFrame(() => {
        for (const plot of $$(`#tab-${tab.id} .js-plotly-plot`)) Plotly.Plots.resize(plot);
      });
    }
  }

  /* The cards of the start page: each opens a tab with a ready-made case. */
  const pick = (selector, value) => {
    const select = $(selector);
    select.value = value;
    select.dispatchEvent(new Event("change"));
  };
  const demos = {
    methanol() { showTab("reaction"); pick("#rx-select", "co2_methanol"); },
    break() {
      showTab("reaction");
      const input = $("#rx-equation");
      input.value = "CH4 + O2 -> CO2 + H2O";
      input.dispatchEvent(new Event("input"));
      $("#rx-run").click();
    },
    ammonia() { showTab("pressure"); $("#pr-P").value = 200; pick("#pr-select", "ammonia"); },
    hess() { showTab("combine"); const s = $("#cb-preset"); s.selectedIndex = 0; s.dispatchEvent(new Event("change")); },
    slate() { showTab("network"); pick("#nw-preset", "co2_hydrogenation"); },
    flame() { showTab("heat"); TS.heatView("reactor"); TS.heatExample("methane_burner"); },
    bomb() { showTab("heat"); TS.heatView("calorimeter"); },
    validation() { showTab("validation"); },
  };

  function wireTheme() {
    const button = $("#theme");
    const label = () => { button.textContent = TS.theme.current() === "dark" ? "Light" : "Dark"; };
    button.addEventListener("click", () => { TS.theme.set(TS.theme.current() === "dark" ? "light" : "dark"); label(); });
    label();
  }

  async function start() {
    for (const button of $$(".tabs button")) {
      button.addEventListener("click", () => showTab(button.dataset.tab));
    }
    wireTheme();
    TS.watchTerms();
    for (const button of $$("button.primary, .demo")) button.disabled = true;

    TS.engine = new TS.Engine(setEngine);
    try {
      await TS.engine.ready;
      [TS.library, TS.database] = await Promise.all([TS.engine.call("library"), TS.engine.call("database")]);
    } catch (err) {
      setEngine("failed", err.message);
      $("#rx-out").innerHTML = TS.message("error", `<strong>The solver could not start.</strong> ${TS.esc(err.message)}`);
      return;
    }
    for (const button of $$("button.primary, .demo")) button.disabled = false;
    for (const tab of TS.tabs) tab.init();
    TS.ready = true;
    for (const button of $$(".demo")) {
      button.addEventListener("click", () => {
        const run = demos[button.dataset.demo];
        if (!run) return;
        run();
        window.scrollTo({ top: 0 });
      });
    }
    showTab((location.hash || "#home").slice(1), false);
    window.addEventListener("hashchange", () => showTab(location.hash.slice(1), false));
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
