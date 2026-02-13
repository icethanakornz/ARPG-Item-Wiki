"""
import_items.py
===============
NEW - Import items from CSV/Excel
Admin only - 100% separate from original code
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from database import (
    create_item, get_all_item_types, get_all_rarities,
    get_all_locations, get_all_tiers, check_duplicate_name  # ✅ OK แล้ว
)
from utils import load_css, refresh_master_data
from security.auth import require_role


# ----------------------------------------------------------------------
# CSV Import Functions
# ----------------------------------------------------------------------
class ItemImporter:
    """Handle item import from CSV/Excel"""

    REQUIRED_COLUMNS = ['name', 'type', 'rarity', 'drop_location', 'tier']
    OPTIONAL_COLUMNS = ['description']

    def __init__(self):
        # Load master data for validation
        self.type_dict, self.type_names = get_all_item_types()
        self.rarity_dict, self.rarities_list = get_all_rarities()
        self.location_dict, self.location_names = get_all_locations()
        self.tier_dict, self.tier_names = get_all_tiers()

        # Create name maps for case-insensitive matching
        self.type_map_lower = {k.lower(): v for k, v in self.type_dict.items()}
        self.rarity_map_lower = {k.lower(): v for k, v in self.rarity_dict.items()}
        self.location_map_lower = {k.lower(): v for k, v in self.location_dict.items()}
        self.tier_map_lower = {k.lower(): v for k, v in self.tier_dict.items()}

    def validate_csv_structure(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate CSV has required columns"""
        df_columns = [col.strip().lower() for col in df.columns]

        missing = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df_columns:
                missing.append(col)

        if missing:
            return False, f"❌ คอลัมน์ที่ขาด: {', '.join(missing)}"

        return True, "✅ โครงสร้างไฟล์ถูกต้อง"

    def validate_row(self, row: dict, row_num: int) -> tuple[bool, list[str]]:
        """Validate single row of data"""
        errors = []

        # Check required fields
        name = str(row.get('name', '')).strip()
        if not name:
            errors.append(f"แถว {row_num}: ไม่มีชื่อไอเท็ม")
        elif len(name) < 2:
            errors.append(f"แถว {row_num}: ชื่อไอเท็มสั้นเกินไป (ต้อง >= 2 ตัวอักษร)")

        # Validate type
        type_name = str(row.get('type', '')).strip()
        type_id = self.type_map_lower.get(type_name.lower())
        if not type_id:
            errors.append(f"แถว {row_num}: ไม่พบประเภท '{type_name}' ในระบบ")

        # Validate rarity
        rarity_name = str(row.get('rarity', '')).strip()
        rarity_id = self.rarity_map_lower.get(rarity_name.lower())
        if not rarity_id:
            errors.append(f"แถว {row_num}: ไม่พบความหายาก '{rarity_name}' ในระบบ")

        # Validate location
        location_name = str(row.get('drop_location', '')).strip()
        location_id = self.location_map_lower.get(location_name.lower())
        if not location_id:
            errors.append(f"แถว {row_num}: ไม่พบสถานที่ดรอป '{location_name}' ในระบบ")

        # Validate tier
        tier_name = str(row.get('tier', '')).strip()
        tier_id = self.tier_map_lower.get(tier_name.lower())
        if not tier_id:
            errors.append(f"แถว {row_num}: ไม่พบ Tier '{tier_name}' ในระบบ")

        # Check duplicate
        if name and check_duplicate_name(name):
            errors.append(f"แถว {row_num}: ไอเท็ม '{name}' มีอยู่แล้วในระบบ")

        return len(errors) == 0, errors

    def import_from_dataframe(self, df: pd.DataFrame) -> dict:
        """Import items from DataFrame"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'success_items': []
        }

        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]

        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 because Excel starts at 1 and header is row 1

            # Validate row
            is_valid, errors = self.validate_row(row, row_num)

            if not is_valid:
                results['failed'] += 1
                results['errors'].extend(errors)
                continue

            try:
                # Get IDs
                type_id = self.type_map_lower[str(row['type']).strip().lower()]
                rarity_id = self.rarity_map_lower[str(row['rarity']).strip().lower()]
                location_id = self.location_map_lower[str(row['drop_location']).strip().lower()]
                tier_id = self.tier_map_lower[str(row['tier']).strip().lower()]

                # Get description (optional)
                description = str(row.get('description', '')).strip() if 'description' in row else ''

                # Create item
                create_item(
                    name=str(row['name']).strip(),
                    type_id=type_id,
                    rarity_id=rarity_id,
                    location_id=location_id,
                    tier_id=tier_id,
                    description=description,
                    image_path=None  # No image for imported items
                )

                results['success'] += 1
                results['success_items'].append(str(row['name']).strip())

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"แถว {row_num}: {str(e)}")

        return results

    def get_master_data_summary(self) -> dict:
        """Get summary of available master data"""
        return {
            'types': len(self.type_dict),
            'rarities': len(self.rarity_dict),
            'locations': len(self.location_dict),
            'tiers': len(self.tier_dict),
            'type_list': list(self.type_dict.keys())[:5],  # Show first 5
            'rarity_list': list(self.rarity_dict.keys()),
            'location_list': list(self.location_dict.keys())[:5],
            'tier_list': list(self.tier_dict.keys())
        }


# ----------------------------------------------------------------------
# Template Generator
# ----------------------------------------------------------------------
def generate_template_csv() -> bytes:
    """Generate template CSV file for download"""
    template_data = {
        'name': ['ดาบแห่งเพลิง', 'เกราะน้ำแข็ง', 'แหวนแห่งโชค'],
        'type': ['อาวุธ', 'เกราะ', 'เครื่องประดับ'],
        'rarity': ['Legendary', 'Epic', 'Rare'],
        'drop_location': ['ดันเจี้ยนไฟ', 'ยอดเขานิรันดร์', 'ป่าลึกลับ'],
        'tier': ['T4', 'T3', 'T2'],
        'description': [
            'ดาบที่เต็มไปด้วยพลังแห่งเพลิง',
            'เกราะที่ทอจากน้ำแข็ง',
            'เพิ่มอัตราคริติคอล 15%'
        ]
    }

    df = pd.DataFrame(template_data)
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')


# ----------------------------------------------------------------------
# Import Page UI
# ----------------------------------------------------------------------
@require_role(['admin'])
def render_import_page():
    """Render import items page - Admin only"""

    st.markdown("## 📥 นำเข้าไอเท็มจากไฟล์")
    st.markdown("---")

    # Initialize importer
    importer = ItemImporter()

    # Show master data status
    with st.expander("📊 ข้อมูลหลักในระบบ", expanded=False):
        summary = importer.get_master_data_summary()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 ประเภท", summary['types'])
            if summary['types'] > 0:
                st.caption(f"เช่น {', '.join(summary['type_list'])}...")

        with col2:
            st.metric("⭐ ความหายาก", summary['rarities'])
            if summary['rarities'] > 0:
                st.caption(f"{', '.join(summary['rarity_list'])}")

        with col3:
            st.metric("📍 สถานที่", summary['locations'])
            if summary['locations'] > 0:
                st.caption(f"เช่น {', '.join(summary['location_list'])}...")

        with col4:
            st.metric("📊 Tier", summary['tiers'])
            if summary['tiers'] > 0:
                st.caption(f"{', '.join(summary['tier_list'])}")

        if summary['types'] == 0 or summary['rarities'] == 0:
            st.warning("⚠️ กรุณาเพิ่มข้อมูลหลัก (ประเภท, ความหายาก) ก่อนนำเข้าไอเท็ม")

    # Template download
    col1, col2 = st.columns([3, 1])
    with col2:
        template_csv = generate_template_csv()
        st.download_button(
            label="📥 ดาวน์โหลด Template CSV",
            data=template_csv,
            file_name="item_import_template.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col1:
        st.markdown("### 1. ดาวน์โหลด Template")
        st.caption("ไฟล์ตัวอย่างสำหรับกรอกข้อมูลไอเท็ม")

    st.markdown("---")

    # File upload
    st.markdown("### 2. อัปโหลดไฟล์ CSV")

    uploaded_file = st.file_uploader(
        "เลือกไฟล์ CSV",
        type=['csv'],
        help="ไฟล์ต้องมีคอลัมน์: name, type, rarity, drop_location, tier (description ไม่จำเป็น)",
        key="import_file_uploader"
    )

    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            # Validate structure
            is_valid, message = importer.validate_csv_structure(df)

            if not is_valid:
                st.error(message)
                st.stop()

            # Show preview
            st.markdown("### 3. ตรวจสอบข้อมูล")
            st.success(f"✅ พบ {len(df)} รายการในไฟล์")

            with st.expander("👁️ แสดงตัวอย่างข้อมูล", expanded=True):
                # Show first 5 rows
                preview_df = df.head(5).copy()

                # Add validation status column
                statuses = []
                for idx, row in preview_df.iterrows():
                    is_valid, errors = importer.validate_row(row, idx + 2)
                    statuses.append("✅" if is_valid else "❌")

                preview_df.insert(0, 'สถานะ', statuses)
                st.dataframe(preview_df, use_container_width=True)

                if len(df) > 5:
                    st.caption(f"แสดง 5 จาก {len(df)} รายการ")

            # Import button
            st.markdown("### 4. ยืนยันการนำเข้า")

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ นำเข้าข้อมูล", type="primary", use_container_width=True):
                    with st.spinner("🔄 กำลังนำเข้าข้อมูล..."):
                        results = importer.import_from_dataframe(df)

                        # Show results
                        st.markdown("---")
                        st.markdown("### 📊 ผลการนำเข้า")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ สำเร็จ", results['success'])
                        with col2:
                            st.metric("❌ ล้มเหลว", results['failed'])
                        with col3:
                            st.metric("📦 รวม", results['success'] + results['failed'])

                        if results['success'] > 0:
                            st.success(f"✅ นำเข้าไอเท็มสำเร็จ {results['success']} รายการ")
                            st.balloons()

                            # Show success items
                            if results['success_items']:
                                with st.expander("📋 รายการที่นำเข้าสำเร็จ"):
                                    for name in results['success_items'][:10]:
                                        st.markdown(f"- {name}")
                                    if len(results['success_items']) > 10:
                                        st.caption(f"และอีก {len(results['success_items']) - 10} รายการ")

                        if results['errors']:
                            st.error(f"❌ พบข้อผิดพลาด {results['failed']} รายการ")
                            with st.expander("📋 รายละเอียดข้อผิดพลาด"):
                                for error in results['errors'][:20]:
                                    st.markdown(f"- {error}")
                                if len(results['errors']) > 20:
                                    st.caption(f"และอีก {len(results['errors']) - 20} ข้อผิดพลาด")

                        # Refresh cache
                        refresh_master_data()

            with col2:
                if st.button("🔄 เลือกไฟล์ใหม่", use_container_width=True):
                    st.rerun()

        except Exception as e:
            st.error(f"❌ ไม่สามารถอ่านไฟล์ได้: {str(e)}")
            st.info("💡 กรุณาตรวจสอบว่าไฟล์เป็น CSV และมี encoding UTF-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    render_import_page()


if __name__ == "__main__":
    main()