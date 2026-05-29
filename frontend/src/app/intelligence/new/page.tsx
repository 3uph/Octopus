"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/layout/Shell";
import { apiFetch } from "@/lib/api";

export default function NewIntelligenceAnalysis() {
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    root_domain: "",
    country: "ES",
    nif: "",
    aliases: "",
    depth: "standard",
    include_documents: true,
    include_github: true,
    include_public_records: true,
    include_social: true,
    include_news: true,
    include_leaks: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm({ ...form, [k]: v });
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.company_name.trim()) { setError("company_name is required"); return; }
    if (form.root_domain && (!form.root_domain.includes(".") || form.root_domain.includes(" "))) {
      setError("invalid domain format"); return;
    }
    setBusy(true);
    try {
      const body = {
        ...form,
        root_domain: form.root_domain.trim() || null,
        nif: form.nif.trim() || null,
        aliases: form.aliases.split(",").map((s) => s.trim()).filter(Boolean),
      };
      const res = await apiFetch<{ id: string }>("/intelligence/analyses", {
        method: "POST",
        body: JSON.stringify(body),
      });
      router.push(`/intelligence/${res.id}`);
    } catch (err) {
      setError(`Failed: ${(err as Error).message} (operator role required)`);
      setBusy(false);
    }
  }

  const input: React.CSSProperties = { width: "100%", padding: 8, border: "1px solid #ccc", borderRadius: 4, marginBottom: 10 };
  const toggles: [keyof typeof form, string][] = [
    ["include_documents", "Documents"],
    ["include_github", "GitHub"],
    ["include_public_records", "Spanish public records"],
    ["include_social", "Social"],
    ["include_news", "News"],
    ["include_leaks", "Leaks (authorized)"],
  ];

  return (
    <Shell>
      <h1 style={{ fontSize: 22, marginBottom: 16 }}>New Intelligence Analysis</h1>
      <form onSubmit={submit} style={{ maxWidth: 560, background: "#fff", padding: 20, borderRadius: 8, border: "1px solid #eee" }}>
        <label style={{ fontSize: 13, fontWeight: 600 }}>Company name *</label>
        <input style={input} value={form.company_name} onChange={(e) => set("company_name", e.target.value)} placeholder="Empresa Ejemplo S.A." />

        <label style={{ fontSize: 13, fontWeight: 600 }}>Root domain</label>
        <input style={input} value={form.root_domain} onChange={(e) => set("root_domain", e.target.value)} placeholder="empresa-ejemplo.com" />

        <div style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600 }}>Country</label>
            <input style={input} value={form.country} onChange={(e) => set("country", e.target.value)} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600 }}>NIF/CIF</label>
            <input style={input} value={form.nif} onChange={(e) => set("nif", e.target.value)} placeholder="optional" />
          </div>
        </div>

        <label style={{ fontSize: 13, fontWeight: 600 }}>Aliases (comma separated)</label>
        <input style={input} value={form.aliases} onChange={(e) => set("aliases", e.target.value)} placeholder="Brand A, Brand B" />

        <label style={{ fontSize: 13, fontWeight: 600 }}>Depth</label>
        <select style={input} value={form.depth} onChange={(e) => set("depth", e.target.value)}>
          <option value="light">light</option>
          <option value="standard">standard</option>
          <option value="deep">deep</option>
        </select>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, margin: "8px 0 14px" }}>
          {toggles.map(([k, label]) => (
            <label key={k} style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 5 }}>
              <input type="checkbox" checked={form[k] as boolean} onChange={(e) => set(k, e.target.checked as never)} />
              {label}
            </label>
          ))}
        </div>

        {error && <div style={{ color: "#c00", marginBottom: 10 }}>{error}</div>}
        <button type="submit" disabled={busy} style={{ padding: "10px 20px", background: busy ? "#888" : "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: busy ? "wait" : "pointer" }}>
          {busy ? "Running analysis…" : "Launch analysis"}
        </button>
      </form>
    </Shell>
  );
}
