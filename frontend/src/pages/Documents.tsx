import { useEffect, useRef, useState } from "react";
import { Upload, Trash2, FileText, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "@/api/client";

type Doc = { id: number; filename: string; size_bytes: number; num_chunks: number; created_at: string };

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function load() {
    const { data } = await api.get<Doc[]>("/documents");
    setDocs(data);
  }

  useEffect(() => {
    load().catch(() => toast.error("Could not load documents"));
  }, []);

  async function upload(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    setUploading(true);
    try {
      await api.post("/documents", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`Indexed ${file.name}`);
      load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this document?")) return;
    await api.delete(`/documents/${id}`);
    setDocs((d) => d.filter((x) => x.id !== id));
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold text-white">Documents</h1>
        <p className="text-sm text-slate-400 mt-1">Upload PDFs, .txt or .md files to chat with via RAG.</p>

        <div className="mt-6 card p-6 border-dashed border-2 border-slate-800 text-center">
          <Upload className="h-8 w-8 text-slate-500 mx-auto mb-2" />
          <p className="text-sm text-slate-400 mb-3">PDF, TXT or MD · max 20 MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.md"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
          />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="btn-primary"
          >
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {uploading ? "Indexing…" : "Choose file"}
          </button>
        </div>

        <div className="mt-6 space-y-2">
          {docs.length === 0 ? (
            <div className="text-slate-500 text-sm text-center py-6">No documents yet.</div>
          ) : (
            docs.map((d) => (
              <div key={d.id} className="card p-3 flex items-center gap-3">
                <FileText className="h-5 w-5 text-brand-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">{d.filename}</div>
                  <div className="text-xs text-slate-500">
                    {(d.size_bytes / 1024).toFixed(1)} KB · {d.num_chunks} chunks ·{" "}
                    {new Date(d.created_at).toLocaleDateString()}
                  </div>
                </div>
                <button onClick={() => remove(d.id)} className="btn-ghost text-red-400 hover:text-red-300">
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
