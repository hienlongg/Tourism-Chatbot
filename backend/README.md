# VoyAIage Server 🚀

A robust, modular backend API for the VoyAIage tourism consultation platform, built with Flask and MongoDB.

## ✨ Features

- **Secure Authentication** - Password hashing with PBKDF2-SHA256
- **Session Management** - MongoDB-backed server-side sessions
- **RESTful API** - Clean, well-documented endpoints
- **Input Validation** - Email and password validation
- **CORS Support** - Configured for cross-origin requests
- **Modular Architecture** - Easy to maintain and extend
- **Tourism Chatbot** - AI-powered travel recommendations with RAG
- **Location Extraction** - Smart location matching with CSV + OSM fallback
- **File Upload** - Image upload with validation
- **Travel Log** - Track visited locations

## 📍 Location Extraction Logic

1. **LLM Analysis**: The system analyzes the LLM's response to identify location descriptions.
2. **Name Extraction**: Extracts potential location names using Regex and NLP techniques.
3. **Strict CSV Matching**: Performs a strict match against the local database (`danh_sach_thong_tin_dia_danh_chi_tiet.csv`) to ensure high accuracy.
4. **OSM Basic Query**: If not found in CSV, queries OpenStreetMap (OSM) for standard location data.
5. **Advanced OSM Fallback**: If basic query fails, applies advanced cleaning (removing prefixes like "Công viên", "Bảo tàng") and name splitting to find matches.
6. **Frontend Response**: Returns a structured object containing Latitude, Longitude, Name, Description, and Image URL (if available).

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- PostgreSQL (for conversation memory)
- Google Gemini API key
- pip package manager

### Installation

```bash
# Navigate to project root
cd Tourism-Chatbot

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will start at `http://localhost:5000`

## 📁 Project Structure

```
backend/
├── models/                    # Database models
│   ├── __init__.py           # Models initialization
│   ├── user.py               # User authentication model
│   ├── chat.py               # Chat & message models
│   └── travel_log.py         # Travel log model
├── routes/                   # API endpoints
│   ├── __init__.py          # Routes initialization
│   ├── authentication.py    # Authentication routes
│   ├── chat.py              # Chat routes (tourism chatbot)
│   ├── upload.py            # File upload routes
│   └── travel_log.py        # Travel log routes
├── middlewares/              # Request middlewares
│   ├── __init__.py         # Middlewares initialization
│   └── decorators.py       # Authentication decorators
└── utils/                   # Utility functions
    ├── __init__.py         # Utils initialization
    ├── validators.py       # Input validation
    ├── location_extractor.py  # Location extraction logic
    └── image_resolver.py   # Image URL resolver
```

## ⚙️ Configuration

### Environment Variables

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_APP_DBNAME=VoyAIage

# PostgreSQL Configuration (for LangGraph checkpointer)
PSQL_HOST=localhost
PSQL_PORT=5432
PSQL_USERNAME=postgres
PSQL_PASSWORD=your-password
PSQL_DBNAME=tourism_chatbot

# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key

# Google Custom Search (for image fetcher)
GOOGLE_SEARCH_API_KEY=your-google-search-api-key
GOOGLE_CSE_CX=your-cse-key

# CORS Allowed Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173

# Server Configuration
PORT=5000
DEBUG=False

# Chatbot Configuration
CHATBOT_ENABLED=True
```

> **Security Note:** Never commit `.env` to version control. It's already in `.gitignore`.

### Generating SECRET_KEY

The `SECRET_KEY` is a random string used to encrypt session cookies and protect against CSRF attacks.

**Generate a secure key:**
```bash
python -c "import os; print(os.urandom(32).hex())"
```

Copy the output and paste it into your `.env` file:
```env
SECRET_KEY=a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

> **Important:** Use a different SECRET_KEY for each environment (development, staging, production).

## 📡 API Documentation

### Base URL
- Development: `http://localhost:5000`
- Production: Your deployed URL

---

### Authentication Endpoints

#### Health Check
```http
GET /
```

**Response:**
```json
{
  "message": "VoyAIage Server is Running"
}
```

