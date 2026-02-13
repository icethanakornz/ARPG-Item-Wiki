"""
view_items.py
=============
Advanced item search and display with real-time filtering.
FIXED: Filter reset using version counter - 100% working
FIXED: HTML rendering without whitespace
"""
import streamlit as st
from database import search_items, get_item_by_id, get_all_items_with_details
from database import get_all_item_types, get_all_rarities, get_all_locations, get_all_tiers
from utils import load_css, get_image_base64, get_rarity_color
from models import Item

load_css()

# ----------------------------------------------------------------------
# View Components
# ----------------------------------------------------------------------
def render_card_view(items_data):
    """Render items as beautiful cards."""
    if not items_data:
        return

    cols = st.columns(3)

    for idx, row in enumerate(items_data):
        row_dict = dict(row) if hasattr(row, 'keys') else row
        item = Item.from_db_row(row_dict)

        with cols[idx % 3]:
            img_base64 = get_image_base64(item.image_path)
            if img_base64:
                st.markdown(
                    f'<img src="data:image/png;base64,{img_base64}" '
                    f'style="width:100%; height:200px; object-fit:cover; border-radius:12px 12px 0 0;">',
                    unsafe_allow_html=True
                )

            card_html = f'''<div class="item-card rarity-{item.rarity_name}">
<h3 style="color: {item.rarity_color}; margin-top: 0; margin-bottom: 8px;">{item.name}</h3>
<div style="display: flex; gap: 8px; margin: 8px 0;">
<span style="background: #2A2A2A; padding: 4px 8px; border-radius: 4px;">📦 {item.type_name}</span>
<span style="background: #2A2A2A; padding: 4px 8px; border-radius: 4px;">{item.tier_name}</span>
</div>
<p style="color: #AAA; min-height: 60px; margin: 8px 0;">{item.description[:120]}{'...' if len(item.description) > 120 else ''}</p>
<hr style="margin: 16px 0; border: none; border-top: 1px solid #3A3A3A;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: #f39c12;">📍 {item.location_name}</span>
<span style="color: {item.rarity_color};">{item.rarity_icon} {item.rarity_name}</span>
</div>
</div>'''

            st.markdown(card_html, unsafe_allow_html=True)

            if st.button("🔍 ดูรายละเอียด", key=f"view_{item.id}", use_container_width=True):
                st.session_state.selected_item_id = item.id
                st.session_state.show_detail = True
                st.rerun()

def render_table_view(items_data):
    """Render items as sortable table."""
    if not items_data:
        return

    import pandas as pd

    table_data = []
    for row in items_data:
        row_dict = dict(row) if hasattr(row, 'keys') else row
        item = Item.from_db_row(row_dict)
        table_data.append({
            "ชื่อ": item.name,
            "ประเภท": item.type_name,
            "ความหายาก": f"{item.rarity_icon} {item.rarity_name}",
            "Tier": item.tier_name,
            "สถานที่ดรอป": item.location_name,
            "รายละเอียด": item.description[:50] + "..." if len(item.description) > 50 else item.description,
        })

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ชื่อ": st.column_config.TextColumn("ชื่อ", width="medium"),
            "ความหายาก": st.column_config.TextColumn("ความหายาก", width="small"),
            "รายละเอียด": st.column_config.TextColumn("รายละเอียด", width="large"),
        }
    )

def render_item_detail(item_id):
    """Render detailed view of single item."""
    item_data = get_item_by_id(item_id)

    if not item_data:
        st.error("ไม่พบไอเท็ม")
        return

    item_dict = dict(item_data) if hasattr(item_data, 'keys') else item_data
    item = Item.from_db_row(item_dict)

    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            img_base64 = get_image_base64(item.image_path)
            if img_base64:
                st.markdown(
                    f'<img src="data:image/png;base64,{img_base64}" '
                    f'style="width:100%; border-radius:16px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">',
                    unsafe_allow_html=True
                )

        with col2:
            st.markdown(f"# {item.name}")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""
                <div style="background: #2A2A2A; padding: 12px; border-radius: 8px; text-align: center;">
                    <small>ประเภท</small><br>
                    <strong>{item.type_name}</strong>
                </div>
                """, unsafe_allow_html=True)

            with col_b:
                st.markdown(f"""
                <div style="background: #2A2A2A; padding: 12px; border-radius: 8px; text-align: center;">
                    <small>ความหายาก</small><br>
                    <strong style="color: {item.rarity_color};">{item.rarity_name}</strong>
                </div>
                """, unsafe_allow_html=True)

            with col_c:
                st.markdown(f"""
                <div style="background: #2A2A2A; padding: 12px; border-radius: 8px; text-align: center;">
                    <small>Tier</small><br>
                    <strong>{item.tier_name}</strong>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📖 คำอธิบาย")
            st.markdown(f">{item.description if item.description else 'ไม่มีคำอธิบาย'}")
            st.markdown("---")
            st.markdown(f"**📍 สถานที่ดรอป:** {item.location_name}")

            if item.created_at:
                st.caption(f"เพิ่มเมื่อ: {item.created_at}")
            if item.updated_at:
                st.caption(f"อัปเดตล่าสุด: {item.updated_at}")

        if st.button("← กลับไปค้นหา", use_container_width=True):
            st.session_state.show_detail = False
            st.session_state.selected_item_id = None
            st.rerun()

