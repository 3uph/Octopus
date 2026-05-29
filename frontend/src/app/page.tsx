"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getToken() ? "/companies" : "/login");
  }, [router]);
  return <main style={{ padding: 24, fontFamily: "system-ui" }}>Loading…</main>;
}
