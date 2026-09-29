"use client";
import { useEffect, useState } from "react";
import { api, ChatOut, Mem } from "@/lib/api";
import MemoryCard from "@/components/MemoryCard";

type Status = { local: { total: number; by_kind: Record<string, number>; by_agent: Record<string, number>; avg_confidence: number; avg_decay: number };
  hindsight_enabled: boolean; hindsight_error: string | null };
type Demo = { question: string; before_learning: ChatOut; learned: string[]; after_learning: ChatOut; other_agent_benefits: ChatOut; improved: boolean };

export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [recent, setRecent] = useState<Mem[]>([]);
  const [demo, setDemo] = useState<Demo | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    try {
      setStatus(await api<Status>("/api/analytics/memory"));
      setRecent(await api<Mem[]>("/api/memories?limit=6"));
      setErr("");
    } catch (e) { setErr(String(e)); }
  }
  useEffect(() => { load(); }, []);

  async function runDemo() {
    setBusy(true);
    try { setDemo(await api<Demo>("/api/demo/learning-loop", { method: "POST" })); await load(); }
    catch (e) { setErr(String(e)); }
    setBusy(false);
  }

  const total = status?.local.total ?? 0;
  return (
    <div className="space-y-4">
      {err && <div className="glass border-rose-300 p-3 text-sm text-rose-700">{err}</div>}
      <section className="grid gap-4 sm:grid-cols-4">
        {[["Memories", total], ["Avg confidence", `${((status?.local.avg_confidence ?? 0) * 100).toFixed(0)}%`],
          ["Memory health (decay)", `${((status?.local.avg_decay ?? 0) * 100).toFixed(0)}%`],
          ["Hindsight Cloud", status?.hindsight_enabled ? "Connected" : "Local mode"]].map(([k, v]) => (
          <div key={String(k)} className="glass p-4"><div className="text-xs opacity-60">{k}</div><div className="text-2xl font-semibold">{v}</div></div>
        ))}
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <div className="glass p-4">
          <h2 className="mb-2 font-semibold">Memories by kind</h2>
          {Object.entries(status?.local.by_kind ?? {}).map(([k, n]) => (
            <div key={k} className="mb-1 flex items-center gap-2 text-sm">
              <span className="w-24">{k}</span>
              <div className="h-3 flex-1 rounded bg-slate-200 dark:bg-white/10"><div className="h-3 rounded bg-brand" style={{ width: `${(n / Math.max(total, 1)) * 100}%` }} /></div>
              <span>{n}</span>
            </div>))}
          {!total && <p className="text-sm opacity-60">No memories yet. Run the learning loop demo or seed data.</p>}
        </div>
        <div className="glass p-4">
          <h2 className="mb-2 font-semibold">Agent activity</h2>
          {Object.entries(status?.local.by_agent ?? {}).map(([k, n]) => (
            <div key={k} className="flex justify-between border-b border-slate-200/50 py-1 text-sm dark:border-white/10"><span>{k}</span><span>{n} memories</span></div>))}
        </div>
      </section>
      <section className="glass p-4">
        <div className="mb-3 flex items-center justify-between">
          <div><h2 className="font-semibold">Learning loop demo</h2>
            <p className="text-sm opacity-60">Same question, before and after the agent learns from outcomes.</p></div>
          <button className="btn" onClick={runDemo} disabled={busy}>{busy ? "Running..." : "Run demo"}</button>
        </div>
        {demo && (
          <div className="grid gap-3 md:grid-cols-3 text-sm">
            <div><h3 className="font-medium text-rose-600">Before (no memory)</h3><p className="whitespace-pre-wrap">{demo.before_learning.answer}</p></div>
            <div><h3 className="font-medium text-emerald-600">After (learned)</h3><p className="whitespace-pre-wrap">{demo.after_learning.answer}</p></div>
            <div><h3 className="font-medium text-violet-600">DevOps agent, same brain</h3><p className="whitespace-pre-wrap">{demo.other_agent_benefits.answer}</p></div>
          </div>)}
      </section>
      <section>
        <h2 className="mb-2 font-semibold">Recent memories</h2>
        <div className="grid gap-3 md:grid-cols-2">{recent.map((m) => <MemoryCard key={m.id} m={m} />)}</div>
      </section>
    </div>
  );
}
