# Agent Observability Demo v0.1

**What this is:** A self-contained FastAPI simulation of a utility customer-service agent with in-memory traces, policy-boundary escalation, source citations, and a 5-check eval gate (`deploy` / `block`). No LLM API keys or database required — it demonstrates observability patterns for regulated enterprise agents, not a production deployment.

Related writing: [The Operator Model](https://vaibhavkhandelwal.com/writing/the-operator-model) · [Agent Observability for Boards](https://vaibhavkhandelwal.com/writing/agent-observability-for-boards)

## Live demo

**Live URL:** _Deploy pending — see [Deploy on Render (free)](#deploy-on-render-free) below._

Open the link → try the API at `/docs`, or run the examples below.

## Quick start

### Try it live (recommended)

Visit the live URL above once deployed.

- **API docs:** `/docs` — interactive Swagger UI
- **Run agent:** `POST /api/v1/agents/run`
- **Eval gate:** `POST /api/v1/evals/run`
- **Dashboard:** `GET /api/v1/dashboard`

_Free tier: may sleep after ~15 min idle; first load can take 30–60s._

### Run locally

```bash
git clone https://github.com/vaibhav-dev-arch/agent-observability-demo.git
cd agent-observability-demo
python3 -m pip install -r requirements.txt
python3 app.py
```

Server: **http://127.0.0.1:8090** · API docs: **/docs**

```bash
# Another terminal — CLI walkthrough
python3 scripts/run_demo.py

# Or one shot
bash scripts/run_demo.sh
```

## Deploy on Render (free)

Same pattern as [ai-bcdr-governance](https://github.com/vaibhav-dev-arch/ai-bcdr-governance).

1. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
2. Connect GitHub and select `vaibhav-dev-arch/agent-observability-demo`
3. Render reads [`render.yaml`](render.yaml) automatically:
   - Build: `pip install -r requirements.txt`
   - Start: `python app.py`
   - Health check: `/health`
4. Deploy → copy the `*.onrender.com` URL into this README's Live demo section

**Or Web Service:** **New** → **Web Service** → pick the repo → Python 3, same build/start commands, health check `/health`, plan **Free**.

If the repo doesn't appear: [GitHub Settings → Applications → Render](https://github.com/settings/installations) → grant access to `agent-observability-demo`.

### Deployment notes

- The app binds to `0.0.0.0` and reads `PORT` from the environment (Render injects this automatically).
- **Traces are in-memory only** — lost on restart or redeploy. Expected for v0.1 demo, not a bug.
- No environment variables required.

## Tech stack (verified June 2026)

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| FastAPI | ≥0.104.0 |
| Uvicorn | ≥0.24.0 |
| Pydantic | ≥2.5.0 |
| pytest | ≥7.0 (dev) |

Traces are **in-memory only** (lost on restart). v0.2 will add OTLP export, SQLite persistence, and an HTML trace viewer.

## Tests

```bash
python3 -m pip install -r requirements-dev.txt
pytest
```

All 5 tests should pass (health, agent run, traces, eval gate).

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/dashboard` | Summary |
| POST | `/api/v1/agents/run` | Run stub utility CS agent |
| GET | `/api/v1/agents/traces` | List traces |
| GET | `/api/v1/agents/traces/{id}` | Trace detail |
| GET | `/api/v1/metrics` | Metrics summary |
| POST | `/api/v1/evals/run` | Eval gate on a trace |
| GET | `/api/v1/evals` | List eval results |

## Example

```bash
# Local or replace host with your *.onrender.com URL
curl -s -X POST http://127.0.0.1:8090/api/v1/agents/run \
  -H 'Content-Type: application/json' \
  -d '{"query":"Is there a power outage?","account_zip":"90210"}' | jq

curl -s -X POST http://127.0.0.1:8090/api/v1/evals/run \
  -H 'Content-Type: application/json' \
  -d '{"trace_id":"<TRACE_ID>"}' | jq
```

## What it demonstrates

- **Telemetry** — full decision-path trace (intent → retrieval → policy → action/escalation)
- **Governance** — credit/refund requests escalate; agent cannot exceed action boundary
- **Citations** — sources logged on retrieval and response
- **Eval gate** — 5 checks → score + `deploy` / `block` recommendation

## Project structure

```
agent-observability-demo/
├── app.py
├── agent_observability_demo/
│   ├── api.py
│   ├── observability.py
│   ├── stub_agent.py
│   └── evals.py
├── scripts/run_demo.py, run_demo.sh
├── tests/test_demo.py
├── requirements.txt
└── render.yaml
```

## Related

- [ai-bcdr-governance](https://github.com/vaibhav-dev-arch/ai-bcdr-governance) — calibrated autonomy + evidence trail (Pillar 3)
- [Synerim](https://synerim.com) — production AI for regulated enterprise
- [Vaibhav Khandelwal](https://vaibhavkhandelwal.com/writing) — operator-grade writing on production AI

## v0.2 roadmap

- OpenTelemetry export (OTLP)
- SQLite trace persistence
- HTML trace viewer
- Optional real LLM tracing (env flag)
