"""
Owns: T2-8 — conditional credential requirements for source/sink adapter types.
Must not: import concrete adapters or read real credentials from disk.
May import: config (reloaded per test), core.errors, stdlib.

not_measured: real .env file on disk, actual filesystem paths, real adapter
              credentials, real database connections, real network services.
"""
# Owns: T2-8 conditional-credential gating tests (SOURCE_TYPE/SINK_TYPE).
# Must not: import concrete adapters or real credentials.
# May import: config (reloaded), core.errors, stdlib.

from __future__ import annotations

import importlib

import pytest

from core.errors import ConfigError

# All unconditionally-required vars plus fake adapter types as the baseline.
# Tests override SOURCE_TYPE / SINK_TYPE and credentials as needed.
_BASE_ENV = {
    "DB_PATH": "/tmp/test.db",
    "LOG_DIR": "/tmp/logs",
    "DOWNLOAD_DIR": "/tmp/downloads",
    "SOURCE_TYPE": "fake",
    "SINK_TYPE": "null",
    "SINK_BOARD_ID": "board-test",
    "SINK_RECEIVED_GROUP_ID": "grp_recv",
    "SINK_NO_MATCH_GROUP_ID": "grp_nm",
    "SINK_ATTENTION_GROUP_ID": "grp_att",
    "SINK_READY_GROUP_ID": "grp_ready",
    "SINK_INVENTORY_ID_COL": "col_inv",
    "SINK_MODEL_COL": "col_model",
    "SINK_SERIAL_COL": "col_serial",
    "SINK_STATUS_COL": "col_status",
    "RECEIVER_TYPE": "fake",
}

_ALL_ENV_VARS = list(_BASE_ENV.keys()) + [
    "SOURCE_BASE_URL",
    "SOURCE_USERNAME",
    "SOURCE_PASSWORD",
    "SINK_BASE_URL",
    "SINK_API_TOKEN",
    "POLL_INTERVAL_SECS",
    "SCANNER_TYPE",
    "PRINTER_TYPE",
    "FAKE_SOURCE_DATA",
    "RECEIVE_LOCATION",
    "RECEIVE_WHSE_LOCATION",
    "RECEIVE_SCREENSHOT_DIR",
]


def _reload(monkeypatch, env: dict):
    for var in _ALL_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import config

    return importlib.reload(config)


# ── SOURCE credential gating ──────────────────────────────────────────────────


def test_fake_source_no_creds_passes(monkeypatch):
    """SOURCE_TYPE=fake with no USERNAME/PASSWORD — validate() raises no problem."""
    cfg = _reload(monkeypatch, _BASE_ENV)
    cfg.validate(dotenv_path=None)
    assert cfg.SOURCE_TYPE == "fake"


def test_fake_source_no_base_url_passes(monkeypatch):
    """SOURCE_TYPE=fake with no SOURCE_BASE_URL — validate() passes; accessor is ''."""
    cfg = _reload(monkeypatch, _BASE_ENV)
    cfg.validate(dotenv_path=None)
    assert cfg.SOURCE_BASE_URL == ""


def test_portal_source_missing_username_raises(monkeypatch):
    """SOURCE_TYPE=portal without SOURCE_USERNAME — ConfigError names the missing var."""
    env = {
        **_BASE_ENV,
        "SOURCE_TYPE": "portal",
        "SOURCE_BASE_URL": "https://portal.example",
        "SOURCE_PASSWORD": "testpass",
    }
    cfg = _reload(monkeypatch, env)
    with pytest.raises(ConfigError) as exc:
        cfg.validate(dotenv_path=None)
    assert "SOURCE_USERNAME" in str(exc.value)


def test_portal_source_missing_password_raises(monkeypatch):
    """SOURCE_TYPE=portal without SOURCE_PASSWORD — ConfigError names the missing var."""
    env = {
        **_BASE_ENV,
        "SOURCE_TYPE": "portal",
        "SOURCE_BASE_URL": "https://portal.example",
        "SOURCE_USERNAME": "testuser",
    }
    cfg = _reload(monkeypatch, env)
    with pytest.raises(ConfigError) as exc:
        cfg.validate(dotenv_path=None)
    assert "SOURCE_PASSWORD" in str(exc.value)


def test_portal_source_missing_base_url_raises(monkeypatch):
    """SOURCE_TYPE=portal without SOURCE_BASE_URL — ConfigError names the missing var."""
    env = {
        **_BASE_ENV,
        "SOURCE_TYPE": "portal",
        "SOURCE_USERNAME": "testuser",
        "SOURCE_PASSWORD": "testpass",
    }
    cfg = _reload(monkeypatch, env)
    with pytest.raises(ConfigError) as exc:
        cfg.validate(dotenv_path=None)
    assert "SOURCE_BASE_URL" in str(exc.value)


# ── SINK credential gating ────────────────────────────────────────────────────


def test_null_sink_no_token_passes(monkeypatch):
    """SINK_TYPE=null with no SINK_API_TOKEN — validate() raises no problem."""
    cfg = _reload(monkeypatch, _BASE_ENV)
    cfg.validate(dotenv_path=None)
    assert cfg.SINK_TYPE == "null"


def test_null_sink_no_base_url_passes(monkeypatch):
    """SINK_TYPE=null with no SINK_BASE_URL — validate() passes; accessor is ''."""
    cfg = _reload(monkeypatch, _BASE_ENV)
    cfg.validate(dotenv_path=None)
    assert cfg.SINK_BASE_URL == ""


def test_graphql_sink_missing_token_raises(monkeypatch):
    """SINK_TYPE=graphql without SINK_API_TOKEN — ConfigError names the missing var."""
    env = {
        **_BASE_ENV,
        "SINK_TYPE": "graphql",
        "SINK_BASE_URL": "https://api.example.com/v2",
    }
    cfg = _reload(monkeypatch, env)
    with pytest.raises(ConfigError) as exc:
        cfg.validate(dotenv_path=None)
    assert "SINK_API_TOKEN" in str(exc.value)


def test_graphql_sink_missing_base_url_raises(monkeypatch):
    """SINK_TYPE=graphql without SINK_BASE_URL — ConfigError names the missing var."""
    env = {
        **_BASE_ENV,
        "SINK_TYPE": "graphql",
        "SINK_API_TOKEN": "testtoken",
    }
    cfg = _reload(monkeypatch, env)
    with pytest.raises(ConfigError) as exc:
        cfg.validate(dotenv_path=None)
    assert "SINK_BASE_URL" in str(exc.value)


# ── Full real-mode regression guard ──────────────────────────────────────────


def test_full_real_mode_validates(monkeypatch):
    """SOURCE_TYPE=portal + SINK_TYPE=graphql with all creds — validate() passes.

    PASS: validate() returns without raising; accessors populated.
    KILL: validate() raises, or any accessor is wrong.
    not_measured: real network, real DB, actual .env on disk.
    """
    env = {
        **_BASE_ENV,
        "SOURCE_TYPE": "portal",
        "SOURCE_BASE_URL": "https://portal.example",
        "SOURCE_USERNAME": "user",
        "SOURCE_PASSWORD": "pass",
        "SINK_TYPE": "graphql",
        "SINK_BASE_URL": "https://api.example.com/v2",
        "SINK_API_TOKEN": "token",
    }
    cfg = _reload(monkeypatch, env)
    cfg.validate(dotenv_path=None)
    assert cfg.SOURCE_TYPE == "portal"
    assert cfg.SOURCE_USERNAME == "user"
    assert cfg.SINK_TYPE == "graphql"
    assert cfg.SINK_API_TOKEN == "token"
