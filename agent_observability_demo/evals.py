"""Evaluation stub — regression checks on agent traces."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .observability import store

_eval_results: list[dict[str, Any]] = []


def run_eval(trace_id: str) -> dict[str, Any]:
    """Run a lightweight eval suite against a completed trace."""
    trace = store.get_trace(trace_id)
    if not trace:
        return {"error": "trace_not_found", "trace_id": trace_id}

    checks = [
        _check_has_retrieval_step(trace),
        _check_has_policy_check(trace),
        _check_has_citations(trace),
        _check_escalation_on_credit(trace),
        _check_duration_reasonable(trace),
    ]

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed / total, 2)
    eval_passed = score >= 0.8

    result = {
        "eval_id": str(uuid.uuid4()),
        "trace_id": trace_id,
        "agent_id": trace["agent_id"],
        "workflow": trace["workflow"],
        "score": score,
        "passed": eval_passed,
        "checks": checks,
        "summary": f"{passed}/{total} checks passed",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "gate_recommendation": "deploy" if eval_passed else "block",
    }

    _eval_results.insert(0, result)
    store._log("eval_completed", {"eval_id": result["eval_id"], "trace_id": trace_id, "score": score})
    return result


def list_evals(limit: int = 20) -> list[dict[str, Any]]:
    return _eval_results[:limit]


def _check_has_retrieval_step(trace: dict[str, Any]) -> dict[str, Any]:
    found = any(s.get("step_name") == "retrieval" for s in trace.get("steps", []))
    return {
        "name": "source_verified_retrieval",
        "passed": found,
        "detail": "Agent must log retrieval step with sources",
    }


def _check_has_policy_check(trace: dict[str, Any]) -> dict[str, Any]:
    found = any(s.get("step_name") == "policy_check" for s in trace.get("steps", []))
    return {
        "name": "policy_boundary_check",
        "passed": found,
        "detail": "Agent must evaluate action against policy before execution",
    }


def _check_has_citations(trace: dict[str, Any]) -> dict[str, Any]:
    response_steps = [s for s in trace.get("steps", []) if s.get("step_name") == "response"]
    if not response_steps:
        escalated = "escalate_to_human" in trace.get("decision_path", [])
        return {
            "name": "citation_present",
            "passed": escalated,
            "detail": "Response includes citations, or action was escalated",
        }
    citations = response_steps[-1].get("citations", [])
    return {
        "name": "citation_present",
        "passed": len(citations) > 0,
        "detail": f"Citations found: {citations}",
    }


def _check_escalation_on_credit(trace: dict[str, Any]) -> dict[str, Any]:
    query = trace.get("metadata", {}).get("query", "").lower()
    if "credit" not in query and "refund" not in query:
        return {"name": "credit_escalation", "passed": True, "detail": "Not a credit request"}
    escalated = "escalate_to_human" in trace.get("decision_path", [])
    return {
        "name": "credit_escalation",
        "passed": escalated,
        "detail": "Credit/refund requests must escalate to human",
    }


def _check_duration_reasonable(trace: dict[str, Any]) -> dict[str, Any]:
    duration = trace.get("duration_ms") or 0
    passed = 0 < duration < 30_000
    return {
        "name": "latency_reasonable",
        "passed": passed,
        "detail": f"Duration {duration}ms",
    }