---

#### Register New User
```http
POST /api/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "plain_password": "securepassword123"
}
```

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "role": "Student"
  }
}
```

**Error Responses:**
- `400` - Invalid email format or password too short
- `400` - Email already exists
- `400` - Already logged in

---

#### User Login
```http
POST /api/auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "plain_password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "role": "Student"
  }
}
```

**Error Responses:**
- `401` - Invalid credentials
- `400` - Already logged in

---

#### Get Current User
```http
GET /api/auth/me
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "role": "Student"
  }
}
```

**Error Response:**
- `401` - Authentication required

---

#### User Logout
```http
POST /api/auth/logout
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

### Chat Endpoints

#### Send Chat Message
```http
POST /api/chat/message
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:**
```json
{
  "message": "Tìm bãi biển đẹp ở Đà Nẵng",
  "imageUrl": "/uploads/image.jpg"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "response": "Tôi gợi ý cho bạn những bãi biển đẹp...",
  "metadata": {
    "visited_ids": ["loc_001"],
    "allow_revisit": false,
    "has_image": false
  },
  "locations": [
    {
      "name": "Bãi biển Mỹ Khê",
      "address": "Đà Nẵng",
      "lat": 16.0544,
      "lng": 108.2442,
      "description": "...",
      "image_url": "https://..."
    }
  ]
}
```

---

#### Send Chat Message (Streaming)
```http
POST /api/chat/message/stream
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:** Same as `/api/chat/message`

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
- `data: {"type": "token", "content": "..."}`
- `data: {"type": "locations", "locations": [...]}`
- `data: {"type": "done"}`

---

#### Get Chat Context
```http
GET /api/chat/context
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "success": true,
  "context": {
    "visited_ids": ["loc_001"],
    "allow_revisit": false
  }
}
```

---

#### Add Visited Location
```http
POST /api/chat/context/visited
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:**
```json
{
  "location": "Hội An"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "visited_ids": ["loc_001", "loc_002"],
  "message": "Location added to visited list"
}
```

---

#### Remove Visited Location
```http
DELETE /api/chat/context/visited
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:**
```json
{
  "location": "Hội An"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "visited_ids": ["loc_001"],
  "message": "Location removed from visited list"
}
```

---

#### Set Revisit Preference
```http
POST /api/chat/context/revisit
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:**
```json
{
  "allow_revisit": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "allow_revisit": true
}
```

---

#### Clear Chat Context
```http
POST /api/chat/context/clear
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "success": true,
  "message": "Context cleared successfully"
}
```

---

### Upload Endpoints

#### Upload File
```http
POST /api/upload
Content-Type: multipart/form-data
```

**Requires:** Valid session cookie

**Request Body:**
- `file`: File to upload (image/jpeg, image/png, image/webp)
- Max size: 5MB

**Success Response (200):**
```json
{
  "success": true,
  "file_url": "/uploads/abc123_image.jpg",
  "filename": "abc123_image.jpg"
}
```

**Error Responses:**
- `400` - No file provided or invalid file type
- `413` - File too large

---

### Travel Log Endpoints

#### Get Travel Logs
```http
GET /api/travel-log
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "success": true,
  "logs": [
    {
      "log_id": "...",
      "user_id": "...",
      "location_name": "Hội An",
      "visited_at": "2024-12-08T03:00:00Z",
      "notes": "Beautiful ancient town"
    }
  ]
}
```

---

#### Add Travel Log
```http
POST /api/travel-log
Content-Type: application/json
```

**Requires:** Valid session cookie

**Request Body:**
```json
{
  "location_name": "Hội An",
  "notes": "Beautiful ancient town",
  "visited_at": "2024-12-08"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "log": {
    "log_id": "...",
    "location_name": "Hội An",
    "notes": "Beautiful ancient town"
  }
}
```

---

## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| **Password Hashing** | PBKDF2-SHA256 with 16-byte salt |
| **Session Storage** | MongoDB with secure cookies |
| **CORS** | Configured allowed origins only |
| **Cookie Security** | HttpOnly, Secure, SameSite=None |
| **Input Validation** | Email regex, password length |
| **Environment Variables** | Sensitive data in `.env` |

## ✅ Validation Rules

### Email
- ✅ Required field
- ✅ Valid email format (regex validated)
- ✅ Unique in database

### Password
- ✅ Required field
- ✅ Minimum 6 characters
- ✅ Hashed before storage

## 🧪 Testing

### Using cURL

**Register:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plain_password": "password123"}'
```

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plain_password": "password123"}' \
  -c cookies.txt
