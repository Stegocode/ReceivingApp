"""
Owns: Tkinter desktop UI for the barcode scanner receiving workflow.
Must not: import sqlite3, the DB adapter, the result sink adapter, playwright, or selenium.
May import: tkinter, winsound, core.schema, core.errors, services.receive (via injection).

Scope assumptions: single-writer, single-machine, no concurrent users, no browser.
"""
