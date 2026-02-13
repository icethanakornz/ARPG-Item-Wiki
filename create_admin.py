"""
create_admin.py
===============
PRODUCTION - Admin User Creation Tool
Run this script to create additional admin users
"""
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from datetime import datetime

def create_admin_user():
    """Create a new admin user"""

    config_path = Path(".streamlit/auth_config.yaml")

    if not config_path.exists():
        print("❌ ไม่พบไฟล์ auth_config.yaml")
        return

    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    print("\n" + "="*50)
    print("👑 สร้าง Admin User ใหม่")
    print("="*50)

    username = input("ชื่อผู้ใช้: ").strip()
    password = input("รหัสผ่าน: ").strip()
    email = input("อีเมล: ").strip()
    name = input("ชื่อ-นามสกุล: ").strip()

    if not all([username, password, email, name]):
        print("❌ กรุณากรอกข้อมูลให้ครบ")
        return

    if username in config['credentials']['usernames']:
        print(f"❌ ชื่อผู้ใช้ '{username}' มีอยู่แล้ว")
        return

    hashed_password = stauth.Hasher([password]).generate()[0]

    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_password,
        'role': 'admin',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'created_by': 'system'
    }

    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.dump(config, file, allow_unicode=True)

    print(f"✅ สร้าง Admin User '{username}' เรียบร้อย")

if __name__ == "__main__":
    create_admin_user()