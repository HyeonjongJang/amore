"""
Configuration for CRM Message Generation System
"""
import os
from pathlib import Path

# Load .env file if exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not installed, use environment variables

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAG_DIR = PROJECT_ROOT / "rag"

# Raw data path
RAW_PRODUCTS_PATH = PROJECT_ROOT.parent / "final_products.json"

# Processed data paths
PROCESSED_PRODUCTS_PATH = DATA_DIR / "products" / "processed_products.json"
PERSONAS_PATH = DATA_DIR / "personas" / "personas_kadence_enriched.json"
BRAND_TONES_PATH = DATA_DIR / "brand_tones" / "brand_tones.json"
CRM_EXAMPLES_PATH = DATA_DIR / "crm_examples" / "crm_examples.json"

# Vector DB paths
CHROMA_PERSIST_DIR = RAG_DIR / "chroma_db"

# OpenAI settings - support both local .env and Streamlit Cloud secrets
def get_openai_api_key():
    """Get OpenAI API key from environment or Streamlit secrets"""
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        return api_key

    # Try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'openai' in st.secrets:
            return st.secrets["openai"]["api_key"]
    except:
        pass

    return ""

OPENAI_API_KEY = get_openai_api_key()
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Brands to exclude (non-cosmetics)
EXCLUDE_BRANDS = {
    "OSULLOC",           # Tea products
    "VITALBEAUTIE",      # Health supplements
    "Gift With Purchase", # Not actual products
    "Global Amore Mall",  # Not actual products
    "K-POP Collaboration", # Merchandise
    "Love Life Beauty",   # Non-cosmetic
}

# Cosmetic brands to include (main Amorepacific brands)
COSMETIC_BRANDS = {
    # Premium
    "Sulwhasoo", "HERA", "AMORE PACIFIC",
    # Core
    "LANEIGE", "IOPE", "Mamonde", "Primera", "innisfree", "ETUDE", "espoir",
    # Derma/Sensitive
    "AESTURA", "ILLIYOON", "LABO-H",
    # Hair
    "AYUNCHE", "mise-en-scene", "AMOS PROFESSIONAL",
    # Others
    "HANYUL", "HAPPYBATH", "ODYSSEY", "HOLITUAL", "B.READY", "MEDIAN",
    "tonework", "Custom Match", "Longtake", "AMORE SEONGSU", "TWO SLASH FOUR",
    "Alternativestereo", "PUZZLEWOOD", "BY AMORE", "SKIN U", "AMORE BASIC",
    # Hidden variants (keep for data)
    "CYOUNG_HIDDEN", "SKIN U_HIDDEN", "AESTURA_HIDDEN",
}

# Minimum description length to include
MIN_DESCRIPTION_LENGTH = 50

# RAG settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5

# Brand name normalization mapping (for consistent brand names)
BRAND_NAME_MAPPING = {
    "innisfree": "이니스프리",
    "LANEIGE": "라네즈",
    "Sulwhasoo": "설화수",
    "HERA": "헤라",
    "IOPE": "아이오페",
    "ETUDE": "에뛰드",
    "Mamonde": "마몽드",
    "Primera": "프리메라",
    "espoir": "에스쁘아",
    "AESTURA": "에스트라",
    "HANYUL": "한율",
    "ILLIYOON": "일리윤",
    "ODYSSEY": "오딧세이",
    "HAPPYBATH": "해피바스",
    "mise-en-scene": "미장센",
    "AYUNCHE": "아윤채",
    "tonework": "톤워크",
}
