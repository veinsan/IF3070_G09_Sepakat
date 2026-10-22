"use strict";

const $ = (id) => document.getElementById(id);
const number = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
const fmt = (value) => Number.isFinite(value) ? number.format(value) : "–";
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const state = {
  bootstrap: null, upload: null, runs: new Map(), completed: [], activeId: null, viewedId: null,
  ship: 0, vehicle: null, view: "current", compare: false, selectedStep: 0, followLatest: true,
  playing: false, playTimer: null, pollTimer: null, polling: false, submitting: false,
  sort: { key: "order", direction: 1 }, series: [], dataPage: 0, inspectionSource: "final",
  retainedIds: null,
  renderMode: "2d", scene: null, sceneFactory: null, sceneLoading: false, sceneFailed: false,
  showGrid: true, showLabels: true, panel: "panel-config", disposed: false,
};
state.chartSource = null;
state.chartSeriesCache = [];
const statusText = { running: "Sedang mencari", completed: "Selesai", cancelled: "Dibatalkan", failed: "Gagal" };
const viewed = () => state.runs.get(state.viewedId);
const draftProblem = () => state.upload || state.bootstrap?.datasets.find((item) => item.id === $("dataset").value)?.problem;
const shownProblem = () => viewed()?.problem || draftProblem();
const frames = () => viewed()?.frames || [];
const algorithmLabel = (id) => state.bootstrap?.algorithms.find((item) => item.id === id)?.label || id;
const stepName = (run = viewed()) => run?.algorithm === "ga" ? "Generasi" : "Iterasi";
const unitName = (run = viewed()) => run?.objective === "eta" ? "unit urgensi ETA" : "juta Rp";

function errorText(error) {
  const detail = error?.detail ?? error;
  if (Array.isArray(detail)) return detail.map((item) => {
    const field = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : "";
    return `${field ? `${field}: ` : ""}${item.msg || errorText(item)}`;
  }).join("; ");
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Permintaan tidak dapat diproses. Periksa koneksi ke server lokal.";
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers } });
    if (!response.ok) {
      let detail;
      try { detail = await response.json(); } catch { detail = `Server mengembalikan HTTP ${response.status}.`; }
      const error = new Error(errorText(detail));
      error.status = response.status;
      throw error;
    }
    return options.blob ? await response.blob() : await response.json();
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Server lokal belum merespons dalam 15 detik. Proses mungkin masih berjalan; sambungkan kembali untuk melihat statusnya.");
    if (error instanceof TypeError) throw new Error("Tidak dapat terhubung ke server lokal. Pastikan aplikasi Python masih berjalan, lalu coba lagi.");
    throw error;
  } finally { clearTimeout(timeout); }
}

function showError(id, message) {
  $(id).textContent = errorText(message);
  $(id).hidden = !message;
}

async function bootstrap() {
  $("retry-bootstrap").disabled = true;
  $("boot-error").hidden = true;
  try {
    state.bootstrap = await request("/api/bootstrap");
    $("dataset").innerHTML = state.bootstrap.datasets.map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`).join("");
    $("algorithm").innerHTML = state.bootstrap.algorithms.map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`).join("");
    $("config-fields").disabled = false;
    $("run-form").setAttribute("aria-busy", "false");
    configureAlgorithm();
    renderInput();
    render();
  } catch (error) {
    $("boot-error").hidden = false;
    $("boot-error-text").textContent = errorText(error);
    $("status-label").textContent = "Koneksi terputus";
  } finally { $("retry-bootstrap").disabled = false; }
}

function configureAlgorithm() {
  const algorithm = state.bootstrap.algorithms.find((item) => item.id === $("algorithm").value);
  $("algorithm-description").textContent = algorithm.description;
  const params = Object.entries(algorithm.params);
  $("parameter-count").textContent = `(${params.length})`;
  $("parameter-fields").innerHTML = params.map(([key, param]) => `<div class="parameter-field"><label for="param-${esc(key)}">${esc(param.label)}</label><input id="param-${esc(key)}" name="${esc(key)}" type="number" value="${esc(param.default)}" min="${esc(param.min)}" max="${esc(param.max)}" step="${esc(param.step ?? 1)}" required aria-describedby="limits-${esc(key)}"><p id="limits-${esc(key)}" class="parameter-limits">Batas ${fmt(param.min)} hingga ${fmt(param.max)}</p></div>`).join("");
}

function renderInput() {
  const problem = draftProblem();
  if (!problem) return;
  const area = problem.ships.reduce((total, ship) => total + ship.width * ship.length, 0);
  const capacity = problem.ships.reduce((total, ship) => total + ship.max_capacity, 0);
  $("input-summary").innerHTML = `<strong>${esc(problem.name)}</strong>${fmt(problem.ships.length)} kapal · ${fmt(problem.vehicles.length)} kendaraan<br>${fmt(area)} sel · kapasitas gabungan ${fmt(capacity)} unit berat${state.upload ? "<br>Masukan dari unggahan JSON" : ""}`;
  if (!state.viewedId) { state.ship = 0; state.vehicle = null; render(); }
}

async function uploadProblem(event) {
  const file = event.target.files[0];
  if (!file) return;
  showError("upload-error", "");
  $("upload").removeAttribute("aria-invalid");
  try {
    const maxBytes = state.bootstrap?.limits?.max_body_bytes || 131072;
    if (file.size > maxBytes) throw new Error(`JSON terlalu besar. Batas permintaan server ${fmt(maxBytes)} byte, termasuk parameter run.`);
    let problem;
    try { problem = JSON.parse(await file.text()); } catch { throw new Error("JSON tidak dapat dibaca. Periksa tanda kutip, koma, dan struktur file."); }
    if (!problem || typeof problem !== "object" || !Array.isArray(problem.ships) || !problem.ships.length || !Array.isArray(problem.vehicles) || !problem.vehicles.length) throw new Error("Masukan harus memiliki array ships dan vehicles yang tidak kosong.");
    const ids = (items) => items.every((item) => item && typeof item.id === "string" && item.id.length > 0) && new Set(items.map((item) => item.id)).size === items.length;
    if (!ids(problem.ships) || !ids(problem.vehicles)) throw new Error("Setiap kapal dan kendaraan harus memiliki id teks yang unik.");
    const positive = (value) => typeof value === "number" && Number.isFinite(value) && value > 0;
    const maxDimension = state.bootstrap.limits.max_dimension;
    const dimension = (value) => positive(value) && Number.isInteger(value) && value <= maxDimension;
    if (!problem.ships.every((ship) => dimension(ship.width) && dimension(ship.length) && positive(ship.max_capacity))) throw new Error(`Ukuran kapal harus bilangan bulat positif hingga ${maxDimension}; kapasitas harus angka positif.`);
    if (!problem.vehicles.every((vehicle) => dimension(vehicle.width) && dimension(vehicle.length) && positive(vehicle.weight) && typeof vehicle.shipping_fee === "number" && Number.isFinite(vehicle.shipping_fee) && vehicle.shipping_fee >= 0 && Number.isInteger(vehicle.eta) && vehicle.eta >= 0)) throw new Error("Periksa ukuran kendaraan, fee nonnegatif, berat positif, serta ETA bilangan bulat nonnegatif.");
    const name = file.name.split(/[\\/]/).pop().replace(/[^\p{L}\p{N}_. -]/gu, "_").slice(0, 80) || "Unggahan";
    state.upload = { ...problem, name };
    $("dataset").disabled = true;
    $("upload-note").innerHTML = `${esc(name)} dipilih. <button id="clear-upload" type="button">Gunakan dataset bawaan</button>`;
    $("clear-upload").addEventListener("click", clearUpload);
    renderInput();
  } catch (error) {
    $("upload").setAttribute("aria-invalid", "true");
    showError("upload-error", error);
    $("upload").value = "";
  }
}

