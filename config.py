"""
Configuration module for Flask application.
Loads environment variables and defines app settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI')

     # Database name for APP (Travel Log + Image Cache)
    MONGODB_APP_DBNAME = os.getenv('MONGODB_APP_DBNAME', 'VoyAIage')

    # Google Custom Search for image fetcher
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX")
    
    # PostgreSQL Configuration (for LangGraph checkpointer)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    @classmethod
    def get_database_uri(cls):
        """
        Get PostgreSQL database URI from DATABASE_URL environment variable.
        
        Returns:
            str: Database connection URI
        
        Raises:
            ValueError: If DATABASE_URL environment variable is missing
        """
        if not cls.DATABASE_URL:
            raise ValueError("Missing required environment variable: DATABASE_URL")
        
        return cls.DATABASE_URL
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # OpenMap API Configuration
    OPENMAP_API_KEY = os.getenv('OPENMAP_API_KEY')
    
    # Session Configuration
    SESSION_TYPE = "mongodb"
    SESSION_PERMANENT = True
    
        # Cookie settings
    # - If your frontend and backend are on different domains (e.g. ngrok), you typically need:
    #     SESSION_COOKIE_SAMESITE=None
    #     SESSION_COOKIE_SECURE=True
    # - Allow overriding via env vars to support local+ngrok without switching FLASK_ENV.
    IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

    _cookie_samesite_override = os.getenv('SESSION_COOKIE_SAMESITE')
    _cookie_secure_override = os.getenv('SESSION_COOKIE_SECURE')

    if _cookie_samesite_override is not None:
        SESSION_COOKIE_SAMESITE = _cookie_samesite_override
    else:
        SESSION_COOKIE_SAMESITE = "None" if IS_PRODUCTION else "Lax"

    if _cookie_secure_override is not None:
        SESSION_COOKIE_SECURE = _cookie_secure_override.lower() == 'true'
    else:
        SESSION_COOKIE_SECURE = True if IS_PRODUCTION else False
    
    SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SAMESITE = "Lax"  
    # SESSION_COOKIE_SECURE = False
    # SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days in seconds
    
   
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')    
    # Server Configuration
    PORT = int(os.getenv('PORT', '5000'))  # Render sets PORT as string, convert to int
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Chatbot Configuration
    CHATBOT_ENABLED = os.getenv('CHATBOT_ENABLED', 'True').lower() == 'true'

    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    
    # RAG System Configuration
    # Paths (relative to project root)
    RAG_CSV_PATH = os.getenv('RAG_CSV_PATH', 'data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv')
    RAG_CHROMA_DB_PATH = os.getenv('RAG_CHROMA_DB_PATH', 'data/vector_db/chroma_tourism')
    
    # RAG Model Configuration
    RAG_EMBEDDING_MODEL = os.getenv('RAG_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    RAG_GEMINI_MODEL = os.getenv('RAG_GEMINI_MODEL', 'gemini-2.5-flash-lite')
    RAG_TOP_K_RESULTS = int(os.getenv('RAG_TOP_K_RESULTS', '5'))
    RAG_LLM_TEMPERATURE = float(os.getenv('RAG_LLM_TEMPERATURE', '0.7'))
    
    # Remote Embedding API Configuration (HuggingFace Spaces)
    USE_REMOTE_EMBEDDINGS = os.getenv('USE_REMOTE_EMBEDDINGS', 'False').lower() == 'true'
    REMOTE_EMBEDDING_API_URL = os.getenv('REMOTE_EMBEDDING_API_URL', None)
    EMBEDDING_API_TIMEOUT = int(os.getenv('EMBEDDING_API_TIMEOUT', '30'))
    EMBEDDING_API_FALLBACK_LOCAL = os.getenv('EMBEDDING_API_FALLBACK_LOCAL', 'True').lower() == 'true'
