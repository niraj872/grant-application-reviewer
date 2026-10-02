from app import demo_data
from app.core import sha256
from app.services import compute_completion
G = lambda t=demo_data.GUIDELINE: {"file": ("g.txt", t.encode())}
A = lambda t=demo_data.APPLICATION: {"file": ("a.txt", t.encode())}
def setup(c):
    g = c.post("/api/guidelines", files=G()).json(); a = c.post("/api/applications", files=A()).json()
    return g, a, c.post("/api/assessments", json={"guideline_version_id": g["version_id"], "application_version_id": a["version_id"]}).json()
def test_upload_hash_and_validation(client):
    g = client.post("/api/guidelines", files=G()).json()
    assert g["version"] == 1 and g["content_hash"] == sha256(g["extracted_text"])
    assert client.post("/api/guidelines", files={"file": ("x.png", b"x")}).status_code == 415
    assert client.post("/api/guidelines", files={"file": ("x.txt", b"  ")}).status_code == 422
def test_versioning(client):
    g1 = client.post("/api/guidelines", files=G()).json()
    g2 = client.post("/api/guidelines", files=G(demo_data.GUIDELINE + "\nApplicants MUST x yyyyy."), data={"guideline_id": g1["id"]}).json()
    assert g2["version"] == 2 and g2["content_hash"] != g1["content_hash"]
def test_requirements_mappings_and_5_2_1(client):
    _, _, s = setup(client); reqs = client.get(f"/api/assessments/{s['assessment_id']}/requirements").json()
    assert all(r["requirement"]["source"]["page"] for r in reqs) and all(r["source"] for r in reqs if r["evidence"])
    m = s["completion"]["mandatory"]
    assert (m["total"], m["satisfied"], m["missing"], m["weak"]) == (8, 5, 2, 1) and m["complete"] == 0  # nothing reviewed yet
    assert s["completion"]["recommended"]["total"] == 1 and s["unsupported_claims"] == 1 and s["questions"]
def test_review_flow_and_completion(client):
    _, _, s = setup(client); reqs = client.get(f"/api/assessments/{s['assessment_id']}/requirements").json()
    for r in reqs:
        if r["ai_status"] == "satisfied": assert client.patch(f"/api/mappings/{r['id']}", json={"decision": "confirm"}).json()["review_state"] == "confirmed"
    sm = client.get(f"/api/assessments/{s['assessment_id']}/summary").json()
    assert sm["completion"]["mandatory"]["percent"] == 62.5 and sm["status"] == "in_review"
    weak = next(r for r in reqs if r["ai_status"] == "weak")
    assert client.patch(f"/api/mappings/{weak['id']}", json={"decision": "correct"}).status_code == 422
    assert client.patch(f"/api/mappings/{weak['id']}", json={"decision": "correct", "corrected_status": "satisfied", "corrected_evidence": "x"}).json()["review_state"] == "corrected"
    assert client.get(f"/api/assessments/{s['assessment_id']}/summary").json()["completion"]["mandatory"]["percent"] == 75.0
    miss = next(r for r in reqs if r["ai_status"] == "missing")
    assert client.patch(f"/api/mappings/{miss['id']}", json={"decision": "reject"}).json()["effective_status"] == "rejected"
def test_deterministic_70_percent():
    items = [("mandatory", "satisfied", True)] * 7 + [("mandatory", "missing", True)] * 2 + [("mandatory", "weak", True)] + [("recommended", "satisfied", True)]
    c = compute_completion(items)
    assert c["mandatory"]["percent"] == 70.0 and c["mandatory"]["missing"] == 2 and c["mandatory"]["weak"] == 1 and c["recommended"]["total"] == 1
    assert compute_completion([("mandatory", "satisfied", False)])["mandatory"]["percent"] == 0.0  # unreviewed doesn't count
def test_stale_detection(client):
    g, a, s = setup(client); assert s["status"] == "draft" and not s["stale"]
    client.post("/api/applications", files=A(demo_data.APPLICATION + "\nMore."), data={"application_id": a["id"]})
    s2 = client.get(f"/api/assessments/{s['assessment_id']}").json()
    assert s2["status"] == "stale" and "stale" in s2["stale_warning"]
    rid = client.get(f"/api/assessments/{s['assessment_id']}/requirements").json()[0]["id"]
    assert client.patch(f"/api/mappings/{rid}", json={"decision": "confirm"}).status_code == 409
def test_supporting_documents(client):
    import json
    docs = [{"name": "Budget.pdf", "required": True, "state": "missing"}, {"name": "Reg", "state": "provided"}]
    a = client.post("/api/applications", files=A(), data={"supporting_documents": json.dumps(docs)}).json()
    g = client.post("/api/guidelines", files=G()).json()
    s = client.post("/api/assessments", json={"guideline_version_id": g["version_id"], "application_version_id": a["version_id"]}).json()
    assert s["supporting_documents"]["provided"] == 1 and s["supporting_documents"]["missing"] == ["Budget.pdf"]
    d = client.patch(f"/api/supporting-documents/{a['supporting_documents'][0]['id']}", json={"state": "not_applicable"}).json()
    assert d["state"] == "not_applicable"
    assert client.get(f"/api/assessments/{s['assessment_id']}").json()["supporting_documents"]["total"] == 1
def test_demo_seed_and_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    s = client.post("/api/demo").json(); m = s["completion"]["mandatory"]
    assert m["complete"] == 5 and m["percent"] == 62.5 and m["weak"] == 1 and s["supporting_documents"]["provided"] == 3