function clearUpload() {
  state.upload = null;
  $("upload").value = "";
  $("dataset").disabled = false;
  $("upload-note").textContent = "File diproses di memori, tidak disimpan ke disk.";
  showError("upload-error", "");
  renderInput();
}

async function startRun(event) {
  event.preventDefault();
  if (state.submitting || state.runs.get(state.activeId)?.status === "running") return;
  if (!$("run-form").reportValidity()) return;
  showError("run-error", "");
  showError("job-error", "");
  const params = Object.fromEntries([...$("parameter-fields").querySelectorAll("input")].map((input) => [input.name, Number(input.value)]));
  const body = { algorithm: $("algorithm").value, dataset: $("dataset").value, objective: $("objective").value, seed: Number($("seed").value), params, ...(state.upload ? { problem: state.upload } : {}) };
  const problem = draftProblem();
  state.submitting = true;
  $("run-button").disabled = true;
  $("run-button").textContent = "Mengirim konfigurasi…";
  try {
    const response = await request("/api/runs", { method: "POST", body: JSON.stringify(body) });
    const run = { ...body, ...response, problem, frames: [], result: null, progress: { step: null, target: null }, error: null };
    for (const existingId of state.runs.keys()) if (!state.completed.includes(existingId)) state.runs.delete(existingId);
    state.runs.set(run.id, run);
    state.activeId = run.id;
    state.viewedId = run.id;
    state.ship = 0;
    state.vehicle = null;
    state.selectedStep = 0;
    state.followLatest = true;
    state.compare = false;
    pause();
    render();
    schedulePoll(0);
    if (window.matchMedia("(max-width: 767px)").matches) {
      $("workspace").focus({ preventScroll: true });
      $("workspace").scrollIntoView({ behavior: "auto", block: "start" });
    }
  } catch (error) {
    showError("run-error", error);
    $("run-error").focus();
  } finally { state.submitting = false; renderRunButton(); }
}

function schedulePoll(delay = 400) {
  clearTimeout(state.pollTimer);
  state.pollTimer = setTimeout(poll, delay);
}

function trackRetention(run) {
  if (!Array.isArray(run.retained_ids)) return;
  state.retainedIds = new Set(run.retained_ids);
  state.completed = state.completed.filter((id) => state.retainedIds.has(id));
  for (const [id, saved] of state.runs) {
    if (saved.status !== "running" && id !== state.viewedId && !state.retainedIds.has(id)) state.runs.delete(id);
  }
}

async function poll() {
  const id = state.activeId;
  if (!id || state.polling || state.runs.get(id)?.status !== "running") return;
  state.polling = true;
  let keepPolling = false;
  try {
    const run = await request(`/api/runs/${encodeURIComponent(id)}`);
    const previous = state.runs.get(id);
    if (previous?.status !== "running" && run.status === "running") return;
    state.runs.set(id, { ...previous, ...run });
    trackRetention(run);
    $("resume-poll").hidden = true;
    if (run.status === "completed" && !state.completed.includes(id)) {
      state.completed.unshift(id);
      if (state.viewedId === id && state.followLatest) state.view = "best";
      if (state.completed.length > state.bootstrap.limits.history_size) {
        const removed = state.completed.pop();
        if (removed !== state.viewedId) state.runs.delete(removed);
      }
    }
    keepPolling = run.status === "running";
    if (run.status === "failed") showError("job-error", run.error || "Pencarian gagal. Periksa parameter lalu jalankan kembali.");
    if (state.viewedId === id) render();
    else { renderActiveStatus(); renderHistory(); renderRunButton(); }
  } catch (error) {
    showError("job-error", error);
    if (error.status === 404) {
      state.runs.set(id, { ...state.runs.get(id), status: "failed", error: error.message });
      state.activeId = null;
      $("resume-poll").hidden = true;
      render();
    } else $("resume-poll").hidden = false;
  } finally {
    state.polling = false;
    if (keepPolling) schedulePoll();
  }
}

async function cancelRun() {
  const id = state.activeId;
  if (!id) return;
  $("cancel-button").disabled = true;
  try {
    await request(`/api/runs/${encodeURIComponent(id)}/cancel`, { method: "POST" });
    const response = await request(`/api/runs/${encodeURIComponent(id)}`);
    state.runs.set(id, { ...state.runs.get(id), ...response });
    trackRetention(response);
    if (response.status === "completed" && !state.completed.includes(id)) {
      state.completed.unshift(id);
      if (state.completed.length > state.bootstrap.limits.history_size) {
        const removed = state.completed.pop();
        if (removed !== state.viewedId) state.runs.delete(removed);
      }
    }
    $("resume-poll").hidden = true;
    if (response.status === "running") schedulePoll(0);
    render();
  } catch (error) { showError("job-error", error); }
  finally { $("cancel-button").disabled = false; }
}

function renderRunButton() {
  const busy = state.submitting || state.runs.get(state.activeId)?.status === "running";
  $("run-button").disabled = busy || !state.bootstrap;
  $("run-button").textContent = state.submitting ? "Mengirim konfigurasi…" : busy ? "Pencarian berlangsung…" : "Jalankan simulasi";
}

function renderActiveStatus() {
  const active = state.runs.get(state.activeId);
  $("show-active-run").hidden = !active || active.id === state.viewedId || active.status !== "running";
  $("cancel-button").hidden = active?.status !== "running";
  $("progress-region").hidden = active?.status !== "running";
  if (active?.status === "running") {
    const progress = active.progress || {};
    if (Number.isFinite(progress.target) && progress.target > 0) {
      $("run-progress").max = progress.target;
      $("run-progress").value = Math.min(progress.step || 0, progress.target);
    } else $("run-progress").removeAttribute("value");
    $("progress-text").textContent = Number.isFinite(progress.step) ? `${stepName(active)} teramati ${fmt(progress.step)}${progress.target ? ` / batas ${fmt(progress.target)}` : ""}${active.id !== state.viewedId ? " · proses lain sedang ditampilkan" : ""}` : "Menunggu snapshot pertama…";
  }
}

