// "Who's using the tracker?": pick or add a name (no password); loads that user's saved prefs.

import { api } from "./api.js";
import { applyPrefsToControls, loadJobs } from "./dashboard.js";
import { DEFAULT_PREFS, state } from "./state.js";
import { $, esc, store } from "./util.js";

export async function initUser() {
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

async function setUser(user) {
  state.user = user;
  store("jct_user", user);
  $("#userBtn").textContent = user.name;
  state.prefs = { ...DEFAULT_PREFS, ...(await api(`/api/users/${user.id}/prefs`)) };
  applyPrefsToControls();
  await loadJobs();
}

export function initUsers() {
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
}
