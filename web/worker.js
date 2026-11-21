/* Web worker: runs the Python solver (thermosolver/) in the browser with Pyodide.
 *
 * The page never re-implements any thermodynamics in JavaScript. Every number
 * shown comes from the same Python package that the unit tests exercise.
 */
const PYODIDE_VERSION = "0.26.4";
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

// Order does not matter: all files are written to the virtual file system
// before the package is imported.
const FILES = [
  "__init__.py", "constants.py", "errors.py", "formula.py", "data.py", "heatcap.py",
  "species.py", "reaction.py", "realgas.py", "equilibrium.py", "combine.py",
  "electrochem.py", "audit.py", "library.py", "benchmarks.py", "literature.py", "api.py",
];

function status(message) {
  self.postMessage({ type: "status", message });
}

const ready = (async () => {
  status("Downloading the Python runtime…");
  importScripts(PYODIDE_BASE + "pyodide.js");
  const pyodide = await loadPyodide({ indexURL: PYODIDE_BASE });

  status("Loading the solver…");
  const dir = "/home/pyodide/thermosolver";
  pyodide.FS.mkdirTree(dir);
  const base = new URL("../thermosolver/", self.location.href);
  await Promise.all(FILES.map(async (name) => {
    const response = await fetch(new URL(name, base), { cache: "no-cache" });
    if (!response.ok) throw new Error(`Could not load thermosolver/${name} (HTTP ${response.status})`);
    pyodide.FS.writeFile(`${dir}/${name}`, await response.text());
  }));

  pyodide.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
from thermosolver import api as _api
`);
  return pyodide.globals.get("_api").call;
})();

ready.then(
  () => self.postMessage({ type: "ready" }),
  (err) => self.postMessage({ type: "failed", message: String(err && err.message ? err.message : err) }),
);

self.onmessage = async (event) => {
  const { id, endpoint, payload } = event.data;
  let text;
  try {
    const call = await ready;
    text = call(endpoint, JSON.stringify(payload || {}));
  } catch (err) {
    text = JSON.stringify({
      ok: false,
      error: { kind: "engine_error", message: `The calculation engine failed: ${err}`, details: {} },
    });
  }
  self.postMessage({ type: "result", id, text });
};
