import json
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import demo_data, services as S
from .core import sha256
from .db import SessionLocal, engine, get_db
from .models import *
from .schemas import *
@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine); yield
app = FastAPI(title="Grant Application Reviewer", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
def make_version(db, Parent, Version, fk, filename, pages, name, parent_id):
    parent = db.get(Parent, parent_id) if parent_id else None
    if parent_id and not parent: raise HTTPException(404, "Parent document not found")
    if not parent: parent = Parent(name=name or filename); db.add(parent); db.flush()
    text = "\n".join(pages)
    v = Version(**{fk: parent.id}, version=len(parent.versions) + 1, filename=filename, text=text, pages=pages, content_hash=sha256(text))
    db.add(v); db.flush(); return parent, v
def ver_out(parent, v, extra=None):
    return {"id": parent.id, "name": parent.name, "version_id": v.id, "version": v.version, "filename": v.filename, "content_hash": v.content_hash,
            "uploaded_at": v.uploaded_at.isoformat(), "extracted_text": v.text, **(extra or {})}
@app.get("/api/health")
def health(): return {"status": "ok"}
@app.post("/api/guidelines", status_code=201)
async def upload_guideline(file: UploadFile = File(...), name: str = Form(None), guideline_id: int = Form(None), db: Session = Depends(get_db)):
    pages = S.parse_document(file.filename or "", await file.read())
    p, v = make_version(db, Guideline, GuidelineVersion, "guideline_id", file.filename, pages, name, guideline_id); db.commit(); return ver_out(p, v)
@app.post("/api/applications", status_code=201)
async def upload_application(file: UploadFile = File(...), name: str = Form(None), application_id: int = Form(None),
                             supporting_documents: str = Form("[]"), db: Session = Depends(get_db)):
    try: docs = json.loads(supporting_documents); assert isinstance(docs, list)
    except Exception: raise HTTPException(422, "supporting_documents must be a JSON list")
    pages = S.parse_document(file.filename or "", await file.read())
    p, v = make_version(db, Application, ApplicationVersion, "application_id", file.filename, pages, name, application_id)
    for d in docs:
        if not d.get("name") or d.get("state", "missing") not in ("provided", "missing", "not_applicable"): raise HTTPException(422, "Invalid supporting document")
        db.add(SupportingDocument(application_version_id=v.id, name=d["name"], doc_type=d.get("doc_type", ""), required=d.get("required", True),
                                  state=d.get("state", "missing"), description=d.get("description", "")))
    db.commit(); return ver_out(p, v, {"supporting_documents": [S.doc_out(d) for d in v.supporting_documents]})
@app.get("/api/guidelines")
def list_guidelines(db: Session = Depends(get_db)):
    return [{"id": g.id, "name": g.name, "versions": [{"version_id": v.id, "version": v.version, "filename": v.filename} for v in g.versions]} for g in db.query(Guideline)]
@app.get("/api/applications")
def list_applications(db: Session = Depends(get_db)):
    return [{"id": g.id, "name": g.name, "versions": [{"version_id": v.id, "version": v.version, "filename": v.filename} for v in g.versions]} for g in db.query(Application)]
@app.post("/api/assessments", status_code=201)
def create_assessment(body: AssessmentIn, db: Session = Depends(get_db)):
    gv, av = db.get(GuidelineVersion, body.guideline_version_id), db.get(ApplicationVersion, body.application_version_id)
    if not gv or not av: raise HTTPException(404, "Guideline or application version not found")
    a = S.build_assessment(db, gv, av); return S.summary(db, a)
def get_a(db, id):
    a = db.get(Assessment, id)
    if not a: raise HTTPException(404, "Assessment not found")
    return a
@app.get("/api/assessments")
def list_assessments(db: Session = Depends(get_db)):
    return [{"id": a.id, "status": S.lifecycle(db, a), "guideline": f"{a.guideline_version.guideline.name} v{a.guideline_version.version}",
             "application": f"{a.application_version.application.name} v{a.application_version.version}"} for a in db.query(Assessment).order_by(Assessment.id.desc())]
@app.get("/api/assessments/{id}")
def get_assessment(id: int, db: Session = Depends(get_db)): return S.summary(db, get_a(db, id))
@app.get("/api/assessments/{id}/requirements")
def get_requirements(id: int, db: Session = Depends(get_db)): return [S.mapping_out(m) for m in get_a(db, id).mappings]
@app.get("/api/assessments/{id}/summary")
def get_summary(id: int, db: Session = Depends(get_db)): return S.summary(db, get_a(db, id))
@app.patch("/api/mappings/{id}")
def review_mapping(id: int, body: ReviewIn, db: Session = Depends(get_db)):
    m = db.get(RequirementMapping, id)
    if not m: raise HTTPException(404, "Mapping not found")
    if S.is_stale(db, m.assessment): raise HTTPException(409, "Assessment is stale; create a new assessment")
    if body.decision == "correct" and not body.corrected_status: raise HTTPException(422, "corrected_status is required when correcting")
    db.add(ReviewerDecision(mapping_id=m.id, decision=body.decision, corrected_status=body.corrected_status, corrected_evidence=body.corrected_evidence, note=body.note))
    db.commit(); db.refresh(m); return S.mapping_out(m)
@app.patch("/api/supporting-documents/{id}")
def set_doc_state(id: int, body: DocStateIn, db: Session = Depends(get_db)):
    d = db.get(SupportingDocument, id)
    if not d: raise HTTPException(404, "Supporting document not found")
    d.state = body.state; db.commit(); return S.doc_out(d)
@app.post("/api/demo", status_code=201)
def seed_demo(db: Session = Depends(get_db)):
    """Creates sample guideline + application + assessment; pre-confirms the satisfied/missing mandatory mappings (not the weak one)."""
    p, gv = make_version(db, Guideline, GuidelineVersion, "guideline_id", "sample-guideline.txt", demo_data.GUIDELINE.split("\f"), "Sample Community Grant Guidelines", None)
    ap, av = make_version(db, Application, ApplicationVersion, "application_id", "sample-application.txt", [demo_data.APPLICATION], "Greenway Funding Application", None)
    for n, t, r, s in demo_data.DOCS: db.add(SupportingDocument(application_version_id=av.id, name=n, doc_type=t, required=r, state=s))
    db.commit()
    from .ai import client
    prev = __import__("os").environ.get("AI_PROVIDER"); __import__("os").environ["AI_PROVIDER"] = "demo"
    try: a = S.build_assessment(db, gv, av)
    finally:
        if prev is None: __import__("os").environ.pop("AI_PROVIDER", None)
        else: __import__("os").environ["AI_PROVIDER"] = prev
    for m in a.mappings:
        if m.requirement.importance == "mandatory" and m.status != "weak":
            db.add(ReviewerDecision(mapping_id=m.id, decision="confirm", note="Demo seeded decision"))
    db.commit(); return S.summary(db, a)
