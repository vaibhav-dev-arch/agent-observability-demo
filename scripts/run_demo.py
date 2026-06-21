#!/usr/bin/env python3
"""CLI demo — run agent, inspect trace, run eval gate."""

from __future__ import annotations

import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8090"


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=10.0)

    print("=== Agent Observability Demo v0.1 ===\n")
    print(f"Health: {client.get('/health').json()}\n")

    print("1) Running utility CS agent — outage inquiry (90210)...")
    run1 = client.post(
        "/api/v1/agents/run",
        json={"query": "Is there a power outage in my area?", "account_zip": "90210"},
    ).json()
    print(json.dumps(run1, indent=2))
    trace1 = run1["trace_id"]

    print("\n2) Running utility CS agent — credit request (should escalate)...")
    run2 = client.post(
        "/api/v1/agents/run",
        json={"query": "I need a credit on my bill", "account_zip": "23220"},
    ).json()
    print(json.dumps(run2, indent=2))

    time.sleep(0.2)

    print(f"\n3) Trace detail for {trace1}...")
    trace = client.get(f"/api/v1/agents/traces/{trace1}").json()
    print(f"   Steps: {len(trace['steps'])} | Decisions: {trace['decision_path']}")

    print(f"\n4) Eval gate on {trace1}...")
    print(json.dumps(client.post("/api/v1/evals/run", json={"trace_id": trace1}).json(), indent=2))

    print(f"\n5) Eval gate on escalated trace {run2['trace_id']}...")
    print(json.dumps(client.post("/api/v1/evals/run", json={"trace_id": run2['trace_id']}).json(), indent=2))

    print("\n6) Dashboard...")
    print(json.dumps(client.get("/api/v1/dashboard").json(), indent=2))
    print("\n✅ Demo complete. Open http://127.0.0.1:8090/docs")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("❌ Start the server first: python app.py", file=sys.stderr)
        sys.exit(1)
