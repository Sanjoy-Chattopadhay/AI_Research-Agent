import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Trash2, Download, MessageSquare } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "@/api/client";

type Conv = { id: number; title: string; provider: string; created_at: string; updated_at: string };

export default function History() {
  const [convs, setConvs] = useState<Conv[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const { data } = await api.get<Conv[]>("/conversations");
      setConvs(data);
    } catch {
      toast.error("Could not load history");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(id: number) {
    if (!confirm("Delete this conversation?")) return;
    await api.delete(`/conversations/${id}`);
    setConvs((c) => c.filter((x) => x.id !== id));
    toast.success("Deleted");
  }

  async function exportMd(id: number, title: string) {
    const res = await api.get(`/conversations/${id}/export.md`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9-_]/gi, "_") || "conversation"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold text-white">History</h1>
        <p className="text-sm text-slate-400 mt-1">All your saved research conversations.</p>

        <div className="mt-6 space-y-2">
          {loading ? (
            <div className="text-slate-500 text-sm">Loading…</div>
          ) : convs.length === 0 ? (
            <div className="card p-6 text-center text-slate-400">
              No conversations yet. <Link to="/chat" className="text-brand-400 hover:underline">Start one →</Link>
            </div>
          ) : (
            convs.map((c) => (
              <div key={c.id} className="card p-4 flex items-center gap-3 hover:border-slate-700 transition">
                <MessageSquare className="h-4 w-4 text-slate-500" />
                <Link to={`/chat/${c.id}`} className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">{c.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {new Date(c.updated_at).toLocaleString()} · {c.provider}
                  </div>
                </Link>
                <button onClick={() => exportMd(c.id, c.title)} className="btn-ghost" title="Export Markdown">
                  <Download className="h-4 w-4" />
                </button>
                <button onClick={() => remove(c.id)} className="btn-ghost text-red-400 hover:text-red-300" title="Delete">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