function frameIndex() {
  const list = frames();
  if (!list.length) return -1;
  if (state.followLatest) return list.length - 1;
  let nearest = 0;
  for (let index = 1; index < list.length; index++) if (Math.abs(list[index].step - state.selectedStep) < Math.abs(list[nearest].step - state.selectedStep)) nearest = index;
  return nearest;
}

function selectedFrame() { return frames()[frameIndex()] || null; }
function selectedView() { return selectedFrame()?.[state.view] || null; }
function originalFee(problem, view) { return view ? problem.vehicles.reduce((sum, vehicle, index) => sum + (view.positions[index] ? vehicle.shipping_fee : 0), 0) : 0; }

function render() {
  const problem = shownProblem();
  if (!problem) return;
  const run = viewed();
  $("run-context").textContent = run ? `${algorithmLabel(run.algorithm)} · seed ${run.seed}` : "Pratinjau masukan";
  $("run-title").textContent = problem.name;
  $("run-subtitle").textContent = run ? `${run.objective === "eta" ? "Objective urgensi ETA" : "Objective pendapatan"} · ${fmt(problem.ships.length)} kapal · ${fmt(problem.vehicles.length)} kendaraan${run.result ? ` · ${fmt(run.result.duration_s)} dtk pencarian` : ""}` : `${fmt(problem.ships.length)} kapal · ${fmt(problem.vehicles.length)} kendaraan · belum ada hasil pencarian`;
  $("status-label").textContent = run ? statusText[run.status] || run.status : "Belum dijalankan";
  $("status-label").dataset.status = run?.status || "preview";
  if (run?.error) showError("job-error", run.error);
  if (state.ship >= problem.ships.length) state.ship = 0;
  const shipOptions = problem.ships.map((ship, index) => `<option value="${index}">${esc(ship.id)} · ${ship.width} × ${ship.length}</option>`).join("");
  if ($("ship-select").innerHTML !== shipOptions) $("ship-select").innerHTML = shipOptions;
  $("ship-select").value = String(state.ship);
  $("ship-select").disabled = problem.ships.length < 2;
  const available = frames().length > 0;
  $("view-current").disabled = !available || state.compare;
  $("view-best").disabled = !available || state.compare;
  $("view-current").setAttribute("aria-pressed", String(state.view === "current"));
  $("view-best").setAttribute("aria-pressed", String(state.view === "best"));
  $("compare-button").disabled = !available || run?.status !== "completed";
  $("compare-button").setAttribute("aria-pressed", String(state.compare));
  $("compare-button").textContent = state.compare ? "Kembali ke snapshot" : "Bandingkan awal / akhir";
  const frame = selectedFrame();
  $("frame-caption").textContent = state.compare ? "Awal aktual vs hasil akhir feasible" : frame ? `${stepName()} ${fmt(frame.step)} · ${state.view === "best" ? "terbaik feasible" : "state pencarian"}` : run ? "Menunggu snapshot pencarian" : "Pratinjau masukan · belum dijalankan";
  renderDeck();
  renderSummary();
  renderPlayback();
  renderInspection();
  renderChart();
  renderHistory();
  renderActiveStatus();
  renderRunButton();
  const expired = !!run?.result && state.retainedIds && !state.retainedIds.has(run.id);
  $("download-json").disabled = !run?.result || expired;
  $("download-png").disabled = !run?.result || expired;
  if (expired) $("run-subtitle").textContent += " · ekspor sudah kedaluwarsa";
}

function deckSVG(problem, view, prefix, title) {
  const ship = problem.ships[state.ship];
  const items = problem.vehicles.flatMap((vehicle, index) => {
    const position = view?.positions[index];
    if (!position || position[0] !== state.ship) return [];
    return [{ vehicle, index, x: position[1], y: position[2], width: position[3] === "H" ? vehicle.width : vehicle.length, height: position[3] === "H" ? vehicle.length : vehicle.width, orientation: position[3] }];
  });
  const scale = Math.max(ship.width, ship.length);
  const pad = Math.max(1, scale * .075);
  const minX = Math.min(0, ...items.map((item) => item.x));
  const minY = Math.min(0, ...items.map((item) => item.y));
  const maxX = Math.max(ship.width, ...items.map((item) => item.x + item.width));
  const maxY = Math.max(ship.length, ...items.map((item) => item.y + item.height));
  const font = Math.max(.3, scale / 48);
  let grid = "";
  for (let x = 0; x <= ship.width; x++) grid += `<line class="grid-line" x1="${x}" y1="0" x2="${x}" y2="${ship.length}"/>`;
  for (let y = 0; y <= ship.length; y++) grid += `<line class="grid-line" x1="0" y1="${y}" x2="${ship.width}" y2="${y}"/>`;
  const vehicles = items.map((item) => {
    const out = item.x < 0 || item.y < 0 || item.x + item.width > ship.width || item.y + item.height > ship.length;
    return `<g class="vehicle${state.vehicle === item.index ? " is-selected" : ""}" role="button" tabindex="0" data-vehicle="${item.index}" data-source="${prefix}" aria-label="${esc(item.vehicle.id)}, kapal ${esc(ship.id)}, x ${item.x}, y ${item.y}, orientasi ${item.orientation}${out ? ", keluar batas" : ""}" aria-pressed="${state.vehicle === item.index}"><title>${esc(item.vehicle.id)} · ${item.width} × ${item.height}${out ? " · keluar batas" : ""}</title><rect class="body" x="${item.x + .04}" y="${item.y + .04}" width="${Math.max(.1, item.width - .08)}" height="${Math.max(.1, item.height - .08)}" rx=".1"/><text x="${item.x + item.width / 2}" y="${item.y + item.height / 2}" dominant-baseline="central" text-anchor="middle" font-size="${Math.min(.65, item.width / Math.max(2, String(item.vehicle.id).length) * 1.3, item.height * .4)}">${esc(item.vehicle.id)}</text>${out ? `<rect x="${item.x}" y="${item.y}" width="${item.width}" height="${item.height}" fill="url(#${prefix}-violation)" pointer-events="none"/>` : ""}</g>`;
  }).join("");
  let overlaps = "";
  for (let a = 0; a < items.length; a++) for (let b = a + 1; b < items.length; b++) {
    const x = Math.max(items[a].x, items[b].x, 0), y = Math.max(items[a].y, items[b].y, 0);
    const w = Math.min(items[a].x + items[a].width, items[b].x + items[b].width, ship.width) - x;
    const h = Math.min(items[a].y + items[a].height, items[b].y + items[b].height, ship.length) - y;
    if (w > 0 && h > 0) overlaps += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${prefix}-violation)" pointer-events="none"/>`;
  }
  return `<svg class="deck-svg" xmlns="http://www.w3.org/2000/svg" viewBox="${minX - pad} ${minY - pad} ${maxX - minX + pad * 2} ${maxY - minY + pad * 2}" role="group" aria-labelledby="${prefix}-title ${prefix}-description"><title id="${prefix}-title">${esc(title)}: kapal ${esc(ship.id)}</title><desc id="${prefix}-description">Lebar ${ship.width} sel, panjang ${ship.length} sel. ${items.length} kendaraan. Pilih kendaraan dengan Tab lalu Enter. Arsiran menunjukkan pelanggaran geometri.</desc><defs><pattern id="${prefix}-violation" width=".45" height=".45" patternUnits="userSpaceOnUse"><path d="M0 .45L.45 0" stroke="var(--danger)" stroke-width=".07"/></pattern></defs><rect class="ship-outline" x="0" y="0" width="${ship.width}" height="${ship.length}"/>${grid}${vehicles}${overlaps}<text class="axis-label" x="0" y="${-.3 * pad}" font-size="${font}">0</text><text class="axis-label" x="${ship.width}" y="${-.3 * pad}" text-anchor="end" font-size="${font}">x = ${ship.width}</text><text class="axis-label" x="0" y="${ship.length + .65 * pad}" font-size="${font}">y = ${ship.length}</text></svg>`;
}

