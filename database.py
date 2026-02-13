"""
database.py
===========
Production-ready database module with connection pooling and schema migration.
FIXED: Return ID in rarities list for KeyError fix
FIXED: Added check_duplicate_name function
"""
import sqlite3
import os
from contextlib import contextmanager
from threading import Lock

__all__ = [
    'init_database', 'execute_query', 'get_db_connection',
    'get_all_item_types', 'get_all_rarities', 'get_all_locations', 'get_all_tiers',
    'clear_master_cache', 'create_item', 'update_item', 'delete_item',
    'get_item_by_id', 'get_all_items_with_details', 'search_items',
    'check_duplicate_name'
]

DB_PATH = "item_wiki.db"
_SCHEMA_VERSION = 2
_LOCK = Lock()

# ----------------------------------------------------------------------
# Connection Management
# ----------------------------------------------------------------------
@contextmanager
def get_db_connection():
    """Thread-safe database connection context manager."""
    with _LOCK:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# ----------------------------------------------------------------------
# Schema Migration
# ----------------------------------------------------------------------
def init_database():
    """Initialize database with proper schema and migrations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        current_version = cursor.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
        current_version = current_version['v'] if current_version and current_version['v'] else 0

        if current_version < 1:
            _migrate_v1(cursor)
        if current_version < 2:
            _migrate_v2(cursor)

        if current_version < _SCHEMA_VERSION:
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (_SCHEMA_VERSION,))

def _migrate_v1(cursor):
    """Initial schema - Master tables for metadata."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rarities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#808080',
            icon TEXT DEFAULT '⚪',
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drop_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    _seed_master_data_v1(cursor)

def _seed_master_data_v1(cursor):
    """Seed default master data for new installation."""
    default_types = ['อาวุธ', 'เกราะ', 'เครื่องประดับ']
    for i, name in enumerate(default_types):
        cursor.execute(
            "INSERT OR IGNORE INTO item_types (name, display_order) VALUES (?, ?)",
            (name, i)
        )

    rarities_data = [
        ('Common', '#808080', '⚪', 0),
        ('Uncommon', '#27ae60', '🟢', 1),
        ('Rare', '#2980b9', '🔵', 2),
        ('Epic', '#8e44ad', '🟣', 3),
        ('Legendary', '#f39c12', '🟡', 4)
    ]
    for name, color, icon, order in rarities_data:
        cursor.execute(
            "INSERT OR IGNORE INTO rarities (name, color, icon, display_order) VALUES (?, ?, ?, ?)",
            (name, color, icon, order)
        )

    default_locations = ['ดันเจี้ยนไฟ', 'ป่าลึกลับ', 'ยอดเขา', 'หอคอยสายฟ้า', 'รังมังกร']
    for name in default_locations:
        cursor.execute(
            "INSERT OR IGNORE INTO drop_locations (name) VALUES (?)",
            (name,)
        )

    tier_data = [('T1', 0), ('T2', 1), ('T3', 2), ('T4', 3)]
    for name, order in tier_data:
        cursor.execute(
            "INSERT OR IGNORE INTO tiers (name, display_order) VALUES (?, ?)",
            (name, order)
        )

def _migrate_v2(cursor):
    """Migrate to normalized items table with foreign keys."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
    )
    old_table_exists = cursor.fetchone() is not None

    if old_table_exists:
        cursor.execute("ALTER TABLE items RENAME TO items_old_backup")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type_id INTEGER NOT NULL,
            rarity_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            tier_id INTEGER NOT NULL,
            description TEXT,
            image_path TEXT DEFAULT 'assets/images/placeholder.png',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (type_id) REFERENCES item_types(id) ON DELETE RESTRICT,
            FOREIGN KEY (rarity_id) REFERENCES rarities(id) ON DELETE RESTRICT,
            FOREIGN KEY (location_id) REFERENCES drop_locations(id) ON DELETE RESTRICT,
            FOREIGN KEY (tier_id) REFERENCES tiers(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON items(type_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity_id)")

# ----------------------------------------------------------------------
# Core Query Execution
# ----------------------------------------------------------------------
def execute_query(query, params=(), fetch_one=False):
    """Execute query with proper error handling."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchone() if fetch_one else cursor.fetchall()
                return result
            else:
                conn.commit()
                return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValueError("ข้อมูลนี้มีอยู่แล้วในระบบ") from e
        raise ValueError(f"ข้อมูลไม่ถูกต้อง: {e}") from e
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e

