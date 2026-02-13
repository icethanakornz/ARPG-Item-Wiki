"""
admin_panel.py
==============
NEW - Admin Panel for User Management
Separate from original admin.py - 100% backward compatible
"""
import streamlit as st
from security.auth import auth_manager, require_role
from security.sanitizer import output_sanitizer
from utils import load_css

st.set_page_config(layout="wide", page_icon="👥", page_title="จัดการผู้ใช้")
load_css()

# ----------------------------------------------------------------------
# Admin Authentication Check
# ----------------------------------------------------------------------
@require_role(['admin'])
def admin_user_management():
    """Admin panel for user management"""

    st.markdown("# 👥 จัดการผู้ใช้ระบบ")
    st.markdown("---")

    if not auth_manager.is_authenticated():
        st.warning("🔒 กรุณาเข้าสู่ระบบ")
        return

    user = auth_manager.get_current_user()
    if user['role'] != 'admin':
        st.error("🚫 เฉพาะ Admin เท่านั้นที่เข้าถึงหน้านี้ได้")
        return

    tab1, tab2 = st.tabs(["👤 สร้างผู้ใช้ใหม่", "📋 รายการผู้ใช้"])

    with tab1:
        st.markdown("### ➕ สร้างผู้ใช้ใหม่")

        with st.form("create_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("ชื่อผู้ใช้*", placeholder="เช่น john.doe")
                password = st.text_input("รหัสผ่าน*", type="password", placeholder="อย่างน้อย 8 ตัว")
                email = st.text_input("อีเมล*", placeholder="user@example.com")

            with col2:
                full_name = st.text_input("ชื่อ-นามสกุล*", placeholder="เช่น จอห์น โด")
                role = st.selectbox("สิทธิ์ผู้ใช้*", ["viewer"], index=0)
                confirm_password = st.text_input("ยืนยันรหัสผ่าน*", type="password")

            submitted = st.form_submit_button("✅ สร้างผู้ใช้", use_container_width=True)

            if submitted:
                errors = []
                if not username or len(username) < 3:
                    errors.append("ชื่อผู้ใช้ต้องมีความยาวอย่างน้อย 3 ตัวอักษร")
                if not password or len(password) < 8:
                    errors.append("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
                if password != confirm_password:
                    errors.append("รหัสผ่านไม่ตรงกัน")
                if not email or '@' not in email:
                    errors.append("กรุณาระบุอีเมลให้ถูกต้อง")
                if not full_name:
                    errors.append("กรุณาระบุชื่อ-นามสกุล")

                if errors:
                    for error in errors:
                        st.error(f"⚠️ {error}")
                else:
                    success, message = auth_manager.create_user(
                        username=username.strip(),
                        password=password,
                        email=email.strip(),
                        name=full_name.strip(),
                        role=role
                    )

                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        st.markdown("### 📋 รายการผู้ใช้ทั้งหมด")

        users = auth_manager.list_users()

        if not users:
            st.info("ยังไม่มีผู้ใช้ในระบบ")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 ผู้ใช้ทั้งหมด", len(users))
            with col2:
                admin_count = len([u for u in users if u['role'] == 'admin'])
                st.metric("👑 Admin", admin_count)
            with col3:
                viewer_count = len([u for u in users if u['role'] == 'viewer'])
                st.metric("👤 Viewer", viewer_count)

            st.markdown("---")

            for user_data in users:
                with st.expander(f"{user_data['username']} - {user_data['name']}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**อีเมล:** {user_data['email']}")
                        st.markdown(f"**สิทธิ์:** {'👑 Admin' if user_data['role'] == 'admin' else '👤 Viewer'}")
                        st.markdown(f"**สร้างเมื่อ:** {user_data['created_at']}")
                        st.markdown(f"**สร้างโดย:** {user_data['created_by']}")

                    with col2:
                        current_user = auth_manager.get_current_user()
                        if (user_data['username'] != current_user['username'] and
                            user_data['role'] != 'admin'):
                            if st.button("🔄 เปลี่ยนรหัส", key=f"reset_{user_data['username']}"):
                                st.session_state.reset_user = user_data['username']
                                st.rerun()

                    if st.session_state.get('reset_user') == user_data['username']:
                        with st.form(f"reset_password_form_{user_data['username']}"):
                            new_password = st.text_input("รหัสผ่านใหม่", type="password")
                            confirm_new = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("✅ ยืนยัน"):
                                    if new_password == confirm_new and len(new_password) >= 8:
                                        success, msg = auth_manager.reset_password(
                                            user_data['username'],
                                            new_password
                                        )
                                        if success:
                                            st.success(msg)
                                            st.session_state.reset_user = None
                                            st.rerun()
                                        else:
                                            st.error(msg)
                                    else:
                                        st.error("⚠️ รหัสผ่านไม่ตรงกันหรือสั้นเกินไป")
                            with col2:
                                if st.form_submit_button("❌ ยกเลิก"):
                                    st.session_state.reset_user = None
                                    st.rerun()

def main():
    admin_user_management()

if __name__ == "__main__":
    main()