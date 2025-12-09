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
    # Priority: DATABASE_URL (Render) > Individual PSQL_* vars (Local)
    PSQL_HOST = os.getenv('PSQL_HOST', 'localhost')
    PSQL_PORT = os.getenv('PSQL_PORT', '5432')
    PSQL_USERNAME = os.getenv('PSQL_USERNAME')
    PSQL_PASSWORD = os.getenv('PSQL_PASSWORD')
    PSQL_DBNAME = os.getenv('PSQL_DBNAME')
    
    @classmethod
    def get_database_uri(cls):
        """
        Get PostgreSQL database URI.
        Supports both Render (DATABASE_URL) and local (PSQL_*) configurations.
        """
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Render deployment - use DATABASE_URL directly
            return database_url
        else:
            # Local development - construct from individual variables
            username = cls.PSQL_USERNAME
            password = cls.PSQL_PASSWORD
            host = cls.PSQL_HOST
            port = cls.PSQL_PORT
            dbname = cls.PSQL_DBNAME
            
            if not all([username, password, host, port, dbname]):
                raise ValueError("Missing PostgreSQL configuration. Set DATABASE_URL or PSQL_* environment variables.")
            
            return f"postgresql+psycopg://{username}:{password}@{host}:{port}/{dbname}"
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Session Configuration
    SESSION_TYPE = "mongodb"
    SESSION_PERMANENT = True
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
    
    # Server Configuration
    PORT = int(os.getenv('PORT', '5000'))  # Render sets PORT as string, convert to int
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Chatbot Configuration
    CHATBOT_ENABLED = os.getenv('CHATBOT_ENABLED', 'True').lower() == 'true'
    
    # RAG System Configuration
    # Paths (relative to project root)
    RAG_CSV_PATH = os.getenv('RAG_CSV_PATH', 'data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv')
    RAG_CHROMA_DB_PATH = os.getenv('RAG_CHROMA_DB_PATH', 'data/vector_db/chroma_tourism')
    
    # RAG Model Configuration
    RAG_EMBEDDING_MODEL = os.getenv('RAG_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    RAG_GEMINI_MODEL = os.getenv('RAG_GEMINI_MODEL', 'gemini-2.5-flash-lite')
    RAG_TOP_K_RESULTS = int(os.getenv('RAG_TOP_K_RESULTS', '5'))
    RAG_LLM_TEMPERATURE = float(os.getenv('RAG_LLM_TEMPERATURE', '0.7'))
