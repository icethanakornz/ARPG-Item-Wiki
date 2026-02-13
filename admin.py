"""
admin.py
========
Professional admin panel for master data management.
FIXED: Handle sqlite3.Row objects with .get() method
"""
import streamlit as st
from utils import load_css, refresh_master_data

st.set_page_config(layout="wide", page_icon="⚙️", page_title="จัดการข้อมูลหลัก")
load_css()

# ----------------------------------------------------------------------
# Generic Master Data Manager
# ----------------------------------------------------------------------
class MasterDataManager:
    """Generic manager for master data entities."""

    def __init__(self, title, icon, table_name, fields, display_order=False):
        self.title = title
        self.icon = icon
        self.table_name = table_name
        self.fields = fields
        self.display_order = display_order

    def render(self):
        """Render complete management UI."""
        from database import execute_query

        st.markdown(f"### {self.icon} {self.title}")

        col1, col2 = st.columns([2, 1])

        with col2:
            self._render_add_form()

        with col1:
            self._render_list()

    def _render_add_form(self):
        """Render add form."""
        st.markdown("**➕ เพิ่มใหม่**")

        with st.form(f"add_{self.table_name}_form"):
            values = {}
            for field_name, field_type, label, default in self.fields:
                if field_type == "text":
                    values[field_name] = st.text_input(label, placeholder=default)
                elif field_type == "color":
                    values[field_name] = st.color_picker(label, value=default)
                elif field_type == "icon":
                    values[field_name] = st.text_input(label, value=default, help="emoji หรือตัวอักษร")
                elif field_type == "order":
                    values[field_name] = st.number_input(label, min_value=0, value=0)

            submitted = st.form_submit_button("💾 บันทึก", use_container_width=True)

            if submitted:
                self._handle_add(values)

    def _handle_add(self, values):
        """Handle add submission."""
        from database import execute_query

        try:
            name = values.get('name', '').strip()
            if not name:
                st.error("⚠️ กรุณาระบุชื่อ")
                return

            fields = []
            placeholders = []
            params = []

            for field_name, field_type, _, _ in self.fields:
                if field_name in values and values[field_name] is not None:
                    fields.append(field_name)
                    placeholders.append('?')
                    val = values[field_name].strip() if isinstance(values[field_name], str) else values[field_name]
                    params.append(val)

            query = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            execute_query(query, params)

            st.success(f"✅ เพิ่ม '{values['name']}' เรียบร้อย!")
            refresh_master_data()
            st.rerun()

        except ValueError as e:
            st.error(f"⚠️ {e}")
        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")

    def _render_list(self):
        """Render list view with delete buttons."""
        from database import execute_query

        order_by = 'display_order, ' if self.display_order else ''
        query = f"SELECT * FROM {self.table_name} ORDER BY {order_by}name"
        records = execute_query(query)

        if not records:
            st.info(f"ยังไม่มี{self.title}")
            return

        for record in records:
            record_dict = dict(record) if hasattr(record, 'keys') else record

            col_a, col_b = st.columns([3, 1])

            with col_a:
                if self.table_name == 'rarities':
                    color = record_dict.get('color', '#808080')
                    icon = record_dict.get('icon', '⚪')
                    name = record_dict.get('name', '')
                    st.markdown(f"<span style='color:{color};'>{icon} {name}</span>",
                              unsafe_allow_html=True)
                else:
                    name = record_dict.get('name', '')
                    st.markdown(f"• {name}")

                if self.table_name == 'rarities' and record_dict.get('display_order') is not None:
                    st.caption(f"ลำดับ: {record_dict['display_order']}")

            with col_b:
                record_id = record_dict.get('id')
                if record_id and st.button("🗑️", key=f"del_{self.table_name}_{record_id}"):
                    self._handle_delete(record_dict)

    def _handle_delete(self, record):
        """Handle delete with referential integrity check."""
        from database import execute_query

        try:
            record_id = record.get('id')
            record_name = record.get('name', '')

            fk_map = {
                'item_types': 'type_id',
                'rarities': 'rarity_id',
                'drop_locations': 'location_id',
                'tiers': 'tier_id'
            }

            if self.table_name in fk_map:
                fk_field = fk_map[self.table_name]
                count = execute_query(
                    f"SELECT COUNT(*) as c FROM items WHERE {fk_field} = ?",
                    (record_id,),
                    fetch_one=True
                )

                if count and count['c'] > 0:
                    st.error(f"⚠️ ไม่สามารถลบได้: มีไอเท็ม {count['c']} ชิ้นที่ใช้งานอยู่")
                    return

            execute_query(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,))
            st.success(f"✅ ลบ '{record_name}' เรียบร้อย!")
            refresh_master_data()
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ ไม่สามารถลบได้: {e}")

