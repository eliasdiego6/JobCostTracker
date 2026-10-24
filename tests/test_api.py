from app.qb.fake import FAKE_JOBS, _job


ESTIMATES = {"est_labor": 14000, "est_material": 16000, "est_sub": 11000, "est_misc": 1500, "contract": 52000}


def add_job(client, number="24-146"):
    matches = client.get("/api/qb/search", params={"q": number}).json()
    assert len(matches) == 1
    r = client.post("/api/jobs", json={**ESTIMATES, "job_number": number, "qb_list_id": matches[0]["list_id"]})
    assert r.status_code == 200, r.text
    return r.json()


def test_add_job_pulls_actuals_from_qb(client):
    job = add_job(client)
    assert job["customer"] == "Patel Residence"
    assert job["synced_at"]
    assert job["overall"]["contract"] == 52000
    detail = client.get(f"/api/jobs/{job['id']}").json()
    assert detail["transactions"]
    labor_txns = sum(t["amount"] for t in detail["transactions"] if t["bucket"] == "labor")
    assert round(labor_txns, 2) == detail["buckets"][0]["actual"]


def test_duplicate_job_rejected(client):
    add_job(client)
    qb = _job(next(r for r in FAKE_JOBS if r[0] == "24-146"))
    r = client.post("/api/jobs", json={**ESTIMATES, "job_number": "24-146", "qb_list_id": qb.list_id})
    assert r.status_code == 409


def test_unknown_qb_job_rejected(client):
    r = client.post("/api/jobs", json={**ESTIMATES, "job_number": "99-999", "qb_list_id": "nope"})
    assert r.status_code == 404


def test_hide_and_star_are_per_user(client):
    job = add_job(client)
    alice = client.post("/api/users", json={"name": "Alice"}).json()
    bob = client.post("/api/users", json={"name": "Bob"}).json()
    client.put(f"/api/users/{alice['id']}/jobs/{job['id']}", json={"hidden": True, "starred": True})

    a = client.get("/api/jobs", params={"user_id": alice["id"]}).json()["jobs"][0]
    b = client.get("/api/jobs", params={"user_id": bob["id"]}).json()["jobs"][0]
    assert a["hidden"] and a["starred"]
    assert not b["hidden"] and not b["starred"]


def test_same_name_returns_existing_user(client):
    a = client.post("/api/users", json={"name": "Alice"}).json()
    again = client.post("/api/users", json={"name": "alice"}).json()
    assert again["id"] == a["id"]


def test_edit_notes_and_delete(client):
    job = add_job(client)
    r = client.put(f"/api/jobs/{job['id']}", json={**ESTIMATES, "est_labor": 20000, "pct_complete": 50})
    assert r.json()["buckets"][0]["estimate"] == 20000
    assert r.json()["pct_complete"] == 50

    client.post(f"/api/jobs/{job['id']}/notes", json={"body": "Waiting on change order", "author": "Alice"})
    assert client.get(f"/api/jobs/{job['id']}").json()["notes"][0]["body"] == "Waiting on change order"

    assert client.delete(f"/api/jobs/{job['id']}").status_code == 200
    assert client.get("/api/jobs").json()["jobs"] == []
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_prefs_round_trip(client):
    u = client.post("/api/users", json={"name": "Alice"}).json()
    client.put(f"/api/users/{u['id']}/prefs", json={"sort": "profit", "starredOnly": True})
    assert client.get(f"/api/users/{u['id']}/prefs").json() == {"sort": "profit", "starredOnly": True}


def test_sync_and_export(client):
    add_job(client)
    assert client.post("/api/sync").json() == {"synced": 1}
    r = client.get("/api/export.xlsx")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"  # xlsx is a zip file
