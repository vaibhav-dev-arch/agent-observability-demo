# Agent Observability Demo v0.1

**What this is:** A self-contained FastAPI simulation of a utility customer-service agent with in-memory traces, policy-boundary escalation, source citations, and a 5-check eval gate (`deploy` / `block`). No LLM API keys or database required — it demonstrates observability patterns for regulated enterprise agents, not a production deployment.

Live demo: _Deploy pending — see [Deploy on Render](#deploy-on-render) below._

Related writing: [The Operator Model](https://vaibhavkhandelwal.com/writing/the-operator-model) · [Agent Observability for Boards](https://vaibhavkhandelwal.com/writing/agent-observability-for-boards)

## Tech stack (verified June 2026)

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| FastAPI | ≥0.104.0 |
| Uvicorn | ≥0.24.0 |
| Pydantic | ≥2.5.0 |
| pytest | ≥7.0 (dev) |

Traces are **in-memory only** (lost on restart). v0.2 will add OTLP export, SQLite persistence, and an HTML trace viewer.

## Quick start

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

## Deploy on Render

1. Fork or use this repo: `vaibhav-dev-arch/agent-observability-demo`
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service** → connect repo
3. Runtime: Python 3 · Build: `pip install -r requirements.txt` · Start: `python app.py`
4. Health check path: `/health`

Or use the included `render.yaml` Blueprint.

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

- [Synerim](https://synerim.com) — production AI for regulated enterprise
- [Vaibhav Khandelwal](https://vaibhavkhandelwal.com/writing) — operator-grade writing on production AI

## v0.2 roadmap

- OpenTelemetry export (OTLP)
- SQLite trace persistence
- HTML trace viewer
- Optional real LLM tracing (env flag)
