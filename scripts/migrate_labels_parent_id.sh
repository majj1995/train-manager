#!/bin/bash
set -e

echo "=== 数据库迁移：labels 表添加 parent_id 列 ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT/backend"

python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SHOW COLUMNS FROM labels LIKE \"parent_id\"'))
    if result.fetchall():
        print('parent_id column already exists, skipping.')
    else:
        conn.execute(text('ALTER TABLE labels ADD COLUMN parent_id INT NULL'))
        conn.execute(text('ALTER TABLE labels ADD CONSTRAINT fk_labels_parent_id FOREIGN KEY (parent_id) REFERENCES labels(id)'))
        conn.commit()
        print('parent_id column and FK added successfully.')
"
