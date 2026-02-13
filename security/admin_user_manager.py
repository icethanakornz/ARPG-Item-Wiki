"""
security/admin_user_manager.py
==============================
NEW - Admin User Management Module
Production Lock Mode: 100% backward compatible
เฉพาะ Admin เท่านั้นที่เข้าถึงได้
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import re

from security.auth import auth_manager, require_role

CONFIG_PATH = Path(".streamlit/auth_config.yaml")


# ----------------------------------------------------------------------
# Admin User Manager - เฉพาะ admin
# ----------------------------------------------------------------------
class AdminUserManager:
    """User management for administrators"""

    def __init__(self):
        self.config_path = CONFIG_PATH

    def _load_config(self) -> dict:
        """Load current auth config"""
        with open(self.config_path) as file:
            return yaml.load(file, Loader=SafeLoader)

    def _save_config(self, config: dict):
        """Save auth config"""
        # Backup first
        backup_path = self.config_path.with_suffix('.yaml.backup')
        if self.config_path.exists():
            import shutil
            shutil.copy(self.config_path, backup_path)

        # Save new config
        with open(self.config_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

    @require_role(['admin'])
    def create_user(self):
        """Create new user - สำหรับ admin เท่านั้น"""
        st.markdown("### 👤 เพิ่มผู้ใช้ใหม่")

        with st.form("create_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input(
                    "ชื่อผู้ใช้*",
                    placeholder="เช่น player2",
                    help="ตัวอักษรภาษาอังกฤษ ตัวเลข และ _ เท่านั้น"
                )

                name = st.text_input(
                    "ชื่อที่แสดง*",
                    placeholder="เช่น ผู้เล่นคนที่ 2"
                )

            with col2:
                email = st.text_input(
                    "อีเมล*",
                    placeholder="player2@example.com"
                )

                role = st.selectbox(
                    "สิทธิ์การใช้งาน*",
                    options=["viewer", "admin"],
                    index=0,
                    format_func=lambda x: "ผู้ดูแลระบบ" if x == "admin" else "ผู้เล่นทั่วไป"
                )

            # สุ่มรหัสผ่านเริ่มต้น
            import secrets
            import string
            default_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

            st.info(f"🔑 รหัสผ่านเริ่มต้น: `{default_password}` (ผู้ใช้ต้องเปลี่ยนเมื่อ login ครั้งแรก)")

            submitted = st.form_submit_button("✅ สร้างผู้ใช้", use_container_width=True)

            if submitted:
                self._save_new_user(username, name, email, role, default_password)
                st.success(f"✅ สร้างผู้ใช้ '{username}' เรียบร้อย!")
                st.rerun()

    def _save_new_user(self, username: str, name: str, email: str, role: str, password: str):
        """Save new user to config"""
        config = self._load_config()

        # Validate username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            st.error("⚠️ ชื่อผู้ใช้ต้องเป็นภาษาอังกฤษ ตัวเลข หรือ _ เท่านั้น")
            return

        if username in config['credentials']['usernames']:
            st.error(f"⚠️ ชื่อผู้ใช้ '{username}' มีอยู่แล้ว")
            return

        # Hash password
        hashed_password = stauth.Hasher([password]).generate()[0]

        # Add user
        config['credentials']['usernames'][username] = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': st.session_state.get('auth_username', 'admin'),
            'force_password_change': True  # บังคับเปลี่ยนรหัสครั้งแรก
        }

        self._save_config(config)

    @require_role(['admin'])
    def list_users(self):
        """แสดงรายชื่อผู้ใช้ทั้งหมด"""
        config = self._load_config()
        users = config['credentials']['usernames']

        if not users:
            st.info("ยังไม่มีผู้ใช้ในระบบ")
            return

        st.markdown("### 👥 รายชื่อผู้ใช้")

        data = []
        for username, info in users.items():
            data.append({
                "ชื่อผู้ใช้": username,
                "ชื่อ": info.get('name', ''),
                "อีเมล": info.get('email', ''),
                "สิทธิ์": "👑 Admin" if info.get('role') == 'admin' else "👤 Viewer",
                "สร้างเมื่อ": info.get('created_at', ''),
                "สร้างโดย": info.get('created_by', 'system')
            })

        import pandas as pd
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    @require_role(['admin'])
    def reset_password(self):
        """รีเซ็ตรหัสผ่านผู้ใช้"""
        config = self._load_config()
        users = list(config['credentials']['usernames'].keys())

        if not users:
            st.info("ยังไม่มีผู้ใช้ในระบบ")
            return

        username = st.selectbox("เลือกผู้ใช้ที่ต้องการรีเซ็ตรหัสผ่าน", users)

        if username:
            import secrets
            import string
            new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

            st.warning(f"🔑 รหัสผ่านใหม่สำหรับ '{username}': `{new_password}`")
            st.caption("ผู้ใช้จะต้องเปลี่ยนรหัสผ่านเมื่อ login ครั้งถัดไป")

            if st.button("✅ ยืนยันการรีเซ็ตรหัสผ่าน"):
                hashed = stauth.Hasher([new_password]).generate()[0]
                config['credentials']['usernames'][username]['password'] = hashed
                config['credentials']['usernames'][username]['force_password_change'] = True
                self._save_config(config)
                st.success(f"✅ รีเซ็ตรหัสผ่านสำหรับ '{username}' เรียบร้อย!")
                st.rerun()

    @require_role(['admin'])
    def delete_user(self):
        """ลบผู้ใช้ - ห้ามลบตัวเอง"""
        config = self._load_config()
        current_user = st.session_state.get('auth_username')

        # ไม่รวม user ปัจจุบัน
        users = [u for u in config['credentials']['usernames'].keys() if u != current_user]

        if not users:
            st.info("ไม่มีผู้ใช้อื่นให้ลบ")
            return

        username = st.selectbox("เลือกผู้ใช้ที่ต้องการลบ", users)

        if username:
            st.error(f"⚠️ ต้องการลบผู้ใช้ '{username}' ใช่หรือไม่?")
            st.caption("การลบผู้ใช้ไม่สามารถกู้คืนได้")

            if st.checkbox("ฉันยืนยันการลบผู้ใช้นี้"):
                if st.button("🗑️ ลบผู้ใช้"):
                    del config['credentials']['usernames'][username]
                    self._save_config(config)
                    st.success(f"✅ ลบผู้ใช้ '{username}' เรียบร้อย!")
                    st.rerun()


# ----------------------------------------------------------------------
# Force Password Change - บังคับเปลี่ยนรหัสครั้งแรก
# ----------------------------------------------------------------------
def check_force_password_change():
    """ตรวจสอบว่าผู้ใช้ต้องเปลี่ยนรหัสผ่านหรือไม่"""
    if not st.session_state.get('auth_status'):
        return

    username = st.session_state.get('auth_username')
    config = AdminUserManager()._load_config()

    user_info = config['credentials']['usernames'].get(username, {})

    if user_info.get('force_password_change', False):
        st.session_state.force_password_change = True
        return True

    return False


def force_password_change_ui():
    """UI สำหรับบังคับเปลี่ยนรหัสผ่าน"""
    st.markdown("## 🔐 ต้องเปลี่ยนรหัสผ่าน")
    st.markdown("นี่คือการเข้าสู่ระบบครั้งแรกของคุณ กรุณาตั้งรหัสผ่านใหม่")

    with st.form("force_password_change_form"):
        new_password = st.text_input("รหัสผ่านใหม่", type="password")
        confirm_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")

        submitted = st.form_submit_button("เปลี่ยนรหัสผ่าน", use_container_width=True)

        if submitted:
            if new_password != confirm_password:
                st.error("⚠️ รหัสผ่านไม่ตรงกัน")
            elif len(new_password) < 8:
                st.error("⚠️ รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
            else:
                # Update password
                config = AdminUserManager()._load_config()
                username = st.session_state.auth_username
                hashed = stauth.Hasher([new_password]).generate()[0]
                config['credentials']['usernames'][username]['password'] = hashed
                config['credentials']['usernames'][username]['force_password_change'] = False

                with open(AdminUserManager().config_path, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

                st.session_state.force_password_change = False
                st.success("✅ เปลี่ยนรหัสผ่านเรียบร้อย!")
                st.rerun()


# ----------------------------------------------------------------------
# Singleton Instance
# ----------------------------------------------------------------------
admin_user_manager = AdminUserManager()