# ----------------------------------------------------------------------
# Main - FIXED: Version counter for filter reset
# ----------------------------------------------------------------------
def main():
    st.markdown("# 🔍 ค้นหาไอเท็ม")
    st.markdown("---")

    if st.session_state.get('show_detail') and st.session_state.get('selected_item_id'):
        render_item_detail(st.session_state.selected_item_id)
        return

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

    if 'filter_version' not in st.session_state:
        st.session_state.filter_version = 0

    with st.sidebar:
        st.markdown("## 🎯 ตัวกรอง")
        st.markdown("---")

        selected_types = st.multiselect(
            "📦 ประเภทไอเท็ม",
            options=type_names,
            key=f"filter_types_v{st.session_state.filter_version}"
        )

        rarity_options = [r['name'] for r in rarities_list]
        selected_rarities = st.multiselect(
            "⭐ ความหายาก",
            options=rarity_options,
            key=f"filter_rarities_v{st.session_state.filter_version}"
        )

        if selected_rarities:
            colors_html = ""
            for r_name in selected_rarities:
                color = get_rarity_color(r_name)
                colors_html += f'<span style="color:{color};">● {r_name}</span> '
            st.markdown(colors_html, unsafe_allow_html=True)

        selected_locations = st.multiselect(
            "📍 สถานที่ดรอป",
            options=location_names,
            key=f"filter_locations_v{st.session_state.filter_version}"
        )

        selected_tiers = st.multiselect(
            "📊 Tier",
            options=tier_names,
            key=f"filter_tiers_v{st.session_state.filter_version}"
        )

        st.markdown("---")

        if st.button("🔄 ล้างตัวกรอง", use_container_width=True):
            st.session_state.filter_version += 1
            st.rerun()

        st.markdown("### 📊 สถิติ")
        all_items = get_all_items_with_details()
        st.metric("ไอเท็มทั้งหมด", len(all_items))

    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "🔎 ค้นหาชื่อไอเท็ม",
            placeholder="พิมพ์ชื่อไอเท็มที่ต้องการค้นหา...",
            label_visibility="collapsed"
        )

    with col2:
        view_mode = st.radio(
            "รูปแบบ",
            ["📱 การ์ด", "📊 ตาราง"],
            horizontal=True,
            label_visibility="collapsed"
        )

    filters = {}

    if search_query:
        filters['search'] = search_query

    if selected_types:
        filters['type_ids'] = [type_dict[t] for t in selected_types if t in type_dict]

    if selected_rarities:
        rarity_ids = []
        for r_name in selected_rarities:
            if r_name in rarity_dict:
                rarity_ids.append(rarity_dict[r_name])
            else:
                for r in rarities_list:
                    if r['name'] == r_name:
                        rarity_ids.append(r['id'])
                        break
        filters['rarity_ids'] = rarity_ids

    if selected_locations:
        filters['location_ids'] = [location_dict[l] for l in selected_locations if l in location_dict]

    if selected_tiers:
        filters['tier_ids'] = [tier_dict[t] for t in selected_tiers if t in tier_dict]

    items = search_items(filters)

    if not items:
        st.warning("😢 ไม่พบไอเท็มที่ค้นหา")

        if filters:
            st.info("💡 ลองเปลี่ยนคำค้นหาหรือตัวกรอง")

            sample_items = get_all_items_with_details()[:3]
            if sample_items:
                st.markdown("### 🔥 ไอเท็มแนะนำ")
                render_card_view(sample_items)
    else:
        st.success(f"✨ พบ {len(items)} รายการ")

        if view_mode == "📊 ตาราง":
            render_table_view(items)
        else:
            render_card_view(items)

if __name__ == "__main__":
    main()