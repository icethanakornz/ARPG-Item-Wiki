"""
init_db.py
==========
Database initialization and migration script.
Run this script to set up or migrate the database.
"""
from database import init_database, execute_query
from utils import create_placeholder_image
import sqlite3

def check_existing_data():
    """Check if there's existing data to migrate."""
    try:
        result = execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items_old_backup'",
            fetch_one=True
        )
        return result is not None
    except Exception:
        return False

def migrate_old_data():
    """Migrate data from old schema to new normalized schema."""
    print("🔄 กำลังตรวจสอบข้อมูลเดิม...")

    if not check_existing_data():
        print("ℹ️ ไม่พบข้อมูลเดิมที่ต้อง migrate")
        return

    try:
        old_items = execute_query("SELECT * FROM items_old_backup")

        if not old_items:
            print("ℹ️ ไม่มีข้อมูลในตารางเดิม")
            return

        print(f"✅ พบข้อมูลเดิม {len(old_items)} รายการ กำลัง migrate...")

        type_map = {row['name']: row['id'] for row in execute_query("SELECT id, name FROM item_types")}
        rarity_map = {row['name']: row['id'] for row in execute_query("SELECT id, name FROM rarities")}
        location_map = {row['name']: row['id'] for row in execute_query("SELECT id, name FROM drop_locations")}
        tier_map = {row['name']: row['id'] for row in execute_query("SELECT id, name FROM tiers")}

        migrated = 0
        errors = []

        for old_item in old_items:
            try:
                if old_item['name'].startswith('[TYPE]') or \
                   old_item['name'].startswith('[RARITY]') or \
                   old_item['name'].startswith('[LOCATION]') or \
                   old_item['name'].startswith('[TIER]'):
                    continue

                type_name = old_item['type']
                if type_name not in type_map:
                    new_id = execute_query(
                        "INSERT INTO item_types (name) VALUES (?)",
                        (type_name,)
                    )
                    type_map[type_name] = new_id

                rarity_name = old_item['rarity']
                if rarity_name not in rarity_map:
                    new_id = execute_query(
                        "INSERT INTO rarities (name) VALUES (?)",
                        (rarity_name,)
                    )
                    rarity_map[rarity_name] = new_id

                location_name = old_item['drop_location']
                if location_name not in location_map:
                    new_id = execute_query(
                        "INSERT INTO drop_locations (name) VALUES (?)",
                        (location_name,)
                    )
                    location_map[location_name] = new_id

                tier_name = old_item['tier']
                if tier_name not in tier_map:
                    new_id = execute_query(
                        "INSERT INTO tiers (name) VALUES (?)",
                        (tier_name,)
                    )
                    tier_map[tier_name] = new_id

                execute_query("""
                    INSERT INTO items 
                    (id, name, type_id, rarity_id, location_id, tier_id, 
                     description, image_path, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    old_item['id'],
                    old_item['name'],
                    type_map[type_name],
                    rarity_map[rarity_name],
                    location_map[location_name],
                    tier_map[tier_name],
                    old_item['description'],
                    old_item['image_path'],
                    old_item['created_at'],
                    old_item['updated_at']
                ))

                migrated += 1

            except ValueError as e:
                errors.append(f"Item ID {old_item['id']}: {e}")
            except sqlite3.Error as e:
                errors.append(f"Item ID {old_item['id']}: Database error - {e}")

        print(f"✅ Migrate สำเร็จ {migrated} รายการ")

        if errors:
            print(f"⚠️ มีข้อผิดพลาด {len(errors)} รายการ:")
            for err in errors[:5]:
                print(f"   - {err}")

    except sqlite3.Error as e:
        print(f"❌ เกิดข้อผิดพลาดในการ migrate: {e}")

def main():
    """Main initialization function."""
    print("🎮 ARPG Item Wiki - ระบบจัดการฐานข้อมูล")
    print("=" * 50)

    print("🔄 กำลังสร้างโครงสร้างฐานข้อมูล...")
    init_database()
    print("✅ สร้างโครงสร้างฐานข้อมูลเรียบร้อย")

    print("🔄 กำลังสร้างรูป placeholder...")
    create_placeholder_image()
    print("✅ สร้างรูป placeholder เรียบร้อย")

    migrate_old_data()

    print("=" * 50)
    print("✅ ระบบพร้อมใช้งาน!")
    print("\n📌 วิธีเริ่มต้น:")
    print("   streamlit run app.py")
    print("\n📊 ระบบจัดการข้อมูลหลัก:")
    print("   - ประเภทไอเท็ม")
    print("   - ความหายาก (ปรับสีและไอคอนได้)")
    print("   - สถานที่ดรอป")
    print("   - Tier")
    print("\n🎯 เข้าสู่ระบบได้ที่:")
    print("   http://localhost:8501")

if __name__ == "__main__":
    main()