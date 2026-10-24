// Shared constants and the single in-memory state object every module reads and updates.
// Status and bucket keys match app/domain/buckets.py.

export const STATUS = {
  ok: { label: "On track", icon: "✓" },
  trending: { label: "Trending over", icon: "▲" },
  over: { label: "Over budget", icon: "!" },
};
export const STATUS_RANK = { ok: 0, trending: 1, over: 2 };
export const BUCKET_NAMES = { labor: "Labor", material: "Material", sub: "Subcontractor", misc: "Direct exp. / misc" };
export const DEFAULT_PREFS = { search: "", status: "all", customer: "all", sort: "over", starredOnly: false, showHidden: false };

export const state = { user: null, jobs: [], lastSync: null, prefs: { ...DEFAULT_PREFS }, editing: null, lookupPick: null, detail: null };
