import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import toast from "react-hot-toast";
import { Send, Sparkles, Wrench, Loader2, FileText } from "lucide-react";
import { api, streamChat, Provider } from "@/api/client";

type ChatMsg = { role: "user" | "assistant"; content: string; tools?: string[]; tokens?: number };

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: "auto", label: "Auto" },
  { id: "groq", label: "Groq" },
  { id: "openrouter", label: "OpenRouter" },
  { id: "hf", label: "Hugging Face" },
  { id: "ollama", label: "Ollama (local)" },
  { id: "openai", label: "OpenAI" },
];

const SUGGESTIONS = [
  "Summarize the latest research on retrieval-augmented generation",
  "Compare LangGraph and AutoGen for agent orchestration",
  "What are the key results in DeepSeek-V3's paper?",
  "Explain mixture-of-experts in 5 bullet points",
];

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [convId, setConvId] = useState<number | null>(conversationId ? Number(conversationId) : null);
  const [provider, setProvider] = useState<Provider>("auto");
  const [useRag, setUseRag] = useState(false);
  const [docs, setDocs] = useState<{ id: number; filename: string }[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [statusLine, setStatusLine] = useState("");
  const scrollerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get("/documents").then((r) => setDocs(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      setConvId(null);
      return;
    }
    setConvId(Number(conversationId));
    api
      .get(`/conversations/${conversationId}`)
      .then((r) => {
        setMessages(
          r.data.messages.map((m: any) => ({
            role: m.role,
            content: m.content,
            tokens: m.tokens,
          }))
        );
      })
      .catch(() => toast.error("Could not load conversation"));
  }, [conversationId]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, statusLine]);

  async function send(query: string) {
    if (!query.trim() || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: query }, { role: "assistant", content: "" }]);

    try {
      const stream = streamChat({
        query,
        conversation_id: convId,
        provider,
        use_rag: useRag && selectedDocs.length > 0,
        document_ids: selectedDocs,
      });
      const collectedTools: string[] = [];
      for await (const ev of stream) {
        if (ev.event === "meta") {
          setConvId(ev.data.conversation_id);
          if (!conversationId) navigate(`/chat/${ev.data.conversation_id}`, { replace: true });
        } else if (ev.event === "status") {
          setStatusLine(ev.data.message);
        } else if (ev.event === "tool") {
          collectedTools.push(ev.data.name);
          setStatusLine(`🔧 ${ev.data.name}(${JSON.stringify(ev.data.args)})`);
        } else if (ev.event === "token") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: next[next.length - 1].content + ev.data.text,
            };
            return next;
          });
        } else if (ev.event === "done") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: ev.data.answer,
              tools: ev.data.tools_used,
              tokens: ev.data.tokens,
            };
            return next;
          });
          setStatusLine(
            `${ev.data.provider}:${ev.data.model} · ${ev.data.tokens} tokens · ${(ev.data.latency_ms / 1000).toFixed(1)}s`
          );
        } else if (ev.event === "error") {
          toast.error(ev.data.message);
        }
      }
    } catch (e: any) {
      toast.error(e?.message ?? "Stream failed");
    } finally {
      setBusy(false);
      setTimeout(() => setStatusLine(""), 4000);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-full flex-col">
      <header className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-slate-800 bg-slate-950/60">
        <div className="flex items-center gap-3">
          <Sparkles className="h-4 w-4 text-brand-400" />
          <div className="text-sm text-slate-300 font-medium">
            {convId ? `Conversation #${convId}` : "New conversation"}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
            className="input py-1.5 text-xs w-36"
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
          <label className="pill cursor-pointer">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="accent-brand-500"
            />
            RAG
          </label>
        </div>
      </header>

      {useRag && (
        <div className="px-5 py-2 border-b border-slate-800 bg-slate-900/40 flex items-center gap-2 overflow-x-auto">
          <FileText className="h-4 w-4 text-slate-500 shrink-0" />
          {docs.length === 0 ? (
            <span className="text-xs text-slate-500">No documents uploaded — see Documents tab.</span>
          ) : (
            docs.map((d) => {
              const active = selectedDocs.includes(d.id);
              return (
                <button
                  key={d.id}
                  onClick={() =>
                    setSelectedDocs((cur) =>
                      cur.includes(d.id) ? cur.filter((x) => x !== d.id) : [...cur, d.id]
                    )
                  }
                  className={`pill whitespace-nowrap ${
                    active ? "bg-brand-600/20 border-brand-500 text-brand-200" : ""
                  }`}
                >
                  {d.filename}
                </button>
              );
            })
          )}
        </div>
      )}

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {isEmpty && (
            <div className="text-center py-16">
              <Sparkles className="h-10 w-10 text-brand-500 mx-auto mb-3" />
              <h2 className="text-2xl font-semibold text-white mb-2">What do you want to research?</h2>
              <p className="text-slate-400 mb-8">
                Ask anything. The agent will pull from arXiv, the web, Wikipedia, and your uploaded docs.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-2xl mx-auto">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="card p-3 text-left text-sm text-slate-300 hover:border-brand-500/60 hover:bg-slate-800/60 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} msg={m} loading={busy && i === messages.length - 1 && m.role === "assistant" && !m.content} />
          ))}
        </div>
      </div>

      <form onSubmit={onSubmit} className="border-t border-slate-800 bg-slate-950/80 px-4 py-3">
        <div className="max-w-3xl mx-auto">
          {statusLine && (
            <div className="text-[11px] text-slate-500 mb-1.5 px-1 flex items-center gap-1.5">
              {busy && <Loader2 className="h-3 w-3 animate-spin" />}
              {statusLine}
            </div>
          )}
          <div className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder="Ask a research question… (Shift+Enter for newline)"
              rows={1}
              className="input resize-none max-h-40"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()} className="btn-primary h-10 shrink-0">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

function MessageBubble({ msg, loading }: { msg: ChatMsg; loading: boolean }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} animate-slideUp`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-brand-600 text-white"
            : "bg-slate-900 border border-slate-800 text-slate-100"
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap text-[15px]">{msg.content}</div>
        ) : (
          <>
            <div className="markdown text-[15px]">
              {loading && !msg.content ? (
                <span className="text-slate-500 italic">Thinking…</span>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content || " "}</ReactMarkdown>
              )}
            </div>
            {(msg.tools?.length || msg.tokens) && (
              <div className="mt-3 pt-2 border-t border-slate-800 flex flex-wrap gap-2">
                {msg.tools?.map((t, i) => (
                  <span key={i} className="pill">
                    <Wrench className="h-3 w-3" />
                    {t}
                  </span>
                ))}
                {msg.tokens ? <span className="pill">{msg.tokens} tokens</span> : null}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
