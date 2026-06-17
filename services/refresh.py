"""
Owns: full DB rebuild use-case — wipe and reload all open orders from source.
Must not: import concrete adapters; must not call input() — the entry point prompts.
May import: core.schema, core.errors, core.ports.
"""
