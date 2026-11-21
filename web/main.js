/* Start-up: boot the Python engine, load the library and database, wire the tabs. */
"use strict";
(() => {
  const { $, $$ } = TS;

  function setEngine(state, text) {
    const el = $("#engine");
    el.className = `engine ${state}`;
    $("#engine-text").textContent = text;
  }

  function showTab(id, push = true) {
    const tab = TS.tabs.find((t) => t.id === id) || TS.tabs[0];
    for (const button of $$(".tabs button")) {
      const active = button.dataset.tab === tab.id;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
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

  async function start() {
    for (const button of $$(".tabs button")) {
      button.addEventListener("click", () => showTab(button.dataset.tab));
    }
    for (const button of $$("button.primary")) button.disabled = true;

    TS.engine = new TS.Engine(setEngine);
    try {
      await TS.engine.ready;
      [TS.library, TS.database] = await Promise.all([TS.engine.call("library"), TS.engine.call("database")]);
    } catch (err) {
      setEngine("failed", err.message);
      $("#rx-out").innerHTML = TS.message("error", `<strong>The solver could not start.</strong> ${TS.esc(err.message)}`);
      return;
    }
    for (const button of $$("button.primary")) button.disabled = false;
    for (const tab of TS.tabs) tab.init();
    TS.ready = true;
    showTab((location.hash || "#reaction").slice(1), false);
    window.addEventListener("hashchange", () => showTab(location.hash.slice(1), false));
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
