"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { Table } from "@/components/ui/Table";
import { apiFetch, getToken } from "@/lib/api";
import type { Company } from "@/lib/types";

export default function CompaniesPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setCompanies(await apiFetch<Company[]>("/companies/"));
    } catch {
      setError("Failed to load companies (are you logged in?)");
    }
  }

  useEffect(() => {
    if (!getToken()) { router.push("/login"); return; }
    load();
  }, [router]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await apiFetch("/companies/", { method: "POST", body: JSON.stringify({ name_legal: name }) });
      setName("");
      load();
    } catch {
      setError("Create failed (need operator role)");
    }
  }

  return (
    <Shell>
      <h1 style={{ fontSize: 22, marginBottom: 16 }}>Companies</h1>
      <form onSubmit={create} style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="New company legal name"
          style={{ padding: 8, border: "1px solid #ccc", borderRadius: 4, width: 280 }} />
        <button type="submit" style={{ padding: "8px 16px", background: "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>Create</button>
      </form>
      {error && <div style={{ color: "#c00", marginBottom: 12 }}>{error}</div>}
      <Table
        columns={["Name", "Commercial", "Created", ""]}
        rows={companies.map((c) => [
          c.name_legal,
          c.name_commercial || "—",
          new Date(c.created_at).toLocaleDateString(),
          <Link key={c.id} href={`/companies/${c.id}`} style={{ color: "#2d6cdf" }}>Open →</Link>,
        ])}
      />
    </Shell>
  );
}
