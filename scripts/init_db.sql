CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL,
    eta TEXT NOT NULL,
    carrier TEXT NOT NULL,
    can_cancel BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_inr INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS session_history (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE session_history ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';
ALTER TABLE session_history ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_session_history_session_created ON session_history(session_id, created_at);

INSERT INTO orders (order_id, customer_name, status, eta, carrier, can_cancel) VALUES
('ORD-001', 'Priya Shah', 'Shipped', '2026-06-18', 'BlueDart', false),
('ORD-002', 'Maya Rao', 'Processing', '2026-06-20', 'DTDC', true),
('ORD-003', 'Aarav Sharma', 'Delivered', 'Delivered on 2026-06-10', 'FedEx', false),
('ORD-004', 'Leena Fernandes', 'Cancelled', 'N/A', 'N/A', false)
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO products (product_id, sku, name, category, price_inr, stock, active) VALUES
('PHONE-A55', 'PRD-101', 'Samsung Galaxy A55', 'phone', 39999, 18, true),
('PHONE-RN13', 'PRD-102', 'Redmi Note 13', 'phone', 17999, 42, true),
('PHONE-M35', 'PRD-103', 'Samsung Galaxy M35', 'phone', 19999, 24, true),
('PHONE-NORDCE4', 'PRD-104', 'OnePlus Nord CE4', 'phone', 24999, 13, true),
('TV-SAM55', 'PRD-201', 'Samsung Crystal 55 inch 4K TV', 'tv', 52999, 9, true),
('TV-LG43', 'PRD-202', 'LG 43 inch 4K WebOS TV', 'tv', 34999, 16, true),
('DECODER-X1', 'PRD-301', 'StreamBox X1 TV Decoder', 'decoder', 3999, 63, true),
('ACC-C65', 'PRD-401', '65 W USB-C Fast Charger', 'accessory', 1499, 75, true)
ON CONFLICT (product_id) DO NOTHING;
