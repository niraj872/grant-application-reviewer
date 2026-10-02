import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
const api = async (u: string, o?: RequestInit) => { const r = await fetch("/api" + u, o); const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.detail || r.statusText); return j; };
const B = ({ s }: { s: string }) => <span className={`badge ${s}`}>{s.replace("_", " ")}</span>;
const Disclaimer = () => <p style={{ fontSize: 12 }}>AI findings are suggestions for human review. This tool does not make legal, compliance or funding-eligibility decisions.</p>;
function Dashboard() {
  const [list, setList] = useState<any[]>([]); const nav = useNavigate(); const [err, setErr] = useState("");
  useEffect(() => { api("/assessments").then(setList).catch(e => setErr(e.message)); }, []);
  return <><h2>Grant Application Review</h2>{err && <p className="warn">{err}</p>}
    <button onClick={() => api("/demo", { method: "POST" }).then(s => nav(`/assessment/${s.assessment_id}`))}>Load demo assessment</button>
    <div className="card scroll"><table><thead><tr><th>#</th><th>Guideline</th><th>Application</th><th>Status</th></tr></thead><tbody>
      {list.map(a => <tr key={a.id}><td><Link to={`/assessment/${a.id}`}>{a.id}</Link></td><td>{a.guideline}</td><td>{a.application}</td><td><B s={a.status} /></td></tr>)}</tbody></table></div><Disclaimer /></>;
}
function Upload() {
  const nav = useNavigate(); const [g, setG] = useState<File>(); const [a, setA] = useState<File>(); const [docs, setDocs] = useState<any[]>([]);
  const [gid, setGid] = useState(""); const [aid, setAid] = useState(""); const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  const run = async () => { setBusy(true); setErr(""); try {
    const fg = new FormData(); fg.append("file", g!); if (gid) fg.append("guideline_id", gid);
    const fa = new FormData(); fa.append("file", a!); if (aid) fa.append("application_id", aid); fa.append("supporting_documents", JSON.stringify(docs.filter(d => d.name)));
    const gv = await api("/guidelines", { method: "POST", body: fg }), av = await api("/applications", { method: "POST", body: fa });
    const s = await api("/assessments", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ guideline_version_id: gv.version_id, application_version_id: av.version_id }) });
    nav(`/assessment/${s.assessment_id}`); } catch (e: any) { setErr(e.message); } setBusy(false); };
  const up = (i: number, k: string, v: any) => setDocs(docs.map((d, j) => j === i ? { ...d, [k]: v } : d));
  return <><h2>Upload Documents</h2><div className="card"><h4>Grant guideline (PDF/DOCX/TXT)</h4><input type="file" onChange={e => setG(e.target.files?.[0])} />
    <p>Existing guideline ID for a new version (optional): <input size={4} value={gid} onChange={e => setGid(e.target.value)} /></p></div>
    <div className="card"><h4>Draft application</h4><input type="file" onChange={e => setA(e.target.files?.[0])} />
    <p>Existing application ID for a new version (optional): <input size={4} value={aid} onChange={e => setAid(e.target.value)} /></p>
    <h4>Supporting documents (metadata only)</h4>{docs.map((d, i) => <p key={i}><input placeholder="Name" value={d.name} onChange={e => up(i, "name", e.target.value)} />{" "}
      <input placeholder="Type" value={d.doc_type} onChange={e => up(i, "doc_type", e.target.value)} />{" "}
      <select value={d.state} onChange={e => up(i, "state", e.target.value)}><option value="provided">Provided</option><option value="missing">Missing</option><option value="not_applicable">Not applicable</option></select>{" "}
      <label><input type="checkbox" checked={d.required} onChange={e => up(i, "required", e.target.checked)} />required</label></p>)}
    <button onClick={() => setDocs([...docs, { name: "", doc_type: "", state: "missing", required: true }])}>+ Add document</button></div>
    {err && <p className="warn">{err}</p>}<button disabled={!g || !a || busy} onClick={run}>{busy ? "Analyzing…" : "Create assessment"}</button><Disclaimer /></>;
}
function Assessment({ tab }: { tab: "overview" | "requirements" | "summary" }) {
  const { id } = useParams(); const [s, setS] = useState<any>(); const [reqs, setReqs] = useState<any[]>([]); const [sel, setSel] = useState<any>(); const [err, setErr] = useState("");
  const load = () => { api(`/assessments/${id}`).then(setS).catch(e => setErr(e.message)); api(`/assessments/${id}/requirements`).then(setReqs).catch(() => {}); };
  useEffect(load, [id]);
  const review = async (m: any, decision: string) => { let body: any = { decision };
    if (decision === "correct") { const st = prompt("Corrected status (satisfied|weak|missing|ambiguous|unsupported)"); if (!st) return; body = { ...body, corrected_status: st, corrected_evidence: prompt("Corrected evidence (optional)") || "" }; }
    try { const r = await api(`/mappings/${m.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); setSel(r); load(); } catch (e: any) { setErr((e as Error).message); } };
  const setDoc = (d: any, state: string) => api(`/supporting-documents/${d.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ state }) }).then(load);
  if (!s) return <p>{err || "Loading…"}</p>; const m = s.completion.mandatory, r = s.completion.recommended, pg = (x: any) => x?.page ? `p.${x.page}` : "—";
  return <><h2>Assessment #{s.assessment_id} <B s={s.status} /></h2>
    <p><Link to={`/assessment/${id}`}>Overview</Link> · <Link to={`/assessment/${id}/requirements`}>Requirements</Link> · <Link to={`/assessment/${id}/summary`}>Summary</Link></p>
    {s.stale && <div className="warn">{s.stale_warning}</div>}{err && <p className="warn">{err}</p>}
    <div className="card"><p>Guideline: <b>{s.guideline.name} v{s.guideline.version}</b> · Application: <b>{s.application.name} v{s.application.version}</b></p>
      <div className="grid">{[["Mandatory completion", m.percent + "%"], ["Mandatory", `${m.complete} / ${m.total}`], ["Satisfied", m.satisfied], ["Missing", m.missing], ["Weak", m.weak], ["Ambiguous", m.ambiguous], ["Pending review", m.pending_review],
        ["Unsupported claims", s.unsupported_claims], ["Docs provided", `${s.supporting_documents.provided} / ${s.supporting_documents.total}`], ["Recommended", `${r.satisfied} / ${r.total} satisfied`]].map(([k, v]) => <div key={k as string} className="card stat"><b>{v}</b>{k}</div>)}</div></div>
    {tab !== "summary" && <div className="card scroll"><table><thead><tr><th>Requirement</th><th>Type</th><th>Evidence</th><th>Source</th><th>Status</th><th>Review</th></tr></thead><tbody>
      {reqs.map(x => <tr key={x.id} className="click" onClick={() => setSel(x)}><td>{x.requirement.text}</td><td>{x.requirement.importance}</td><td>{x.evidence ? "Found" : "Missing"}</td><td>{pg(x.source)}</td>
        <td><B s={x.effective_status} /></td><td><B s={x.review_state} /></td></tr>)}</tbody></table></div>}
    {sel && tab !== "summary" && <div className="card"><h4>Evidence viewer</h4><b>Guideline</b> ({sel.requirement.source.document}, {pg(sel.requirement.source)}, {sel.requirement.source.section || "—"})
      <div className="ev">{sel.requirement.text}</div><b>Application</b> ({sel.source ? `${sel.source.document}, ${pg(sel.source)}, ${sel.source.section || "—"}` : "no source"})<div className="ev">{sel.evidence || "No supplied evidence found."}</div>
      <b>AI-generated assessment</b> (suggestion, confidence {sel.confidence}): <B s={sel.ai_status} /><div className="ev">{sel.reason}</div>
      <p>AI Suggestion: <B s={sel.ai_status} /> Reviewer: <button onClick={() => review(sel, "confirm")}>Confirm</button><button onClick={() => review(sel, "correct")}>Correct</button><button onClick={() => review(sel, "reject")}>Reject</button></p></div>}
    {tab !== "requirements" && <>
      <div className="card"><h4>Missing evidence</h4>{(["missing", "weak", "ambiguous"] as const).map(k => <div key={k}><B s={k} />{s.missing_evidence[k].length ? <ul>{s.missing_evidence[k].map((g: any) => <li key={g.mapping_id}>{g.requirement} ({g.importance})</li>)}</ul> : " none"}</div>)}</div>
      <div className="card"><h4>Unsupported claims</h4>{s.claims.length ? s.claims.map((c: any) => <div key={c.id} className="ev"><b>Claim:</b> “{c.claim}” ({pg(c.source)})<br />{c.note}. Evidence: no supplied supporting evidence found. Reviewer action required.</div>) : "None identified"}</div>
      <div className="card"><h4>Clarification questions</h4><ol>{s.questions.map((q: any) => <li key={q.id}>{q.question}</li>)}</ol></div>
      <div className="card"><h4>Supporting documents</h4>{s.supporting_documents.items.map((d: any) => <p key={d.id}>{d.name} · required: {d.required ? "Yes" : "No"} · <B s={d.state} /> {["provided", "missing", "not_applicable"].map(st => <button key={st} onClick={() => setDoc(d, st)}>{st.replace("_", " ")}</button>)}</p>)}</div></>}
    <Disclaimer /></>;
}
export default function App() {
  return <><header><b>Grant Application Reviewer</b><Link to="/">Dashboard</Link><Link to="/upload">Upload</Link></header><main><Routes>
    <Route path="/" element={<Dashboard />} /><Route path="/upload" element={<Upload />} /><Route path="/assessment/:id" element={<Assessment tab="overview" />} />
    <Route path="/assessment/:id/requirements" element={<Assessment tab="requirements" />} /><Route path="/assessment/:id/summary" element={<Assessment tab="summary" />} /></Routes></main></>;
}
