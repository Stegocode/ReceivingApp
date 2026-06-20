"""
Owns: in-memory ResultSink fake for use in tests.
Must not: perform any API calls.
May import: core.schema.
"""
# Owns: in-memory ResultSink fake.
# Must not: make API calls or import concrete adapters.
# May import: core.schema.

from __future__ import annotations

from core.schema import ReceivingRecord


class FakeResultSink:
    """In-memory ResultSink that deduplicates on receiving_id.

    emit and surface_attention are idempotent: a second call with the same
    receiving_id is a silent no-op (matches the real adapter's _seen guard).
    """

    def __init__(self) -> None:
        self.emitted: list[ReceivingRecord] = []
        self.attention: list[ReceivingRecord] = []
        self._seen: set[str] = set()

    def emit(self, record: ReceivingRecord) -> None:
        if record.receiving_id not in self._seen:
            self._seen.add(record.receiving_id)
            self.emitted.append(record)

    def surface_attention(self, record: ReceivingRecord) -> None:
        if record.receiving_id not in self._seen:
            self._seen.add(record.receiving_id)
            self.attention.append(record)
