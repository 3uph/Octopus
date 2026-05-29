"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { Table } from "@/components/ui/Table";
import { apiFetch } from "@/lib/api";
import type { Company, Program } from "@/lib/types";

const TYPES = ["bug_bounty", "external_audit", "osint", "surface_review", "private_program", "other"];

export default function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [name, setName] = useState("");
  const [ptype, setPtype] = useState("bug_bounty");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setCompany(await apiFetch<Company>(`/companies/${companyId}`));
      setPrograms(await apiFetch<Program[]>(`/companies/${companyId}/programs/`));
    } catch {
      setError("Failed to load");
    }
  }
  useEffect(() => { load(); }, [companyId]);

  async function createProgram(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiFetch(`/companies/${companyId}/programs/`, {
        method: "POST",
        body: JSON.stringify({ name, program_type: ptype }),
      });
      setName("");
      load();
    } catch {
      setError("Create program failed (need operator)");
    }
  }

  return (
    <Shell>
      <Link href="/companies" style={{ color: "#2d6cdf", fontSize: 13 }}>← Companies</Link>
      <h1 style={{ fontSize: 22, margin: "8px 0 4px" }}>{company?.name_legal || "…"}</h1>
      <Link href={`/companies/${companyId}/intelligence`} style={{ color: "#2d6cdf", fontSize: 14 }}>
        🧠 Corporate Intelligence →
      </Link>

      <h2 style={{ fontSize: 17, margin: "20px 0 10px" }}>Programs</h2>
      <form onSubmit={createProgram} style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Program name"
          style={{ padding: 8, border: "1px solid #ccc", borderRadius: 4 }} />
        <select value={ptype} onChange={(e) => setPtype(e.target.value)} style={{ padding: 8, border: "1px solid #ccc", borderRadius: 4 }}>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <button type="submit" style={{ padding: "8px 16px", background: "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>Add</button>
      </form>
      {error && <div style={{ color: "#c00", marginBottom: 12 }}>{error}</div>}
      <Table
        columns={["Name", "Type", "Platform", "Status", ""]}
        rows={programs.map((p) => [
          p.name, p.program_type, p.platform, p.status,
          <Link key={p.id} href={`/companies/${companyId}/programs/${p.id}`} style={{ color: "#2d6cdf" }}>Open →</Link>,
        ])}
      />
    </Shell>
  );
}
