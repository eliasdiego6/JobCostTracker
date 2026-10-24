// Add / edit job dialog (with QuickBooks lookup) and the delete confirmation.

import { api } from "./api.js";
import { loadJobs } from "./dashboard.js";
import { openDetail } from "./detail.js";
import { state } from "./state.js";
import { $, esc, fmt, toast } from "./util.js";

const form = $("#jobForm");
const FIELDS = ["est_labor", "est_material", "est_sub", "est_misc", "contract", "pct_complete"];

export function openJobForm(job = null) {
  state.editing = job;
  state.lookupPick = null;
  form.reset();
  $("#jobFormTitle").textContent = job ? `Edit job ${job.job_number}` : "Add job";
  $("#lookupSection").hidden = !!job;
  $("#lookupResults").innerHTML = "";
  $("#jobFormError").hidden = true;
  if (job) {
    for (const b of job.buckets) form.elements[`est_${b.key}`].value = b.estimate;
    form.elements.contract.value = job.overall.contract;
    form.elements.pct_complete.value = job.pct_complete ?? "";
  }
  updateFormSummary();
  $("#jobDialog").showModal();
  (job ? form.elements.est_labor : $("#jobNumber")).focus();
}

async function lookup() {
  const q = $("#jobNumber").value.trim();
  const out = $("#lookupResults");
  if (!q) return;
  out.innerHTML = `<span class="muted">Searching QuickBooks…</span>`;
  try {
    const matches = await api(`/api/qb/search?q=${encodeURIComponent(q)}`);
    if (!matches.length) {
      out.innerHTML = `<span class="error">No QuickBooks job matches “${esc(q)}”.</span>`;
      return;
    }
    out.innerHTML = matches
      .map(
        (m, i) => `<label><input type="radio" name="qbpick" value="${i}" ${matches.length === 1 ? "checked" : ""}>
          ${esc(m.full_name)}</label>`
      )
      .join("");
    out.onchange = () => (state.lookupPick = matches[Number(out.querySelector("[name=qbpick]:checked").value)]);
    state.lookupPick = matches.length === 1 ? matches[0] : null;
  } catch (err) {
    out.innerHTML = `<span class="error">${esc(err.message)}</span>`;
  }
}

function formValues() {
  const v = {};
  for (const f of FIELDS) {
    const raw = form.elements[f].value;
    v[f] = raw === "" ? (f === "pct_complete" ? null : 0) : Number(raw);
  }
  return v;
}

function updateFormSummary() {
  const v = formValues();
  const cost = v.est_labor + v.est_material + v.est_sub + v.est_misc;
  const profit = v.contract - cost;
  const margin = v.contract ? ` (${Math.round((profit / v.contract) * 100)}% margin)` : "";
  $("#formSummary").textContent = `Estimated cost ${fmt(cost)} · estimated profit ${fmt(profit)}${margin}`;
}

export function confirmDelete(job) {
  $("#confirmTitle").textContent = `Delete job ${job.job_number}?`;
  $("#confirmText").innerHTML =
    `This removes <b>${esc(job.job_number)} ${esc(job.customer)}</b> from the tracker for <b>all users</b>, ` +
    `including its estimates and notes. QuickBooks is not changed.<br><br>` +
    `To remove it only from your view, use <b>Hide</b> instead.`;
  $("#confirmOk").onclick = async () => {
    await api(`/api/jobs/${job.id}`, { method: "DELETE" });
    $("#confirmDialog").close();
    $("#detailDialog").close();
    toast(`Job ${job.job_number} deleted`);
    loadJobs();
  };
  $("#confirmDialog").showModal();
}

export function initForms() {
  $("#addBtn").addEventListener("click", () => openJobForm());
  $("#lookupBtn").addEventListener("click", lookup);
  $("#jobNumber").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      lookup();
    }
  });
  form.addEventListener("input", updateFormSummary);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("#jobFormError");
    err.hidden = true;
    try {
      if (state.editing) {
        await api(`/api/jobs/${state.editing.id}`, { method: "PUT", body: formValues() });
        toast(`Job ${state.editing.job_number} updated`);
      } else {
        if (!state.lookupPick) throw new Error("Find the job in QuickBooks and select it first.");
        const job = await api("/api/jobs", {
          method: "POST",
          body: {
            ...formValues(),
            job_number: $("#jobNumber").value.trim(),
            qb_list_id: state.lookupPick.list_id,
            created_by: state.user.name,
          },
        });
        toast(`Job ${job.job_number} added`);
      }
      $("#jobDialog").close();
      await loadJobs();
      if (state.detail && state.editing) openDetail(state.editing.id);
    } catch (ex) {
      err.textContent = ex.message;
      err.hidden = false;
    }
  });
}
