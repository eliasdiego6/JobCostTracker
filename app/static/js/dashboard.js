// The main screen: summary tiles, filters/sort (saved per user), and one card per job.

import { api } from "./api.js";
import { openDetail } from "./detail.js";
import { confirmDelete, openJobForm } from "./forms.js";
import { BUCKET_NAMES, STATUS, STATUS_RANK, state } from "./state.js";
import { $, esc, fmt, pct, toast, when } from "./util.js";

// ---------- filters & prefs ----------

const controls = {
  search: ["#search", "value"],
  status: ["#statusFilter", "value"],
  customer: ["#customerFilter", "value"],
  sort: ["#sortBy", "value"],
  starredOnly: ["#starredOnly", "checked"],
  showHidden: ["#showHidden", "checked"],
};

export function applyPrefsToControls() {
  for (const [key, [sel, prop]] of Object.entries(controls)) $(sel)[prop] = state.prefs[key];
}

function severity(j) {
  // how far over (or close to over) the worst line is, for "most over budget" sorting
  const ratios = [...j.buckets, j.overall].map((b) =>
    b.estimate ? (b.projected ?? b.actual) / b.estimate : b.actual > 0 ? 9 : 0
  );
  return STATUS_RANK[j.status] * 100 + Math.max(...ratios);
}

function visibleJobs() {
  const p = state.prefs;
  const q = p.search.trim().toLowerCase();
  const jobs = state.jobs.filter(
    (j) =>
      (p.showHidden || !j.hidden) &&
      (!p.starredOnly || j.starred) &&
      (p.status === "all" || j.status === p.status) &&
      (p.customer === "all" || j.customer === p.customer) &&
      (!q || `${j.job_number} ${j.name} ${j.customer}`.toLowerCase().includes(q))
  );
  const sorters = {
    over: (a, b) => severity(b) - severity(a),
    profit: (a, b) => a.overall.projected_profit - b.overall.projected_profit,
    number: (a, b) => a.job_number.localeCompare(b.job_number, undefined, { numeric: true }),
    customer: (a, b) => a.customer.localeCompare(b.customer) || a.job_number.localeCompare(b.job_number),
    newest: (a, b) => b.created_at.localeCompare(a.created_at),
  };
  return jobs.sort(sorters[p.sort] ?? sorters.over);
}

// ---------- rendering ----------

export async function loadJobs() {
  const data = await api(`/api/jobs?user_id=${state.user.id}`);
  state.jobs = data.jobs;
  state.lastSync = data.last_sync;
  render();
}

export function render() {
  $("#lastSync").textContent = `Last synced ${when(state.lastSync)}`;
  renderCustomerOptions();
  renderTiles();
  const jobs = visibleJobs();
  $("#jobs").innerHTML = jobs.map(cardHtml).join("");
  const empty = $("#empty");
  empty.hidden = jobs.length > 0;
  empty.textContent = state.jobs.length ? "No jobs match these filters." : "No jobs yet. Click “+ Add job” to add your first one.";
}

function renderCustomerOptions() {
  const sel = $("#customerFilter");
  const customers = [...new Set(state.jobs.map((j) => j.customer))].sort();
  sel.innerHTML =
    `<option value="all">All customers</option>` +
    customers.map((c) => `<option ${c === state.prefs.customer ? "selected" : ""}>${esc(c)}</option>`).join("");
  if (!customers.includes(state.prefs.customer)) sel.value = "all";
}

function renderTiles() {
  const active = state.jobs.filter((j) => !j.hidden);
  const count = (s) => active.filter((j) => j.status === s).length;
  const sum = (f) => active.reduce((t, j) => t + f(j), 0);
  const tiles = [
    ["Jobs in view", active.length],
    [`<span class="var over">!</span> Over budget`, count("over")],
    [`<span class="var trending">▲</span> Trending over`, count("trending")],
    ["Total contracts", fmt(sum((j) => j.overall.contract))],
    ["Projected profit", fmt(sum((j) => j.overall.projected_profit))],
  ];
  $("#tiles").innerHTML = tiles.map(([label, value]) => tile(label, value)).join("");
}

export const tile = (label, value) => `<div class="tile"><div class="label">${label}</div><div class="value">${value}</div></div>`;

export function chip(status) {
  const s = STATUS[status];
  return `<span class="chip ${status}">${s.icon} ${s.label}</span>`;
}

function varianceText(b) {
  if (!b.estimate && !b.actual) return `<span class="var na">not used</span>`;
  const s = STATUS[b.status];
  if (b.status === "over") return `<span class="var over">${s.icon} ${fmt(b.variance)} over</span>`;
  if (b.status === "trending" && b.projected != null)
    return `<span class="var trending">${s.icon} on pace for ${fmt(b.projected - b.estimate)} over</span>`;
  return `<span class="var ${b.status}">${s.icon} ${fmt(-b.variance)} left</span>`;
}

function tipFor(label, b) {
  const lines = [`${label}`, `Spent ${fmt(b.actual)} of ${fmt(b.estimate)} estimate (${pct(b.pct_used)})`];
  if (b.projected != null) lines.push(`Projected at completion: ${fmt(b.projected)}`);
  return lines.join("\n");
}

function barRow(b) {
  const scale = Math.max(b.estimate, b.actual) || 1;
  return `
    <div class="bar-row" data-tip="${esc(tipFor(b.label, b))}">
      <div class="bar-label">${esc(BUCKET_NAMES[b.key])}</div>
      <div class="track-wrap"><div class="track">
        <div class="fill ${b.status}" style="width:${(b.actual / scale) * 100}%"></div>
        ${b.estimate ? `<div class="mark" style="left:${(b.estimate / scale) * 100}%"></div>` : ""}
      </div></div>
      <div class="bar-figs">${fmt(b.actual)} / ${fmt(b.estimate)}${varianceText(b)}</div>
    </div>`;
}

