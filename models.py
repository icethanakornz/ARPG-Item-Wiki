"""
models.py
=========
Domain models with validation and business logic.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import re

@dataclass
class Item:
    """Item domain model with validation."""
    id: Optional[int] = None
    name: str = ""
    type_id: Optional[int] = None
    type_name: str = ""
    rarity_id: Optional[int] = None
    rarity_name: str = ""
    rarity_color: str = "#808080"
    rarity_icon: str = "⚪"
    location_id: Optional[int] = None
    location_name: str = ""
    tier_id: Optional[int] = None
    tier_name: str = ""
    description: str = ""
    image_path: str = "assets/images/placeholder.png"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]):
        """Create Item from database row (with joins)."""
        return cls(
            id=row.get('id'),
            name=row.get('name', ''),
            type_id=row.get('type_id'),
            type_name=row.get('type_name', ''),
            rarity_id=row.get('rarity_id'),
            rarity_name=row.get('rarity_name', ''),
            rarity_color=row.get('color', '#808080'),
            rarity_icon=row.get('icon', '⚪'),
            location_id=row.get('location_id'),
            location_name=row.get('location_name', ''),
            tier_id=row.get('tier_id'),
            tier_name=row.get('tier_name', ''),
            description=row.get('description', ''),
            image_path=row.get('image_path', 'assets/images/placeholder.png'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def validate(self) -> list[str]:
        """Validate item data."""
        errors = []

        if not self.name or len(self.name.strip()) < 2:
            errors.append("ชื่อไอเท็มต้องมีความยาวอย่างน้อย 2 ตัวอักษร")

        if not self.type_id:
            errors.append("กรุณาเลือกประเภทไอเท็ม")

        if not self.rarity_id:
            errors.append("กรุณาเลือกความหายาก")

        if not self.location_id:
            errors.append("กรุณาเลือกสถานที่ดรอป")

        if not self.tier_id:
            errors.append("กรุณาเลือก Tier")

        # Sanitize description
        if self.description:
            # Remove potential XSS
            self.description = re.sub(r'<[^>]*>', '', self.description)

        return errors

    @property
    def display_name_with_rarity(self) -> str:
        """Get formatted name with rarity color HTML."""
        return f'<span style="color:{self.rarity_color};">{self.name}</span>'

@dataclass
class MasterData:
    """Base class for master data entities."""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None

    def validate(self) -> list[str]:
        errors = []
        if not self.name or len(self.name.strip()) < 1:
            errors.append("กรุณาระบุชื่อ")
        return errors

@dataclass
class ItemType(MasterData):
    display_order: int = 0

@dataclass
class Rarity(MasterData):
    color: str = "#808080"
    icon: str = "⚪"
    display_order: int = 0

@dataclass
class DropLocation(MasterData):
    description: str = ""

@dataclass
class Tier(MasterData):
    display_order: int = 0