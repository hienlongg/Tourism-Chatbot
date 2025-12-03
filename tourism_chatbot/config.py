"""
Configuration management for Tourism Chatbot
"""

import os
from typing import Optional
from pathlib import Path


class Config:
    """
    Centralized configuration for the Tourism Chatbot application.
    """
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    VECTOR_DB_DIR = DATA_DIR / "vector_db"
    
    # Data files
    CSV_PATH = PROCESSED_DATA_DIR / "danh_sach_thong_tin_dia_danh_chi_tiet.csv"
    CHROMA_DB_PATH = VECTOR_DB_DIR / "chroma_tourism"
    
    # Model configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    LLM_TEMPERATURE = 0.7
    TOP_K_RESULTS = 5
    
    # API Keys (from environment)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Database configuration
    PSQL_HOST = os.getenv("PSQL_HOST", "localhost")
    PSQL_PORT = os.getenv("PSQL_PORT", "5432")
    PSQL_DBNAME = os.getenv("PSQL_DBNAME", "tourism_db")
    PSQL_USERNAME = os.getenv("PSQL_USERNAME", "tourism")
    PSQL_PASSWORD = os.getenv("PSQL_PASSWORD")
    
    # Connection pool settings
    DB_POOL_MIN_SIZE = 2
    DB_POOL_MAX_SIZE = 10
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_db_uri(cls) -> str:
        """
        Get database connection URI.
        
        Returns:
            str: PostgreSQL connection URI
        """
        return f"postgresql://{cls.PSQL_USERNAME}:{cls.PSQL_PASSWORD}@{cls.PSQL_HOST}:{cls.PSQL_PORT}/{cls.PSQL_DBNAME}"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            bool: True if valid, False otherwise
        """
        required = [
            ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
            ("PSQL_PASSWORD", cls.PSQL_PASSWORD),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            print(f"❌ Missing required configuration: {', '.join(missing)}")
            return False
        
        return True
    
    @classmethod
    def display(cls):
        """Display current configuration (safe - no secrets)."""
        print("⚙️  Tourism Chatbot Configuration:")
        print(f"   Project Root: {cls.PROJECT_ROOT}")
        print(f"   Data Directory: {cls.DATA_DIR}")
        print(f"   CSV Path: {cls.CSV_PATH}")
        print(f"   Vector DB Path: {cls.CHROMA_DB_PATH}")
        print(f"   Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"   Gemini Model: {cls.GEMINI_MODEL}")
        print(f"   Database: {cls.PSQL_HOST}:{cls.PSQL_PORT}/{cls.PSQL_DBNAME}")
        print(f"   Database User: {cls.PSQL_USERNAME}")
        print(f"   Log Level: {cls.LOG_LEVEL}")
        print(f"   API Key Set: {'✅' if cls.GEMINI_API_KEY else '❌'}")
        print(f"   DB Password Set: {'✅' if cls.PSQL_PASSWORD else '❌'}")


# Global config instance
config = Config()
