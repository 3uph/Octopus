"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { Table } from "@/components/ui/Table";
import { apiFetch, getToken } from "@/lib/api";

interface Analysis {
  id: string;
  target_company_name: string;
  target_root_domain: string | null;
  status: string;
  depth: string;
  created_at: string;
  summary_json: { kpis?: Record<string, number> } | null;
  exposure_score_json: { overall?: number } | null;
}

export default function IntelligenceDashboard() {
  const router = useRouter();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setAnalyses(await apiFetch<Analysis[]>("/intelligence/analyses"));
    } catch {
      setError("Failed to load analyses (logged in?)");
    }
  }
  useEffect(() => {
    if (!getToken()) { router.push("/login"); return; }
    load();
  }, [router]);

  return (
    <Shell>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1 style={{ fontSize: 22 }}>Intelligence Analyses</h1>
        <Link href="/intelligence/new" style={{ padding: "8px 16px", background: "#2d6cdf", color: "#fff", borderRadius: 4, textDecoration: "none" }}>
          + New intelligence analysis
        </Link>
      </div>
      {error && <div style={{ color: "#c00", marginBottom: 12 }}>{error}</div>}
      <Table
        columns={["Company", "Domain", "Status", "Depth", "Score", "Findings", "Risks", "Date", ""]}
        rows={analyses.map((a) => [
          a.target_company_name,
          a.target_root_domain || "—",
          a.status,
          a.depth,
          a.exposure_score_json?.overall ?? "—",
          a.summary_json?.kpis?.total_findings ?? 0,
          a.summary_json?.kpis?.risk_hypotheses ?? 0,
          new Date(a.created_at).toLocaleString(),
          <Link key={a.id} href={`/intelligence/${a.id}`} style={{ color: "#2d6cdf" }}>Open →</Link>,
        ])}
      />
    </Shell>
  );
}
