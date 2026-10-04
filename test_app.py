import pytest
from app import create_app, compute_priority, label

@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path / "t.db")).test_client()

def mk(client, **kw):
    d = dict(title="Leak", category="water_leak", location="Ward 5", severity="medium", affected=20)
    d.update(kw)
    return client.post("/api/issues", json=d)

# --- unit tests: priority engine
def test_TC01_priority_base_low():      assert compute_priority("streetlight", "low", 1) == 2
def test_TC02_priority_high_severity(): assert compute_priority("water_leak", "high", 5) == 7
def test_TC03_priority_reach_bonus():   assert compute_priority("pothole", "medium", 150) == 6
def test_TC04_priority_capped_at_10():  assert compute_priority("power_outage", "high", 500) == 10
def test_TC05_labels():
    assert [label(x) for x in (2, 4, 6, 8)] == ["Low", "Medium", "High", "Critical"]

# --- API tests
def test_TC06_create_issue_routes_dept(client):
    r = mk(client, category="pothole")
    assert r.status_code == 201 and r.json["department"] == "Roads Dept" and r.json["status"] == "Reported"

def test_TC07_missing_title_rejected(client):
    r = mk(client, title="  ")
    assert r.status_code == 400 and "title is required" in r.json["errors"]

def test_TC08_invalid_category_rejected(client):
    assert mk(client, category="alien").status_code == 400

def test_TC09_invalid_affected_rejected(client):
    assert mk(client, affected=0).status_code == 400 and mk(client, affected="abc").status_code == 400

def test_TC10_listing_sorted_by_priority(client):
    mk(client, title="light", category="streetlight", severity="low", affected=1)
    mk(client, title="outage", category="power_outage", severity="high", affected=200)
    assert [i["title"] for i in client.get("/api/issues").json] == ["outage", "light"]

def test_TC11_filter_by_status(client):
    mk(client); i2 = mk(client).json["id"]
    client.patch(f"/api/issues/{i2}/status", json={"status": "Assigned"})
    assert len(client.get("/api/issues?status=Assigned").json) == 1

def test_TC12_workflow_happy_path(client):
    i = mk(client).json["id"]
    for s in ("Assigned", "In Progress", "Resolved"):
        assert client.patch(f"/api/issues/{i}/status", json={"status": s}).json["status"] == s

def test_TC13_cannot_skip_status(client):
    i = mk(client).json["id"]
    assert client.patch(f"/api/issues/{i}/status", json={"status": "Resolved"}).status_code == 409

def test_TC14_unknown_issue_404(client):
    assert client.patch("/api/issues/999/status", json={"status": "Assigned"}).status_code == 404

def test_TC15_invalid_status_400(client):
    i = mk(client).json["id"]
    assert client.patch(f"/api/issues/{i}/status", json={"status": "Done"}).status_code == 400

def test_TC16_stats(client):
    mk(client, category="power_outage", severity="high", affected=200)
    i = mk(client).json["id"]
    for s in ("Assigned", "In Progress", "Resolved"):
        client.patch(f"/api/issues/{i}/status", json={"status": s})
    s = client.get("/api/stats").json
    assert (s["total"], s["open"], s["resolved"], s["critical_open"]) == (2, 1, 1, 1)

def test_TC17_empty_body_400(client):
    assert client.post("/api/issues", data="notjson").status_code == 400

def test_TC18_ui_served(client):
    assert b"CityServe" in client.get("/").data

def test_TC19_sql_injection_filter_safe(client):
    mk(client)
    assert client.get("/api/issues?status=' OR 1=1 --").json == []

def test_TC20_categories_endpoint(client):
    assert client.get("/api/categories").json["waste"]["department"] == "Sanitation Dept"
