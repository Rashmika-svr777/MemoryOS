# MemoryOS: AI Employees That Remember, Learn, and Collaborate

Five agents (Sales, Support, Meeting, DevOps, Strategy) share **one persistent memory brain**.
Every interaction is retained; every outcome reinforces or corrects memory; the next answer gets better.

## Status (honest)
| Part | State |
|---|---|
| Backend: memory engine, 5 agents, learning loop, graph, auth, REST API | Built. Memory/agent/auth logic is unit-tested (6 tests pass). |
| `app/main.py` (FastAPI) | Written and syntax-checked, **not yet run** (no network to install FastAPI when built). |
| Hindsight Cloud mirroring | Written against the documented `hindsight-client` (`retain`, `recall`, `reflect`); **untested with a live key**. |
| Groq LLM | Optional; offline composer used without a key. |
| Sample data | Generated: 50 employees, 100 customers, 500 tickets, 100 deals, 300 meetings, 1000 emails, 300 incidents, 200 documents (CSV). |
| Frontend (Next.js 15 + Tailwind + React Flow): Dashboard, Agents, Memory Explorer, Knowledge Graph, dark/light, demo login | Written; **not compiled or run** (no network to `npm install` when built). |
| Predictions, voice, file ingestion, Supabase schema, slides, demo kit | **Not built yet.** |

## Run
Frontend: http://localhost:3000 (Docker Compose starts it), or `cd frontend && npm install && npm run dev`.

```bash
cp .env.example .env        # keys optional
docker compose up --build   # API on :8000, docs at /docs
```
Or locally: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
Tests (no dependencies): `cd backend && python -m unittest discover -s tests -v`
Seed: `cd backend && python seed.py --load`

## The memory model
Each memory has a kind (episodic, outcome, preference, relationship, success, failure, semantic), tags, entities,
**confidence**, **importance**, a **decay** score (exponential, slowed by reinforcement) and a reinforcement count.
Recall score = relevance x confidence x decay x importance x agent bias x outcome boost, so proven fixes rank above
untested ones and failures are surfaced as "avoid". Writes are mirrored to Hindsight when `HINDSIGHT_API_KEY` is set.

## Try the judge demo
```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/demo-login | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s -X POST localhost:8000/api/demo/learning-loop -H "Authorization: Bearer $TOKEN"
```
It asks the Support Agent a question (generic answer), records a failed and a successful fix, asks again
(answer now cites the proven fix and warns against the failed one), then shows the DevOps agent benefiting from the same memory.

## API
`POST /api/auth/demo-login` · `GET /api/agents` · `POST /api/chat` · `POST /api/outcomes` · `POST|GET /api/memories` ·
`DELETE /api/memories/{id}` · `GET /api/search` · `GET /api/graph` · `GET /api/analytics/memory` · `POST /api/demo/learning-loop` · `GET /health`
