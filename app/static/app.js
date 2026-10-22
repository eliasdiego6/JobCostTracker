// Job Cost Tracker dashboard. Plain JS, no build step.

const $ = (sel, el = document) => el.querySelector(sel);
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const fmt = (v) => (v == null ? "—" : money.format(v));
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const STATUS = {
  ok: { label: "On track", icon: "✓" },
  trending: { label: "Trending over", icon: "▲" },
  over: { label: "Over budget", icon: "!" },
};
const STATUS_RANK = { ok: 0, trending: 1, over: 2 };
const BUCKET_NAMES = { labor: "Labor", material: "Material", sub: "Subcontractor", misc: "Direct exp. / misc" };
const DEFAULT_PREFS = { search: "", status: "all", customer: "all", sort: "over", starredOnly: false, showHidden: false };

const state = { user: null, jobs: [], lastSync: null, prefs: { ...DEFAULT_PREFS }, editing: null, lookupPick: null, detail: null };

// ---------- helpers ----------

function store(key, value) {
  try {
    if (value === undefined) return JSON.parse(localStorage.getItem(key));
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    return null;
  }
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: { "Content-Type": "application/json" },
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const d = await res.json();
      msg = typeof d.detail === "string" ? d.detail : d.detail?.map((e) => e.msg).join(", ") ?? msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

let toastTimer;
function toast(msg, bad = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 3500);
}

function when(iso) {
  if (!iso) return "never";
  const d = new Date(iso);
  const time = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return d.toDateString() === new Date().toDateString() ? `today ${time}` : `${d.toLocaleDateString()} ${time}`;
}

const pct = (v) => (v == null ? "—" : `${Math.round(v)}%`);

// ---------- user ----------

async function initUser() {
  const saved = store("jct_user");
  const users = await api("/api/users");
  const match = saved && users.find((u) => u.id === saved.id);
  if (match) return setUser(match);
  showUserPicker(users);
}

function showUserPicker(users) {
  const list = $("#userList");
  list.innerHTML = users.map((u) => `<button class="btn" type="button" data-id="${u.id}">${esc(u.name)}</button>`).join("");
  list.onclick = (e) => {
    const b = e.target.closest("button[data-id]");
    if (!b) return;
    $("#userDialog").close();
    setUser(users.find((u) => u.id === Number(b.dataset.id)));
  };
  $("#userDialog").showModal();
}

$("#userDialog").addEventListener("cancel", (e) => {
  if (!state.user) e.preventDefault(); // must pick a name the first time
});

$("#newUserForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const user = await api("/api/users", { method: "POST", body: { name: $("#newUserName").value } });
  $("#newUserName").value = "";
  $("#userDialog").close();
  setUser(user);
});

$("#userBtn").addEventListener("click", async () => showUserPicker(await api("/api/users")));

async function setUser(user) {
  state.user = user;
  store("jct_user", user);
  $("#userBtn").textContent = user.name;
  state.prefs = { ...DEFAULT_PREFS, ...(await api(`/api/users/${user.id}/prefs`)) };
  applyPrefsToControls();
  await loadJobs();
}

// ---------- filters & prefs ----------

const controls = {
  search: ["#search", "value"],
  status: ["#statusFilter", "value"],
  customer: ["#customerFilter", "value"],
  sort: ["#sortBy", "value"],
  starredOnly: ["#starredOnly", "checked"],
  showHidden: ["#showHidden", "checked"],
};

function applyPrefsToControls() {
  for (const [key, [sel, prop]] of Object.entries(controls)) $(sel)[prop] = state.prefs[key];
}

let prefsTimer;
for (const [key, [sel, prop]] of Object.entries(controls)) {
  $(sel).addEventListener("input", () => {
    state.prefs[key] = $(sel)[prop];
    render();
    clearTimeout(prefsTimer);
    prefsTimer = setTimeout(() => api(`/api/users/${state.user.id}/prefs`, { method: "PUT", body: state.prefs }), 500);
  });
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

async function loadJobs() {
  const data = await api(`/api/jobs?user_id=${state.user.id}`);
  state.jobs = data.jobs;
  state.lastSync = data.last_sync;
  render();
}

function render() {
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
  $("#tiles").innerHTML = tiles
    .map(([label, value]) => `<div class="tile"><div class="label">${label}</div><div class="value">${value}</div></div>`)
    .join("");
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

function chip(status) {
  const s = STATUS[status];
  return `<span class="chip ${status}">${s.icon} ${s.label}</span>`;
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

// ---------- card actions ----------

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

async function setUserJob(job, change) {
  await api(`/api/users/${state.user.id}/jobs/${job.id}`, { method: "PUT", body: change });
  Object.assign(job, change);
  if ("hidden" in change) toast(change.hidden ? `Job ${job.job_number} hidden from your view` : `Job ${job.job_number} unhidden`);
  render();
  if (state.detail?.id === job.id) openDetail(job.id);
}

function confirmDelete(job) {
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

// ---------- add / edit job ----------

const form = $("#jobForm");
const FIELDS = ["est_labor", "est_material", "est_sub", "est_misc", "contract", "pct_complete"];

function openJobForm(job = null) {
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

$("#addBtn").addEventListener("click", () => openJobForm());

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

$("#lookupBtn").addEventListener("click", lookup);
$("#jobNumber").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    lookup();
  }
});

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

// ---------- job detail ----------

async function openDetail(id) {
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

const tile = (label, value) => `<div class="tile"><div class="label">${label}</div><div class="value">${value}</div></div>`;

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

// ---------- dialogs, refresh, export ----------

document.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]")) e.target.closest("dialog").close();
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

// ---------- tooltip ----------

const tip = $("#tooltip");
document.addEventListener("mousemove", (e) => {
  const el = e.target.closest("[data-tip]");
  if (!el) return (tip.hidden = true);
  tip.textContent = el.dataset.tip;
  tip.hidden = false;
  const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  const y = e.clientY + 16 + tip.offsetHeight > window.innerHeight ? e.clientY - tip.offsetHeight - 10 : e.clientY + 16;
  tip.style.left = `${x}px`;
  tip.style.top = `${y}px`;
});

// Pick up changes made by other people every 2 minutes (the server syncs QB on its own schedule).
setInterval(() => state.user && !document.hidden && loadJobs(), 120_000);

initUser().catch((err) => toast(`Could not reach the server: ${err.message}`, true));
