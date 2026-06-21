"""In-memory agent observability — traces, metrics, and logs for the v0.1 demo."""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class AgentTrace:
    trace_id: str
    agent_id: str
    task_id: str
    workflow: str
    start_time: datetime
    end_time: datetime | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    decision_path: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "workflow": self.workflow,
            "start_time": _iso(self.start_time),
            "end_time": _iso(self.end_time),
            "duration_ms": (
                int((self.end_time - self.start_time).total_seconds() * 1000)
                if self.end_time
                else None
            ),
            "steps": self.steps,
            "decision_path": self.decision_path,
            "metadata": self.metadata,
        }


class AgentObservability:
    """Lightweight observability store used by the demo API."""

    def __init__(self) -> None:
        self.traces: dict[str, AgentTrace] = {}
        self.metrics: list[dict[str, Any]] = []
        self.logs: list[dict[str, Any]] = []

    def start_trace(
        self,
        agent_id: str,
        task_id: str,
        workflow: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentTrace:
        trace_id = str(uuid.uuid4())
        trace = AgentTrace(
            trace_id=trace_id,
            agent_id=agent_id,
            task_id=task_id,
            workflow=workflow,
            start_time=_now(),
            metadata=metadata or {},
        )
        self.traces[trace_id] = trace
        self._record_metric("tasks_started", 1, agent_id, MetricType.COUNTER)
        self._log("trace_started", {"trace_id": trace_id, "agent_id": agent_id, "task_id": task_id})
        return trace

    def add_step(self, trace_id: str, step_name: str, data: dict[str, Any]) -> None:
        trace = self.traces.get(trace_id)
        if not trace:
            return
        trace.steps.append({"step_name": step_name, "timestamp": _iso(_now()), **data})

    def add_decision(self, trace_id: str, decision: str, reasoning: str | None = None) -> None:
        trace = self.traces.get(trace_id)
        if not trace:
            return
        trace.decision_path.append(decision)
        trace.steps.append(
            {
                "type": "decision",
                "decision": decision,
                "reasoning": reasoning,
                "timestamp": _iso(_now()),
            }
        )

    def end_trace(self, trace_id: str, status: str = "completed", error: str | None = None) -> None:
        trace = self.traces.get(trace_id)
        if not trace:
            return
        trace.end_time = _now()
        trace.metadata["status"] = status
        if error:
            trace.metadata["error"] = error
            self._record_metric("tasks_failed", 1, trace.agent_id, MetricType.COUNTER)
            self._log("trace_failed", {"trace_id": trace_id, "error": error})
        else:
            duration_ms = int((trace.end_time - trace.start_time).total_seconds() * 1000)
            self._record_metric("task_duration_ms", duration_ms, trace.agent_id, MetricType.HISTOGRAM)
            self._record_metric("tasks_completed", 1, trace.agent_id, MetricType.COUNTER)
            self._log("trace_completed", {"trace_id": trace_id, "duration_ms": duration_ms})

    def list_traces(self, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        traces = list(self.traces.values())
        if agent_id:
            traces = [t for t in traces if t.agent_id == agent_id]
        traces.sort(key=lambda t: t.start_time, reverse=True)
        return [t.to_dict() for t in traces[:limit]]

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        trace = self.traces.get(trace_id)
        return trace.to_dict() if trace else None

    def get_metrics_summary(self, agent_id: str | None = None) -> dict[str, Any]:
        metrics = self.metrics
        if agent_id:
            metrics = [m for m in metrics if m["agent_id"] == agent_id]

        grouped: dict[str, list[float]] = defaultdict(list)
        for metric in metrics:
            grouped[metric["name"]].append(metric["value"])

        summary = {}
        for name, values in grouped.items():
            summary[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 2),
                "latest": values[-1],
            }

        return {"agent_id": agent_id, "metrics": summary, "total_datapoints": len(metrics)}

    def get_dashboard(self) -> dict[str, Any]:
        agent_ids = {t.agent_id for t in self.traces.values()}
        return {
            "total_agents": len(agent_ids),
            "total_traces": len(self.traces),
            "total_evals": len([log for log in self.logs if log["event_type"] == "eval_completed"]),
            "recent_traces": self.list_traces(limit=5),
        }

    def _record_metric(
        self,
        name: str,
        value: float,
        agent_id: str,
        metric_type: MetricType,
        tags: dict[str, str] | None = None,
    ) -> None:
        self.metrics.append(
            {
                "name": name,
                "value": value,
                "agent_id": agent_id,
                "metric_type": metric_type.value,
                "tags": tags or {},
                "timestamp": _iso(_now()),
            }
        )

    def _log(self, event_type: str, data: dict[str, Any]) -> None:
        self.logs.append({"timestamp": _iso(_now()), "event_type": event_type, **data})


store = AgentObservability()