function activatePanel(id, focus = false) {
  state.panel = id;
  for (const tab of document.querySelectorAll("[data-panel]")) {
    const active = tab.dataset.panel === id;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    $(tab.dataset.panel).hidden = !active;
    if (active && focus) tab.focus();
  }
}

function sceneFailure(error) {
  if (state.sceneFailed) return;
  state.sceneFailed = true;
  state.renderMode = "2d";
  const scene = state.scene;
  state.scene = null;
  scene?.dispose();
  showError("scene-error", `Tampilan 3D tidak tersedia. Mode 2D tetap berfungsi. ${error?.message || String(error)}`);
  renderDeck();
}

function syncScene() {
  const enabled = state.renderMode === "3d" && !state.compare && !state.sceneFailed;
  const host = $("scene-3d");
  host.hidden = !enabled;
  $("deck-canvas").hidden = enabled;
  $("viewport-shell").dataset.mode = enabled ? "3d" : "2d";
  $("render-2d").setAttribute("aria-pressed", String(!enabled));
  $("render-3d").setAttribute("aria-pressed", String(enabled));
  $("render-3d").disabled = state.sceneFailed;
  $("scene-note").textContent = state.compare
    ? "Perbandingan awal / akhir memakai 2D. Tutup perbandingan untuk kembali ke mode sebelumnya."
    : enabled
      ? "3D ilustratif · tanpa constraint tinggi. Drag: orbit · scroll: zoom · klik: inspeksi."
      : "Grid 2D adalah acuan constraint. Pilih 3D untuk menginspeksi susunan dari sudut lain.";
  for (const id of ["camera-reset", "camera-top", "camera-zoom-in", "camera-zoom-out", "camera-orbit-left", "camera-orbit-right"]) {
    $(id).disabled = !enabled || !state.scene;
  }
  const position = selectedView()?.positions[state.vehicle];
  $("camera-focus").disabled = !enabled || !state.scene || !position || position[0] !== state.ship;
  if (!enabled) {
    state.scene?.setActive(false);
    return false;
  }
  try {
    if (!state.scene && state.sceneFactory) {
      host.replaceChildren();
      state.scene = state.sceneFactory(host, {
        onSelect: (index) => inspectVehicle(index),
        onError: sceneFailure,
      });
      return syncScene();
    }
    if (state.scene) {
      state.scene.setActive(!document.hidden);
      state.scene.update({
        problem: shownProblem(), view: selectedView(), shipIndex: state.ship,
        selectedVehicle: state.vehicle, showGrid: state.showGrid, showLabels: state.showLabels,
      });
    } else if (!state.sceneLoading) {
      state.sceneLoading = true;
      host.textContent = "Menyiapkan renderer 3D lokal…";
      import("/static/scene3d.js").then((module) => {
        if (state.disposed || state.sceneFailed) return;
        state.sceneFactory = module.createCargoScene;
        renderDeck();
      }).catch(sceneFailure).finally(() => { state.sceneLoading = false; });
    }
  } catch (error) {
    sceneFailure(error);
    return false;
  }
  return true;
}

function chooseRenderMode(mode) {
  state.renderMode = mode;
  state.compare = false;
  render();
}

function renderDeck() {
  const problem = shownProblem();
  const list = frames();
  const canvas = $("deck-canvas");
  canvas.classList.toggle("hidden-grid", !state.showGrid);
  canvas.classList.toggle("hidden-labels", !state.showLabels);
  canvas.classList.toggle("comparing", state.compare);
  if (syncScene()) return;
  const focus = canvas.contains(document.activeElement) ? { vehicle: document.activeElement.dataset.vehicle, source: document.activeElement.dataset.source } : null;
  if (state.compare && list.length) {
    canvas.innerHTML = `<figure class="deck-figure"><figcaption>Awal · ${stepName()} ${fmt(list[0].step)}<br>Objective ${fmt(list[0].current.objective)} ${esc(unitName())} · fee asli ${fmt(originalFee(problem, list[0].current))}<br>${list[0].current.feasible ? "Feasible" : "Tidak feasible"}</figcaption>${deckSVG(problem, list[0].current, "initial", "Penempatan awal")}</figure><figure class="deck-figure"><figcaption>Akhir · ${stepName()} ${fmt(list.at(-1).step)} · terbaik feasible<br>Objective ${fmt(list.at(-1).best.objective)} ${esc(unitName())} · fee asli ${fmt(originalFee(problem, list.at(-1).best))}<br>${list.at(-1).best.feasible ? "Feasible" : "Tidak feasible"}</figcaption>${deckSVG(problem, list.at(-1).best, "final", "Penempatan akhir")}</figure>`;
  } else canvas.innerHTML = deckSVG(problem, selectedView(), "deck", selectedView() ? "Snapshot terpilih" : "Pratinjau kosong");
  if (focus?.vehicle !== undefined) canvas.querySelector(`[data-vehicle="${focus.vehicle}"][data-source="${focus.source}"]`)?.focus({ preventScroll: true });
}

