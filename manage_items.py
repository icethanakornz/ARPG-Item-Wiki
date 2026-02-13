"""
manage_items.py
===============
Item management with proper repository pattern and transaction safety.
FIXED: Dynamic form keys to prevent duplicate key error
"""
import streamlit as st
import os

from database import (
    create_item, update_item, delete_item, get_item_by_id,
    get_all_item_types, get_all_rarities, get_all_locations,
    get_all_tiers, get_all_items_with_details
)
from utils import (
    load_css, save_uploaded_image, delete_image_file,
    get_rarity_color, refresh_master_data, get_image_base64
)
from models import Item

st.set_page_config(layout="wide", page_icon="📝", page_title="จัดการไอเท็ม")
load_css()

# ----------------------------------------------------------------------
# Session State Initialization
# ----------------------------------------------------------------------
def init_session_state():
    """Initialize session state variables."""
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_item_id' not in st.session_state:
        st.session_state.edit_item_id = None
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = {}

init_session_state()

# ----------------------------------------------------------------------
# Form Components - FIXED: Dynamic form key
# ----------------------------------------------------------------------
def render_item_form(item=None, is_edit=False):
    """Render item form with proper data binding."""

    type_dict, type_names = get_all_item_types()
    rarity_dict, rarities_list = get_all_rarities()
    location_dict, location_names = get_all_locations()
    tier_dict, tier_names = get_all_tiers()

    if not type_names:
        type_names = ["อาวุธ"]
        type_dict = {"อาวุธ": 1}
    if not rarities_list:
        rarities_list = [{'id': 1, 'name': 'Common', 'color': '#808080', 'icon': '⚪'}]
        rarity_dict = {'Common': 1}
    if not location_names:
        location_names = ["ดันเจี้ยนไฟ"]
        location_dict = {"ดันเจี้ยนไฟ": 1}
    if not tier_names:
        tier_names = ["T1"]
        tier_dict = {"T1": 1}

    item_id = None
    if is_edit and item:
        item_keys = item.keys() if hasattr(item, 'keys') else []
        item_id = item['id'] if 'id' in item_keys else None

    form_key = f"item_form_{'edit' if is_edit else 'add'}_{item_id if item_id else 'new'}"

    if is_edit and item:
        item_keys = item.keys() if hasattr(item, 'keys') else []
        default_name = item['name'] if 'name' in item_keys else ''
        default_type = item['type_name'] if 'type_name' in item_keys else (type_names[0] if type_names else '')
        default_rarity = item['rarity_name'] if 'rarity_name' in item_keys else (rarities_list[0]['name'] if rarities_list else '')
        default_location = item['location_name'] if 'location_name' in item_keys else (location_names[0] if location_names else '')
        default_tier = item['tier_name'] if 'tier_name' in item_keys else (tier_names[0] if tier_names else '')
        default_desc = item['description'] if 'description' in item_keys else ''
    else:
        default_name = ''
        default_type = type_names[0] if type_names else ''
        default_rarity = rarities_list[0]['name'] if rarities_list else ''
        default_location = location_names[0] if location_names else ''
        default_tier = tier_names[0] if tier_names else ''
        default_desc = ''

    with st.form(form_key):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("ชื่อไอเท็ม*", value=default_name,
                               placeholder="เช่น ดาบแห่งเพลิง")

            type_index = type_names.index(default_type) if default_type in type_names else 0
            item_type = st.selectbox("ประเภทไอเท็ม*", type_names, index=type_index)

            rarity_names = [r['name'] for r in rarities_list]
            rarity_index = rarity_names.index(default_rarity) if default_rarity in rarity_names else 0
            selected_rarity = st.selectbox("ความหายาก*", rarity_names, index=rarity_index)

            rarity_color = get_rarity_color(selected_rarity)
            st.markdown(f"<small style='color:{rarity_color};'>● {selected_rarity}</small>",
                       unsafe_allow_html=True)

        with col2:
            location_index = location_names.index(default_location) if default_location in location_names else 0
            location = st.selectbox("สถานที่ดรอป*", location_names, index=location_index)

            tier_index = tier_names.index(default_tier) if default_tier in tier_names else 0
            tier = st.selectbox("Tier*", tier_names, index=tier_index)

            st.markdown("**รูปภาพ**")
            if is_edit and item:
                item_keys = item.keys() if hasattr(item, 'keys') else []
                image_path = item['image_path'] if 'image_path' in item_keys else None

                if image_path and image_path != "assets/images/placeholder.png":
                    img_base64 = get_image_base64(image_path)
                    if img_base64:
                        st.markdown(f'<img src="data:image/png;base64,{img_base64}" style="width:100px; border-radius:8px;">',
                                  unsafe_allow_html=True)

            image_file = st.file_uploader("อัปโหลดรูปใหม่", type=['png', 'jpg', 'jpeg'])

        description = st.text_area("คำอธิบาย", value=default_desc,
                                 placeholder="ระบุรายละเอียดของไอเท็ม...", height=100)

        col1, col2, col3 = st.columns(3)
        with col1:
            submit_label = "💾 อัปเดต" if is_edit else "💾 บันทึก"
            submitted = st.form_submit_button(submit_label, use_container_width=True)
        with col2:
            if is_edit:
                delete_btn = st.form_submit_button("🗑️ ลบ", use_container_width=True)
            else:
                delete_btn = False
        with col3:
            cancel_btn = st.form_submit_button("↩️ ยกเลิก", use_container_width=True)

        if submitted:
            return {
                'action': 'save',
                'data': {
                    'name': name,
                    'type_id': type_dict[item_type],
                    'rarity_id': rarity_dict[selected_rarity],
                    'location_id': location_dict[location],
                    'tier_id': tier_dict[tier],
                    'description': description,
                    'image_file': image_file
                }
            }

        if delete_btn:
            return {'action': 'delete'}

        if cancel_btn:
            return {'action': 'cancel'}

    return None

