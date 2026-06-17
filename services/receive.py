"""
Owns: process_scan use-case — match a scanned barcode against a purchase order.
Must not: import concrete adapters; must not read environment variables or perform I/O directly.
May import: core.schema, core.matching, core.errors, core.ports.
"""
