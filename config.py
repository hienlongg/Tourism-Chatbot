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
    PSQL_HOST = os.getenv('PSQL_HOST', 'localhost')
    PSQL_PORT = os.getenv('PSQL_PORT', '5432')
    PSQL_USERNAME = os.getenv('PSQL_USERNAME')
    PSQL_PASSWORD = os.getenv('PSQL_PASSWORD')
    PSQL_DBNAME = os.getenv('PSQL_DBNAME')
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Session Configuration
    SESSION_TYPE = "mongodb"
    SESSION_PERMANENT = True
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SAMESITE = "Lax"  
    # SESSION_COOKIE_SECURE = False
    # SESSION_COOKIE_HTTPONLY = True
    
   
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')    
    # Server Configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Chatbot Configuration
    CHATBOT_ENABLED = os.getenv('CHATBOT_ENABLED', 'True').lower() == 'true'

    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')