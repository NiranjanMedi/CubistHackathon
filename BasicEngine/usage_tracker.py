"""In-memory singleton for tracking Claude API usage across the session."""

import threading
from typing import List


class _UsageTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._calls: List[dict] = []

    def record(self, call_stats: dict):
        with self._lock:
            self._calls.append(call_stats)

    def get_stats(self) -> dict:
        with self._lock:
            if not self._calls:
                return {
                    "total_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "avg_latency_ms": 0.0,
                    "calls": [],
                }
            total_in = sum(c["input_tokens"] for c in self._calls)
            total_out = sum(c["output_tokens"] for c in self._calls)
            total_cost = sum(c["cost_usd"] for c in self._calls)
            avg_lat = sum(c["latency_ms"] for c in self._calls) / len(self._calls)
            return {
                "total_calls": len(self._calls),
                "total_input_tokens": total_in,
                "total_output_tokens": total_out,
                "total_cost_usd": round(total_cost, 6),
                "avg_latency_ms": round(avg_lat, 1),
                "calls": list(self._calls),
            }

    def reset(self):
        with self._lock:
            self._calls.clear()


tracker = _UsageTracker()