# ----------------------------------------------------------------------
# Main Admin Interface
# ----------------------------------------------------------------------
def main():
    from database import execute_query

    st.markdown("# ⚙️ จัดการข้อมูลหลัก (Admin)")
    st.markdown("---")
    st.caption("จัดการข้อมูลประเภทไอเท็ม ความหายาก สถานที่ดรอป และ Tier")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 ประเภทไอเท็ม",
        "⭐ ความหายาก",
        "📍 สถานที่ดรอป",
        "📊 Tier"
    ])

    with tab1:
        type_manager = MasterDataManager(
            title="จัดการประเภทไอเท็ม",
            icon="📦",
            table_name="item_types",
            fields=[
                ('name', 'text', 'ชื่อประเภท', 'เช่น อาวุธ'),
                ('display_order', 'order', 'ลำดับการแสดง', 0)
            ],
            display_order=True
        )
        type_manager.render()

    with tab2:
        rarity_manager = MasterDataManager(
            title="จัดการความหายาก",
            icon="⭐",
            table_name="rarities",
            fields=[
                ('name', 'text', 'ชื่อความหายาก', 'เช่น Legendary'),
                ('color', 'color', 'สีที่ใช้แสดง', '#808080'),
                ('icon', 'icon', 'ไอคอน', '⚪'),
                ('display_order', 'order', 'ลำดับการแสดง', 0)
            ],
            display_order=True
        )
        rarity_manager.render()

    with tab3:
        location_manager = MasterDataManager(
            title="จัดการสถานที่ดรอป",
            icon="📍",
            table_name="drop_locations",
            fields=[
                ('name', 'text', 'ชื่อสถานที่', 'เช่น ดันเจี้ยนไฟ'),
                ('description', 'text', 'คำอธิบาย', '')
            ],
            display_order=False
        )
        location_manager.render()

    with tab4:
        tier_manager = MasterDataManager(
            title="จัดการ Tier",
            icon="📊",
            table_name="tiers",
            fields=[
                ('name', 'text', 'ชื่อ Tier', 'เช่น T1, T2'),
                ('display_order', 'order', 'ลำดับการแสดง', 0)
            ],
            display_order=True
        )
        tier_manager.render()

    st.markdown("---")
    st.markdown("### 📊 สถานะระบบ")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        count = execute_query("SELECT COUNT(*) as c FROM item_types", fetch_one=True)
        st.metric("📦 ประเภท", count['c'] if count else 0)

    with col2:
        count = execute_query("SELECT COUNT(*) as c FROM rarities", fetch_one=True)
        st.metric("⭐ ความหายาก", count['c'] if count else 0)

    with col3:
        count = execute_query("SELECT COUNT(*) as c FROM drop_locations", fetch_one=True)
        st.metric("📍 สถานที่", count['c'] if count else 0)

    with col4:
        count = execute_query("SELECT COUNT(*) as c FROM tiers", fetch_one=True)
        st.metric("📊 Tier", count['c'] if count else 0)

    with st.expander("⚠️ การบำรุงรักษา"):
        st.warning("การลบข้อมูลหลักอาจส่งผลต่อไอเท็มที่ใช้งานอยู่")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ ลบข้อมูลตัวอย่าง", use_container_width=True):
                st.info("ระบบจะลบเฉพาะข้อมูลที่เพิ่มเติมเข้ามา")

        with col2:
            if st.button("🔄 รีเฟรชแคช", use_container_width=True):
                refresh_master_data()
                st.success("✅ รีเฟรชแคชเรียบร้อย!")
                st.rerun()

if __name__ == "__main__":
    main()