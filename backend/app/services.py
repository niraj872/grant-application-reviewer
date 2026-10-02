import io, re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .ai import client, demo, prompts
from .ai.client import AIError
from .models import *
from .schemas import *
DOC_EXT = {".pdf", ".docx", ".txt"}
def parse_document(filename: str, data: bytes) -> list[str]:
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in DOC_EXT: raise HTTPException(415, "Only PDF, DOCX and TXT files are supported")
    try:
        if ext == ".txt": pages = data.decode("utf-8", "replace").split("\f")
        elif ext == ".pdf":
            from pypdf import PdfReader
            pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]
        else:
            import docx
            pages = ["\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)]
    except Exception: raise HTTPException(422, "Could not parse document")
    if not "".join(pages).strip(): raise HTTPException(422, "No extractable text found (OCR is not supported)")
    return pages
def paged(pages): return "\n".join(f"[PAGE {i}]\n{p}" for i, p in enumerate(pages, 1))
# ---------- deterministic business logic (no LLM) ----------
def effective(m: RequirementMapping):
    """Returns (status, reviewed). Only confirmed/corrected decisions count as reviewed."""
    d = m.decisions[-1] if m.decisions else None
    if not d: return m.status, False
    if d.decision == "reject": return "rejected", False
    if d.decision == "correct": return d.corrected_status or m.status, True
    return m.status, True
def compute_completion(items):
    """items: (importance, status, reviewed). Mandatory completion = reviewed-satisfied mandatory / total mandatory."""
    def block(imp):
        sel = [(s, r) for i, s, r in items if i == imp]
        c = {k: sum(1 for s, _ in sel if s == k) for k in ("satisfied", "weak", "missing", "ambiguous", "unsupported", "rejected")}
        complete = sum(1 for s, r in sel if s == "satisfied" and r)
        return {"total": len(sel), "complete": complete, "pending_review": sum(1 for _, r in sel if not r), **c,
                "percent": round(complete / len(sel) * 100, 1) if sel else 0.0}
    return {"mandatory": block("mandatory"), "recommended": block("recommended")}
def is_stale(db: Session, a: Assessment) -> bool:
    g = a.guideline_version.guideline.versions[-1]; p = a.application_version.application.versions[-1]
    return g.id != a.guideline_version_id or p.id != a.application_version_id or \
        g.content_hash != a.guideline_version.content_hash or p.content_hash != a.application_version.content_hash
def lifecycle(db, a):
    if is_stale(db, a): return "stale"
    n = sum(1 for m in a.mappings if m.decisions)
    return "draft" if n == 0 else "reviewed" if n == len(a.mappings) else "in_review"
# ---------- AI orchestration ----------
def _norm(s): return re.sub(r"\s+", " ", s).strip().lower()
def build_assessment(db: Session, gv: GuidelineVersion, av: ApplicationVersion) -> Assessment:
    try:
        reqs = list(gv.requirements)
        if not reqs:
            rl = demo.extract(gv.filename, gv.pages) if client.is_demo() else client.call(ReqList, prompts.EXTRACT.format(doc=gv.filename, text=paged(gv.pages)))
            if not rl.requirements: raise AIError("No requirements could be extracted")
            for r in rl.requirements:
                db.add(Requirement(guideline_version_id=gv.id, text=r.requirement_text, category=r.category, importance=r.importance,
                                   ambiguous=r.ambiguous, source=r.source.model_dump()))
            db.flush(); db.refresh(gv); reqs = list(gv.requirements)
        rq = [(r.id, r.text) for r in reqs]
        ml = demo.map_reqs(av.filename, rq, av.pages) if client.is_demo() else client.call(MapList, prompts.MAP.format(
            doc=av.filename, reqs="\n".join(f"{i}: {t}" for i, t in rq), text=paged(av.pages)))
        cl = demo.claims(av.filename, av.pages) if client.is_demo() else client.call(ClaimList, prompts.CLAIMS.format(
            doc=av.filename, text=paged(av.pages), docs=[d.name for d in av.supporting_documents if d.state == "provided"]))
    except AIError as e: db.rollback(); raise HTTPException(502, str(e))
    a = Assessment(guideline_version_id=gv.id, application_version_id=av.id); db.add(a); db.flush()
    by = {m.requirement_id: m for m in ml.mappings}; text = _norm(av.text); gaps = []
    for rid, rtext in rq:
        m = by.get(rid) or MapOut(requirement_id=rid, status="missing", confidence=1, reason="No mapping returned by AI.")
        ev, src, st, why = m.application_evidence, m.application_source, m.status, m.reason
        # guard: evidence must be a verbatim quote from the application and carry a source
        if st != "missing" and (not ev or not src or _norm(ev) not in text):
            ev, src, st, why = "", None, "missing", (why + " | Evidence not found verbatim in application; downgraded to missing.").strip(" |")
        db.add(RequirementMapping(assessment_id=a.id, requirement_id=rid, evidence=ev, source=src.model_dump() if src else None,
                                  status=st, confidence=m.confidence, reason=why))
        if st in ("missing", "weak", "ambiguous", "unsupported"): gaps.append({"kind": "req", "index": rid, "text": rtext, "status": st})
    claims = []
    for c in cl.claims:
        if _norm(c.claim) not in text: continue
        uc = UnsupportedClaim(assessment_id=a.id, claim=c.claim, source=c.source.model_dump(), note=c.note); db.add(uc); db.flush(); claims.append(uc)
        gaps.append({"kind": "claim", "index": len(claims) - 1, "text": c.claim})
    try: ql = demo.questions(gaps) if client.is_demo() else client.call(QList, prompts.QUESTIONS.format(gaps=gaps))
    except AIError: ql = demo.questions(gaps)  # deterministic template fallback
    rids = {r for r, _ in rq}
    for q in ql.questions:
        rid = q.requirement_id if q.requirement_id in rids else None
        cid = claims[q.claim_index].id if q.claim_index is not None and 0 <= q.claim_index < len(claims) else None
        if rid or cid: db.add(ClarificationQuestion(assessment_id=a.id, question=q.question, requirement_id=rid, claim_id=cid))
    db.commit(); return a
# ---------- serializers ----------
def mapping_out(m):
    st, rev = effective(m); d = m.decisions[-1] if m.decisions else None; r = m.requirement
    return {"id": m.id, "requirement": {"id": r.id, "text": r.text, "category": r.category, "importance": r.importance, "ambiguous": r.ambiguous, "source": r.source},
            "evidence": m.evidence, "source": m.source, "ai_status": m.status, "confidence": m.confidence, "reason": m.reason,
            "review_state": {"confirm": "confirmed", "correct": "corrected", "reject": "rejected"}[d.decision] if d else "ai_suggested",
            "effective_status": st, "reviewed": rev,
            "reviewer": {"decision": d.decision, "corrected_status": d.corrected_status, "corrected_evidence": d.corrected_evidence, "note": d.note} if d else None}
def doc_out(d): return {"id": d.id, "name": d.name, "doc_type": d.doc_type, "required": d.required, "state": d.state, "description": d.description}
def summary(db, a):
    ms = [mapping_out(m) for m in a.mappings]
    comp = compute_completion([(m["requirement"]["importance"], m["effective_status"], m["reviewed"]) for m in ms])
    gaps = {k: [{"mapping_id": m["id"], "requirement": m["requirement"]["text"], "importance": m["requirement"]["importance"]}
                for m in ms if m["effective_status"] == k] for k in ("missing", "weak", "ambiguous")}
    docs = a.application_version.supporting_documents; applicable = [d for d in docs if d.state != "not_applicable"]
    stale = is_stale(db, a)
    return {"assessment_id": a.id, "status": lifecycle(db, a), "stale": stale,
            "stale_warning": "⚠ This assessment is stale because the guideline/application version has changed. Please create a new assessment." if stale else None,
            "guideline": {"name": a.guideline_version.guideline.name, "version": a.guideline_version.version, "hash": a.guideline_version.content_hash},
            "application": {"name": a.application_version.application.name, "version": a.application_version.version, "hash": a.application_version.content_hash},
            "completion": comp, "missing_evidence": gaps, "unsupported_claims": len(a.claims),
            "supporting_documents": {"provided": sum(d.state == "provided" for d in docs), "total": len(applicable),
                "missing": [d.name for d in applicable if d.required and d.state == "missing"], "items": [doc_out(d) for d in docs]},
            "questions": [{"id": q.id, "question": q.question, "requirement_id": q.requirement_id, "claim_id": q.claim_id} for q in a.questions],
            "claims": [{"id": c.id, "claim": c.claim, "source": c.source, "note": c.note} for c in a.claims],
            "disclaimer": __import__("app.core", fromlist=["x"]).DISCLAIMER}
