"""Deterministic offline stand-in for the LLM (AI_PROVIDER=demo). Keyword-overlap heuristics, for demos/tests only."""
import re
from ..schemas import *
STOP = {"applicants", "applicant", "must", "should", "provide", "include", "describe", "application", "submit", "name", "have"}
def _lines(pages):
    for pi, p in enumerate(pages, 1):
        sec = None
        for ln in p.splitlines():
            ln = ln.strip()
            if ln.startswith("## "): sec = ln[3:]
            elif ln: yield pi, sec, ln
def _tok(t): return {w for w in re.findall(r"[a-z][a-z\-]+", t.lower()) if len(w) > 4 and w not in STOP}
def extract(doc, pages):
    out = []
    for pi, sec, ln in _lines(pages):
        m = "mandatory" if " MUST " in f" {ln} " else "recommended" if " SHOULD " in f" {ln} " else None
        if not m: continue
        l = ln.lower(); cat = next((c for k, c in [("registered", "eligibility"), ("operating", "eligibility"), ("budget", "budget"), ("timeline", "timeline"),
              ("letter", "documentation"), ("project", "project")] if k in l), "other")
        out.append(ReqOut(requirement_text=ln, category=cat, importance=m, ambiguous="as appropriate" in l, source=Source(document=doc, page=pi, section=sec)))
    return ReqList(requirements=out)
def map_reqs(doc, reqs, pages):
    out = []
    for rid, text in reqs:
        t = _tok(text); best = (0.0, None)
        for pi, sec, ln in _lines(pages):
            sc = len(t & _tok(ln)) / max(len(t), 1)
            if sc > best[0]: best = (sc, (pi, sec, ln))
        sc, hit = best
        if sc >= .5: st = "satisfied"
        elif sc >= .25: st = "weak"
        else: st, hit = "missing", None
        out.append(MapOut(requirement_id=rid, application_evidence=hit[2] if hit else "", confidence=round(min(.95, .3 + sc), 2),
            application_source=Source(document=doc, page=hit[0], section=hit[1]) if hit else None, status=st,
            reason={"satisfied": "The supplied application appears to address this requirement (keyword overlap).",
                    "weak": "Partial overlap only; the evidence may not fully address the requirement.",
                    "missing": "No supplied evidence found for this requirement."}[st]))
    return MapList(mappings=out)
def claims(doc, pages):
    out = []
    for pi, sec, ln in _lines(pages):
        for s in re.split(r"(?<=[.!?])\s+", ln):
            if re.search(r"\d+\s?%", s): out.append(ClaimOut(claim=s, source=Source(document=doc, page=pi, section=sec)))
    return ClaimList(claims=out)
def questions(gaps):
    qs = []
    for g in gaps:
        if g["kind"] == "claim": qs.append(QOut(question=f"Please provide evidence supporting the stated claim: \"{g['text']}\"", claim_index=g["index"]))
        else: qs.append(QOut(question=f"Please provide or clarify evidence for ({g['status']}): {g['text']}", requirement_id=g["index"]))
    return QList(questions=qs)
