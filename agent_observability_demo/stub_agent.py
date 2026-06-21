"""Stub utility customer-service agent — simulates a governed production workflow."""

from __future__ import annotations

import random
import time
import uuid
from typing import Any

from .observability import MetricType, store

AGENT_ID = "utility-cs-agent-v1"
WORKFLOW = "utility_customer_service"

OUTAGE_KB = {
    "90210": {"status": "no_outage", "eta_restore": None, "source": "grid-status-api/feed-4412"},
    "23220": {
        "status": "active_outage",
        "eta_restore": "2026-06-21T18:30:00Z",
        "source": "grid-status-api/feed-4412",
    },
}

POLICY = {
    "max_auto_actions": ["lookup_outage", "provide_billing_summary"],
    "escalate_actions": ["issue_credit", "modify_account"],
}


def run_customer_service_task(query: str, account_zip: str = "90210") -> dict[str, Any]:
    """Simulate a bounded utility CS agent: retrieve → reason → decide → act or escalate."""
    task_id = str(uuid.uuid4())[:8]
    trace = store.start_trace(
        agent_id=AGENT_ID,
        task_id=task_id,
        workflow=WORKFLOW,
        metadata={"query": query, "account_zip": account_zip, "policy_version": "2026.06"},
    )
    trace_id = trace.trace_id

    try:
        time.sleep(0.05)
        intent = _classify_intent(query)
        store.add_step(trace_id, "intent_classification", {"intent": intent, "confidence": 0.92})
        store.add_decision(trace_id, f"intent={intent}", "Query maps to regulated CS workflow")

        time.sleep(0.08)
        kb_hit = OUTAGE_KB.get(account_zip, OUTAGE_KB["90210"])
        store.add_step(
            trace_id,
            "retrieval",
            {
                "sources": [kb_hit["source"]],
                "citations": [f"grid-status:{account_zip}"],
                "retrieved_fields": list(kb_hit.keys()),
            },
        )

        proposed_action = _propose_action(intent, kb_hit)
        store.add_step(
            trace_id,
            "policy_check",
            {
                "proposed_action": proposed_action,
                "allowed": proposed_action in POLICY["max_auto_actions"],
                "policy": POLICY,
            },
        )

        if proposed_action in POLICY["escalate_actions"]:
            store.add_decision(
                trace_id,
                "escalate_to_human",
                "Action exceeds agent boundary — human operator required",
            )
            response = {
                "answer": "I've found your account information but need a specialist to complete this request.",
                "escalated": True,
                "action_taken": None,
            }
        else:
            store.add_decision(trace_id, f"execute:{proposed_action}", "Within bounded action space")
            time.sleep(0.05)
            response = _execute_action(proposed_action, kb_hit, query)
            store.add_step(trace_id, "response", response)

        store._record_metric(
            "token_cost_usd", round(random.uniform(0.002, 0.008), 4), AGENT_ID, MetricType.GAUGE
        )
        store.end_trace(trace_id, status="completed")

        return {
            "trace_id": trace_id,
            "agent_id": AGENT_ID,
            "task_id": task_id,
            "workflow": WORKFLOW,
            "response": response,
        }

    except Exception as exc:  # pragma: no cover
        store.end_trace(trace_id, status="failed", error=str(exc))
        raise


def _classify_intent(query: str) -> str:
    q = query.lower()
    if "credit" in q or "refund" in q:
        return "credit_request"
    if "outage" in q or "power" in q:
        return "outage_inquiry"
    if "bill" in q or "charge" in q:
        return "billing_inquiry"
    return "general_inquiry"


def _propose_action(intent: str, kb_hit: dict[str, Any]) -> str:
    if intent == "outage_inquiry":
        return "lookup_outage"
    if intent == "billing_inquiry":
        return "provide_billing_summary"
    if intent == "credit_request":
        return "issue_credit"
    return "lookup_outage"


def _execute_action(action: str, kb_hit: dict[str, Any], query: str) -> dict[str, Any]:
    if action == "lookup_outage":
        if kb_hit["status"] == "active_outage":
            return {
                "answer": f"An outage is affecting your area. Estimated restoration: {kb_hit['eta_restore']}.",
                "escalated": False,
                "action_taken": action,
                "citations": [kb_hit["source"]],
            }
        return {
            "answer": "No active outages reported for your service address.",
            "escalated": False,
            "action_taken": action,
            "citations": [kb_hit["source"]],
        }

    return {
        "answer": "Your current balance is $142.18, due July 5. Source: billing-api/ledger.",
        "escalated": False,
        "action_taken": action,
        "citations": ["billing-api/ledger"],
    }
