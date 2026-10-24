// Job Cost Tracker dashboard. Plain JS ES modules, no build step.
//
//   util.js       formatting, $, local storage, toast
//   api.js        fetch wrapper for /api
//   state.js      constants + the shared state object
//   users.js      pick / add your name, load your prefs
//   dashboard.js  tiles, filters, job cards, star/hide
//   forms.js      add/edit job dialog, delete confirm
//   detail.js     job detail dialog, notes, transactions
//
// Modules import each other's functions (e.g. dashboard <-> detail); that's fine because nothing
// runs until the init* calls below, after every module has loaded.

import { initDashboard } from "./dashboard.js";
import { initDetail } from "./detail.js";
import { initForms } from "./forms.js";
import { initUser, initUsers } from "./users.js";
import { $, toast } from "./util.js";

initUsers();
initDashboard();
initForms();
initDetail();

document.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]")) e.target.closest("dialog").close();
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

initUser().catch((err) => toast(`Could not reach the server: ${err.message}`, true));
