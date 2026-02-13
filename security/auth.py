"""
security/auth.py
================
PRODUCTION - Authentication and Authorization Module
FIXED: Logout button error when clicked twice
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Literal, Dict, Any
import secrets

CONFIG_PATH = Path(".streamlit/auth_config.yaml")
UserRole = Literal["admin", "viewer"]

class AuthManager:
    """Authentication manager - ทำงานแยกจากของเดิม completely"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not CONFIG_PATH.exists():
            self._create_production_config()

        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            self.config = yaml.load(file, Loader=SafeLoader)

        self.authenticator = stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days'],
            self.config.get('preauthorized', {})
        )

        self._initialized = True

    def _create_production_config(self):
        """Create production auth config with secure defaults"""
        CONFIG_PATH.parent.mkdir(exist_ok=True)

        secure_key = secrets.token_hex(32)
        admin_password = stauth.Hasher(['Arpg@Admin2026']).generate()[0]
        viewer_password = stauth.Hasher(['View@1234']).generate()[0]

        production_config = {
            'credentials': {
                'usernames': {
                    'admin': {
                        'email': 'admin@arpg-wiki.com',
                        'name': 'Administrator',
                        'password': admin_password,
                        'role': 'admin',
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'created_by': 'system'
                    },
                    'viewer1': {
                        'email': 'viewer1@example.com',
                        'name': 'ผู้ใช้งานทั่วไป 1',
                        'password': viewer_password,
                        'role': 'viewer',
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'created_by': 'system'
                    },
                    'viewer2': {
                        'email': 'viewer2@example.com',
                        'name': 'ผู้ใช้งานทั่วไป 2',
                        'password': viewer_password,
                        'role': 'viewer',
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'created_by': 'system'
                    }
                }
            },
            'cookie': {
                'name': 'arpg_item_wiki_production',
                'key': secure_key,
                'expiry_days': 30
            },
            'preauthorized': {
                'emails': []
            }
        }

        with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
            yaml.dump(production_config, file, allow_unicode=True)

        print("✅ PRODUCTION AUTH CONFIG CREATED")
        print("=" * 50)
        print("🔐 DEFAULT LOGIN CREDENTIALS:")
        print("   Admin:  admin / Arpg@Admin2026")
        print("   Viewer: viewer1 / View@1234")
        print("   Viewer: viewer2 / View@1234")
        print("=" * 50)
        print("⚠️  CHANGE PASSWORDS IMMEDIATELY AFTER FIRST LOGIN!")

    def login_widget(self, location: str = "main"):
        """Render login widget"""
        name, authentication_status, username = self.authenticator.login(location)

        if authentication_status:
            st.session_state.auth_name = name
            st.session_state.auth_username = username
            st.session_state.auth_status = True
            st.session_state.auth_role = self._get_user_role(username)
            return True
        elif authentication_status == False:
            st.error('❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
            return False
        else:
            return False

    # ===== FIXED: Logout button with error handling =====
    def logout_button(self, location: str = "sidebar"):
        """Render logout button - FIXED: Prevent double-click error"""
        try:
            if st.session_state.get('auth_status') and self.is_authenticated():
                self.authenticator.logout('🔓 ออกจากระบบ', location)
        except Exception:
            # Clean up session state if already logged out
            for key in ['auth_status', 'auth_name', 'auth_username', 'auth_role']:
                if key in st.session_state:
                    del st.session_state[key]

    def _get_user_role(self, username: str) -> UserRole:
        """Get user role from config"""
        try:
            return self.config['credentials']['usernames'][username].get('role', 'viewer')
        except:
            return 'viewer'

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user info"""
        if st.session_state.get('auth_status'):
            return {
                'name': st.session_state.get('auth_name'),
                'username': st.session_state.get('auth_username'),
                'role': st.session_state.get('auth_role', 'viewer')
            }
        return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('auth_status', False)

    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role"""
        if not self.is_authenticated():
            return False
        user_role = st.session_state.get('auth_role', 'viewer')

        if required_role == 'admin':
            return user_role == 'admin'
        return True

    def create_user(self, username: str, password: str, email: str, name: str, role: UserRole = 'viewer') -> Tuple[bool, str]:
        """Create new user (Admin only)"""
        if not self.has_role('admin'):
            return False, "❌ เฉพาะ Admin เท่านั้นที่สร้างผู้ใช้ได้"

        try:
            if username in self.config['credentials']['usernames']:
                return False, f"❌ ชื่อผู้ใช้ '{username}' มีอยู่แล้ว"

            hashed_password = stauth.Hasher([password]).generate()[0]

            self.config['credentials']['usernames'][username] = {
                'email': email,
                'name': name,
                'password': hashed_password,
                'role': role,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': st.session_state.get('auth_username', 'admin')
            }

            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, allow_unicode=True)

            return True, f"✅ สร้างผู้ใช้ '{username}' เรียบร้อย"

        except Exception as e:
            return False, f"❌ เกิดข้อผิดพลาด: {str(e)}"

    def list_users(self) -> list:
        """List all users (Admin only)"""
        if not self.has_role('admin'):
            return []

        users = []
        for username, data in self.config['credentials']['usernames'].items():
            users.append({
                'username': username,
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'role': data.get('role', 'viewer'),
                'created_at': data.get('created_at', ''),
                'created_by': data.get('created_by', '')
            })
        return users

    def reset_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password (Admin only)"""
        if not self.has_role('admin'):
            return False, "❌ เฉพาะ Admin เท่านั้นที่เปลี่ยนรหัสผ่านได้"

        try:
            if username not in self.config['credentials']['usernames']:
                return False, f"❌ ไม่พบผู้ใช้ '{username}'"

            hashed_password = stauth.Hasher([new_password]).generate()[0]
            self.config['credentials']['usernames'][username]['password'] = hashed_password
            self.config['credentials']['usernames'][username]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, allow_unicode=True)

            return True, f"✅ เปลี่ยนรหัสผ่านของ '{username}' เรียบร้อย"

        except Exception as e:
            return False, f"❌ เกิดข้อผิดพลาด: {str(e)}"

# ----------------------------------------------------------------------
# Authorization Decorators
# ----------------------------------------------------------------------
def require_role(allowed_roles: list[UserRole]):
    """Decorator for role-based access control"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not auth_manager.is_authenticated():
                st.warning("🔒 กรุณาเข้าสู่ระบบก่อนใช้งาน")
                return None

            if not auth_manager.has_role(allowed_roles[0] if allowed_roles else 'viewer'):
                st.error("🚫 คุณไม่มีสิทธิ์ใช้งานส่วนนี้")
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_authentication(func):
    """Decorator for pages that require login"""
    def wrapper(*args, **kwargs):
        if not auth_manager.is_authenticated():
            st.warning("🔒 กรุณาเข้าสู่ระบบก่อนใช้งาน")
            return None
        return func(*args, **kwargs)
    return wrapper

auth_manager = AuthManager()