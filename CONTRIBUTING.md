# Contributing

Thanks for taking the time to contribute!

## Quick setup

```bash
git clone https://github.com/Sanjoy-Chattopadhay/AI_Research-Agent.git
cd AI_Research-Agent
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # add at least one provider key
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`, so the React
app at <http://localhost:5173> talks to the FastAPI backend transparently.

## Running tests

```bash
pytest -q                 # backend
cd frontend && npm run build  # frontend type-check + bundle
```

## Pull requests

- Keep PRs focused — one feature or fix per PR.
- Add or update tests when you change behaviour.
- Run `pytest` and `npm run build` locally before pushing.
- Format Python with `ruff format` if you have it; keep TS/TSX clean.

## Reporting bugs

Open an issue with reproduction steps, expected vs. actual behaviour, and any
relevant log output. Screenshots help for UI bugs.
