// Dependency-free horizontal bar chart (the project has no chart library).
const COLORS = ["#2d6cdf", "#1a7f37", "#9a6700", "#c0392b", "#8e44ad", "#16a085", "#d35400"];

export function BarChart({
  title,
  data,
}: {
  title: string;
  data: { label: string; value: number }[];
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 8, padding: 14 }}>
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>{title}</div>
      {data.length === 0 ? (
        <div style={{ color: "#999", fontSize: 13 }}>No data.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {data.map((d, i) => (
            <div key={d.label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <div style={{ width: 130, textAlign: "right", color: "#555", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.label}</div>
              <div style={{ flex: 1, background: "#f0f1f4", borderRadius: 3, height: 18, position: "relative" }}>
                <div style={{ width: `${(d.value / max) * 100}%`, background: COLORS[i % COLORS.length], height: "100%", borderRadius: 3, minWidth: d.value > 0 ? 2 : 0 }} />
              </div>
              <div style={{ width: 36, color: "#333", fontWeight: 600 }}>{d.value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function KpiCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 8, padding: "12px 16px", minWidth: 110 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: "#1a1d23" }}>{value}</div>
      <div style={{ fontSize: 12, color: "#777" }}>{label}</div>
    </div>
  );
}
