"""
security/pages/admin_users.py
==============================
NEW - Admin User Management Page
แยกหน้าเฉพาะสำหรับ Admin
"""
import streamlit as st
from security.auth import auth_manager, require_role
from security.admin_user_manager import admin_user_manager, force_password_change_ui, check_force_password_change
from utils import load_css

st.set_page_config(layout="wide", page_icon="👑", page_title="จัดการผู้ใช้")
load_css()


# ----------------------------------------------------------------------
# Main Admin Page
# ----------------------------------------------------------------------
@require_role(['admin'])
def main():
    st.markdown("# 👑 จัดการผู้ใช้ระบบ")
    st.markdown("---")

    # Check if need to change password
    if check_force_password_change():
        force_password_change_ui()
        return

    # Display current user
    user = auth_manager.get_current_user()
    st.sidebar.success(f"👑 Admin: {user['name']}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ เพิ่มผู้ใช้",
        "👥 รายชื่อผู้ใช้",
        "🔄 รีเซ็ตรหัสผ่าน",
        "🗑️ ลบผู้ใช้"
    ])

    with tab1:
        admin_user_manager.create_user()

    with tab2:
        admin_user_manager.list_users()

    with tab3:
        admin_user_manager.reset_password()

    with tab4:
        admin_user_manager.delete_user()

    # Logout button
    st.markdown("---")
    auth_manager.logout_button()


if __name__ == "__main__":
    main()