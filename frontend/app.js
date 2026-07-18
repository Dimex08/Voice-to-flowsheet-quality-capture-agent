(function () {
  let FIELDS = [];
  let fieldsById = {};
  let SCENARIOS = [];

  const el = id => document.getElementById(id);
  const GCS_FIELDS = ["gcs_eye", "gcs_verbal", "gcs_motor"];

  async function boot() {
    [FIELDS, SCENARIOS] = await Promise.all([
      fetch("/api/fields").then(r => r.json()),
      fetch("/api/scenarios").then(r => r.json()),
    ]);
    fieldsById = Object.fromEntries(FIELDS.map(f => [f.id, f]));
    renderTable();
    renderScenarios();
    recomputeGcsTotal();
  }

  // ---------- legacy flowsheet (always-editable dropdowns) ----------
  function renderTable() {
    const body = el("flowsheet-body");
    body.innerHTML = "";
    let currentGroup = null;
    FIELDS.forEach(f => {
      if (f.group !== currentGroup) {
        currentGroup = f.group;
        const gr = document.createElement("tr");
        gr.className = "group-row";
        gr.innerHTML = `<td colspan="2">${currentGroup}</td>`;
        body.appendChild(gr);
      }
      const tr = document.createElement("tr");

      const labelTd = document.createElement("td");
      labelTd.className = "field-label";
      labelTd.textContent = f.label;

      const valueTd = document.createElement("td");
      valueTd.className = "field-value";
      valueTd.id = `cell-${f.id}`;

      const sel = document.createElement("select");
      sel.className = "win field-select";
      sel.id = `field-${f.id}`;
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "— select —";
      sel.appendChild(placeholder);
      f.options.forEach(o => {
        const opt = document.createElement("option");
        opt.value = o.value;
        opt.textContent = o.label;
        sel.appendChild(opt);
      });
      sel.addEventListener("change", () => {
        // A manual edit clears the agent's provenance note for that field.
        el(`meta-${f.id}`).textContent = "";
        valueTd.classList.remove("charted", "flagged");
        recomputeGcsTotal();
      });

      const meta = document.createElement("span");
      meta.className = "field-meta";
      meta.id = `meta-${f.id}`;

      valueTd.appendChild(sel);
      valueTd.appendChild(meta);
      tr.appendChild(labelTd);
      tr.appendChild(valueTd);
      body.appendChild(tr);
    });
  }

  function recomputeGcsTotal() {
    const vals = GCS_FIELDS.map(id => el(`field-${id}`).value);
    const bar = el("gcs-total-bar");
    if (vals.every(v => v !== "")) {
      const total = vals.reduce((a, v) => a + Number(v), 0);
      el("gcs-total-value").textContent = `${total} / 15`;
      const band = total >= 13 ? "mild" : total >= 9 ? "moderate" : "severe";
      const label = total >= 13 ? "Mild" : total >= 9 ? "Moderate" : "Severe";
      el("gcs-total-note").textContent = `E${vals[0]} V${vals[1]} M${vals[2]} · ${label}`;
      bar.className = `gcs-total-bar ${band}`;
    } else {
      el("gcs-total-value").textContent = "—";
      el("gcs-total-note").textContent = "";
      bar.className = "gcs-total-bar";
    }
  }

  // ---------- narration panel ----------
  function renderScenarios() {
    const sel = el("scenario-select");
    sel.innerHTML = "";
    SCENARIOS.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.label;
      sel.appendChild(opt);
    });
    sel.addEventListener("change", loadScenario);
    if (SCENARIOS.length) loadScenario();
  }

  function loadScenario() {
    const s = SCENARIOS.find(x => x.id === el("scenario-select").value);
    if (!s) return;
    el("narration-text").value = s.text;
    el("room-label").textContent = s.label;
    clearFlowsheet();
    el("eval-card").hidden = true;
    el("checks-card").hidden = true;
  }

  function clearFlowsheet() {
    FIELDS.forEach(f => {
      el(`field-${f.id}`).value = "";
      el(`meta-${f.id}`).textContent = "";
      el(`cell-${f.id}`).classList.remove("charted", "flagged");
    });
    recomputeGcsTotal();
  }

  function currentScenarioId() {
    const s = SCENARIOS.find(x => x.id === el("scenario-select").value);
    // Only claim a scenario id (which unlocks scoring) if the text is unchanged.
    return s && el("narration-text").value.trim() === s.text.trim() ? s.id : null;
  }

  async function fill() {
    const btn = el("fill-btn");
    btn.disabled = true;
    btn.textContent = "Filling…";
    clearFlowsheet();
    el("eval-card").hidden = true;
    el("checks-card").hidden = true;

    let data;
    try {
      const res = await fetch("/api/fill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: el("narration-text").value,
          scenario_id: currentScenarioId(),
        }),
      });
      data = await res.json();
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Fill flowsheet →";
      el("mode-note").textContent = "Could not reach the agent — is the server running?";
      return;
    }

    el("mode-badge").textContent = data.mode === "live" ? "LIVE AGENT" : "MOCK AGENT";
    el("mode-badge").className = `badge-mode ${data.mode}`;
    el("mode-note").textContent = data.mock_note || "";

    // Stagger the fills so the chart visibly populates (cosmetic; currency is
    // the real server-measured latency, shown in the scorecard).
    const updates = data.updates || [];
    for (let i = 0; i < updates.length; i++) {
      setTimeout(() => applyUpdate(updates[i]), 120 * i);
    }
    setTimeout(() => {
      (data.flags || []).forEach(applyFlag);
      renderChecks(data.consistency || [], data.flags || []);
      if (data.eval) renderEval(data.eval);
      btn.disabled = false;
      btn.textContent = "Fill flowsheet →";
    }, 120 * updates.length + 60);
  }

  function applyUpdate(u) {
    const sel = el(`field-${u.field_id}`);
    if (!sel) return;
    sel.value = u.value;
    el(`cell-${u.field_id}`).classList.add("charted");
    el(`cell-${u.field_id}`).classList.remove("flagged");
    el(`meta-${u.field_id}`).textContent =
      `agent · ${Math.round(u.confidence * 100)}% · "${u.quote}"`;
    if (GCS_FIELDS.includes(u.field_id)) recomputeGcsTotal();
  }

  function applyFlag(f) {
    const cell = el(`cell-${f.field_id}`);
    if (!cell) return;
    cell.classList.add("flagged");
    cell.classList.remove("charted");
    el(`meta-${f.field_id}`).textContent = "⚑ left blank — needs confirmation";
  }

  function renderChecks(consistency, flags) {
    const cList = el("consistency-list");
    cList.innerHTML = consistency.map(c =>
      `<div class="check ${c.level}"><span class="check-icon">${c.level === "ok" ? "✓" : "⚠"}</span>${c.message}</div>`
    ).join("");

    const fList = el("flags-list");
    fList.innerHTML = flags.map(f => {
      const label = fieldsById[f.field_id] ? fieldsById[f.field_id].label : f.field_id;
      return `<div class="flag">
        <div class="flag-head">⚑ ${label} — needs a data manager's confirmation</div>
        <div class="flag-reason">${f.reason}</div>
        <div class="flag-question">Suggested question: <em>${f.clarifying_question}</em></div>
      </div>`;
    }).join("");

    el("checks-card").hidden = consistency.length === 0 && flags.length === 0;
  }

  function scoreClass(v) {
    return v >= 90 ? "good" : v >= 70 ? "warning" : "critical";
  }

  function renderEval(ev) {
    el("eval-card").hidden = false;
    [["completeness", ev.completeness], ["correctness", ev.correctness], ["currency", ev.currency]]
      .forEach(([k, v]) => {
        const cls = scoreClass(v);
        el(`val-${k}`).textContent = `${v}%`;
        el(`val-${k}`).className = `val ${cls}`;
        const f = el(`fill-${k}`);
        f.style.width = `${v}%`;
        f.className = `meter-fill ${cls}`;
      });
    const legacyMin = Math.round(ev.legacy_charting_lag_seconds / 60);
    el("eval-summary").innerHTML =
      `${ev.fields_charted}/${ev.fields_total} charted · ${ev.fields_correct} correct · ` +
      `${ev.fields_flagged} flagged instead of guessed<br>` +
      `Charted <strong>${ev.fill_latency_seconds}s</strong> after paste ` +
      `(vs. ~${legacyMin} min illustrative for retrospective paper charting).`;
  }

  el("fill-btn").addEventListener("click", fill);
  boot();
})();
