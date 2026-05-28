import { Link } from "react-router-dom";
import { Sparkles, Search, Brain, Library, Zap, Lock } from "lucide-react";
import { useAuthStore } from "@/store/auth";

const features = [
  { icon: Search, title: "Live web + arXiv + Wikipedia", body: "DuckDuckGo, arXiv and Wikipedia — no paid keys needed." },
  { icon: Brain, title: "Tool-calling agent", body: "Plans, searches, computes and synthesizes citations." },
  { icon: Library, title: "Chat with your PDFs", body: "Upload research papers and query them with RAG (FAISS + HF embeddings)." },
  { icon: Zap, title: "Streaming responses", body: "Server-Sent Events stream tokens live, just like ChatGPT." },
  { icon: Lock, title: "Multi-user accounts", body: "JWT auth, persistent conversations, per-user metrics." },
  { icon: Sparkles, title: "Free LLM providers", body: "Groq, OpenRouter, Hugging Face or local Ollama." },
];

export default function Landing() {
  const token = useAuthStore((s) => s.token);
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
      <nav className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-white">Research Agent</span>
        </div>
        <div className="flex items-center gap-2">
          {token ? (
            <Link to="/chat" className="btn-primary">Open app</Link>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">Sign in</Link>
              <Link to="/register" className="btn-primary">Get started</Link>
            </>
          )}
        </div>
      </nav>

      <header className="max-w-4xl mx-auto px-6 pt-16 pb-24 text-center">
        <div className="inline-flex items-center gap-2 pill mb-6">
          <Sparkles className="h-3 w-3 text-brand-400" />
          Open-source LLMs · Free to run
        </div>
        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight text-white mb-5">
          Your AI research assistant,
          <br />
          <span className="bg-gradient-to-r from-brand-400 to-cyan-400 bg-clip-text text-transparent">
            powered by open models.
          </span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
          A multi-agent research system that searches the web, reads arXiv, summarizes Wikipedia,
          and answers questions about your own documents — using free providers like Groq, OpenRouter,
          and Hugging Face.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link to={token ? "/chat" : "/register"} className="btn-primary px-5 py-2.5 text-base">
            Start researching →
          </Link>
          <a
            href="/api/docs"
            target="_blank"
            rel="noreferrer"
            className="btn-outline px-5 py-2.5 text-base"
          >
            API docs
          </a>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map(({ icon: Icon, title, body }) => (
          <div key={title} className="card p-5">
            <div className="h-9 w-9 rounded-lg bg-slate-800 flex items-center justify-center mb-3">
              <Icon className="h-4 w-4 text-brand-400" />
            </div>
            <div className="text-white font-medium mb-1">{title}</div>
            <div className="text-sm text-slate-400">{body}</div>
          </div>
        ))}
      </section>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        Built with FastAPI · React · LangChain-style tool calling · FAISS
      </footer>
    </div>
  );
}