function renderSummary() {
  const problem = shownProblem();
  const list = frames();
  const view = state.compare ? list.at(-1)?.best : selectedView();
  const notice = $("state-notice");
  notice.classList.toggle("has-violation", !!view && !view.feasible);
  if (!view) {
    notice.textContent = viewed() ? "Belum ada snapshot yang diterima. Geometri ini bukan hasil pencarian." : "Pratinjau kosong bukan hasil optimasi. Jalankan simulasi untuk melihat penempatan.";
    $("state-summary").innerHTML = "";
    $("ship-capacities").innerHTML = problem.ships.map((ship) => `<span>${esc(ship.id)}: kapasitas ${fmt(ship.max_capacity)} unit berat</span>`).join("");
    return;
  }
  const violations = `${fmt(view.overlap_cells)} sel tumpang tindih · ${fmt(view.out_of_bound_cells)} sel keluar batas · ${fmt(view.weight_units)} unit penalti berat`;
  notice.textContent = `${state.compare ? "Ringkasan hasil akhir. " : ""}${view.feasible ? "Feasible: semua kendala terpenuhi." : `Tidak feasible: ${violations}.`}`;
  if ((state.compare || state.view === "best") && viewed()?.result?.extra.empty_baseline_used) {
    notice.textContent = "Belum ada kandidat feasible yang ditemukan. Hasil ini memakai baseline kapal kosong, bukan keberhasilan optimasi.";
  }
  const loaded = view.positions.filter(Boolean).length;
  const occupied = view.occupied_cells.reduce((sum, value) => sum + value, 0);
  const area = problem.ships.reduce((sum, ship) => sum + ship.width * ship.length, 0);
  const metrics = [
    ["Objective (setelah penalti)", fmt(view.objective), unitName()],
    ["Pendapatan asli", fmt(originalFee(problem, view)), "juta Rp"],
    ["Kendaraan dimuat", `${fmt(loaded)} / ${fmt(problem.vehicles.length)}`, "kendaraan"],
    ["Sel terisi gabungan", `${fmt(100 * occupied / area)}%`, `${fmt(occupied)} / ${fmt(area)} sel`],
  ];
  $("state-summary").innerHTML = metrics.map(([label, value, unit]) => `<dl><dt>${esc(label)}</dt><dd>${esc(value)} <small>${esc(unit)}</small></dd></dl>`).join("");
  $("ship-capacities").innerHTML = problem.ships.map((ship, index) => `<span class="${view.used_weight[index] > ship.max_capacity + 1e-9 ? "overweight" : ""}">${esc(ship.id)}: ${fmt(view.used_weight[index])} / ${fmt(ship.max_capacity)} unit berat${view.used_weight[index] > ship.max_capacity + 1e-9 ? " · kapasitas terlampaui" : ""}</span>`).join("");
}

function renderPlayback() {
  const list = frames();
  const index = frameIndex();
  const disabled = !list.length || state.compare;
  $("frame-range").max = String(Math.max(0, list.length - 1));
  $("frame-range").value = String(Math.max(0, index));
  $("frame-range").disabled = disabled;
  $("frame-range").setAttribute("aria-valuetext", list.length ? `${stepName()} ${list[index].step}, snapshot ${index + 1} dari ${list.length}` : "Belum ada snapshot");
  $("timeline-label").textContent = list.length ? `Snapshot ${index + 1} / ${list.length} · ${stepName().toLowerCase()} ${fmt(list[index].step)}${state.followLatest && viewed()?.status === "running" ? " · mengikuti terbaru" : ""}` : "Belum ada snapshot";
  $("reset-frame").disabled = disabled || index <= 0;
  $("previous-frame").disabled = disabled || index <= 0;
  $("next-frame").disabled = disabled || index >= list.length - 1;
  $("last-frame").disabled = disabled || index >= list.length - 1;
  $("play-button").disabled = disabled || list.length < 2;
  $("play-button").textContent = state.playing ? "Jeda" : "Putar";
}

function selectFrame(index) {
  const list = frames();
  if (!list.length) return;
  const bounded = Math.max(0, Math.min(index, list.length - 1));
  state.selectedStep = list[bounded].step;
  state.followLatest = false;
  render();
}

function pause() {
  state.playing = false;
  clearTimeout(state.playTimer);
  $("play-button").textContent = "Putar";
}

function playbackTick() {
  if (!state.playing || document.hidden) return pause();
  const index = frameIndex();
  if (index >= frames().length - 1) { pause(); renderPlayback(); return; }
  selectFrame(index + 1);
  state.playTimer = setTimeout(playbackTick, Number($("play-speed").value));
}

function togglePlayback() {
  if (state.playing) { pause(); return; }
  if (frameIndex() >= frames().length - 1) selectFrame(0);
  state.playing = true;
  renderPlayback();
  state.playTimer = setTimeout(playbackTick, Number($("play-speed").value));
}

function inspectVehicle(index, source = "final") {
  state.vehicle = index;
  state.inspectionSource = source;
  pause();
  const view = state.compare
    ? source === "initial" ? frames()[0]?.current : frames().at(-1)?.best
    : selectedView();
  const position = view?.positions[index];
  if (position) state.ship = position[0];
  activatePanel("panel-inspect");
  render();
}