function overallRow(o) {
  const scale = Math.max(o.contract, o.actual, o.estimate) || 1;
  const profitClass = o.projected_profit < 0 ? "over" : o.status;
  const tip = [
    "Overall job",
    `Total cost ${fmt(o.actual)} · estimated cost ${fmt(o.estimate)}`,
    `Contract ${fmt(o.contract)} · invoiced ${fmt(o.invoiced)}`,
    `Estimated profit ${fmt(o.estimated_profit)} → projected ${fmt(o.projected_profit)}`,
  ].join("\n");
  return `
    <div class="bar-row overall" data-tip="${esc(tip)}">
      <div class="bar-label">Overall<br><span class="muted" style="font-weight:400;font-size:12px">vs contract</span></div>
      <div class="track-wrap"><div class="track">
        <div class="fill ${o.status}" style="width:${(o.actual / scale) * 100}%"></div>
        <div class="mark" style="left:${(o.estimate / scale) * 100}%"></div>
        <div class="inv" style="width:${(Math.min(o.invoiced, scale) / scale) * 100}%"></div>
      </div></div>
      <div class="bar-figs">${fmt(o.actual)} / ${fmt(o.contract)}
        <span class="var ${profitClass}">${STATUS[profitClass].icon} ${o.loss ? "Projected loss " : "Proj. profit "}${fmt(o.projected_profit)}</span>
      </div>
    </div>`;
}

function cardHtml(j) {
  const o = j.overall;
  const margin = o.contract ? ` (${Math.round((o.projected_profit / o.contract) * 100)}%)` : "";
  return `
    <article class="card ${j.status} ${j.hidden ? "is-hidden" : ""}" data-id="${j.id}">
      <div class="card-head">
        <button class="star" type="button" data-act="star" aria-pressed="${j.starred}" title="${j.starred ? "Remove from My jobs" : "Add to My jobs"}">${j.starred ? "★" : "☆"}</button>
        <div class="card-title">
          <div><span class="jobno">${esc(j.job_number)}</span> · <span class="jobname">${esc(j.name.replace(j.job_number, "").trim())}</span></div>
          <div class="cust">${esc(j.customer)}</div>
        </div>
        ${chip(j.status)}
      </div>
      <div class="card-meta">
        ${j.pct_complete != null ? `${Math.round(j.pct_complete)}% complete · ` : "% complete not set · "}
        synced ${when(j.synced_at)}${j.hidden ? " · hidden from your view" : ""}
        ${j.sync_error ? `<div class="err">! Last sync failed: ${esc(j.sync_error)}</div>` : ""}
      </div>
      ${j.buckets.map(barRow).join("")}
      ${overallRow(o)}
      <div class="card-foot">
        <span>Est. profit <b>${fmt(o.estimated_profit)}</b></span>
        <span>Projected <b>${fmt(o.projected_profit)}${margin}</b></span>
        <span>Invoiced <b>${fmt(o.invoiced)}</b></span>
        <span class="card-actions">
          <button class="btn" type="button" data-act="edit">Edit</button>
          <button class="btn" type="button" data-act="hide">${j.hidden ? "Unhide" : "Hide"}</button>
          <button class="btn" type="button" data-act="delete">Delete</button>
        </span>
      </div>
    </article>`;
}

// ---------- actions ----------

export async function setUserJob(job, change) {
  await api(`/api/users/${state.user.id}/jobs/${job.id}`, { method: "PUT", body: change });
  Object.assign(job, change);
  if ("hidden" in change) toast(change.hidden ? `Job ${job.job_number} hidden from your view` : `Job ${job.job_number} unhidden`);
  render();
  if (state.detail?.id === job.id) openDetail(job.id);
}

export function initDashboard() {
  let prefsTimer;
  for (const [key, [sel, prop]] of Object.entries(controls)) {
    $(sel).addEventListener("input", () => {
      state.prefs[key] = $(sel)[prop];
      render();
      clearTimeout(prefsTimer);
      prefsTimer = setTimeout(() => api(`/api/users/${state.user.id}/prefs`, { method: "PUT", body: state.prefs }), 500);
    });
  }

  $("#jobs").addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (!card) return;
    const job = state.jobs.find((j) => j.id === Number(card.dataset.id));
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "star") return setUserJob(job, { starred: !job.starred });
    if (act === "hide") return setUserJob(job, { hidden: !job.hidden });
    if (act === "edit") return openJobForm(job);
    if (act === "delete") return confirmDelete(job);
    openDetail(job.id);
  });

  $("#refreshBtn").addEventListener("click", async () => {
    const btn = $("#refreshBtn");
    btn.disabled = true;
    btn.textContent = "Syncing…";
    try {
      const r = await api("/api/sync", { method: "POST" });
      await loadJobs();
      toast(`Synced ${r.synced} jobs from QuickBooks`);
    } catch (err) {
      toast(`Sync failed: ${err.message}`, true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Refresh now";
    }
  });

  $("#exportBtn").addEventListener("click", () => {
    location.href = `/api/export.xlsx?user_id=${state.user.id}&include_hidden=${state.prefs.showHidden}`;
  });

  // Pick up changes made by other people every 2 minutes (the server syncs QB on its own schedule).
  setInterval(() => state.user && !document.hidden && loadJobs(), 120_000);
}
