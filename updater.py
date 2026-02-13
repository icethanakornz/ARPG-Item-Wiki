"""
updater.py
==========
Auto Update System - Check for updates from GitHub
"""
import os
import zipfile
import requests
import streamlit as st
from pathlib import Path
import shutil
import tempfile
import subprocess
import sys


class AutoUpdater:
    """จัดการระบบ Auto Update"""

    def __init__(self):
        self.github_base = "https://raw.githubusercontent.com/icethanakornz/ARPG-Item-Wiki/main/"
        self.github_repo = "https://github.com/icethanakornz/ARPG-Item-Wiki/raw/main/"
        self.version_file = "latest_version.txt"
        self.notes_file = "update_notes.txt"
        self.db_zip = "item_wiki_db.zip"

        # โฟลเดอร์ปัจจุบัน
        self.app_path = Path(__file__).parent.absolute()
        self.current_version = self.get_current_version()

    def get_current_version(self):
        """อ่าน version ปัจจุบันจากไฟล์"""
        version_file = self.app_path / "version.txt"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
        return "2.0.0"  # default

    def check_for_updates(self):
        """เช็ค GitHub ว่ามี version ใหม่ไหม"""
        try:
            # ดึง version ล่าสุดจาก GitHub
            url = f"{self.github_base}{self.version_file}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                latest_version = response.text.strip()

                # ดึงอัปเดตโน้ต
                notes_url = f"{self.github_base}{self.notes_file}"
                notes_response = requests.get(notes_url, timeout=5)
                notes = notes_response.text if notes_response.status_code == 200 else "ไม่มีรายละเอียด"

                return {
                    'has_update': latest_version > self.current_version,
                    'latest_version': latest_version,
                    'current_version': self.current_version,
                    'notes': notes
                }
        except Exception as e:
            print(f"Update check failed: {e}")

        return {'has_update': False}

    def download_and_update(self):
        """ดาวน์โหลด zip และอัปเดตไฟล์"""
        try:
            # ดาวน์โหลด zip
            zip_url = f"{self.github_repo}{self.db_zip}"
            response = requests.get(zip_url, stream=True)

            if response.status_code != 200:
                st.error("ไม่สามารถดาวน์โหลดอัปเดตได้")
                return False

            # สร้าง temp folder
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "update.zip"

                # save zip
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # unzip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                # Backup ไฟล์สำคัญ
                self.backup_current_files()

                # Replace ไฟล์
                self.replace_files(tmpdir)

                # อัปเดต version
                self.update_version_file()

                return True

        except Exception as e:
            st.error(f"อัปเดตล้มเหลว: {e}")
            return False

    def backup_current_files(self):
        """Backup ไฟล์เดิมก่อน replace"""
        backup_dir = self.app_path / "backup"
        backup_dir.mkdir(exist_ok=True)

        # Backup database
        db_path = self.app_path / "item_wiki.db"
        if db_path.exists():
            shutil.copy2(db_path, backup_dir / "item_wiki.db.bak")

        # Backup auth config
        auth_path = self.app_path / ".streamlit" / "auth_config.yaml"
        if auth_path.exists():
            shutil.copy2(auth_path, backup_dir / "auth_config.yaml.bak")

    def replace_files(self, source_dir):
        """Replace ไฟล์เก่าด้วยของใหม่"""
        # คัดลอก database
        new_db = Path(source_dir) / "item_wiki.db"
        if new_db.exists():
            shutil.copy2(new_db, self.app_path / "item_wiki.db")

        # คัดลอก auth config
        new_auth = Path(source_dir) / ".streamlit" / "auth_config.yaml"
        if new_auth.exists():
            auth_target = self.app_path / ".streamlit"
            auth_target.mkdir(exist_ok=True)
            shutil.copy2(new_auth, auth_target / "auth_config.yaml")

        # คัดลอกรูปภาพ
        new_images = Path(source_dir) / "assets" / "images"
        if new_images.exists():
            images_target = self.app_path / "assets" / "images"
            images_target.mkdir(parents=True, exist_ok=True)

            for img_file in new_images.glob("*"):
                shutil.copy2(img_file, images_target / img_file.name)

    def update_version_file(self):
        """อัปเดตไฟล์ version.txt"""
        # ดึง version ล่าสุดอีกครั้ง
        try:
            url = f"{self.github_base}{self.version_file}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                latest = response.text.strip()
                with open(self.app_path / "version.txt", 'w') as f:
                    f.write(latest)
        except:
            pass

    def restart_app(self):
        """Restart โปรแกรม"""
        python = sys.executable
        subprocess.Popen([python, "-m", "streamlit", "run", "app.py"])
        sys.exit()


# สร้าง instance
updater = AutoUpdater()