function renderInspection() {
  const problem = shownProblem();
  const view = state.compare ? state.inspectionSource === "initial" ? frames()[0]?.current : frames().at(-1)?.best : selectedView();
  const outside = problem.vehicles.flatMap((vehicle, index) => !view?.positions[index] ? [{ vehicle, index }] : []);
  $("outside-title").textContent = view ? "Di luar kapal" : "Kendaraan masukan";
  $("outside-count").textContent = fmt(outside.length);
  const vehicleOptions = '<option value="">Pilih kendaraan…</option>' + problem.vehicles.map((vehicle, index) => {
    const position = view?.positions[index];
    const location = position ? problem.ships[position[0]].id : view ? "di luar kapal" : "belum ditempatkan";
    return `<option value="${index}">${esc(vehicle.id)} · ${esc(location)}</option>`;
  }).join("");
  if ($("vehicle-select").innerHTML !== vehicleOptions) $("vehicle-select").innerHTML = vehicleOptions;
  $("vehicle-select").value = state.vehicle === null ? "" : String(state.vehicle);
  const outsideFocus = $("outside-list").contains(document.activeElement) ? document.activeElement.dataset.outside : undefined;
  $("outside-list").innerHTML = outside.length ? outside.map(({ vehicle, index }) => `<button type="button" data-outside="${index}" aria-pressed="${state.vehicle === index}" aria-label="Inspeksi ${esc(vehicle.id)}${view ? ", di luar kapal" : ", belum ditempatkan"}">${esc(vehicle.id)}</button>`).join("") : "<p class=\"help\">Semua kendaraan telah dimuat.</p>";
  if (outsideFocus !== undefined) $("outside-list").querySelector(`[data-outside="${outsideFocus}"]`)?.focus({ preventScroll: true });
  const vehicle = problem.vehicles[state.vehicle];
  if (!vehicle) {
    $("vehicle-detail").innerHTML = "<p class=\"muted\">Pilih kendaraan di geladak atau daftar kendaraan untuk melihat ukuran, fee, berat, dan penempatannya.</p>";
    return;
  }
  const position = view?.positions[state.vehicle];
  const facts = [["Ukuran asli", `${vehicle.width} × ${vehicle.length} sel`], ["Berat", `${fmt(vehicle.weight)} unit`], ["Fee asli", `${fmt(vehicle.shipping_fee)} juta Rp`], ["ETA", `${fmt(vehicle.eta)} hari`], ["Bobot urgensi ETA", `${fmt(vehicle.shipping_fee * (1 + 1 / (vehicle.eta + 1)))} unit`], ["Orientasi", position ? `${position[3]}${position[3] === "V" ? " (diputar 90°)" : " (asli)"}` : "Belum ditempatkan"]];
  $("vehicle-detail").innerHTML = `<h3>${esc(vehicle.id)}</h3><dl class="vehicle-facts">${facts.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl><p class="placement-note">${position ? `Kapal ${esc(problem.ships[position[0]].id)} · posisi kiri atas (${position[1]}, ${position[2]}).` : view ? "Tidak dimuat ke kapal pada state ini." : "Belum ada penempatan. Jalankan simulasi untuk mengamati pencarian."}${state.compare ? ` Inspeksi mengacu pada state ${state.inspectionSource === "initial" ? "awal" : "akhir"} yang dipilih.` : ""}</p>`;
}

function thinPoints(points, max = 700) {
  if (points.length <= max) return points;
  const selected = [points[0]];
  const bucket = Math.ceil((points.length - 2) / ((max - 2) / 2));
  for (let start = 1; start < points.length - 1; start += bucket) {
    const part = points.slice(start, Math.min(points.length - 1, start + bucket));
    let low = part[0], high = part[0];
    for (const point of part) { if (point[1] < low[1]) low = point; if (point[1] > high[1]) high = point; }
    selected.push(...(low[0] === high[0] ? [low] : low[0] < high[0] ? [low, high] : [high, low]));
  }
  selected.push(points.at(-1));
  return selected;
}

function chartSeries() {
  const run = viewed();
  if (!run) return [];
  const history = run.result?.history;
  const source = history || run.frames;
  if (state.chartSource === source) return state.chartSeriesCache;
  const definitions = [
    { key: "objective", label: run.algorithm === "ga" ? "Maksimum populasi" : "Objective state pencarian", color: "var(--accent)", dash: "", field: "current" },
    { key: "best_feasible", label: "Terbaik feasible", color: "var(--success)", dash: "6 3", field: "best" },
    ...(run.algorithm === "ga" ? [{ key: "mean", label: "Rata-rata populasi", color: "var(--muted)", dash: "2 3", field: null }] : []),
  ];
  const series = definitions.map((definition) => {
    const points = history?.[definition.key] ? history[definition.key].map((value, index) => [index, value]) : frames().flatMap((frame) => {
      const value = definition.field ? frame[definition.field]?.objective : frame.details?.mean;
      return Number.isFinite(value) ? [[frame.step, value]] : [];
    });
    const finite = points.filter((point) => Number.isFinite(point[1]));
    let min = Infinity, max = -Infinity, lastStep = 0;
    for (const [step, value] of finite) { min = Math.min(min, value); max = Math.max(max, value); lastStep = Math.max(lastStep, step); }
    return { ...definition, points: finite, plotPoints: thinPoints(finite), min, max, lastStep, lookup: new Map(finite) };
  }).filter((series) => series.points.length);
  state.chartSource = source;
  state.chartSeriesCache = series;
  return series;
}

