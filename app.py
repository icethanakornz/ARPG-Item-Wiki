"""
app.py
======
Main application entry point with professional dashboard.
SECURITY INTEGRATED - Production Ready
FIXED: Viewer cannot access manage and admin pages
FIXED: Logout error handling
"""
import streamlit as st

from database import init_database, get_all_items_with_details, execute_query
from utils import load_css, create_placeholder_image

try:
    from security.middleware import security_headers
    from security.auth import auth_manager
    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    print("⚠️ Security module not loaded - running in development mode")

st.set_page_config(
    page_title="Item Wiki - ARPG Database",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()
create_placeholder_image()

if SECURITY_ENABLED:
    security_headers.inject_headers()
    security_headers.initialize_session()

if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

PAGES = {
    "🏠 หน้าหลัก": "home",
    "🔍 ค้นหาไอเท็ม": "view",
    "📝 จัดการไอเท็ม": "manage",
    "⚙️ จัดการข้อมูลหลัก": "admin",
    "👥 จัดการผู้ใช้": "users"
}

def main():
    st.sidebar.markdown("# 🎮 ARPG Item Wiki")
    st.sidebar.markdown("---")

    if SECURITY_ENABLED:
        if not auth_manager.is_authenticated():
            st.sidebar.warning("🔒 กรุณาเข้าสู่ระบบ")
        else:
            user = auth_manager.get_current_user()
            if user:
                role_icon = "👑" if user['role'] == 'admin' else "👤"
                st.sidebar.success(f"{role_icon} {user['name']} ({user['role']})")

        auth_manager.login_widget("sidebar")
        auth_manager.logout_button("sidebar")
        st.sidebar.markdown("---")

    selection = st.sidebar.radio(
        "เมนู",
        list(PAGES.keys()),
        index=0
    )

    page = PAGES[selection]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 สถานะระบบ")

    items = get_all_items_with_details()
    st.sidebar.metric("ไอเท็มในระบบ", f"{len(items)} ชิ้น")

    legendary_count = execute_query(
        "SELECT COUNT(*) as c FROM items i JOIN rarities r ON i.rarity_id = r.id WHERE r.name = 'Legendary'",
        fetch_one=True
    )['c']

    st.sidebar.metric("ตำนาน", f"{legendary_count} ชิ้น", delta="✨")

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 ARPG Item Wiki V.1")

    # ===== FIXED: Page Access Control =====
    if SECURITY_ENABLED:
        if page in ['manage', 'admin', 'users']:
            if not auth_manager.is_authenticated():
                st.warning("🔒 กรุณาเข้าสู่ระบบก่อนใช้งานส่วนนี้")
                page = "home"
            elif page in ['manage', 'admin', 'users'] and not auth_manager.has_role('admin'):
                st.error("🚫 เฉพาะ Admin เท่านั้นที่เข้าถึงหน้านี้ได้")
                page = "home"

    if page == "home":
        show_home_page()
    elif page == "view":
        from view_items import main as view_main
        view_main()
    elif page == "manage":
        from manage_items import main as manage_main
        manage_main()
    elif page == "admin":
        from admin import main as admin_main
        admin_main()
    elif page == "users" and SECURITY_ENABLED:
        from admin_panel import main as admin_panel_main
        admin_panel_main()

def show_home_page():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("# 🎮")
    with col2:
        st.markdown("# ARPG Item Database")
        st.markdown("ระบบฐานข้อมูลไอเท็มสำหรับนักผจญภัย")

    st.markdown("---")

    if SECURITY_ENABLED and auth_manager.is_authenticated():
        user = auth_manager.get_current_user()
        st.markdown(f"## 👋 ยินดีต้อนรับ, {user['name']}!")
    else:
        st.markdown("## 👋 ยินดีต้อนรับ!")
        st.markdown("กรุณาเข้าสู่ระบบเพื่อจัดการไอเท็ม")

    st.markdown("""
    ระบบฐานข้อมูลไอเท็มสำหรับเกม ARPG รองรับการค้นหา เพิ่ม แก้ไข และลบไอเท็ม
    
    ### ✨ ความสามารถหลัก:
    - 🔍 **ค้นหาไอเท็มขั้นสูง** - ค้นหาตามชื่อ, ประเภท, ความหายาก, สถานที่ดรอป, Tier
    - 📝 **จัดการไอเท็ม** - เพิ่ม, แก้ไข, ลบไอเท็ม พร้อมระบบอัปโหลดรูปภาพ
    - ⚙️ **จัดการข้อมูลหลัก** - ปรับแต่งประเภท, ความหายาก, สถานที่ดรอป, Tier
    - 👥 **จัดการผู้ใช้** - สำหรับ Admin (สร้างผู้ใช้, เปลี่ยนรหัสผ่าน)
    """)

    st.markdown("---")
    st.markdown("## 📊 สถิติระบบ")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_items = execute_query("SELECT COUNT(*) as c FROM items", fetch_one=True)['c']
        st.metric("📦 ไอเท็มทั้งหมด", f"{total_items:,} ชิ้น")

    with col2:
        total_types = execute_query("SELECT COUNT(*) as c FROM item_types", fetch_one=True)['c']
        st.metric("📋 ประเภท", f"{total_types} ชนิด")

    with col3:
        total_rarities = execute_query("SELECT COUNT(*) as c FROM rarities", fetch_one=True)['c']
        st.metric("⭐ ความหายาก", f"{total_rarities} ระดับ")

    with col4:
        total_locations = execute_query("SELECT COUNT(*) as c FROM drop_locations", fetch_one=True)['c']
        st.metric("📍 สถานที่", f"{total_locations} แห่ง")

    st.markdown("---")
    st.markdown("## 🔥 ไอเท็มล่าสุด")

    recent_items = execute_query("""
        SELECT 
            i.id, i.name, i.image_path,
            t.name as type_name,
            r.name as rarity_name, r.color, r.icon,
            l.name as location_name
        FROM items i
        JOIN item_types t ON i.type_id = t.id
        JOIN rarities r ON i.rarity_id = r.id
        JOIN drop_locations l ON i.location_id = l.id
        ORDER BY i.created_at DESC
        LIMIT 6
    """)

    if recent_items:
        cols = st.columns(3)
        for idx, item in enumerate(recent_items):
            with cols[idx % 3]:
                from utils import get_image_base64
                img_base64 = get_image_base64(item['image_path'])
                if img_base64:
                    st.markdown(
                        f'<img src="data:image/png;base64,{img_base64}" style="width:100%; height:150px; object-fit:cover; border-radius:8px;">',
                        unsafe_allow_html=True
                    )

                st.markdown(f"""
                <div style="background: #1E1E1E; padding: 12px; border-radius: 0 0 8px 8px; margin-bottom: 16px;">
                    <strong style="color: {item['color']};">{item['icon']} {item['name']}</strong><br>
                    <small>{item['type_name']} • {item['location_name']}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีไอเท็มในระบบ")

if __name__ == "__main__":
    main()