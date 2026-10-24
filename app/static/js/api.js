// The one place that talks to the server. Throws Error(message) on any non-2xx response.

export async function api(path, opts = {}) {
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
