import time
import threading
from collections import deque
from dataclasses import dataclass


@dataclass
class RequestRecord:
    timestamp: float
    total_ms: int
    guard_decision: str
    chosen_agent: str | None
    input_tokens: int
    output_tokens: int


class MetricsStore:
    def __init__(self, maxlen: int = 500):
        self._records: deque[RequestRecord] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def record(
        self,
        total_ms: int,
        guard_decision: str,
        chosen_agent: str | None,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        with self._lock:
            self._records.append(RequestRecord(
                timestamp=time.time(),
                total_ms=total_ms,
                guard_decision=guard_decision,
                chosen_agent=chosen_agent,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ))

    def summary(self) -> dict:
        with self._lock:
            records = list(self._records)

        if not records:
            return {
                "total_requests": 0,
                "requests_last_60s": 0,
                "avg_latency_ms": 0,
                "block_rate": 0.0,
                "guard_decisions": {"allowed": 0, "blocked": 0},
                "agent_distribution": {},
                "recent_latencies": [],
                "total_input_tokens": 0,
                "total_output_tokens": 0,
            }

        now = time.time()
        requests_last_60s = sum(1 for r in records if now - r.timestamp <= 60)

        allowed = [r for r in records if r.guard_decision == "allowed"]
        blocked = [r for r in records if r.guard_decision == "not allowed"]

        agent_counts: dict[str, int] = {}
        for r in allowed:
            if r.chosen_agent:
                agent_counts[r.chosen_agent] = agent_counts.get(r.chosen_agent, 0) + 1

        avg_latency = round(sum(r.total_ms for r in records) / len(records))

        recent_latencies = [
            {"ms": r.total_ms, "agent": r.chosen_agent or "blocked"}
            for r in records[-20:]
        ]

        return {
            "total_requests": len(records),
            "requests_last_60s": requests_last_60s,
            "avg_latency_ms": avg_latency,
            "block_rate": round(len(blocked) / len(records) * 100, 1),
            "guard_decisions": {"allowed": len(allowed), "blocked": len(blocked)},
            "agent_distribution": agent_counts,
            "recent_latencies": recent_latencies,
            "total_input_tokens": sum(r.input_tokens for r in records),
            "total_output_tokens": sum(r.output_tokens for r in records),
        }
