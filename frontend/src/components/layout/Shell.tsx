"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const NAV = [
  { href: "/companies", label: "Companies" },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}>
      <aside
        style={{
          width: 200,
          background: "#1a1d23",
          color: "#e6e6e6",
          padding: "16px 12px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 20 }}>🐙 Octopus</div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} style={{ color: "#cdd3da", textDecoration: "none" }}>
              {n.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={logout}
          style={{
            background: "transparent",
            color: "#9aa4af",
            border: "1px solid #333",
            borderRadius: 4,
            padding: "6px 10px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </aside>
      <main style={{ flex: 1, padding: 24, background: "#f7f8fa" }}>{children}</main>
    </div>
  );
}
