from flask import Flask, jsonify, request
from flask_session import Session
from flask_cors import CORS
from pymongo import MongoClient
from mongoengine import connect
from config import Config
from backend.routes import auth_bp, chat_bp, upload_bp, init_chatbot
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------------
# 1. DB Connect
# ---------------------------------------------------------
try:
    connect(host=Config.MONGODB_URI)
    logger.info("✅ Connected to MongoDB via MongoEngine")
except Exception as e:
    logger.error(f"❌ Failed to connect MongoEngine: {e}")

try:
    mongo_client = MongoClient(Config.MONGODB_URI)
    app.config["SESSION_MONGODB"] = mongo_client
    app.config["SESSION_MONGODB_DB"] = "Authentication"
    app.config["SESSION_MONGODB_COLLECT"] = "Sessions"
    app.config["APP_MONGO_CLIENT"] = mongo_client
    app.config["APP_MONGO_DBNAME"] = getattr(Config, "MONGODB_APP_DBNAME", "VoyAIage")
except Exception as e:
    logger.error(f"❌ Failed to connect PyMongo: {e}")

# Initialize Flask-Session
Session(app)

# ---------------------------------------------------------
# 2. CẤU HÌNH CORS (PHIÊN BẢN DEBUG CHI TIẾT)
# ---------------------------------------------------------

# Tắt tự động của thư viện để dùng code thủ công phía dưới
# CORS(app)  <-- Tạm tắt dòng này để tránh xung đột

@app.after_request
def after_request_func(response):
    # Lấy Origin từ request
    origin = request.headers.get('Origin')
    
    # 1. Lấy danh sách cho phép và dọn sạch khoảng trắng thừa
    allowed_origins = [url.strip() for url in Config.ALLOWED_ORIGINS]
    
    # --- LOG DEBUG (Xem ở Terminal CMD) ---
    if origin:
        print(f"🔍 DEBUG CORS: Request from '{origin}' | Allowed: {allowed_origins}")
    
    # 2. Logic kiểm tra và cấp quyền "Gương" (Mirror)
    if origin and (origin in allowed_origins or "*" in allowed_origins):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        print(f"✅ Đã thêm Header CORS cho: {origin}")
    else:
        # Nếu không khớp, thử hard-code luôn localhost:5173 để cứu vãn
        if origin == "http://localhost:5173":
             response.headers['Access-Control-Allow-Origin'] = origin
             response.headers['Access-Control-Allow-Credentials'] = 'true'
             response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
             response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
             print("⚠️ Force allow localhost:5173 (Fallback)")

    return response

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(upload_bp)
# app.register_blueprint(travel_log_bp) # Travel log đang 404 là đúng vì bạn đang comment dòng này

# Serve uploaded files
uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.static_folder = None 
@app.route('/uploads/<filename>')
def serve_upload(filename):
    from flask import send_from_directory, abort
    try:
        return send_from_directory(uploads_dir, filename)
    except Exception:
        abort(404)

# Chatbot
def initialize_chatbot():
    if not Config.CHATBOT_ENABLED: return
    try:
        # (Giữ nguyên logic chatbot của bạn)...
        pass 
    except Exception:
        pass

@app.route('/')
def home():
    return jsonify({"message": "VoyAIage Server is Running"}), 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )