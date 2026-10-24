// Job detail dialog: profit summary, budget vs actual table, notes, and the QB transactions.

import { api } from "./api.js";
import { chip, setUserJob, tile } from "./dashboard.js";
import { confirmDelete, openJobForm } from "./forms.js";
import { BUCKET_NAMES, state } from "./state.js";
import { $, esc, fmt, money, pct, when } from "./util.js";

export async function openDetail(id) {
  const d = await api(`/api/jobs/${id}`);
  const mine = state.jobs.find((j) => j.id === id);
  state.detail = { ...d, starred: mine?.starred, hidden: mine?.hidden };
  renderDetail();
  if (!$("#detailDialog").open) $("#detailDialog").showModal();
}

function renderDetail(bucketFilter = "all") {
  const d = state.detail;
  const o = d.overall;
  const rows = [...d.buckets, { ...o, key: "total", label: "Total cost" }];
  const txns = d.transactions.filter((t) => bucketFilter === "all" || t.bucket === bucketFilter);
  $("#detailBody").innerHTML = `
    <div class="detail-head">
      <div class="titles">
        <h2>${esc(d.job_number)} · ${esc(d.name.replace(d.job_number, "").trim())} ${chip(d.status)}</h2>
        <div class="muted">${esc(d.qb_full_name)} · ${d.pct_complete != null ? `${Math.round(d.pct_complete)}% complete` : "% complete not set"} · synced ${when(d.synced_at)}</div>
      </div>
      <div class="actions no-print">
        <button class="btn" type="button" data-dact="star">${d.starred ? "★ Starred" : "☆ Star"}</button>
        <button class="btn" type="button" data-dact="edit">Edit</button>
        <button class="btn" type="button" data-dact="hide">${d.hidden ? "Unhide" : "Hide"}</button>
        <button class="btn" type="button" data-dact="print">Print / PDF</button>
        <button class="btn" type="button" data-dact="delete">Delete</button>
        <button class="btn primary" type="button" data-dact="close">Close</button>
      </div>
    </div>

    <div class="profit-grid">
      ${tile("Contract", fmt(o.contract))}
      ${tile("Estimated profit", fmt(o.estimated_profit))}
      ${tile("Profit remaining now", fmt(o.profit_remaining))}
      ${tile("Projected profit", `<span class="var ${o.projected_profit < 0 ? "over" : o.status}" style="font-size:inherit">${fmt(o.projected_profit)}</span>`)}
      ${tile("Invoiced to date", `${fmt(o.invoiced)} <span class="muted" style="font-size:13px">${o.contract ? pct((o.invoiced / o.contract) * 100) : ""}</span>`)}
    </div>

    <h3>Budget vs actual</h3>
    <div class="table-scroll"><table class="data">
      <thead><tr><th>Bucket</th><th class="n">Estimate</th><th class="n">Actual</th><th class="n">Over / (under)</th><th class="n">% used</th><th class="n">Projected at finish</th><th>Status</th></tr></thead>
      <tbody>${rows
        .map(
          (r) => `<tr class="${r.key === "total" ? "total" : ""}">
            <td>${esc(r.key === "total" ? "Total cost" : BUCKET_NAMES[r.key])}</td>
            <td class="n">${fmt(r.estimate)}</td><td class="n">${fmt(r.actual)}</td>
            <td class="n">${r.variance > 0 ? fmt(r.variance) : `(${fmt(-r.variance)})`}</td>
            <td class="n">${pct(r.pct_used)}</td><td class="n">${fmt(r.projected)}</td>
            <td>${chip(r.status)}</td></tr>`
        )
        .join("")}</tbody>
    </table></div>

    <h3>Notes</h3>
    <div class="notes">
      <form id="noteForm" class="no-print">
        <textarea id="noteText" placeholder="Add a note (visible to everyone)" required></textarea>
        <div class="dialog-actions" style="margin-top:6px"><button class="btn primary small" type="submit">Add note</button></div>
      </form>
      ${d.notes.length ? "" : `<p class="muted">No notes yet.</p>`}
      ${d.notes
        .map(
          (n) => `<div class="note"><div class="who"><span>${esc(n.author || "Unknown")} · ${when(n.created_at)}</span>
            <button class="linkish no-print" type="button" data-note="${n.id}">delete</button></div>
            <div class="body">${esc(n.body)}</div></div>`
        )
        .join("")}
    </div>

    <h3>QuickBooks transactions (${txns.length})</h3>
    <div class="no-print" style="margin-bottom:8px">
      <select id="txnFilter" aria-label="Filter transactions">
        <option value="all">All buckets</option>
        ${Object.entries(BUCKET_NAMES).map(([k, v]) => `<option value="${k}" ${k === bucketFilter ? "selected" : ""}>${v}</option>`).join("")}
      </select>
    </div>
    <div class="table-scroll"><table class="data">
      <thead><tr><th>Date</th><th>Type</th><th>Ref</th><th>Name</th><th>Account</th><th>Bucket</th><th class="n">Amount</th></tr></thead>
      <tbody>${txns
        .map(
          (t) => `<tr><td>${esc(t.txn_date)}</td><td>${esc(t.txn_type)}</td><td>${esc(t.ref)}</td><td>${esc(t.name)}</td>
            <td>${esc(t.account)}</td><td>${esc(BUCKET_NAMES[t.bucket])}</td><td class="n">${money.format(t.amount)}</td></tr>`
        )
        .join("")}</tbody>
    </table></div>`;

  $("#txnFilter").onchange = (e) => renderDetail(e.target.value);
  $("#noteForm").onsubmit = async (e) => {
    e.preventDefault();
    await api(`/api/jobs/${d.id}/notes`, { method: "POST", body: { body: $("#noteText").value, author: state.user.name } });
    openDetail(d.id);
  };
}

export function initDetail() {
  $("#detailBody").addEventListener("click", async (e) => {
    const d = state.detail;
    const job = state.jobs.find((j) => j.id === d.id);
    const note = e.target.closest("[data-note]");
    if (note) {
      await api(`/api/notes/${note.dataset.note}`, { method: "DELETE" });
      return openDetail(d.id);
    }
    const act = e.target.closest("[data-dact]")?.dataset.dact;
    if (act === "close") $("#detailDialog").close();
    if (act === "print") window.print();
    if (act === "edit") openJobForm(job);
    if (act === "delete") confirmDelete(job);
    if (act === "star") setUserJob(job, { starred: !job.starred });
    if (act === "hide") setUserJob(job, { hidden: !job.hidden });
  });

  $("#detailDialog").addEventListener("close", () => (state.detail = null));
}