# ----------------------------------------------------------------------
# Item Management Pages
# ----------------------------------------------------------------------
def add_item_page():
    """Page for adding new items."""
    st.markdown("### ➤ เพิ่มไอเท็มใหม่")

    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.balloons()
        if st.button("➕ เพิ่มไอเท็มอีกชิ้น"):
            st.session_state.success_message = None
            st.rerun()
        st.markdown("---")

    result = render_item_form(is_edit=False)

    if result:
        if result['action'] == 'save':
            try:
                data = result['data']

                if not data['name'] or len(data['name'].strip()) < 2:
                    st.error("⚠️ กรุณาระบุชื่อไอเท็มอย่างน้อย 2 ตัวอักษร")
                    return

                image_path = None
                if data['image_file']:
                    try:
                        image_path = save_uploaded_image(data['image_file'], data['name'])
                    except ValueError as e:
                        st.error(f"⚠️ {e}")
                        return

                create_item(
                    name=data['name'],
                    type_id=data['type_id'],
                    rarity_id=data['rarity_id'],
                    location_id=data['location_id'],
                    tier_id=data['tier_id'],
                    description=data['description'],
                    image_path=image_path
                )

                st.session_state.success_message = f"✅ เพิ่มไอเท็ม '{data['name']}' เรียบร้อย!"
                refresh_master_data()
                st.rerun()

            except ValueError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")

        elif result['action'] == 'cancel':
            st.rerun()

def edit_item_page():
    """Page for editing/deleting items."""
    st.markdown("### ✏️ แก้ไข/ลบไอเท็ม")

    items = get_all_items_with_details()

    if not items:
        st.info("ℹ️ ยังไม่มีไอเท็มในระบบ")
        return

    item_options = {}
    for item in items:
        if hasattr(item, 'keys'):
            item_id = item['id']
            item_name = item['name']
            rarity_name = item['rarity_name']
        else:
            item_id = item.get('id')
            item_name = item.get('name')
            rarity_name = item.get('rarity_name')

        display_name = f"{item_name} ({rarity_name})"
        item_options[display_name] = item_id

    selected_display = st.selectbox("เลือกไอเท็ม", list(item_options.keys()))

    if selected_display:
        selected_id = item_options[selected_display]
        item_data = get_item_by_id(selected_id)

        if item_data:
            result = render_item_form(item_data, is_edit=True)

            if result:
                if result['action'] == 'save':
                    try:
                        data = result['data']

                        if not data['name'] or len(data['name'].strip()) < 2:
                            st.error("⚠️ กรุณาระบุชื่อไอเท็มอย่างน้อย 2 ตัวอักษร")
                            return

                        item_keys = item_data.keys() if hasattr(item_data, 'keys') else []
                        image_path = item_data['image_path'] if 'image_path' in item_keys else "assets/images/placeholder.png"

                        if data['image_file']:
                            delete_image_file(image_path)
                            try:
                                image_path = save_uploaded_image(data['image_file'], data['name'])
                            except ValueError as e:
                                st.error(f"⚠️ {e}")
                                return

                        update_item(
                            item_id=selected_id,
                            name=data['name'],
                            type_id=data['type_id'],
                            rarity_id=data['rarity_id'],
                            location_id=data['location_id'],
                            tier_id=data['tier_id'],
                            description=data['description'],
                            image_path=image_path
                        )

                        st.session_state.success_message = f"✅ อัปเดต '{data['name']}' เรียบร้อย!"
                        refresh_master_data()
                        st.rerun()

                    except ValueError as e:
                        st.error(f"⚠️ {e}")
                    except Exception as e:
                        st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")

                elif result['action'] == 'delete':
                    if selected_id not in st.session_state.confirm_delete:
                        st.session_state.confirm_delete[selected_id] = True
                        st.warning("⚠️ กด 'ลบ' อีกครั้งเพื่อยืนยัน")
                        st.rerun()
                    else:
                        try:
                            item_keys = item_data.keys() if hasattr(item_data, 'keys') else []
                            item_name = item_data['name'] if 'name' in item_keys else 'ไอเท็ม'

                            delete_item(selected_id)
                            st.session_state.confirm_delete.pop(selected_id, None)
                            st.success(f"🗑️ ลบ '{item_name}' เรียบร้อย!")
                            st.balloons()
                            refresh_master_data()
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ ไม่สามารถลบได้: {e}")

                elif result['action'] == 'cancel':
                    st.rerun()

