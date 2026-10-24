from app.domain import calc


def job(**overrides):
    row = {f"est_{b}": 0.0 for b in calc.BUCKET_LABELS} | {f"act_{b}": 0.0 for b in calc.BUCKET_LABELS}
    row |= {"contract": 0.0, "invoiced": 0.0, "pct_complete": None}
    return row | overrides


def test_status_over_when_actual_exceeds_estimate():
    assert calc.status(1000, 1200, None) == "over"


def test_status_trending_at_90_percent_without_pct_complete():
    assert calc.status(1000, 900, None) == "trending"
    assert calc.status(1000, 899, None) == "ok"


def test_status_uses_projection_when_pct_complete_set():
    # 40% done, 60% spent -> projected 150% of estimate
    assert calc.status(1000, 600, 40) == "trending"
    # 80% done, 70% spent -> projected 87.5%
    assert calc.status(1000, 700, 80) == "ok"


def test_zero_estimate_with_cost_is_over():
    assert calc.status(0, 50, None) == "over"
    assert calc.status(0, 0, None) == "ok"


def test_summarize_overall_and_profit():
    s = calc.summarize(
        job(est_labor=40000, est_material=50000, est_sub=20000, est_misc=5000,
            act_labor=30000, act_material=20000, act_sub=10000, act_misc=0,
            contract=150000, invoiced=60000, pct_complete=50)
    )
    o = s["overall"]
    assert o["estimate"] == 115000
    assert o["actual"] == 60000
    assert o["estimated_profit"] == 35000
    assert o["profit_remaining"] == 90000
    assert o["projected"] == 120000  # 60k at 50% complete
    assert o["projected_profit"] == 30000
    assert o["loss"] is False
    labor = s["buckets"][0]
    assert labor["status"] == "trending"  # 30k at 50% -> 60k projected vs 40k
    assert s["status"] == "trending"


def test_summarize_flags_loss():
    s = calc.summarize(job(est_labor=100, act_labor=200, contract=150))
    assert s["overall"]["loss"] is True
    assert s["status"] == "over"
