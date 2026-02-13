"""
security/sanitizer.py
=====================
PRODUCTION - Input/Output Sanitization Module
"""
import bleach
import re
from pathlib import Path
import magic
from PIL import Image
import io
from typing import Tuple, Optional
import secrets
from datetime import datetime

class HTMLSanitizer:
    """Sanitize HTML input - ป้องกัน XSS"""

    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'br', 'p', 'ul', 'ol', 'li', 'span']
    ALLOWED_ATTRIBUTES = {'span': ['style'], 'p': ['style']}
    ALLOWED_STYLES = ['color', 'font-weight', 'font-style', 'text-decoration']

    @staticmethod
    def sanitize_html(text: str, strip: bool = True) -> str:
        if not text:
            return ""

        cleaned = bleach.clean(
            text,
            tags=HTMLSanitizer.ALLOWED_TAGS,
            attributes=HTMLSanitizer.ALLOWED_ATTRIBUTES,
            styles=HTMLSanitizer.ALLOWED_STYLES,
            strip=strip
        )

        cleaned = re.sub(r'<script.*?>.*?</script>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'on\w+="[^"]*"', '', cleaned)
        cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'data:', '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            return "unknown_file"

        filename = Path(filename).name
        filename = re.sub(r'[^\w\-_. ]', '', filename)

        if len(filename) > 100:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = f"{name[:50]}...{ext}"

        return filename or "unknown_file"

class FileValidator:
    """Validate uploaded files - ป้องกัน RCE"""

    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
    ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/jpg', 'image/gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DIMENSION = 3000

    @staticmethod
    def validate_image(uploaded_file) -> Tuple[bool, Optional[str]]:
        if not uploaded_file:
            return True, None

        try:
            file_size = len(uploaded_file.getvalue())
            if file_size > FileValidator.MAX_FILE_SIZE:
                return False, f"ไฟล์มีขนาดใหญ่เกินไป (สูงสุด {FileValidator.MAX_FILE_SIZE//1024//1024}MB)"

            file_bytes = uploaded_file.getvalue()
            mime_type = magic.from_buffer(file_bytes[:2048], mime=True)

            if mime_type not in FileValidator.ALLOWED_MIME_TYPES:
                return False, "ไฟล์ไม่ใช่รูปภาพที่รองรับ (PNG, JPG, JPEG, GIF)"

            img = Image.open(io.BytesIO(file_bytes))
            img.verify()

            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size

            if width > FileValidator.MAX_DIMENSION or height > FileValidator.MAX_DIMENSION:
                return False, f"รูปภาพมีขนาดใหญ่เกินไป (สูงสุด {FileValidator.MAX_DIMENSION}x{FileValidator.MAX_DIMENSION}px)"

            return True, None

        except Exception as e:
            return False, f"ไฟล์รูปภาพเสียหาย: {str(e)}"

    @staticmethod
    def get_safe_filename(original_filename: str) -> str:
        safe_name = HTMLSanitizer.sanitize_filename(original_filename)
        ext = Path(safe_name).suffix.lower()

        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            ext = '.png'

        timestamp = datetime.now().strftime('%Y%m%d')
        random_id = secrets.token_hex(8)

        return f"{timestamp}_{random_id}{ext}"

class OutputSanitizer:
    """Sanitize data before displaying"""

    @staticmethod
    def safe_text(text: str, max_length: int = 1000) -> str:
        if not text:
            return ""

        if len(text) > max_length:
            text = text[:max_length] + "..."

        return bleach.clean(text, tags=[], strip=True)

    @staticmethod
    def safe_description(description: str) -> str:
        if not description:
            return "ไม่มีคำอธิบาย"
        return HTMLSanitizer.sanitize_html(description, strip=False)

html_sanitizer = HTMLSanitizer()
file_validator = FileValidator()
output_sanitizer = OutputSanitizer()