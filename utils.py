"""
utils.py
========
Utility functions for image handling, validation, and UI helpers.
"""
import os
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image
import streamlit as st

# Lazy import to avoid circular
# from database import get_all_rarities, get_all_item_types, get_all_locations, get_all_tiers, clear_master_cache

# ----------------------------------------------------------------------
# Image Management
# ----------------------------------------------------------------------
def ensure_upload_dir():
    """Ensure upload directory exists with proper permissions."""
    upload_dir = Path("assets/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

def create_placeholder_image():
    """Generate placeholder image if not exists."""
    placeholder_path = Path("assets/images/placeholder.png")
    if placeholder_path.exists():
        return

    ensure_upload_dir()
    img = Image.new('RGB', (200, 200), color=(73, 109, 137))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.text((50, 90), "No Image", fill=(255, 255, 255))
    img.save(placeholder_path)

def save_uploaded_image(uploaded_file, item_name):
    """
    Save uploaded image with secure filename.
    Returns: relative path to saved image
    """
    if not uploaded_file:
        return "assets/images/placeholder.png"

    # Create secure filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name_hash = hashlib.md5(item_name.encode()).hexdigest()[:8]
    ext = Path(uploaded_file.name).suffix.lower()

    # Validate extension
    if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
        raise ValueError("ไฟล์รูปต้องเป็น PNG, JPG, JPEG หรือ GIF เท่านั้น")

    filename = f"{name_hash}_{timestamp}{ext}"
    filepath = Path("assets/images") / filename

    # Save file
    ensure_upload_dir()
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(filepath)

def delete_image_file(image_path):
    """Delete image file if not placeholder."""
    if image_path and image_path != "assets/images/placeholder.png":
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except OSError:
            pass

def get_image_base64(image_path):
    """Convert image to base64 for embedding."""
    try:
        if not os.path.exists(image_path):
            image_path = "assets/images/placeholder.png"

        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (IOError, OSError):
        try:
            with open("assets/images/placeholder.png", "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except (IOError, OSError):
            return None

# ----------------------------------------------------------------------
# CSS and UI Styling
# ----------------------------------------------------------------------
def load_css():
    """Load custom CSS with modern dark theme."""
    st.markdown("""
        <style>
        /* Dark theme */
        .stApp {
            background: linear-gradient(135deg, #0B0C10 0%, #1A1E24 100%);
            color: #E0E0E0;
        }
        
        /* Cards */
        .item-card {
            background: linear-gradient(145deg, #1E1E1E, #252525);
            border-radius: 16px;
            padding: 24px;
            margin: 12px 0;
            border-left: 6px solid;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .item-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.5);
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        /* Rarity borders */
        .rarity-Common { border-left-color: #808080; }
        .rarity-Uncommon { border-left-color: #27ae60; }
        .rarity-Rare { border-left-color: #2980b9; }
        .rarity-Epic { border-left-color: #8e44ad; }
        .rarity-Legendary { 
            border-left-color: #f39c12;
            box-shadow: 0 0 10px rgba(243, 156, 18, 0.2);
        }
        
        /* Buttons */
        .stButton button {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .stButton button:hover {
            background: linear-gradient(45deg, #2980b9, #3498db);
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        /* Inputs */
        .stTextInput input, .stSelectbox, .stTextArea textarea {
            background-color: #262730 !important;
            color: white !important;
            border: 1px solid #3E4A5A !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #3498db !important;
            box-shadow: 0 0 0 2px rgba(52,152,219,0.2) !important;
        }
        
        /* Metrics */
        div[data-testid="stMetricValue"] {
            font-size: 2.2rem;
            color: #3498db;
            font-weight: 700;
        }
        
        div[data-testid="stMetricLabel"] {
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: #1E1E1E;
            padding: 0.5rem;
            border-radius: 12px;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #888;
            border-radius: 8px;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1E1E1E;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #3E4A5A;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #4E6A5A;
        }
        </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Data Helpers - Lazy load database functions
# ----------------------------------------------------------------------
@st.cache_data(ttl=60)
def get_filter_options():
    """Get all filter options with caching."""
    from database import get_all_item_types, get_all_rarities, get_all_locations, get_all_tiers

    _, type_names = get_all_item_types()
    _, rarities_list = get_all_rarities()
    _, location_names = get_all_locations()
    _, tier_names = get_all_tiers()

    return {
        'types': type_names,
        'rarities': [r['name'] for r in rarities_list],
        'locations': location_names,
        'tiers': tier_names,
        'rarities_with_details': rarities_list
    }

def get_rarity_color(rarity_name):
    """Get color for rarity name."""
    from database import get_all_rarities

    _, rarities = get_all_rarities()
    for r in rarities:
        if r['name'] == rarity_name:
            return r['color']
    return "#808080"

def get_rarity_icon(rarity_name):
    """Get icon for rarity name."""
    from database import get_all_rarities

    _, rarities = get_all_rarities()
    for r in rarities:
        if r['name'] == rarity_name:
            return r['icon']
    return "⚪"

def refresh_master_data():
    """Clear cache and refresh master data."""
    from database import clear_master_cache

    clear_master_cache()
    get_filter_options.clear()
    st.cache_data.clear()