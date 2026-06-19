-- Owns: initial database schema for receiving_app.
-- Must not: contain any proprietary names in column or table names.

CREATE TABLE IF NOT EXISTS receiving_items (
    receiving_id     TEXT PRIMARY KEY,
    purchase_order   TEXT NOT NULL,
    inventory_id     TEXT NOT NULL,
    model_number     TEXT NOT NULL,
    product_category TEXT,
    truck            TEXT,
    stop             TEXT,
    sales_order      TEXT,
    product_size     TEXT,            -- JSON blob: {"w": 0, "d": 0, "h": 0}
    quantity         INTEGER NOT NULL DEFAULT 1,
    match_status     TEXT NOT NULL DEFAULT 'no_match',
    timestamp        TEXT NOT NULL,   -- ReceivingRecord.timestamp (receiving event time, ISO-8601)
    emitted          INTEGER NOT NULL DEFAULT 0,  -- 0/1 bool
    created_at       TEXT NOT NULL,   -- row insert time (ISO-8601)
    updated_at       TEXT             -- last update time (ISO-8601)
);

CREATE TABLE IF NOT EXISTS po_inventory (
    inventory_id   TEXT PRIMARY KEY,
    purchase_order TEXT NOT NULL,
    model_number   TEXT NOT NULL,
    description    TEXT,
    brand          TEXT,
    vendor         TEXT,
    tags           TEXT,
    created_at     TEXT NOT NULL
);
