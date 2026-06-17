"""
Owns: tests for services.sync PASS/PARTIAL/KILL outcome paths.
Must not: import concrete adapters; must not perform real network or DB I/O.
May import: pytest, services.sync, tests.fakes.

not_measured: real network calls, real SQLite file, real result sink API,
              real USB scanner device, real Tkinter UI.

KILL_THRESHOLD = 0.5 (mirrors services/sync.py)
PASS:    100% of pending items succeed — no exception, errors == 0.
PARTIAL: success rate >= KILL_THRESHOLD and < 100% — no exception, errors > 0.
KILL:    success rate < KILL_THRESHOLD — SyncKillError raised.
"""
