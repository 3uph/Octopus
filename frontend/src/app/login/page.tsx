"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      router.push("/companies");
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", fontFamily: "system-ui, sans-serif", background: "#f7f8fa" }}>
      <form onSubmit={onSubmit} style={{ background: "#fff", padding: 32, borderRadius: 8, width: 320, boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
        <h1 style={{ fontSize: 20, marginBottom: 16 }}>🐙 Octopus Login</h1>
        <input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 10, border: "1px solid #ccc", borderRadius: 4 }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 10, border: "1px solid #ccc", borderRadius: 4 }}
        />
        {error && <div style={{ color: "#c00", fontSize: 13, marginBottom: 10 }}>{error}</div>}
        <button type="submit" style={{ width: "100%", padding: 10, background: "#2d6cdf", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
          Sign in
        </button>
      </form>
    </div>
  );
}
