"""
Owns: tests for core/logging_setup.py — _ContextFormatter renders extras, setup installs handler.
Must not: modify logging state permanently; must not perform network calls.
May import: pytest, logging, logging.handlers, pathlib.Path, core.logging_setup
            (_ContextFormatter, setup_logging).
"""

import logging
import logging.handlers

import pytest

from core.logging_setup import _ContextFormatter, setup_logging


@pytest.fixture(autouse=True)
def _restore_root_logger():
    """Snapshot root logger state; restore handlers and level after each test."""
    root = logging.getLogger()
    pre_handlers = list(root.handlers)
    pre_level = root.level
    yield
    for h in list(root.handlers):
        if h not in pre_handlers:
            h.close()
            root.removeHandler(h)
    root.handlers[:] = pre_handlers
    root.setLevel(pre_level)


def test_context_formatter_renders_extra_fields():
    """_ContextFormatter appends extra={} fields as key=value to the log line."""
    rec = logging.LogRecord("n", logging.INFO, "p", 1, "portal.fetch_order.start", None, None)
    rec.po_number = "PO-9"
    out = _ContextFormatter("%(message)s").format(rec)
    assert "po_number=PO-9" in out


def test_setup_logging_installs_rotating_handler_at_correct_path(tmp_path):
    """setup_logging attaches a TimedRotatingFileHandler writing to receiving_app.log."""
    setup_logging(tmp_path)
    root = logging.getLogger()
    file_handlers = [
        h for h in root.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)
    ]
    assert file_handlers, "Expected a TimedRotatingFileHandler on the root logger"
    assert any(h.baseFilename == str(tmp_path / "receiving_app.log") for h in file_handlers)
