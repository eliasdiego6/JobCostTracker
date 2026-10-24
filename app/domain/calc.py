"""Budget math: over / trending / on-track for each bucket and the job overall."""

from app.domain.buckets import BUCKET_LABELS, STATUS_RANK

TRENDING_THRESHOLD = 0.9  # with no % complete, flag at 90% of estimate used


def projected(actual: float, pct_complete: float | None) -> float | None:
    if not pct_complete or pct_complete <= 0:
        return None
    return actual / (min(pct_complete, 100) / 100)


def status(estimate: float, actual: float, pct_complete: float | None) -> str:
    if actual > estimate:
        return "over"
    proj = projected(actual, pct_complete)
    if proj is not None:
        return "trending" if proj > estimate else "ok"
    return "trending" if estimate > 0 and actual >= estimate * TRENDING_THRESHOLD else "ok"


def _line(estimate: float, actual: float, pct_complete: float | None) -> dict:
    proj = projected(actual, pct_complete)
    return {
        "estimate": estimate,
        "actual": actual,
        "variance": round(actual - estimate, 2),  # positive = over
        "pct_used": round(actual / estimate * 100, 1) if estimate else None,
        "projected": round(proj, 2) if proj is not None else None,
        "status": status(estimate, actual, pct_complete),
    }


def summarize(job) -> dict:
    """Turn a jobs row (or dict) into everything the dashboard shows."""
    pct = job["pct_complete"]
    buckets = []
    for key, label in BUCKET_LABELS.items():
        line = _line(job[f"est_{key}"], job[f"act_{key}"], pct)
        buckets.append({"key": key, "label": label, **line})

    est_total = sum(b["estimate"] for b in buckets)
    act_total = round(sum(b["actual"] for b in buckets), 2)
    overall = _line(est_total, act_total, pct)
    contract = job["contract"]
    proj_total = overall["projected"] if overall["projected"] is not None else max(act_total, est_total)
    overall.update(
        {
            "contract": contract,
            "invoiced": job["invoiced"],
            "estimated_profit": round(contract - est_total, 2),
            "profit_remaining": round(contract - act_total, 2),
            "projected_profit": round(contract - proj_total, 2),
            "loss": act_total > contract or proj_total > contract,
        }
    )
    worst = max([b["status"] for b in buckets] + [overall["status"]], key=STATUS_RANK.get)
    return {"buckets": buckets, "overall": overall, "status": worst}