function renderChart() {
  state.series = chartSeries();
  const series = state.series;
  const run = viewed();
  $("chart-legend").innerHTML = series.map((item) => `<span><i style="border-color:${item.color};${item.dash ? "border-top-style:dashed" : ""}"></i>${esc(item.label)}</span>`).join("");
  if (!series.length) {
    $("convergence-chart").innerHTML = "<p class=\"chart-empty\">Belum ada data objective. Kurva muncul setelah snapshot pertama diterima.</p>";
    $("chart-note").textContent = "Grafik menggunakan nilai aktual pencarian, bukan estimasi.";
    $("data-page").disabled = true;
    $("data-page").innerHTML = "<option>Belum ada data</option>";
    $("chart-data-table").innerHTML = "<p class=\"help\">Belum ada data numerik.</p>";
    $("data-caption").textContent = "";
    return;
  }
  const width = Math.max(300, $("convergence-chart").clientWidth), height = $("convergence-chart").clientHeight, left = 72, right = 18, top = 20, bottom = 38;
  let min = Infinity, max = -Infinity, lastStep = 0;
  for (const item of series) { min = Math.min(min, item.min); max = Math.max(max, item.max); lastStep = Math.max(lastStep, item.lastStep); }
  const padding = (max - min) * .08 || Math.max(1, Math.abs(max) * .05);
  min -= padding; max += padding;
  const x = (step) => left + step / Math.max(1, lastStep) * (width - left - right);
  const y = (value) => top + (max - value) / (max - min) * (height - top - bottom);
  let axes = "";
  for (let index = 0; index <= 4; index++) {
    const value = min + (max - min) * index / 4;
    axes += `<line class="chart-axis" x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}"/><text class="chart-text" x="${left - 10}" y="${y(value) + 4}" text-anchor="end">${esc(fmt(value))}</text>`;
  }
  const ticks = [...new Set([0, Math.round(lastStep / 2), lastStep])];
  axes += ticks.map((step) => `<text class="chart-text" x="${x(step)}" y="${height - 18}" text-anchor="middle">${fmt(step)}</text>`).join("");
  const paths = series.map((item) => {
    const points = item.plotPoints;
    return `<polyline points="${points.map(([step, value]) => `${x(step)},${y(value)}`).join(" ")}" fill="none" stroke="${item.color}" stroke-width="2" ${item.dash ? `stroke-dasharray="${item.dash}"` : ""}/>${points.length === 1 ? `<circle cx="${x(points[0][0])}" cy="${y(points[0][1])}" r="3" fill="${item.color}"/>` : ""}`;
  }).join("");
  const cursor = selectedFrame();
  const cursorLine = cursor ? `<line class="chart-cursor" x1="${x(cursor.step)}" x2="${x(cursor.step)}" y1="${top}" y2="${height - bottom}"/><text class="chart-text" x="${Math.min(width - 80, Math.max(left + 5, x(cursor.step) + 5))}" y="14">${stepName()} ${fmt(cursor.step)}</text>` : "";
  $("convergence-chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="convergence-title convergence-description"><title id="convergence-title">Objective terhadap ${stepName().toLowerCase()}</title><desc id="convergence-description">${esc(series.map((item) => item.label).join(", "))}. Garis vertikal menunjukkan snapshot terpilih. Nilai lengkap tersedia dalam tabel data.</desc>${axes}${paths}${cursorLine}<text class="chart-text" x="${width - right}" y="${height - 1}" text-anchor="end">${stepName()} · ${esc(unitName())}</text></svg>`;
  const full = !!run.result?.history;
  $("chart-note").textContent = full ? `Riwayat aktual lengkap tersedia di tabel; kurva diringkas dengan mempertahankan ekstrem tiap kelompok bila melebihi 700 titik. Sumbu vertikal: ${unitName()}.` : `Selama proses: hanya snapshot aktual yang diterima. Garis menghubungkan sampel, bukan semua transisi. Sumbu vertikal: ${unitName()}.`;
  const count = Math.max(...series.map((item) => item.points.length));
  const pages = Math.max(1, Math.ceil(count / 30));
  state.dataPage = Math.min(state.dataPage, pages - 1);
  $("data-page").disabled = false;
  const options = Array.from({ length: pages }, (_, index) => `<option value="${index}">${index + 1} / ${pages}</option>`).join("");
  if ($("data-page").innerHTML !== options) $("data-page").innerHTML = options;
  $("data-page").value = String(state.dataPage);
  $("data-caption").textContent = `${fmt(count)} titik ${full ? "riwayat aktual (tanpa pengurangan)" : "snapshot aktual"} · maksimal 30 baris per halaman`;
  if ($("chart-data").open) renderChartData();
}

function renderChartData() {
  const series = state.series;
  if (!series.length) return;
  const start = state.dataPage * 30;
  const points = series[0].points.slice(start, start + 30);
  const lookups = series.map((item) => item.lookup);
  $("chart-data-table").innerHTML = `<table><caption>Nilai objective dalam ${esc(unitName())}</caption><thead><tr><th scope="col">${stepName()}</th>${series.map((item) => `<th scope="col">${esc(item.label)}</th>`).join("")}</tr></thead><tbody>${points.map(([step]) => `<tr><th scope="row">${fmt(step)}</th>${lookups.map((lookup) => `<td>${fmt(lookup.get(step))}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

function finalOriginalFee(run) {
  const loaded = new Set(run.result.final_state.vehicles.filter((vehicle) => vehicle.ship !== null).map((vehicle) => vehicle.id));
  return run.problem.vehicles.reduce((sum, vehicle) => sum + (loaded.has(vehicle.id) ? vehicle.shipping_fee : 0), 0);
}

function renderHistory() {
  const completed = state.completed.map((id) => state.runs.get(id)).filter((run) => run?.result);
  $("history-count").textContent = `${completed.length} run selesai`;
  if (!completed.length) {
    $("history-table").innerHTML = '<p class="empty-history">Belum ada run selesai yang masih tersimpan di server.</p>';
    return;
  }
  const { key, direction } = state.sort;
  const value = (run) => ({ algorithm: algorithmLabel(run.algorithm), seed: run.seed, objective: run.result.final_objective, fee: finalOriginalFee(run), duration: run.result.duration_s, order: state.completed.indexOf(run.id) })[key];
  const sorted = [...completed].sort((a, b) => {
    if (key === "objective") {
      const scopeA = `${a.problem.name}:${a.objective}:${JSON.stringify(a.problem)}`;
      const scopeB = `${b.problem.name}:${b.objective}:${JSON.stringify(b.problem)}`;
      if (scopeA !== scopeB) return scopeA.localeCompare(scopeB, "id");
    }
    const first = value(a), second = value(b);
    return (typeof first === "string" ? first.localeCompare(second, "id") : first - second) * direction;
  });
  const heading = (label, sortKey) => `<th scope="col" aria-sort="${key === sortKey ? direction > 0 ? "ascending" : "descending" : "none"}"><button type="button" data-sort="${sortKey}">${label}${key === sortKey ? direction > 0 ? " ↑" : " ↓" : ""}</button></th>`;
  $("history-table").innerHTML = `<table><caption>Run selesai, bukan hasil benchmark resmi. Sortir objective dikelompokkan menurut masukan dan tujuan.</caption><thead><tr>${heading("Algoritma / parameter", "algorithm")}<th scope="col">Data / tujuan</th>${heading("Seed", "seed")}${heading("Objective", "objective")}${heading("Fee asli", "fee")}${heading("Durasi", "duration")}<th scope="col">Tampilkan</th></tr></thead><tbody>${sorted.map((run) => `<tr class="${run.id === state.viewedId ? "is-active" : ""}"><td class="params-cell">${esc(algorithmLabel(run.algorithm))}<small>${esc(Object.entries(run.result.params || run.params || {}).map(([name, value]) => `${name}=${value}`).join(", "))}</small></td><td>${esc(run.problem.name)}<small>${run.objective === "eta" ? "Urgensi ETA" : "Pendapatan fee"}</small></td><td>${fmt(run.seed)}</td><td>${fmt(run.result.final_objective)}<small>${esc(unitName(run))}</small></td><td>${fmt(finalOriginalFee(run))}</td><td>${fmt(run.result.duration_s)} dtk<small>${fmt(run.result.iterations)} ${stepName(run).toLowerCase()} · ${fmt(run.result.evaluations)} evaluasi</small></td><td><button type="button" data-open-run="${esc(run.id)}" ${run.id === state.viewedId ? 'aria-current="true"' : ""}>${run.id === state.viewedId ? "Terpilih" : "Lihat run"}</button></td></tr>`).join("")}</tbody></table>`;
}

async function download(kind) {
  const run = viewed();
  if (!run?.result) return;
  const button = $(kind === "json" ? "download-json" : "download-png");
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "Menyiapkan…";
  try {
    const blob = await request(`/api/runs/${encodeURIComponent(run.id)}/${kind === "json" ? "download" : "plot.png"}`, { blob: true });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cargo-${run.algorithm}-seed${run.seed}.${kind}`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    if (error.status === 404) {
      state.retainedIds ??= new Set(state.runs.keys());
      state.retainedIds.delete(run.id);
      state.completed = state.completed.filter((id) => id !== run.id);
      render();
    }
    showError("job-error", error);
  } finally {
    button.disabled = !viewed()?.result || (state.retainedIds && !state.retainedIds.has(viewed()?.id));
    button.textContent = label;
  }
}

$("retry-bootstrap").addEventListener("click", bootstrap);
$("run-form").addEventListener("submit", startRun);
$("algorithm").addEventListener("change", configureAlgorithm);
$("dataset").addEventListener("change", renderInput);
$("upload").addEventListener("change", uploadProblem);
$("objective").addEventListener("change", () => {
  $("objective-description").textContent = $("objective").value === "eta" ? "Bobot = fee × (1 + 1/(ETA + 1)); objective mengurangi penalti. Pendapatan asli tetap dilaporkan terpisah." : "Objective = fee asli dikurangi penalti pelanggaran.";
});
$("cancel-button").addEventListener("click", cancelRun);
$("resume-poll").addEventListener("click", () => { $("resume-poll").hidden = true; schedulePoll(0); });
$("ship-select").addEventListener("change", () => { state.ship = Number($("ship-select").value); render(); });
$("view-current").addEventListener("click", () => { state.view = "current"; render(); });
$("view-best").addEventListener("click", () => { state.view = "best"; render(); });
$("compare-button").addEventListener("click", () => { pause(); state.compare = !state.compare; state.inspectionSource = "final"; render(); });
$("reset-frame").addEventListener("click", () => { pause(); selectFrame(0); });
$("previous-frame").addEventListener("click", () => { pause(); selectFrame(frameIndex() - 1); });
$("next-frame").addEventListener("click", () => { pause(); selectFrame(frameIndex() + 1); });
$("last-frame").addEventListener("click", () => { pause(); state.followLatest = true; render(); });
$("frame-range").addEventListener("input", () => { pause(); selectFrame(Number($("frame-range").value)); });
$("play-button").addEventListener("click", togglePlayback);
$("play-speed").addEventListener("change", () => { if (state.playing) { clearTimeout(state.playTimer); state.playTimer = setTimeout(playbackTick, Number($("play-speed").value)); } });
$("deck-canvas").addEventListener("click", (event) => { const target = event.target.closest("[data-vehicle]"); if (target) inspectVehicle(Number(target.dataset.vehicle), target.dataset.source); });
$("deck-canvas").addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { const target = event.target.closest("[data-vehicle]"); if (target) { event.preventDefault(); inspectVehicle(Number(target.dataset.vehicle), target.dataset.source); } } });
$("outside-list").addEventListener("click", (event) => { const target = event.target.closest("[data-outside]"); if (target) { const index = Number(target.dataset.outside); inspectVehicle(index, state.inspectionSource); $("outside-list").querySelector(`[data-outside="${index}"]`)?.focus({ preventScroll: true }); } });
$("vehicle-select").addEventListener("change", () => { if ($("vehicle-select").value !== "") inspectVehicle(Number($("vehicle-select").value), state.inspectionSource); });
$("chart-data").addEventListener("toggle", () => { if ($("chart-data").open) renderChartData(); });
$("data-page").addEventListener("change", () => { state.dataPage = Number($("data-page").value); renderChartData(); });
$("history-table").addEventListener("click", (event) => {
  const sort = event.target.closest("[data-sort]");
  if (sort) { state.sort = { key: sort.dataset.sort, direction: state.sort.key === sort.dataset.sort ? -state.sort.direction : 1 }; renderHistory(); $("history-table").querySelector(`[data-sort="${sort.dataset.sort}"]`)?.focus({ preventScroll: true }); }
  const open = event.target.closest("[data-open-run]");
  if (open) { pause(); state.viewedId = open.dataset.openRun; state.ship = 0; state.vehicle = null; state.compare = false; state.followLatest = true; state.dataPage = 0; showError("job-error", ""); render(); $("workspace").focus({ preventScroll: true }); $("workspace").scrollIntoView({ behavior: "auto", block: "start" }); }
});
$("download-json").addEventListener("click", () => download("json"));
$("download-png").addEventListener("click", () => download("png"));
$("show-active-run").addEventListener("click", () => { pause(); state.viewedId = state.activeId; state.ship = 0; state.vehicle = null; state.compare = false; state.followLatest = true; render(); });
for (const tab of document.querySelectorAll("[data-panel]")) {
  tab.addEventListener("click", () => activatePanel(tab.dataset.panel));
  tab.addEventListener("keydown", (event) => {
    const tabs = [...document.querySelectorAll("[data-panel]")];
    const index = tabs.indexOf(tab);
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) { event.preventDefault(); activatePanel(tabs[next].dataset.panel, true); }
  });
}
$("render-2d").addEventListener("click", () => chooseRenderMode("2d"));
$("render-3d").addEventListener("click", () => chooseRenderMode("3d"));
$("scene-grid").addEventListener("change", () => { state.showGrid = $("scene-grid").checked; renderDeck(); });
$("scene-labels").addEventListener("change", () => { state.showLabels = $("scene-labels").checked; renderDeck(); });
$("camera-reset").addEventListener("click", () => state.scene?.resetView("iso"));
$("camera-top").addEventListener("click", () => state.scene?.resetView("top"));
$("camera-zoom-in").addEventListener("click", () => state.scene?.zoom(1.25));
$("camera-zoom-out").addEventListener("click", () => state.scene?.zoom(0.8));
$("camera-orbit-left").addEventListener("click", () => state.scene?.orbit(-1));
$("camera-orbit-right").addEventListener("click", () => state.scene?.orbit(1));
$("camera-focus").addEventListener("click", () => state.scene?.focusVehicle(state.vehicle));
$("viewport-fullscreen").disabled = !document.fullscreenEnabled;
$("viewport-fullscreen").addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await $("viewport-shell").requestFullscreen();
  } catch {
    showError("scene-error", "Browser tidak mengizinkan layar penuh. Tampilan biasa tetap dapat digunakan.");
  }
});
document.addEventListener("fullscreenchange", () => {
  const active = document.fullscreenElement === $("viewport-shell");
  $("viewport-fullscreen").textContent = active ? "Keluar layar penuh" : "Layar penuh";
  $("viewport-fullscreen").setAttribute("aria-pressed", String(active));
  $("viewport-fullscreen").setAttribute("aria-label", active ? "Keluar dari layar penuh geladak" : "Buka viewport geladak dalam layar penuh");
  state.scene?.resize();
});
document.addEventListener("visibilitychange", () => {
  state.scene?.setActive(!document.hidden && state.renderMode === "3d" && !state.compare);
  if (!document.hidden) renderDeck();
});
window.addEventListener("pagehide", (event) => {
  if (event.persisted) state.scene?.setActive(false);
  else { state.disposed = true; state.scene?.dispose(); }
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) renderDeck();
});
activatePanel("panel-config");
new ResizeObserver(() => { if (state.series.length) renderChart(); }).observe($("convergence-chart"));
document.addEventListener("visibilitychange", () => { if (document.hidden) pause(); });
window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", (event) => { if (event.matches) pause(); });
bootstrap();
