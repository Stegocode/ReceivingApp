"""
Owns: integration tests for the SQLite Repository adapter (adapters.db).
Must not: import adapters.sink or adapters.source.
May import: pytest, adapters.db, core.schema, core.errors.

not_measured: Postgres behaviour, concurrent writes, very large datasets,
              WAL-mode crash recovery, schema migration chains beyond v1.
"""

import pytest

from adapters.db import SQLiteRepository
from core.errors import RepositoryError
from core.schema import ReceivingRecord


def _repo(tmp_path) -> SQLiteRepository:
    return SQLiteRepository(db_path=tmp_path / "test.db")


def _record(**kwargs) -> ReceivingRecord:
    defaults: dict = {
        "receiving_id": "REC-001",
        "purchase_order": "PO-001",
        "inventory_id": "INV-001",
        "model_number": "MDL-001",
        "product_category": "Furniture",
        "truck": "T1",
        "stop": "S1",
        "sales_order": "SO-001",
        "product_size": {"w": 30.0, "d": 20.0, "h": 10.0},
        "quantity": 1,
        "match_status": "received",
        "timestamp": "2026-06-19T10:00:00+00:00",
    }
    defaults.update(kwargs)
    return ReceivingRecord(**defaults)


def _item(**kwargs) -> dict:
    defaults: dict = {
        "inventory_id": "INV-001",
        "purchase_order": "PO-001",
        "model_number": "MDL-001",
        "description": None,
        "brand": None,
        "vendor": None,
        "tags": None,
    }
    defaults.update(kwargs)
    return defaults


def test_ensure_schema_idempotent(tmp_path):
    repo = _repo(tmp_path)
    repo._ensure_schema()  # second call — must not raise


def test_upsert_items_twice_produces_one_row(tmp_path):
    repo = _repo(tmp_path)
    repo.upsert_items([_item()])
    repo.upsert_items([_item()])
    rows = repo.get_purchase_order("PO-001")
    assert len(rows) == 1


def test_save_record_then_get_pending(tmp_path):
    repo = _repo(tmp_path)
    repo.save_record(_record())
    pending = repo.get_pending()
    assert len(pending) == 1
    assert pending[0]["receiving_id"] == "REC-001"
    assert pending[0]["emitted"] == 0


def test_was_emitted_false_then_true(tmp_path):
    repo = _repo(tmp_path)
    repo.save_record(_record())
    assert repo.was_emitted("REC-001") is False
    repo.mark_emitted("REC-001")
    assert repo.was_emitted("REC-001") is True


def test_mark_emitted_missing_raises(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(RepositoryError):
        repo.mark_emitted("DOES-NOT-EXIST")


def test_save_record_twice_produces_one_row(tmp_path):
    repo = _repo(tmp_path)
    repo.save_record(_record())
    repo.save_record(_record())
    pending = repo.get_pending()
    assert len(pending) == 1


def test_save_record_after_emit_preserves_emitted(tmp_path):
    # save → emit → re-save: still one row AND was_emitted still True
    repo = _repo(tmp_path)
    repo.save_record(_record())
    repo.mark_emitted("REC-001")
    assert repo.was_emitted("REC-001") is True
    repo.save_record(_record())
    assert len(repo.get_pending()) == 0
    assert repo.was_emitted("REC-001") is True


def test_timestamp_round_trips(tmp_path):
    ts = "2026-06-19T10:00:00+00:00"
    repo = _repo(tmp_path)
    repo.save_record(_record(timestamp=ts))
    pending = repo.get_pending()
    assert pending[0]["timestamp"] == ts
