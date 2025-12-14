"""
Flask application entry point.
Initializes Flask app, configures session, CORS, and registers blueprints.
"""

from flask import Flask, jsonify
from flask_session import Session
from flask_cors import CORS
from pymongo import MongoClient
from config import Config
from backend.routes import auth_bp, chat_bp, upload_bp, init_chatbot, travel_log_bp, posts_bp
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB client for session storage
mongo_client = MongoClient(Config.MONGODB_URI)
app.config["SESSION_MONGODB"] = mongo_client
app.config["SESSION_MONGODB_DB"] = "Authentication"
app.config["SESSION_MONGODB_COLLECT"] = "Sessions"

# Reuse the same Mongo client for application data (travel log, locations, ...)
app.config["APP_MONGO_CLIENT"] = mongo_client
app.config["APP_MONGO_DBNAME"] = getattr(Config, "MONGODB_APP_DBNAME", "VoyAIage")

# Initialize Flask-Session
Session(app)

# Initialize CORS
CORS(app, supports_credentials=True, origins=Config.ALLOWED_ORIGINS)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(travel_log_bp)
app.register_blueprint(posts_bp)

# Serve uploaded files as static content
uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.static_folder = None  # Disable default static folder
@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded files from the uploads directory."""
    from flask import send_from_directory, abort
    try:
        return send_from_directory(uploads_dir, filename)
    except Exception:
        abort(404)


def initialize_chatbot():
    """
    Initialize the tourism chatbot system.
    This function loads the RAG system, database, and agent.
    """
    if not Config.CHATBOT_ENABLED:
        logger.info("⚠️ Chatbot is disabled via CHATBOT_ENABLED config")
        return
    
    try:
        logger.info("🚀 Initializing tourism chatbot system...")
        
        # Check for required environment variables
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            logger.warning("⚠️ GEMINI_API_KEY not set. Chatbot will not be available.")
            return
        
        # Import chatbot modules
        from tourism_chatbot.rag.rag_engine import initialize_rag_system
        from tourism_chatbot.database import get_connection_pool, initialize_checkpointer
        from tourism_chatbot.database.filtered_checkpointer import FilteredCheckpointer
        from tourism_chatbot.agents.tourism_agent import create_tourism_agent
        
        # Initialize RAG system
        logger.info("📚 Loading RAG system...")
        vector_store, llm = initialize_rag_system(api_key=api_key)
        
        # Initialize database and checkpointer for conversation memory
        logger.info("🗄️ Connecting to PostgreSQL for conversation memory...")
        try:
            pool = get_connection_pool()
            base_checkpointer = initialize_checkpointer(pool)
            # Wrap checkpointer to filter out image URLs before saving
            checkpointer = FilteredCheckpointer(base_checkpointer)
            logger.info("✅ PostgreSQL checkpointer initialized (with image filtering)")
        except Exception as db_error:
            logger.warning(f"⚠️ PostgreSQL not available: {db_error}")
            logger.info("📝 Running without conversation memory persistence")
            checkpointer = None
        
        # Create agent with memory
        logger.info("🤖 Creating tourism agent...")
        agent = create_tourism_agent(checkpointer=checkpointer)
        
        # Initialize chat routes with chatbot components
        init_chatbot(agent, vector_store, llm)
        
        logger.info("✅ Tourism chatbot system initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize chatbot: {str(e)}")
        logger.info("💡 The server will run without chatbot functionality")


@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({"message": "VoyAIage Server is Running"}), 200


# Initialize chatbot when app starts
with app.app_context():
    initialize_chatbot()


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=Config.DEBUG
    )
