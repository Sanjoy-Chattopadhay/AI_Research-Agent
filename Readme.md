# 🔬 AI Research Agent

> A production-grade, multi-agent research assistant that searches the live web, reads arXiv, summarizes Wikipedia, and chats with your own PDFs — powered by **free, open-source LLM providers**.

<p>
  <img alt="Python"   src="https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI"  src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white">
  <img alt="React"    src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white">
  <img alt="Tailwind" src="https://img.shields.io/badge/Tailwind-3-06B6D4?logo=tailwindcss&logoColor=white">
  <img alt="Docker"   src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white">
  <img alt="License"  src="https://img.shields.io/badge/license-MIT-blue">
  <img alt="CI"       src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=github-actions&logoColor=white">
</p>

---

## ✨ What is this?

**AI Research Agent** is an end-to-end full-stack application that lets real users
sign up, ask deep research questions, and watch a tool-using LLM agent
**stream** its answer back in real time — citing sources from the live web, arXiv,
Wikipedia, and the user's own uploaded documents (via RAG).

It is designed to be:

- 💸 **Free to run** — defaults to Groq / OpenRouter / Hugging Face / Ollama. No paid API keys required.
- 🧑‍🤝‍🧑 **Multi-tenant** — JWT auth, per-user conversations, documents, and analytics.
- 🚀 **Deployable in one click** — Docker, Render, Fly.io configs included.
- 🧱 **Cleanly engineered** — modular FastAPI package, typed React app, CI, tests.

> Originally an MTech course project at **NIT Durgapur**, rewritten from scratch
> as a production-grade portfolio app.

---

## 🎬 Features at a glance

| | |
|---|---|
| 🤖 **Tool-calling agent** | Custom ReAct-style loop that plans, calls tools, and answers — no fragile LangChain version pinning. |
| 🔌 **5 LLM providers** | Groq, OpenRouter, Hugging Face, Ollama (local), OpenAI — fully swappable per request. |
| 🌐 **Free research tools** | DuckDuckGo web search, arXiv paper search, Wikipedia, safe Python calculator. |
| 📄 **RAG over your PDFs** | Upload `.pdf`/`.txt`/`.md`, indexed with FAISS + `sentence-transformers/all-MiniLM-L6-v2`. |
| ⚡ **SSE streaming** | Tokens stream into the UI live, with status/tool events shown alongside. |
| 🔐 **Auth & persistence** | bcrypt + JWT, SQLAlchemy + SQLite (Postgres ready). |
| 📊 **Analytics dashboard** | Per-user token, latency, and cost rollups by provider. |
| 🐳 **Docker / CI / Deploy** | Multi-stage Dockerfile, GitHub Actions, Render + Fly configs. |
| 🌑 **Polished UI** | Vite + React + TypeScript + Tailwind, dark-mode native. |

---

## 🏛️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   React + Vite + Tailwind (SPA)              │
│  Landing │ Login │ Chat (SSE) │ History │ Documents │ Stats  │
└───────────────────────────┬──────────────────────────────────┘
                            │ JSON / SSE  (Bearer JWT)
┌───────────────────────────▼──────────────────────────────────┐
│                    FastAPI  (uvicorn, async)                 │
│  /api/auth ▪ /api/chat ▪ /api/conversations ▪ /api/documents │
│  /api/metrics ▪ /api/feedback ▪ /api/health ▪ /api/providers │
├──────────────────────────────────────────────────────────────┤
│   Agent core   →   Tool-calling ReAct loop                   │
│        ├─ providers.py    multi-LLM (OpenAI-compatible)      │
│        ├─ tools.py        web · wiki · arXiv · calc          │
│        └─ rag.py          FAISS + HF embeddings              │
├──────────────────────────────────────────────────────────────┤
│   SQLAlchemy ORM  →  Users · Conversations · Messages ·      │
│                      Documents · Feedback · UsageRecords     │
└─────────┬────────────────────────────────────────────┬───────┘
          ▼                                            ▼
      SQLite / Postgres                         FAISS vector store
                                                (per-document namespace)
```

---

## 🚀 Quickstart

### Prerequisites
- Python **3.11+**
- Node.js **20+**
- (Optional) Docker 24+

### 1. Clone & configure

```bash
git clone https://github.com/Sanjoy-Chattopadhay/AI_Research-Agent.git
cd AI_Research-Agent
cp .env.example .env
```

Then open `.env` and fill in **at least one** of these — all have free tiers:

| Provider     | Get a key                                   | Free tier? |
|--------------|---------------------------------------------|------------|
| **Groq**     | https://console.groq.com                    | ✅ generous, fast |
| OpenRouter   | https://openrouter.ai                       | ✅ free-tier models |
| Hugging Face | https://huggingface.co/settings/tokens      | ✅ rate-limited |
| Ollama       | https://ollama.com (run locally)            | ✅ fully offline |
| OpenAI       | https://platform.openai.com                 | ❌ paid |

```dotenv
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_PROVIDER=groq
SECRET_KEY=please-generate-a-long-random-string-32+chars
```

### 2. Run with Docker (one command)

```bash
docker compose up --build
```

App is live at <http://localhost:8000>. ✅

### 3. Or run locally (dev mode, two terminals)

```bash
# Terminal 1 — backend
python -m venv .venv
.venv\Scripts\activate                # Windows
# source .venv/bin/activate           # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload         # http://localhost:8000

