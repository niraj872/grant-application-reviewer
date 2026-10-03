import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
const api = async (u, o) => { const r = await fetch("/api" + u, o); const j = await r.json().catch(() => ({})); if (!r.ok)
    throw new Error(j.detail || r.statusText); return j; };
const B = ({ s }) => _jsx("span", { className: `badge ${s}`, children: s.replace("_", " ") });
const Disclaimer = () => _jsx("p", { style: { fontSize: 12 }, children: "AI findings are suggestions for human review. This tool does not make legal, compliance or funding-eligibility decisions." });
function Dashboard() {
    const [list, setList] = useState([]);
    const nav = useNavigate();
    const [err, setErr] = useState("");
    useEffect(() => { api("/assessments").then(setList).catch(e => setErr(e.message)); }, []);
    return _jsxs(_Fragment, { children: [_jsx("h2", { children: "Grant Application Review" }), err && _jsx("p", { className: "warn", children: err }), _jsx("button", { onClick: () => api("/demo", { method: "POST" }).then(s => nav(`/assessment/${s.assessment_id}`)), children: "Load demo assessment" }), _jsx("div", { className: "card scroll", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "#" }), _jsx("th", { children: "Guideline" }), _jsx("th", { children: "Application" }), _jsx("th", { children: "Status" })] }) }), _jsx("tbody", { children: list.map(a => _jsxs("tr", { children: [_jsx("td", { children: _jsx(Link, { to: `/assessment/${a.id}`, children: a.id }) }), _jsx("td", { children: a.guideline }), _jsx("td", { children: a.application }), _jsx("td", { children: _jsx(B, { s: a.status }) })] }, a.id)) })] }) }), _jsx(Disclaimer, {})] });
}
function Upload() {
    const nav = useNavigate();
    const [g, setG] = useState();
    const [a, setA] = useState();
    const [docs, setDocs] = useState([]);
    const [gid, setGid] = useState("");
    const [aid, setAid] = useState("");
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState("");
    const run = async () => {
        setBusy(true);
        setErr("");
        try {
            const fg = new FormData();
            fg.append("file", g);
            if (gid)
                fg.append("guideline_id", gid);
            const fa = new FormData();
            fa.append("file", a);
            if (aid)
                fa.append("application_id", aid);
            fa.append("supporting_documents", JSON.stringify(docs.filter(d => d.name)));
            const gv = await api("/guidelines", { method: "POST", body: fg }), av = await api("/applications", { method: "POST", body: fa });
            const s = await api("/assessments", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ guideline_version_id: gv.version_id, application_version_id: av.version_id }) });
            nav(`/assessment/${s.assessment_id}`);
        }
        catch (e) {
            setErr(e.message);
        }
        setBusy(false);
    };
    const up = (i, k, v) => setDocs(docs.map((d, j) => j === i ? { ...d, [k]: v } : d));
    return _jsxs(_Fragment, { children: [_jsx("h2", { children: "Upload Documents" }), _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Grant guideline (PDF/DOCX/TXT)" }), _jsx("input", { type: "file", onChange: e => setG(e.target.files?.[0]) }), _jsxs("p", { children: ["Existing guideline ID for a new version (optional): ", _jsx("input", { size: 4, value: gid, onChange: e => setGid(e.target.value) })] })] }), _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Draft application" }), _jsx("input", { type: "file", onChange: e => setA(e.target.files?.[0]) }), _jsxs("p", { children: ["Existing application ID for a new version (optional): ", _jsx("input", { size: 4, value: aid, onChange: e => setAid(e.target.value) })] }), _jsx("h4", { children: "Supporting documents (metadata only)" }), docs.map((d, i) => _jsxs("p", { children: [_jsx("input", { placeholder: "Name", value: d.name, onChange: e => up(i, "name", e.target.value) }), " ", _jsx("input", { placeholder: "Type", value: d.doc_type, onChange: e => up(i, "doc_type", e.target.value) }), " ", _jsxs("select", { value: d.state, onChange: e => up(i, "state", e.target.value), children: [_jsx("option", { value: "provided", children: "Provided" }), _jsx("option", { value: "missing", children: "Missing" }), _jsx("option", { value: "not_applicable", children: "Not applicable" })] }), " ", _jsxs("label", { children: [_jsx("input", { type: "checkbox", checked: d.required, onChange: e => up(i, "required", e.target.checked) }), "required"] })] }, i)), _jsx("button", { onClick: () => setDocs([...docs, { name: "", doc_type: "", state: "missing", required: true }]), children: "+ Add document" })] }), err && _jsx("p", { className: "warn", children: err }), _jsx("button", { disabled: !g || !a || busy, onClick: run, children: busy ? "AnalyzingÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦" : "Create assessment" }), _jsx(Disclaimer, {})] });
}
function Assessment({ tab }) {
    const { id } = useParams();
    const [s, setS] = useState();
    const [reqs, setReqs] = useState([]);
    const [sel, setSel] = useState();
    const [err, setErr] = useState("");
    const load = () => { api(`/assessments/${id}`).then(setS).catch(e => setErr(e.message)); api(`/assessments/${id}/requirements`).then(setReqs).catch(() => { }); };
    useEffect(load, [id]);
    const review = async (m, decision) => {
        let body = { decision };
        if (decision === "correct") {
            const st = prompt("Corrected status (satisfied|weak|missing|ambiguous|unsupported)");
            if (!st)
                return;
            body = { ...body, corrected_status: st, corrected_evidence: prompt("Corrected evidence (optional)") || "" };
        }
        try {
            const r = await api(`/mappings/${m.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
            setSel(r);
            load();
        }
        catch (e) {
            setErr(e.message);
        }
    };
    const setDoc = (d, state) => api(`/supporting-documents/${d.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ state }) }).then(load);
    if (!s)
        return _jsx("p", { children: err || "LoadingÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦" });
    const m = s.completion.mandatory, r = s.completion.recommended, pg = (x) => x?.page ? `p.${x.page}` : "ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â";
    return _jsxs(_Fragment, { children: [_jsxs("h2", { children: ["Assessment #", s.assessment_id, " ", _jsx(B, { s: s.status })] }), _jsxs("p", { children: [_jsx(Link, { to: `/assessment/${id}`, children: "Overview" }), " \u00B7 ", _jsx(Link, { to: `/assessment/${id}/requirements`, children: "Requirements" }), " \u00B7 ", _jsx(Link, { to: `/assessment/${id}/summary`, children: "Summary" })] }), s.stale && _jsx("div", { className: "warn", children: s.stale_warning }), err && _jsx("p", { className: "warn", children: err }), _jsxs("div", { className: "card", children: [_jsxs("p", { children: ["Guideline: ", _jsxs("b", { children: [s.guideline.name, " v", s.guideline.version] }), " \u00B7 Application: ", _jsxs("b", { children: [s.application.name, " v", s.application.version] })] }), _jsx("div", { className: "grid", children: [["Mandatory completion", m.percent + "%"], ["Mandatory", `${m.complete} / ${m.total}`], ["Satisfied", m.satisfied], ["Missing", m.missing], ["Weak", m.weak], ["Ambiguous", m.ambiguous], ["Pending review", m.pending_review],
                            ["Unsupported claims", s.unsupported_claims], ["Docs provided", `${s.supporting_documents.provided} / ${s.supporting_documents.total}`], ["Recommended", `${r.satisfied} / ${r.total} satisfied`]].map(([k, v]) => _jsxs("div", { className: "card stat", children: [_jsx("b", { children: v }), k] }, k)) })] }), tab !== "summary" && _jsx("div", { className: "card scroll", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Requirement" }), _jsx("th", { children: "Type" }), _jsx("th", { children: "Evidence" }), _jsx("th", { children: "Source" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "Review" })] }) }), _jsx("tbody", { children: reqs.map(x => _jsxs("tr", { className: "click", onClick: () => setSel(x), children: [_jsx("td", { children: x.requirement.text }), _jsx("td", { children: x.requirement.importance }), _jsx("td", { children: x.evidence ? "Found" : "Missing" }), _jsx("td", { children: pg(x.source) }), _jsx("td", { children: _jsx(B, { s: x.effective_status }) }), _jsx("td", { children: _jsx(B, { s: x.review_state }) })] }, x.id)) })] }) }), sel && tab !== "summary" && _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Evidence viewer" }), _jsx("b", { children: "Guideline" }), " (", sel.requirement.source.document, ", ", pg(sel.requirement.source), ", ", sel.requirement.source.section || "-", ")", _jsx("div", { className: "ev", children: sel.requirement.text }), _jsx("b", { children: "Application" }), " (", sel.source ? `${sel.source.document}, ${pg(sel.source)}, ${sel.source.section || "-"}` : "no source", ")", _jsx("div", { className: "ev", children: sel.evidence || "No supplied evidence found." }), _jsx("b", { children: "AI-generated assessment" }), " (suggestion, confidence ", sel.confidence, "): ", _jsx(B, { s: sel.ai_status }), _jsx("div", { className: "ev", children: sel.reason }), _jsxs("p", { children: ["AI Suggestion: ", _jsx(B, { s: sel.ai_status }), " Reviewer: ", _jsx("button", { onClick: () => review(sel, "confirm"), children: "Confirm" }), _jsx("button", { onClick: () => review(sel, "correct"), children: "Correct" }), _jsx("button", { onClick: () => review(sel, "reject"), children: "Reject" })] })] }), tab !== "requirements" && _jsxs(_Fragment, { children: [_jsxs("div", { className: "card", children: [_jsx("h4", { children: "Missing evidence" }), ["missing", "weak", "ambiguous"].map(k => _jsxs("div", { children: [_jsx(B, { s: k }), s.missing_evidence[k].length ? _jsx("ul", { children: s.missing_evidence[k].map((g) => _jsxs("li", { children: [g.requirement, " (", g.importance, ")"] }, g.mapping_id)) }) : " none"] }, k))] }), _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Unsupported claims" }), s.claims.length ? s.claims.map((c) => _jsxs("div", { className: "ev", children: [_jsx("b", { children: "Claim:" }), " \u201C", c.claim, "\u201D (", pg(c.source), ")", _jsx("br", {}), c.note, ". Evidence: no supplied supporting evidence found. Reviewer action required."] }, c.id)) : "None identified"] }), _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Clarification questions" }), _jsx("ol", { children: s.questions.map((q) => _jsx("li", { children: q.question }, q.id)) })] }), _jsxs("div", { className: "card", children: [_jsx("h4", { children: "Supporting documents" }),
s.supporting_documents.items.map((d) => _jsxs("div", {
    style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "10px",
        padding: "10px 0",
        borderBottom: "1px solid #ddd",
        flexWrap: "wrap"
    },
    children: [
        _jsxs("div", {
            children: [
                _jsx("b", { children: d.name }),
                _jsxs("span", {
                    children: [" Ãƒâ€šÃ‚Â· required: ", d.required ? "Yes" : "No"]
                })
            ]
        }),
        _jsxs("div", {
            style: {
                display: "flex",
                gap: "8px", marginRight: "4px",
                flexWrap: "wrap"
            },
            children: [
                _jsx("button", {
                    type: "button",
                    onClick: () => setDoc(d, "provided"),
                    children: "Provided"
                }),
                _jsx("button", {
                    type: "button",
                    onClick: () => setDoc(d, "missing"),
                    children: "Missing"
                }),
                _jsx("button", {
                    type: "button",
                    onClick: () => setDoc(d, "not_applicable"),
                    children: "Not applicable"
                })
            ]
        })
    ]
}, d.id))] }), _jsx(Disclaimer, {})] })] });
}
export default function App() {
    return _jsxs(_Fragment, { children: [_jsxs("header", { children: [_jsx("b", { children: "Grant Application Reviewer" }), _jsx(Link, { to: "/", children: "Dashboard" }), _jsx(Link, { to: "/upload", children: "Upload" })] }), _jsx("main", { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Dashboard, {}) }), _jsx(Route, { path: "/upload", element: _jsx(Upload, {}) }), _jsx(Route, { path: "/assessment/:id", element: _jsx(Assessment, { tab: "overview" }) }), _jsx(Route, { path: "/assessment/:id/requirements", element: _jsx(Assessment, { tab: "requirements" }) }), _jsx(Route, { path: "/assessment/:id/summary", element: _jsx(Assessment, { tab: "summary" }) })] }) })] });
}

