"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { Table } from "@/components/ui/Table";
import { apiFetch } from "@/lib/api";
import type { Asset, Audit, DryRunResult, Program, ScanJob, ScopeSummary } from "@/lib/types";

export default function ProgramDetail() {
  const { companyId, programId } = useParams<{ companyId: string; programId: string }>();
  const base = `/companies/${companyId}/programs/${programId}`;

  const [program, setProgram] = useState<Program | null>(null);
  const [scopeRaw, setScopeRaw] = useState("");
  const [summary, setSummary] = useState<ScopeSummary | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [audits, setAudits] = useState<Audit[]>([]);
  const [reconTargets, setReconTargets] = useState("");
  const [dryRun, setDryRun] = useState<DryRunResult | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setProgram(await apiFetch<Program>(`${base}`));
    try { const s = await apiFetch<{ scope_raw: string | null }>(`${base}/scope/`); setScopeRaw(s.scope_raw || ""); } catch {}
    try { setSummary(await apiFetch<ScopeSummary>(`${base}/scope/summary`)); } catch {}
    try { setAssets(await apiFetch<Asset[]>(`${base}/assets`)); } catch {}
    try { setJobs(await apiFetch<ScanJob[]>(`${base}/scan-jobs`)); } catch {}
    try { setAudits(await apiFetch<Audit[]>(`/programs/${programId}/audits/`)); } catch {}
  }
  useEffect(() => { load(); }, [companyId, programId]);

  async function saveScope() {
    await apiFetch(`${base}/scope/`, { method: "PUT", body: JSON.stringify({ scope_raw: scopeRaw }) });
    setMsg("Scope saved."); load();
  }
  async function parseScope() {
    const r = await apiFetch<Record<string, number>>(`${base}/scope/parse`, { method: "POST" });
    setMsg(`Parsed: ${JSON.stringify(r)}`); load();
  }
  async function doDryRun() {
    const targets = reconTargets.split(/[\s,]+/).filter(Boolean);
    setDryRun(await apiFetch<DryRunResult>(`${base}/recon/passive/dry-run`, { method: "POST", body: JSON.stringify({ targets }) }));
  }
  async function doRun() {
    const targets = reconTargets.split(/[\s,]+/).filter(Boolean);
    try {
      const r = await apiFetch<Record<string, unknown>>(`${base}/recon/passive/run`, { method: "POST", body: JSON.stringify({ targets }) });
      setMsg(`Recon done: ${JSON.stringify(r)}`); load();
    } catch (e) {
      setMsg(`Recon blocked: ${(e as Error).message}`);
    }
  }

  const box = { background: "#fff", padding: 16, borderRadius: 8, marginBottom: 20, border: "1px solid #eee" };

  return (
    <Shell>
      <Link href={`/companies/${companyId}`} style={{ color: "#2d6cdf", fontSize: 13 }}>← Company</Link>
      <h1 style={{ fontSize: 22, margin: "8px 0 16px" }}>{program?.name || "…"} <span style={{ fontSize: 13, color: "#888" }}>({program?.status})</span></h1>

      <div style={box}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Raw Scope</h2>
        <textarea value={scopeRaw} onChange={(e) => setScopeRaw(e.target.value)} rows={6}
          placeholder={"In scope:\n*.example.com\nOut of scope:\nadmin.example.com"}
          style={{ width: "100%", fontFamily: "monospace", padding: 8, border: "1px solid #ccc", borderRadius: 4 }} />
        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
          <button onClick={saveScope} style={btn}>Save scope</button>
          <button onClick={parseScope} style={btn}>Parse scope</button>
        </div>
      </div>

      {summary && (
        <div style={box}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Parsed Scope Summary</h2>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", fontSize: 14 }}>
            <ScopeCol title="✅ Allowed" items={summary.allowed} color="#1a7f37" />
            <ScopeCol title="⛔ Forbidden" items={summary.forbidden} color="#c00" />
            <ScopeCol title="❓ Ambiguous" items={summary.ambiguous} color="#9a6700" />
            <ScopeCol title="🔍 Needs review" items={summary.requires_review} color="#9a6700" />
            <ScopeCol title="📋 Rules" items={summary.rules} color="#555" />
          </div>
        </div>
      )}

      <div style={box}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Passive Recon (Scope-Gated)</h2>
        <input value={reconTargets} onChange={(e) => setReconTargets(e.target.value)} placeholder="example.com, other.com"
          style={{ width: 360, padding: 8, border: "1px solid #ccc", borderRadius: 4 }} />
        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
          <button onClick={doDryRun} style={btn}>Dry-run</button>
          <button onClick={doRun} style={{ ...btn, background: "#1a7f37" }}>Run passive</button>
        </div>
        {dryRun && (
          <div style={{ marginTop: 10, fontSize: 13 }}>
            <div>Eligible: {dryRun.eligible_targets.join(", ") || "—"}</div>
            <div style={{ color: "#c00" }}>Blocked: {dryRun.blocked_targets.map((b) => `${b.target}(${b.decision})`).join(", ") || "—"}</div>
            <div style={{ color: "#888" }}>{dryRun.note}</div>
          </div>
        )}
      </div>

      {msg && <div style={{ marginBottom: 16, color: "#333", fontSize: 13 }}>{msg}</div>}

      <div style={box}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Assets ({assets.length})</h2>
        <Table columns={["Value", "Type", "Source", "Scope", "Score", "Conf"]}
          rows={assets.map((a) => [a.value, a.asset_type, a.discovered_via || "—", a.scope_decision, a.score, a.confidence])} />
      </div>

      <div style={box}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Scan Jobs ({jobs.length})</h2>
        <Table columns={["Mode", "Status", "Summary", "When"]}
          rows={jobs.map((j) => [j.mode, j.status, JSON.stringify(j.summary || {}), new Date(j.created_at).toLocaleString()])} />
      </div>

      <div style={box}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Audits ({audits.length})</h2>
        <Table columns={["Title", "Status", "Created"]}
          rows={audits.map((a) => [a.title, a.status, new Date(a.created_at).toLocaleDateString()])} />
      </div>
    </Shell>
  );
}

const btn: React.CSSProperties = { padding: "8px 14px", background: "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" };

function ScopeCol({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div style={{ minWidth: 140 }}>
      <div style={{ fontWeight: 600, color, marginBottom: 4 }}>{title} ({items.length})</div>
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {items.slice(0, 20).map((it, i) => <li key={i} style={{ fontFamily: "monospace", fontSize: 12 }}>{it}</li>)}
      </ul>
    </div>
  );
}
