"""FastAPI server for the agent observability v0.1 demo."""

from __future__ import annotations

import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .evals import list_evals, run_eval
from .observability import store
from .stub_agent import run_customer_service_task

app = FastAPI(
    title="Agent Observability Demo",
    description=(
        "v0.1 reference demo: LLM agent traces, policy boundaries, "
        "and eval gates for regulated enterprise workflows. No API keys required."
    ),
    version="0.1.0",
)


class RunAgentRequest(BaseModel):
    query: str = Field(..., examples=["Is there a power outage in my area?"])
    account_zip: str = Field(default="90210", examples=["90210", "23220"])


class EvalRequest(BaseModel):
    trace_id: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "demo": "agent-observability-v0.1"}


@app.get("/api/v1/dashboard")
def dashboard() -> dict[str, Any]:
    return store.get_dashboard()


@app.post("/api/v1/agents/run")
def agents_run(body: RunAgentRequest) -> dict[str, Any]:
    return run_customer_service_task(query=body.query, account_zip=body.account_zip)


@app.get("/api/v1/agents/traces")
def agents_traces(agent_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    return {"traces": store.list_traces(agent_id=agent_id, limit=limit)}


@app.get("/api/v1/agents/traces/{trace_id}")
def agents_trace_detail(trace_id: str) -> dict[str, Any]:
    trace = store.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/api/v1/metrics")
def metrics(agent_id: str | None = None) -> dict[str, Any]:
    return store.get_metrics_summary(agent_id=agent_id)


@app.post("/api/v1/evals/run")
def evals_run(body: EvalRequest) -> dict[str, Any]:
    result = run_eval(body.trace_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/evals")
def evals_list(limit: int = 20) -> dict[str, Any]:
    return {"evaluations": list_evals(limit=limit)}


def main() -> None:
    port = int(os.environ.get("PORT", "8090"))
    uvicorn.run("agent_observability_demo.api:app", host="0.0.0.0", port=port, reload=False)