def bulk_delete_page():
    """Page for bulk deletion with safety."""
    st.markdown("### 🗑️ ลบหลายรายการ")

    items = get_all_items_with_details()

    if not items:
        st.info("ℹ️ ยังไม่มีไอเท็ม")
        return

    total = len(items)
    st.metric("ไอเท็มทั้งหมด", f"{total} ชิ้น")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ เลือกทั้งหมด", use_container_width=True):
            for item in items:
                item_id = item['id'] if hasattr(item, '__getitem__') else item.get('id')
                st.session_state[f"bulk_del_{item_id}"] = True
            st.rerun()
    with col2:
        if st.button("❌ ยกเลิกทั้งหมด", use_container_width=True):
            for item in items:
                item_id = item['id'] if hasattr(item, '__getitem__') else item.get('id')
                if f"bulk_del_{item_id}" in st.session_state:
                    st.session_state.pop(f"bulk_del_{item_id}")
            st.rerun()

    st.markdown("---")

    cols = st.columns(3)
    selected_ids = []

    for idx, item in enumerate(items):
        if hasattr(item, 'keys'):
            item_id = item['id']
            item_name = item['name']
            rarity_name = item['rarity_name']
            color = item['color'] if 'color' in item.keys() else '#808080'
        else:
            item_id = item.get('id')
            item_name = item.get('name')
            rarity_name = item.get('rarity_name')
            color = item['color'] if 'color' in item.keys() else '#808080'

        with cols[idx % 3]:
            checkbox_key = f"bulk_del_{item_id}"
            is_selected = st.checkbox(
                f"{item_name}",
                key=checkbox_key,
                help=f"ความหายาก: {rarity_name}"
            )

            if is_selected:
                selected_ids.append(item_id)

            st.markdown(
                f"<small style='color:{color};'>{rarity_name}</small>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    if selected_ids:
        st.warning(f"เลือก {len(selected_ids)} รายการ")

        if st.button(f"🗑️ ลบ {len(selected_ids)} รายการ", type="primary", use_container_width=True):
            if 'bulk_confirm' not in st.session_state:
                st.session_state.bulk_confirm = True
                st.error("⚠️ กดยืนยันอีกครั้งเพื่อลบ!")
                st.rerun()
            else:
                success_count = 0
                for item_id in selected_ids:
                    try:
                        delete_item(item_id)
                        success_count += 1
                    except Exception:
                        pass

                st.session_state.pop('bulk_confirm', None)
                for item_id in selected_ids:
                    if f"bulk_del_{item_id}" in st.session_state:
                        st.session_state.pop(f"bulk_del_{item_id}")

                st.success(f"✅ ลบ {success_count} รายการเรียบร้อย!")
                st.balloons()
                refresh_master_data()
                st.rerun()

    with st.expander("⚠️ โซนอันตราย"):
        st.warning("การลบทั้งหมดไม่สามารถกู้คืนได้")

        if st.checkbox("ฉันต้องการลบไอเท็มทั้งหมด"):
            if st.button("🗑️ ลบทั้งหมด", use_container_width=True):
                if 'delete_all_confirm' not in st.session_state:
                    st.session_state.delete_all_confirm = True
                    st.error("⚠️⚠️ กดยืนยันอีกครั้ง!")
                    st.rerun()
                else:
                    success_count = 0
                    for item in items:
                        try:
                            item_id = item['id'] if hasattr(item, '__getitem__') else item.get('id')
                            delete_item(item_id)
                            success_count += 1
                        except Exception:
                            pass

                    st.session_state.pop('delete_all_confirm', None)
                    st.success(f"✅ ลบทั้งหมด {success_count} รายการ!")
                    st.balloons()
                    refresh_master_data()
                    st.rerun()


def main():
    st.markdown("# 📝 จัดการไอเท็ม")
    st.markdown("---")

    # FIXED: Add 4th tab for import
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ เพิ่มไอเท็มใหม่",
        "✏️ แก้ไข/ลบไอเท็ม",
        "🗑️ ลบหลายรายการ",
        "📥 นำเข้าไฟล์"  # NEW: Import tab
    ])

    with tab1:
        add_item_page()

    with tab2:
        edit_item_page()

    with tab3:
        bulk_delete_page()

    # NEW: Import tab - Admin only
    with tab4:
        try:
            from import_items import main as import_main
            import_main()
        except ImportError as e:
            st.error(f"⚠️ ไม่สามารถโหลดโมดูลนำเข้าได้: {e}")
        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()