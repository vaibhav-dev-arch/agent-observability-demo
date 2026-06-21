"""Tests for agent observability demo."""

import pytest

from agent_observability_demo.evals import list_evals, run_eval
from agent_observability_demo.observability import store
from agent_observability_demo.stub_agent import run_customer_service_task


@pytest.fixture(autouse=True)
def reset_store():
    store.traces.clear()
    store.metrics.clear()
    store.logs.clear()
    yield


def test_outage_inquiry_completes_with_trace():
    result = run_customer_service_task("Is there an outage?", account_zip="90210")
    trace = store.get_trace(result["trace_id"])
    assert trace is not None
    assert trace["metadata"]["status"] == "completed"
    assert len(trace["steps"]) >= 4
    assert result["response"]["escalated"] is False


def test_credit_request_escalates():
    result = run_customer_service_task("I need a credit on my bill", account_zip="23220")
    trace = store.get_trace(result["trace_id"])
    assert "escalate_to_human" in trace["decision_path"]
    assert result["response"]["escalated"] is True


def test_eval_gate_passes_for_valid_trace():
    result = run_customer_service_task("Is there an outage?", account_zip="90210")
    eval_result = run_eval(result["trace_id"])
    assert eval_result["passed"] is True
    assert eval_result["score"] >= 0.8
    assert eval_result["gate_recommendation"] == "deploy"
    assert len(list_evals()) == 1


def test_eval_missing_trace():
    assert run_eval("does-not-exist")["error"] == "trace_not_found"


def test_metrics_recorded():
    run_customer_service_task("billing question", account_zip="90210")
    summary = store.get_metrics_summary(agent_id="utility-cs-agent-v1")
    assert summary["total_datapoints"] > 0
    assert "tasks_completed" in summary["metrics"]