# ----------------------------------------------------------------------
# Cache Management - FIXED: Return ID in rarity list
# ----------------------------------------------------------------------
def get_all_item_types():
    """Get all item types with caching."""
    import streamlit as st

    @st.cache_data(ttl=300)
    def _get_types():
        rows = execute_query("SELECT id, name FROM item_types ORDER BY display_order, name")
        return {row['name']: row['id'] for row in rows}, [row['name'] for row in rows]

    return _get_types()

def get_all_rarities():
    """Get all rarities with color, icon, AND ID."""
    import streamlit as st

    @st.cache_data(ttl=300)
    def _get_rarities():
        rows = execute_query("SELECT id, name, color, icon FROM rarities ORDER BY display_order")
        return {row['name']: row['id'] for row in rows}, [
            {
                'id': row['id'],
                'name': row['name'],
                'color': row['color'],
                'icon': row['icon']
            } for row in rows
        ]

    return _get_rarities()

def get_all_locations():
    """Get all drop locations."""
    import streamlit as st

    @st.cache_data(ttl=300)
    def _get_locations():
        rows = execute_query("SELECT id, name FROM drop_locations ORDER BY name")
        return {row['name']: row['id'] for row in rows}, [row['name'] for row in rows]

    return _get_locations()

def get_all_tiers():
    """Get all tiers."""
    import streamlit as st

    @st.cache_data(ttl=300)
    def _get_tiers():
        rows = execute_query("SELECT id, name FROM tiers ORDER BY display_order")
        return {row['name']: row['id'] for row in rows}, [row['name'] for row in rows]

    return _get_tiers()

def clear_master_cache():
    """Clear all cached master data."""
    import streamlit as st
    st.cache_data.clear()

