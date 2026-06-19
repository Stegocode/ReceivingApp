"""
Owns: sync loop — poll pending records and emit them through the ResultSink port.
Must not: import concrete adapters; must not call input() or read environment variables.
May import: core.schema, core.errors, core.ports.

PASS criteria:    100% of pending items processed without error.
PARTIAL criteria: success rate >= KILL_THRESHOLD and < 100% — completes, logs warnings.
KILL criteria:    success rate < KILL_THRESHOLD — raises SyncKillError immediately.
"""

from core.errors import SyncKillError  # noqa: F401 — used when success rate < KILL_THRESHOLD

KILL_THRESHOLD = 0.5
