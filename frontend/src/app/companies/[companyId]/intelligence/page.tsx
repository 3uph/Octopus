"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { Table } from "@/components/ui/Table";
import { apiFetch } from "@/lib/api";

interface IntelItem { id: string; [k: string]: unknown; }

const ENTITIES = [
  { key: "brands", label: "Brands", fields: ["name"] },
  { key: "products", label: "Products", fields: ["name", "category"] },
  { key: "portals", label: "Public Portals", fields: ["url", "portal_type"] },
  { key: "tech_signals", label: "Tech Signals", fields: ["technology", "evidence_type"] },
  { key: "providers", label: "Providers", fields: ["provider_name", "kind"] },
  { key: "findings", label: "Findings", fields: ["category", "title"] },
];

export default function IntelligencePage() {
  const { companyId } = useParams<{ companyId: string }>();
  const [data, setData] = useState<Record<string, IntelItem[]>>({});
  const [active, setActive] = useState("brands");
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    const out: Record<string, IntelItem[]> = {};
    for (const e of ENTITIES) {
      try { out[e.key] = await apiFetch<IntelItem[]>(`/companies/${companyId}/intelligence/${e.key}`); }
      catch { out[e.key] = []; }
    }
    setData(out);
  }
  useEffect(() => { load(); }, [companyId]);

  const ent = ENTITIES.find((e) => e.key === active)!;

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiFetch(`/companies/${companyId}/intelligence/${active}`, {
        method: "POST", body: JSON.stringify(form),
      });
      setForm({}); setMsg("Added (status: requires_review)."); load();
    } catch (err) {
      setMsg(`Failed: ${(err as Error).message}`);
    }
  }

  return (
    <Shell>
      <Link href={`/companies/${companyId}`} style={{ color: "#2d6cdf", fontSize: 13 }}>← Company</Link>
      <h1 style={{ fontSize: 22, margin: "8px 0 16px" }}>🧠 Corporate Intelligence</h1>
      <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>
        Manual entry. Every item carries confidence + review_status. Intelligence never becomes an active target without Scope Gate.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {ENTITIES.map((e) => (
          <button key={e.key} onClick={() => setActive(e.key)}
            style={{ padding: "6px 12px", borderRadius: 4, border: "1px solid #ccc", cursor: "pointer",
              background: active === e.key ? "#2d6cdf" : "#fff", color: active === e.key ? "#fff" : "#333" }}>
            {e.label} ({data[e.key]?.length || 0})
          </button>
        ))}
      </div>

      <form onSubmit={add} style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {ent.fields.map((f) => (
          <input key={f} placeholder={f} value={form[f] || ""} onChange={(e) => setForm({ ...form, [f]: e.target.value })}
            style={{ padding: 8, border: "1px solid #ccc", borderRadius: 4 }} />
        ))}
        <button type="submit" style={{ padding: "8px 16px", background: "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>Add {ent.label}</button>
      </form>
      {msg && <div style={{ color: "#333", fontSize: 13, marginBottom: 12 }}>{msg}</div>}

      <Table
        columns={[...ent.fields, "confidence", "review_status"]}
        rows={(data[active] || []).map((it) => [
          ...ent.fields.map((f) => String(it[f] ?? "—")),
          String(it.confidence ?? "—"),
          String(it.review_status ?? "—"),
        ])}
      />
    </Shell>
  );
}
