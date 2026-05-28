import { useEffect, useState } from "react";
import { BarChart3, Coins, Timer, MessageSquare } from "lucide-react";
import { api } from "@/api/client";

type Metrics = {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  total_latency_ms: number;
  by_provider: Record<string, { calls: number; tokens: number; cost_usd: number; avg_latency_ms: number }>;
};

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    api.get<Metrics>("/metrics").then((r) => setMetrics(r.data));
  }, []);

  if (!metrics) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  const totalCost = Object.values(metrics.by_provider).reduce((a, b) => a + b.cost_usd, 0);

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold text-white">Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">Your usage across providers.</p>

        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat icon={<MessageSquare className="h-4 w-4" />} label="Conversations" value={metrics.total_conversations} />
          <Stat icon={<BarChart3 className="h-4 w-4" />} label="Messages" value={metrics.total_messages} />
          <Stat icon={<Timer className="h-4 w-4" />} label="Total latency" value={`${(metrics.total_latency_ms / 1000).toFixed(1)}s`} />
          <Stat icon={<Coins className="h-4 w-4" />} label="Est. spend" value={`$${totalCost.toFixed(4)}`} />
        </div>

        <div className="mt-8 card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 text-sm font-medium text-white">
            By provider
          </div>
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="text-left px-4 py-2">Provider</th>
                <th className="text-right px-4 py-2">Calls</th>
                <th className="text-right px-4 py-2">Tokens</th>
                <th className="text-right px-4 py-2">Avg latency</th>
                <th className="text-right px-4 py-2">Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(metrics.by_provider).length === 0 ? (
                <tr>
                  <td className="text-slate-500 px-4 py-4" colSpan={5}>No usage yet — go run a query.</td>
                </tr>
              ) : (
                Object.entries(metrics.by_provider).map(([name, s]) => (
                  <tr key={name} className="border-t border-slate-800">
                    <td className="px-4 py-2 text-white">{name}</td>
                    <td className="px-4 py-2 text-right text-slate-300">{s.calls}</td>
                    <td className="px-4 py-2 text-right text-slate-300">{s.tokens.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right text-slate-300">{(s.avg_latency_ms / 1000).toFixed(1)}s</td>
                    <td className="px-4 py-2 text-right text-slate-300">${s.cost_usd.toFixed(4)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-xs text-slate-500 uppercase tracking-wide">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}