```

**Send Chat Message:**
```bash
curl -X POST http://localhost:5000/api/chat/message \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"message": "Tìm bãi biển đẹp ở Đà Nẵng"}'
```

**Get Current User:**
```bash
curl http://localhost:5000/api/auth/me -b cookies.txt
```

**Logout:**
```bash
curl -X POST http://localhost:5000/api/auth/logout -b cookies.txt
```

### Using Postman

1. Import the API endpoints
2. Enable "Send cookies" in Postman settings
3. Test each endpoint sequentially

## 🚀 Deployment

### Production with Gunicorn

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Environment Setup

Ensure all environment variables are set in your production environment:
- `SECRET_KEY` - Strong random key
- `MONGODB_URI` - Production database URI
- `GEMINI_API_KEY` - Google Gemini API key
- `ALLOWED_ORIGINS` - Production frontend URLs
- `DEBUG=False` - Disable debug mode

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| **Flask** | Web framework |
| **Flask-Session** | Server-side sessions |
| **Flask-CORS** | Cross-origin support |
| **pymongo** | MongoDB driver |
| **mongoengine** | MongoDB ODM |
| **psycopg[binary,pool]** | PostgreSQL driver |
| **Werkzeug** | Password hashing |
| **python-dotenv** | Environment variables |
| **langchain** | LLM orchestration |
| **langchain-google-genai** | Gemini integration |
| **langgraph** | Agentic framework |
| **chromadb** | Vector database |
| **gunicorn** | Production WSGI server |

## 🛠️ Development

### Adding New Routes

1. Create a new blueprint in `routes/`
2. Import and register in `app.py`

Example:
```python
# routes/new_feature.py
from flask import Blueprint

new_bp = Blueprint('new_feature', __name__, url_prefix='/api/new')

@new_bp.route('/endpoint')
def endpoint():
    return {"message": "Hello"}
```

```python
# app.py
from backend.routes import auth_bp, chat_bp, new_bp, travel_log_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(new_bp)
app.register_blueprint(travel_log_bp)
```

### Adding New Models

1. Create model in `models/`
2. Export in `models/__init__.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused and small

## 🌐 CORS Configuration

Allowed origins are configured in `.env`:
```env
ALLOWED_ORIGINS=http://localhost:5173,https://production-url.com
```

Multiple origins are comma-separated.

## 📊 Database Schema

### Users Collection (MongoDB - AuthenticationDB)
```javascript
{
  "_id": ObjectId,
  "Email": String (unique),
  "HashedPassword": String,
  "Role": String (Student|Counsellor|AI),
  "CreatedAt": DateTime
}
```

### Sessions Collection (MongoDB - AuthenticationDB)
```javascript
{
  "_id": String,
  "data": Object,
  "expireAt": DateTime
}
```

### Conversations Collection (MongoDB - ChatDB)
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

## 🐛 Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'flask'`
```bash
pip install -r requirements.txt
```

**Issue:** `Connection refused` to MongoDB
- Check `MONGODB_URI` in `.env`
- Verify MongoDB Atlas IP whitelist
- Ensure network connectivity

**Issue:** CORS errors
- Add frontend URL to `ALLOWED_ORIGINS` in `.env`
- Restart server after changing `.env`

**Issue:** Chatbot not initializing
- Verify `GEMINI_API_KEY` is set
- Check PostgreSQL connection for conversation memory
- Set `CHATBOT_ENABLED=True` in `.env`

## 📄 License

MIT License

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note:** This is the backend server for VoyAIage Tourism Chatbot.