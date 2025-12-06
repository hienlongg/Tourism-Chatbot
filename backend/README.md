# VoyAIage Server 🚀

A robust, modular backend API for the VoyAIage tourism consultation platform, built with Flask and MongoDB.

## ✨ Features

- **Secure Authentication** - Password hashing with PBKDF2-SHA256
- **Session Management** - MongoDB-backed server-side sessions
- **RESTful API** - Clean, well-documented endpoints
- **Input Validation** - Email and password validation
- **CORS Support** - Configured for cross-origin requests
- **Modular Architecture** - Easy to maintain and extend

## 📍 Location Extraction Logic

1. **LLM Analysis**: The system analyzes the LLM's response to identify location descriptions.
2. **Name Extraction**: Extracts potential location names using Regex and NLP techniques.
3. **Strict CSV Matching**: Performs a strict match against the local database (`danh_sach_thong_tin_dia_danh_chi_tiet.csv`) to ensure high accuracy.
4. **OSM Basic Query**: If not found in CSV, queries OpenStreetMap (OSM) for standard location data.
5. **Advanced OSM Fallback**: If basic query fails, applies advanced cleaning (removing prefixes like "Công viên", "Bảo tàng") and name splitting to find matches.
6. **Frontend Response**: Returns a structured object containing Latitude, Longitude, Name, Description, and Image URL (if available).

## � Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- pip package manager

### Installation

```bash
# Navigate to server directory
cd Server

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will start at `http://localhost:5000`

## 📁 Project Structure

```
backend/
├── App.py                 # Application entry point
├── config.py              # Configuration management
├── .env                   # Environment variables (not in git)
├── .env.example          # Environment template
├── requirements.txt       # Python dependencies
├── models/               # Database models
│   ├── __init__.py      # Models initialization
│   ├── user.py          # User authentication model
│   └── chat.py          # Chat & message models
├── routes/              # API endpoints
│   ├── __init__.py     # Routes initialization
│   └── auth.py         # Authentication routes
├── middlewares/         # Request middlewares
│   ├── __init__.py    # Middlewares initialization
│   └── auth.py        # Authentication decorators
└── utils/              # Utility functions
    ├── __init__.py   # Utils initialization
    └── validators.py # Input validation
```

## ⚙️ Configuration

### Environment Variables

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# CORS Allowed Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173

# Server Configuration
PORT=5000
DEBUG=False
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

### Authentication Endpoints

#### Health Check
```http
GET /
```
Returns server status.

**Response:**
```json
{
  "message": "VoyAIage Server is Running"
}
```

---

#### Register New User
```http
POST /auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "Email": "user@example.com",
  "PlainPassword": "securepassword123"
}
```

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "UserID": "507f1f77bcf86cd799439011",
    "Email": "user@example.com",
    "Role": "Student"
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
POST /auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "Email": "user@example.com",
  "PlainPassword": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "UserID": "507f1f77bcf86cd799439011",
    "Email": "user@example.com",
    "Role": "Student"
  }
}
```

**Error Responses:**
- `401` - Invalid credentials
- `400` - Already logged in

---

#### Get Current User
```http
GET /auth/me
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "user": {
    "UserID": "507f1f77bcf86cd799439011",
    "Email": "user@example.com",
    "Role": "Student"
  }
}
```

**Error Response:**
- `401` - Authentication required

---

#### User Logout
```http
POST /auth/logout
```

**Requires:** Valid session cookie

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

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
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"Email": "test@example.com", "PlainPassword": "password123"}'
```

**Login:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"Email": "test@example.com", "PlainPassword": "password123"}' \
  -c cookies.txt
```

**Get Current User:**
```bash
curl http://localhost:5000/auth/me -b cookies.txt
```

**Logout:**
```bash
curl -X POST http://localhost:5000/auth/logout -b cookies.txt
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
| **Werkzeug** | Password hashing |
| **python-dotenv** | Environment variables |
| **gunicorn** | Production WSGI server |

## 🛠️ Development

### Adding New Routes

1. Create a new blueprint in `routes/`
2. Import and register in `App.py`

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
# App.py
from routes import auth_bp, new_bp

app.register_blueprint(auth_bp)
app.register_blueprint(new_bp)
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

### Users Collection
```javascript
{
  "_id": ObjectId,
  "Email": String (unique),
  "HashedPassword": String,
  "Role": String (Student|Counsellor|AI),
  "CreatedAt": DateTime
}
```

### Sessions Collection
```javascript
{
  "_id": String,
  "data": Object,
  "expireAt": DateTime
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

## 📄 License

MIT License

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note:** This is the backend server for VoyAIage.