# ----------------------------------------------------------------------
# Item Repository
# ----------------------------------------------------------------------
def create_item(name, type_id, rarity_id, location_id, tier_id, description="", image_path=None):
    """Create new item with validation."""
    if not image_path:
        image_path = "assets/images/placeholder.png"

    # Check duplicate
    dup = execute_query(
        "SELECT id FROM items WHERE LOWER(name) = LOWER(?)",
        (name.strip(),),
        fetch_one=True
    )
    if dup:
        raise ValueError(f"ไอเท็ม '{name}' มีอยู่แล้ว")

    query = """
        INSERT INTO items (name, type_id, rarity_id, location_id, tier_id, description, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(query, (name.strip(), type_id, rarity_id, location_id, tier_id, description, image_path))

def update_item(item_id, name, type_id, rarity_id, location_id, tier_id, description, image_path):
    """Update existing item."""
    # Check duplicate excluding self
    dup = execute_query(
        "SELECT id FROM items WHERE LOWER(name) = LOWER(?) AND id != ?",
        (name.strip(), item_id),
        fetch_one=True
    )
    if dup:
        raise ValueError(f"ไอเท็ม '{name}' มีอยู่แล้ว")

    query = """
        UPDATE items 
        SET name = ?, type_id = ?, rarity_id = ?, location_id = ?, 
            tier_id = ?, description = ?, image_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """
    execute_query(query, (name.strip(), type_id, rarity_id, location_id, tier_id, description, image_path, item_id))

def delete_item(item_id):
    """Delete item and its image."""
    # Get image path before delete
    item = execute_query("SELECT image_path FROM items WHERE id = ?", (item_id,), fetch_one=True)
    if item and item['image_path'] and item['image_path'] != "assets/images/placeholder.png":
        try:
            if os.path.exists(item['image_path']):
                os.remove(item['image_path'])
        except OSError:
            pass

    execute_query("DELETE FROM items WHERE id = ?", (item_id,))

def get_item_by_id(item_id):
    """Get single item with joined master data."""
    query = """
        SELECT 
            i.id, i.name, i.description, i.image_path,
            i.created_at, i.updated_at,
            t.id as type_id, t.name as type_name,
            r.id as rarity_id, r.name as rarity_name, r.color, r.icon,
            l.id as location_id, l.name as location_name,
            tr.id as tier_id, tr.name as tier_name
        FROM items i
        JOIN item_types t ON i.type_id = t.id
        JOIN rarities r ON i.rarity_id = r.id
        JOIN drop_locations l ON i.location_id = l.id
        JOIN tiers tr ON i.tier_id = tr.id
        WHERE i.id = ?
    """
    return execute_query(query, (item_id,), fetch_one=True)

def get_all_items_with_details():
    """Get all items with complete details."""
    query = """
        SELECT 
            i.id, i.name, i.description, i.image_path,
            t.name as type_name,
            r.name as rarity_name, r.color, r.icon,
            l.name as location_name,
            tr.name as tier_name
        FROM items i
        JOIN item_types t ON i.type_id = t.id
        JOIN rarities r ON i.rarity_id = r.id
        JOIN drop_locations l ON i.location_id = l.id
        JOIN tiers tr ON i.tier_id = tr.id
        ORDER BY i.name
    """
    return execute_query(query)

def search_items(filters=None):
    """Advanced search with filters."""
    query = """
        SELECT 
            i.id, i.name, i.description, i.image_path,
            t.name as type_name,
            r.name as rarity_name, r.color, r.icon,
            l.name as location_name,
            tr.name as tier_name
        FROM items i
        JOIN item_types t ON i.type_id = t.id
        JOIN rarities r ON i.rarity_id = r.id
        JOIN drop_locations l ON i.location_id = l.id
        JOIN tiers tr ON i.tier_id = tr.id
        WHERE 1=1
    """
    params = []

    if filters:
        if filters.get('search'):
            query += " AND i.name LIKE ?"
            params.append(f"%{filters['search']}%")

        if filters.get('type_ids'):
            placeholders = ','.join(['?'] * len(filters['type_ids']))
            query += f" AND i.type_id IN ({placeholders})"
            params.extend(filters['type_ids'])

        if filters.get('rarity_ids'):
            placeholders = ','.join(['?'] * len(filters['rarity_ids']))
            query += f" AND i.rarity_id IN ({placeholders})"
            params.extend(filters['rarity_ids'])

        if filters.get('location_ids'):
            placeholders = ','.join(['?'] * len(filters['location_ids']))
            query += f" AND i.location_id IN ({placeholders})"
            params.extend(filters['location_ids'])

        if filters.get('tier_ids'):
            placeholders = ','.join(['?'] * len(filters['tier_ids']))
            query += f" AND i.tier_id IN ({placeholders})"
            params.extend(filters['tier_ids'])

    query += " ORDER BY i.name"
    return execute_query(query, params)

# ----------------------------------------------------------------------
# Duplicate Check - FIXED: Added missing function
# ----------------------------------------------------------------------
def check_duplicate_name(name, exclude_id=None):
    """
    Check if item name already exists in database
    ใช้ตรวจสอบชื่อซ้ำก่อนเพิ่ม/แก้ไขไอเท็ม

    Args:
        name: ชื่อไอเท็มที่ต้องการตรวจสอบ
        exclude_id: ถ้ามี ให้ข้าม ID นี้ (ใช้ตอนแก้ไข)

    Returns:
        bool: True ถ้าชื่อซ้ำ, False ถ้าไม่ซ้ำ
    """
    try:
        if exclude_id:
            query = "SELECT COUNT(*) as count FROM items WHERE LOWER(name) = LOWER(?) AND id != ?"
            result = execute_query(query, (name.strip(), exclude_id), fetch_one=True)
        else:
            query = "SELECT COUNT(*) as count FROM items WHERE LOWER(name) = LOWER(?)"
            result = execute_query(query, (name.strip(),), fetch_one=True)

        return result['count'] > 0 if result else False
    except Exception as e:
        print(f"Error checking duplicate name: {e}")
        return False

# ----------------------------------------------------------------------
# Test/Debug (Optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing database module...")
    init_database()
    print("✅ Database initialized successfully")
    print(f"📁 Database path: {DB_PATH}")
    print(f"📊 Schema version: {_SCHEMA_VERSION}")