# Terminal 2 — frontend (with hot reload)
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

The Vite dev server proxies `/api/*` to the FastAPI process automatically.

---

## 🧠 Using the agent

1. Open the app, click **Get started**, create an account.
2. Type a research question in chat. The agent will:
   - emit **status** events (which provider, which tool)
   - call tools as needed (web / arXiv / wikipedia / calc)
   - **stream** the final markdown answer back token-by-token
3. To chat with your own papers, go to **Documents → Upload PDF**, then toggle **RAG** in the chat header and select the doc.
4. **History** lists every conversation (re-open, export to Markdown, delete).
5. **Analytics** shows per-provider tokens, latency, and estimated cost.

---

## 📡 API reference (selected)

`POST /api/auth/register`  → `{ access_token, user }`
`POST /api/auth/login`     → `{ access_token, user }`
`GET  /api/auth/me`        → current user

`POST /api/chat`           → non-streaming answer
`POST /api/chat/stream`    → **SSE** stream: `meta`, `status`, `tool`, `token`, `done`, `saved`

`GET  /api/conversations`              → list
`GET  /api/conversations/{id}`         → with messages
`GET  /api/conversations/{id}/export.md`
`DELETE /api/conversations/{id}`

`POST   /api/documents` (multipart)    → upload + index
`GET    /api/documents`                → list
`DELETE /api/documents/{id}`

`GET  /api/metrics`        → per-user usage rollup
`POST /api/feedback`       → 1–5 rating + comment
`GET  /api/health`         → liveness probe
`GET  /api/providers`      → providers configured at runtime

Full interactive docs at **`/api/docs`** (Swagger) and **`/api/redoc`**.

---

## 🛠️ Tech stack

**Backend** &nbsp;FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose · passlib (bcrypt) · slowapi · OpenAI SDK (pointed at Groq/OpenRouter/Ollama/HF/OpenAI) · FAISS · sentence-transformers · pypdf · ddgs · arxiv · wikipedia

**Frontend** &nbsp;React 18 · TypeScript · Vite · Tailwind CSS · React Router · React Query · Zustand · react-markdown · lucide-react · react-hot-toast

**Infra** &nbsp;Docker (multi-stage) · docker-compose · GitHub Actions · Render · Fly.io · Heroku-style Procfile

---

## 📁 Project layout

```
AI_Research-Agent/
├── app/                          # FastAPI backend package
│   ├── main.py                   # app factory, SPA fallback
│   ├── config.py                 # pydantic-settings
│   ├── database.py models.py schemas.py
│   ├── security.py deps.py rate_limit.py logging_config.py
│   ├── agents/
│   │   ├── providers.py          # multi-LLM abstraction
│   │   ├── tools.py              # web / wiki / arxiv / calc
│   │   ├── rag.py                # FAISS + HF embeddings
│   │   └── research_agent.py     # tool-calling ReAct loop
│   └── api/                      # auth, chat, conversations, documents, metrics, health
├── frontend/                     # Vite + React + TS + Tailwind
│   ├── src/pages/                # Landing, Login, Register, Chat, History, Documents, Analytics
│   ├── src/components/Layout.tsx
│   ├── src/api/client.ts         # axios + SSE stream client
│   └── src/store/auth.ts         # Zustand persistent auth
├── tests/                        # pytest (API + tools)
├── .github/workflows/ci.yml      # backend tests · frontend build · docker build
├── Dockerfile docker-compose.yml
├── render.yaml fly.toml Procfile runtime.txt
├── requirements.txt .env.example
├── LICENSE README.md CONTRIBUTING.md
```

---

## 🌐 Deployment

### Render (free tier)
1. Push to GitHub.
2. New Web Service → connect repo → Render detects `render.yaml`.
3. Add `GROQ_API_KEY` (or your provider of choice) in the dashboard.

### Fly.io
```bash
fly launch --copy-config --no-deploy   # uses fly.toml
fly secrets set GROQ_API_KEY=... SECRET_KEY=$(openssl rand -hex 32)
fly volumes create agent_data --size 1
fly deploy
```

### Any Docker host
```bash
docker build -t ai-research-agent .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data ai-research-agent
```

---

## 🧪 Testing

```bash
pytest -q                       # backend
cd frontend && npm run build    # frontend type-check + bundle
docker build -t agent:test .    # full pipeline build
```

---

## 🗺️ Roadmap

- [ ] LangGraph-based multi-agent (Planner / Researcher / Critic)
- [ ] Citations panel with source preview
- [ ] WebSocket streaming with cancellation
- [ ] Per-user API-key vault (BYOK)
- [ ] OAuth (Google / GitHub) login
- [ ] Postgres + pgvector option
- [ ] Voice input via Whisper

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — fastest free LLM inference today
- [OpenRouter](https://openrouter.ai) — universal OpenAI-compatible router
- [Hugging Face](https://huggingface.co) — open-source models & embeddings
- [arXiv](https://arxiv.org) for open scholarly access
- The FastAPI, React, and Tailwind communities

---

## 📝 License

[MIT](./LICENSE) © 2026 Sanjoy Chattopadhyay
