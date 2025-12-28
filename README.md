# 🌏 Tourism Chatbot - Vietnamese AI Travel Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2+-orange.svg)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hugging Face](https://img.shields.io/badge/🤗-Hugging%20Face-yellow)](https://huggingface.co/spaces/hienlong/my-tourism-backend)

An intelligent conversational AI chatbot for Vietnamese tourism recommendations powered by RAG (Retrieval-Augmented Generation), LangGraph agentic workflows, and Flask REST API. Features multi-modal search with image capabilities, personalized travel logs, social features, and persistent conversation memory.

## ✨ Key Features

- 🤖 **LangGraph Agents** - Advanced agentic AI with tool use and state management
- 🔍 **RAG System** - Retrieval-Augmented Generation with ChromaDB vector store
- 🖼️ **Image Search** - Multi-modal search using CLIP for visual tourism discovery
- 📝 **Travel Logs** - Personal travel diary with location tracking
- 👥 **Social Posts** - Share travel experiences with rich media
- 💬 **Persistent Memory** - PostgreSQL-backed conversation checkpointing
- 🇻🇳 **Vietnamese Support** - Full Vietnamese language processing
- 🔐 **Authentication** - Secure user sessions with bcrypt encryption
- 🌊 **Streaming Responses** - Real-time LLM output for better UX

## 📁 Project Structure

```
Tourism-Chatbot/
├── app.py                        # Flask application entry point
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration for deployment
│
├── backend/                      # Backend REST API
│   ├── models/                   # Database models
│   │   ├── user.py              # User authentication model
│   │   ├── chat.py              # Chat history model
│   │   ├── post.py              # Social post model
│   │   └── travel_log.py        # Travel log model
│   ├── routes/                   # API endpoints
│   │   ├── authentication.py    # Auth (login, register, logout)
│   │   ├── chat.py              # Chat with tourism agent
│   │   ├── posts.py             # Social post CRUD
│   │   ├── travel_log.py        # Travel log management
│   │   └── upload.py            # File/image upload
│   ├── middlewares/
│   │   └── decorators.py        # Auth decorators & middleware
│   └── utils/                    # Utility functions
│       ├── validators.py        # Input validation
│       ├── post_validator.py    # Post content validation
│       ├── image_resolver.py    # Image URL resolution
│       └── location_extractor.py # Extract location from text
│
├── tourism_chatbot/              # AI Tourism Agent System
│   ├── agents/
│   │   ├── tourism_agent.py     # LangGraph agent with tools
│   │   └── tools.py             # RAG retrieval & location tools
│   ├── rag/
│   │   └── rag_engine.py        # Vector store & embeddings
│   ├── vision/
│   │   └── image_search.py      # CLIP-based image search
│   ├── database/
│   │   ├── connection.py        # DB connections (MongoDB, PostgreSQL)
│   │   ├── checkpointer.py      # LangGraph memory checkpointer
│   │   └── filtered_checkpointer.py # Filtered conversation history
│   ├── memory/
│   │   └── context_manager.py   # User session context
│   ├── clients/
│   │   ├── embedding_client.py  # Custom embedding API client
│   │   └── langchain_embedding_adapter.py # LangChain adapter
│   └── crawling_data/            # Data collection scripts
│       ├── crawl_desinations_description.py
│       └── crawl_images.py
│
├── data/
│   ├── raw/                      # Raw tourism data
│   │   ├── danh_sach_dia_danh.txt
│   │   ├── dia_danh_vn.json
│   │   └── crawled_images/
│   ├── processed/
│   │   ├── danh_sach_thong_tin_dia_danh_chi_tiet.csv
│   │   └── manifest.csv
│   └── vector_db/
│       └── chroma_tourism/       # ChromaDB vector database
│
├── stt/                          # Speech-to-text module
│   └── routes.py                 # STT API endpoints
│
├── test/                         # Test suite
│   ├── test_integration.py
│   ├── test_rag_functions.py
│   └── manual_rag_test.py
│
├── notebooks/                    # Jupyter notebooks
│   ├── RAG_Tourism_Recommendation.ipynb
│   ├── CLIP.ipynb
│   ├── Chatbot.ipynb
│   └── EDA.ipynb
│
└── uploads/                      # User-uploaded files
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- MongoDB (for session & app data storage)
- PostgreSQL (for LangGraph conversation checkpointing)
- Google Gemini API key (for LLM)
- Hugging Face account (optional, for embeddings)

### 2. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/hienlongg/Tourism-Chatbot.git
cd Tourism-Chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Databases

**MongoDB:**
```bash
# Start MongoDB locally or use MongoDB Atlas
# The app will use two databases:
# - Authentication (for sessions)
# - VoyAIage (for app data: travel logs, posts, locations)
```

**PostgreSQL:**
```bash
# For LangGraph conversation checkpointing
# Create a database named 'tourism_chatbot'
# The schema will be auto-created by LangGraph
```

### 4. Set Environment Variables

Create `.env` file in project root:
```bash
# API Keys
GEMINI_API_KEY=your-google-gemini-api-key

# Database URLs
MONGODB_URI=mongodb://localhost:27017
DATABASE_URL=postgresql://user:password@localhost:5432/tourism_chatbot

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-min-32-chars
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Optional: Custom Embedding API
EMBEDDING_API_URL=your-embedding-api-endpoint
```

**Getting API Keys:**
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas (free tier available)
- **Hugging Face**: https://huggingface.co/settings/tokens (for embeddings)

### 5. Run the Application

**Development Mode:**
```bash
python app.py
# API available at http://localhost:5000
```

**Production Mode (with Gunicorn):**
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
```

**Docker Deployment:**
```bash
docker build -t tourism-chatbot .
docker run -p 7860:7860 --env-file .env tourism-chatbot
```

## 🎯 Features & API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
  - Body: `{"username": "user", "email": "user@example.com", "password": "secure123"}`
- `POST /api/auth/login` - User login with session creation
  - Body: `{"username": "user", "password": "secure123"}`
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/auth/me` - Get current user info

### Chat & Tourism Agent
- `POST /api/chat` - Interact with tourism AI agent
  - Body: `{"message": "Tìm bãi biển đẹp ở Đà Nẵng", "allow_revisit": false}`
  - Response: Streaming SSE or JSON with recommendations
  - Features: RAG search, location filtering, conversation memory

### Travel Logs
- `POST /api/travel-log` - Create travel log entry
  - Body: `{"location": "Hội An", "description": "Beautiful ancient town", "images": [...]}`
- `GET /api/travel-log` - Get user's travel logs
- `PUT /api/travel-log/<log_id>` - Update travel log
- `DELETE /api/travel-log/<log_id>` - Delete travel log

### Social Posts
- `POST /api/posts` - Create new post
  - Body: `{"content": "Amazing trip!", "images": [...], "location": "Đà Lạt"}`
- `GET /api/posts` - Get all posts (with pagination)
- `GET /api/posts/<post_id>` - Get specific post
- `PUT /api/posts/<post_id>` - Update post
- `DELETE /api/posts/<post_id>` - Delete post
- `POST /api/posts/<post_id>/like` - Like/unlike post
- `POST /api/posts/<post_id>/comment` - Add comment

### File Upload
- `POST /api/upload` - Upload images or documents
  - Returns: File URL and metadata
  - Supports: Images (jpg, png, webp), documents

### User Chat Commands (Vietnamese)

#### Search for Places
```
"Tìm bãi biển đẹp ở miền Trung"
"Gợi ý thác nước hoang sơ"
"Chùa chiền cổ kính ở Huế"
"Địa điểm du lịch ở Đà Lạt"
```

#### Report Visited Locations
```
"Tôi đã từng đến Hội An"
"Đã ghé Đà Nẵng và Huế rồi"
"Tôi đã đi Sapa"
```

#### Control Revisit Suggestions
```
"Cho phép gợi ý lại"          # Allow suggesting visited places
"Không cho phép gợi ý lại"    # Only suggest new places
```

#### Image-based Search
```
"Tìm địa điểm giống trong ảnh này"  # Upload image
"Những nơi có phong cảnh tương tự"
```

## 🏗️ Architecture

### System Flow

```
┌─────────────┐
│   Client    │
│  (Web/App)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│          Flask REST API             │
│  ┌──────────────────────────────┐  │
│  │   Auth Middleware            │  │
│  │   (Session Management)       │  │
│  └──────────────┬───────────────┘  │
│                 ▼                   │
│  ┌──────────────────────────────┐  │
│  │   Route Handlers             │  │
│  │   - Chat                     │  │
│  │   - Travel Log               │  │
│  │   - Posts                    │  │
│  └──────────────┬───────────────┘  │
└─────────────────┼───────────────────┘
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
┌──────────────┐      ┌─────────────┐
│   MongoDB    │      │  Tourism    │
│              │      │   Agent     │
│ - Sessions   │      │  (LangGraph)│
│ - Users      │      └──────┬──────┘
│ - Posts      │             │
│ - Logs       │      ┌──────┴──────────┐
└──────────────┘      │                 │
                      ▼                 ▼
              ┌──────────────┐  ┌─────────────┐
              │  RAG Engine  │  │  LLM Agent  │
              │              │  │  (Gemini)   │
              │ - ChromaDB   │  └─────────────┘
              │ - Embeddings │
              │ - CLIP Image │
              └──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ PostgreSQL   │
              │ (Checkpoints)│
              └──────────────┘
```
    │
    ├── Tool: retrieve_context
    │   ├── Query Vector Store (ChromaDB)
    │   ├── Filter by Visit History
    │   ├── Build Context
    │   └── Return Results
    │
    ├── LLM (Gemini): Process Context
    ├── State Management: Track conversation
    └── Checkpointing (PostgreSQL): Persist memory
    ↓
Structured Response
    ↓
Client
```

### Component Architecture

#### 1. Flask Backend (`app.py`, `backend/`)

**Request Flow:**
1. Receives HTTP request
2. Validates session/user (Flask-Session with MongoDB)
3. Routes to appropriate handler
4. Calls tourism agent
5. Returns JSON response

**Routes:**
- Authentication: Login, register, session management
- Chat: Message routing to tourism agent
- Upload: File handling with validation

#### 2. Tourism Agent (`tourism_chatbot/agents/`)

**LangGraph Implementation:**
- **Nodes**: Different processing stages
- **Edges**: Conditional routing based on state
- **State**: Manages conversation history, user context
- **Tools**: Integrates with RAG engine via `retrieve_context`
- **Checkpointer**: PostgreSQL-backed memory persistence

**Agent Behavior:**
```python
# Example of agent interaction
User Query → Agent Process → Tool Call → Vector Search → LLM → Response
                                    ↓
                           Context Building
                                    ↓
                           Filtered Results
```

#### 3. RAG Engine (`tourism_chatbot/rag/`)

**Data Pipeline:**
1. Load CSV with tourism locations
2. Generate embeddings (HuggingFace: all-MiniLM-L6-v2)
3. Store in ChromaDB (persistent vector store)
4. Retrieve similar locations on query

**Recommendation Generation:**
1. Vector similarity search (semantic)
2. Filter by visit history
3. Build context from top-K results
4. Generate response using Gemini LLM

#### 4. Database Layer (`tourism_chatbot/database/`)

**MongoDB:**
- User sessions (Flask-Session)
- User profiles
- Chat history metadata

**PostgreSQL:**
- LangGraph checkpoints (memory)
- Thread state persistence
- Conversation memory

**ChromaDB:**
- Vector embeddings for tourism locations
- Semantic search index
- Persistent vector store

#### 5. Memory Management (`tourism_chatbot/memory/`)

**Context Manager:**
- Tracks user visited locations
- Manages conversation state
- Provides context filtering
- Session lifecycle management

**LangGraph Checkpointer:**
- Persists agent state
- Enables multi-turn conversations
- Recovers from interruptions
- Supports conversation branching

## 📊 Session State Management

### Per-User Session Variables

**MongoDB Session Storage:**
```python
# Flask-Session automatically manages these
session['user_id']           # str: Current user ID
session['username']          # str: Username
session['visited_ids']       # List[str]: Visited location IDs
session['allow_revisit']     # bool: Allow revisit suggestions
session['last_activity']     # datetime: Last activity timestamp
```

### LangGraph State Management

**Agent State Variables:**
```python
# Persisted in PostgreSQL checkpoint
messages: List[BaseMessage]  # Conversation history
context: Dict              # User context and preferences
visited_locations: List    # Visited place tracking
allow_revisit: bool        # Revisit control flag
```

### State Persistence
- **Session**: Stored in MongoDB per browser session
- **Memory**: Persisted in PostgreSQL via LangGraph checkpointer
- **Duration**: Maintained during user session lifetime
- **Data Recovery**: Can resume conversation from checkpoints

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `MONGODB_URI` | Yes | - | MongoDB connection string |
| `DATABASE_URL` | Yes | - | PostgreSQL connection for checkpointing |
| `FLASK_ENV` | No | production | Flask environment (development/production) |
| `SECRET_KEY` | Yes | - | Flask session secret key |
| `ALLOWED_ORIGINS` | No | localhost:3000 | CORS allowed origins |
| `GOOGLE_CLIENT_ID` | Yes | - | Google OAuth Client ID |
| `GOOGLE_CLIENT_ID` | Yes | - | Google OAuth Client ID |

### Model Configuration (in `tourism_chatbot/rag/rag_engine.py`)

```python
# Data paths
CSV_PATH = 'data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv'
CHROMA_DB_PATH = 'data/vector_db/chroma_tourism'

# Model names
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
GEMINI_MODEL = 'gemini-2.5-flash-lite'

# Search parameters
TOP_K_RESULTS = 5              # Number of locations to retrieve
TEMPERATURE = 0.7              # LLM creativity level
```

### Database Configuration (in `config.py`)

```python
# MongoDB for sessions
MONGODB_URI = "mongodb://localhost:27017"
SESSION_MONGODB_DB = "Authentication"
SESSION_MONGODB_COLLECT = "Sessions"

# PostgreSQL for LangGraph
DATABASE_URL = "postgresql://user:password@localhost:5432/tourism_chatbot"

# Flask
FLASK_ENV = "development"
SECRET_KEY = "your-secret-key-here"
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest test/

# Run with coverage
pytest test/ --cov=tourism_chatbot --cov=backend

# Run specific test file
pytest test/test_integration.py -v
```

### Integration Testing

**Manual API Testing with cURL:**

```bash
# 1. Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"pass123"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass123"}' \
  -c cookies.txt

# 3. Send chat message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"message":"Tìm bãi biển đẹp ở Đà Nẵng"}'

# 4. Check visit history
curl -X GET http://localhost:5000/api/chat/history \
  -b cookies.txt
```

### Testing with Python

```python
from tourism_chatbot.rag.rag_engine import initialize_rag_system, generate_recommendation

# Initialize RAG system
vector_store, llm, embeddings = initialize_rag_system()

# Test recommendation generation
result = generate_recommendation(
    vector_store=vector_store,
    llm=llm,
    user_query="Tìm thác nước đẹp",
    user_visited_ids=[],
    allow_revisit=False,
    verbose=True
)

print("Response:", result['final_response'])
print("Retrieved locations:", result['retrieved_locations'])
```

### Test Scenarios

1. **Basic Search**
   - Query: "Tìm bãi biển đẹp"
   - Expected: List of beaches with descriptions

2. **Visit History**
   - Command: "Tôi đã từng đến Đà Nẵng"
   - Query: "Tìm bãi biển đẹp"
   - Expected: Excludes Đà Nẵng beaches

3. **Revisit Control**
   - Command: "Cho phép gợi ý lại"
   - Query: "Tìm bãi biển đẹp"
   - Expected: Includes previously visited places

4. **Session Persistence**
   - Login with user
   - Add visited location
   - Refresh page
   - Expected: Visited locations still available

5. **Conversation Memory**
   - Send multiple messages
   - Verify context carried across messages
   - Check LangGraph checkpoint recovery

## 🔍 How It Works

### 1. User Authentication Phase

```
User Request
    ↓
Check Session Cookie
    ├─ Valid? → Load user context
    └─ Invalid? → Redirect to login
    ↓
Verify credentials (MongoDB)
    ↓
Create session (Flask-Session)
    ↓
Allow API access
```

### 2. Message Processing Phase

```
Receive Chat Message
    ↓
Load User Session
    ├─ Get user_id
    ├─ Get visited_ids
    └─ Get allow_revisit flag
    ↓
Initialize LangGraph Agent
    ├─ Load checkpoint (if exists)
    └─ Set up state
    ↓
Process Message
    │
    ├─ Detect command type:
    │   ├─ Report visited? → Update context
    │   ├─ Revisit control? → Update flag
    │   └─ Search query? → Call agent
    │
    ├─ Agent Execution:
    │   ├─ Call retrieve_context tool
    │   ├─ Vector search in ChromaDB
    │   ├─ Filter by visit history
    │   ├─ Build context
    │   └─ Generate response (Gemini)
    │
    └─ Stream response to client
    ↓
Save checkpoint (PostgreSQL)
    ↓
Return structured response
```

### 3. RAG Pipeline Details

```
Query: "Tìm bãi biển đẹp ở miền Trung"
    ↓
1. Embedding Generation
   - Encode query using HuggingFace model
   - Create query vector
    ↓
2. Vector Search (ChromaDB)
   - Find K-nearest neighbors
   - Retrieve top-5 similar locations
    ↓
3. History Filtering
   - Check allow_revisit flag
   - Remove visited locations if needed
    ↓
4. Context Building
   - Format location details
   - Include metadata
   - Create LLM prompt
    ↓
5. LLM Generation (Gemini)
   - Process context
   - Generate natural Vietnamese response
   - Stream output
    ↓
Response: "Tôi gợi ý cho bạn những bãi biển đẹp..."
```

### 4. Conversation Memory Flow

```
Message 1: "Tôi muốn đi thác nước"
    ↓
    Agent → retrieve_context → filter → response
    ↓
    Save to PostgreSQL checkpoint
    ↓

Message 2: "Gợi ý thêm những nơi khác"
    ↓
    Load checkpoint from PostgreSQL
    ↓
    Agent has context from Message 1
    ↓
    Generate contextual response
    ↓
    Update checkpoint

(Conversation continues with memory...)
```

## 📝 API Key Setup

### Getting Google Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### Setting the API Key in `.env`

```bash
# Create .env file
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Verify Setup

```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {api_key is not None}")
```

### Setting up Google Login

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Keep the project selected. Go to **APIs & Services** > **OAuth consent screen** and configure it.
4. Go to **Credentials**, click **Create Credentials** > **OAuth client ID**.
5. Select **Web application**.
6. Add your frontend URL (e.g., `http://localhost:5173`) to **Authorized JavaScript origins**.
7. Copy the **Client ID** and add it to your `.env` file as `GOOGLE_CLIENT_ID`.


### Setting up Google Login

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Keep the project selected. Go to **APIs & Services** > **OAuth consent screen** and configure it.
4. Go to **Credentials**, click **Create Credentials** > **OAuth client ID**.
5. Select **Web application**.
6. Add your frontend URL (e.g., `http://localhost:5173`) to **Authorized JavaScript origins**.
7. Copy the **Client ID** and add it to your `.env` file as `GOOGLE_CLIENT_ID`.


## 💻 Development Workflow

### Local Development Setup

```bash
# 1. Start PostgreSQL (for checkpointing)
# Using Docker:
docker run --name postgres-tourism -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=tourism_chatbot -p 5432:5432 -d postgres:15

# 2. Start MongoDB (for sessions)
# Using Docker:
docker run --name mongo-tourism -p 27017:27017 -d mongo:latest

# 3. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set environment variables
cp .env.example .env  # Edit with your values

# 6. Run Flask development server
python app.py

# 7. Run tests (optional)
pytest test/ -v
```

### Database Commands

**PostgreSQL:**
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d tourism_chatbot

# Create tables (automatic on first run)
# Check LangGraph tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public';
```

**MongoDB:**
```bash
# Connect to MongoDB
mongosh --host localhost:27017

# List collections
db.Sessions.find().pretty()
db.users.find().pretty()
```

### Development Tips

- **Hot Reload**: Flask development server supports auto-reload on file changes
- **Debug Mode**: Set `FLASK_ENV=development` for better error messages
- **Logging**: Check `app.py` for logging configuration
- **API Testing**: Use cURL or Postman for API testing
- **Database Reset**: Delete checkpointer data to reset conversation memory

## 🐛 Troubleshooting

### Error: "GEMINI_API_KEY not found"
**Cause**: API key not set in environment
**Solution**: 
```bash
# Set in .env file
echo "GEMINI_API_KEY=your-key-here" > .env
# Or export as environment variable
export GEMINI_API_KEY="your-key-here"
```

### Error: "Vector store not found"
**Cause**: ChromaDB files missing or CSV not found
**Solution**: 
- Verify `data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv` exists
- Re-initialize ChromaDB:
```python
from tourism_chatbot.rag.rag_engine import load_data_and_create_docs, initialize_vectorstore
documents = load_data_and_create_docs()
initialize_vectorstore(documents, force_recreate=True)
```

### Error: "Module 'tourism_chatbot' not found"
**Cause**: Not in correct directory or PYTHONPATH not set
**Solution**: 
```bash
# Run from project root
cd /home/hienlong/projects/Tourism-Chatbot
python app.py

# Or set PYTHONPATH
export PYTHONPATH=/home/hienlong/projects/Tourism-Chatbot:$PYTHONPATH
```

### Error: "Connection refused" (PostgreSQL/MongoDB)
**Cause**: Databases not running
**Solution**: 
```bash
# Start PostgreSQL
docker start postgres-tourism
# Or with psql if local install
sudo systemctl start postgresql

# Start MongoDB
docker start mongo-tourism
# Or with local install
mongod
```

### Error: "CORS origin not allowed"
**Cause**: Frontend URL not in ALLOWED_ORIGINS
**Solution**: Update `.env`:
```bash
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000,http://your-frontend.com"
```

### Slow First Response
**Cause**: First request triggers model loading and vector store initialization
**Solution**: This is normal. Subsequent requests will be faster.

### Conversation Memory Not Persisting
**Cause**: PostgreSQL checkpointer not properly configured
**Solution**: 
```bash
# Verify DATABASE_URL is set correctly
# Check PostgreSQL connection
psql -h localhost -U postgres -d tourism_chatbot
# Restart Flask server
```

## 🚢 Deployment

### Local Development
```bash
python app.py
# Runs on http://localhost:5000
```

### Production with Gunicorn
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
# 2 workers, bind to all interfaces, 120s timeout for LLM processing
```

### Docker Deployment

**Build and Run:**
```bash
# Build image
docker build -t tourism-chatbot .

# Run container
docker run -p 7860:7860 --env-file .env tourism-chatbot
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - mongodb

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tourism_chatbot
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  postgres_data:
  mongo_data:
```

### Hugging Face Spaces Deployment

**1. Create a new Space:**
- Go to https://huggingface.co/new-space
- Choose **Docker** as SDK
- Clone your Space repository

**2. Configure environment variables in Space settings:**
```bash
# Required secrets (mark as secret)
GEMINI_API_KEY=your-key
MONGODB_URI=mongodb+srv://...
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
```

**3. Push your code:**
```bash
# Add HF Space as remote
git remote add space https://huggingface.co/spaces/username/space-name
git push space main
```

**4. Space Configuration:**
The `Dockerfile` is already configured for HF Spaces (port 7860).

**Important Notes:**
- HF Spaces runs on port 7860 by default
- Use external MongoDB (MongoDB Atlas) and PostgreSQL (ElephantSQL/Render)
- Keep vector database in the repository or use persistent storage
- Set all environment variables in Space settings (not in code)

### Cloud Platform Deployments

**Render:**
```bash
# Create new Web Service
# Connect GitHub repository
# Add environment variables
# Deploy command: gunicorn app:app --bind 0.0.0.0:$PORT
```

**Railway:**
```bash
# Create new project from GitHub
# Add PostgreSQL and MongoDB services
# Configure environment variables
# Deploy automatically on push
```

**Heroku:**
```bash
# Create Procfile (already included)
heroku create tourism-chatbot
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set GEMINI_API_KEY=your-key
git push heroku main
```

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      MONGODB_URI: mongodb://mongodb:27017
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/tourism_chatbot
      FLASK_ENV: production
    depends_on:
      - postgres
      - mongodb

volumes:
  postgres_data:
  mongo_data:
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

### Environment-Specific Configuration

**Development:**
```bash
FLASK_ENV=development
DEBUG=True
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"
```

**Staging/Production:**
```bash
FLASK_ENV=production
DEBUG=False
ALLOWED_ORIGINS="https://yourdomain.com"
```

## 📦 Dependencies

### Core Framework & Web
```
Flask>=2.3              # Web framework
Flask-Session>=0.5.0    # Session management
Flask-Cors>=3.1         # CORS support
Werkzeug>=2.3          # WSGI utilities
gunicorn>=21.0         # WSGI HTTP server
```

### Database & Storage
```
pymongo>=4.5            # MongoDB driver
mongoengine>=0.29.1     # MongoDB ODM
psycopg[binary,pool]>=3.1.0  # PostgreSQL driver
chromadb>=0.4.0         # Vector database
```

### LangChain & AI
```
langchain>=0.3.0        # LLM orchestration
langchain-core>=0.3.0   # Core abstractions
langchain-google-genai>=2.0.0    # Gemini integration
langchain-huggingface>=0.1.0     # HuggingFace embeddings
langchain-chroma>=0.1.0  # ChromaDB integration
langgraph>=0.2.0        # Agentic framework
langgraph-checkpoint-postgres>=2.0.0  # Checkpointing
```

### ML & Embeddings
```
sentence-transformers>=2.2.0  # Embedding models
torch>=2.0.0                  # PyTorch
```

### Data Processing
```
pandas>=2.0.0           # Data manipulation
python-dotenv>=1.0.0    # Environment variables
```

See `requirements.txt` for complete list with pinned versions.

## 🎨 Customization

### Modify Agent Behavior

**System Prompt (in `tourism_chatbot/agents/tourism_agent.py`):**
```python
prompt = """Bạn là một hướng dẫn viên du lịch Việt Nam...
# Customize this prompt to change agent behavior
"""
```

### Change Vector Search Results

```python
# In tourism_chatbot/rag/rag_engine.py
TOP_K_RESULTS = 10  # Default: 5
```

### Modify LLM Temperature

```python
# Higher = more creative, Lower = more factual
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.9,  # Default: 0.7
)
```

### Change Embedding Model

```python
# In rag_engine.py
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
# Or other HuggingFace models
```

### Add Custom Tools to Agent

```python
# In tourism_chatbot/agents/tools.py
from langchain.tools import tool

@tool
def custom_tool(query: str) -> str:
    """Custom tool description"""
    # Implementation
    return result

# Then add to agent
tools = [retrieve_context, custom_tool]
```

### Customize Filtering Logic

```python
# In tourism_chatbot/memory/context_manager.py
def filter_visited_locations(locations, visited_ids, allow_revisit):
    """Customize filtering behavior"""
    if allow_revisit:
        return locations
    return [loc for loc in locations if loc['id'] not in visited_ids]
```

## 📄 Project Documentation

### Core Modules

- **`app.py`**: Flask application entry point with blueprint registration
- **`config.py`**: Configuration management for all environments
- **`requirements.txt`**: Python dependencies with versions

### Backend Modules

- **`backend/routes/`**: Flask route handlers for authentication, chat, upload
- **`backend/models/`**: Data models for users and chat history
- **`backend/middlewares/`**: Custom Flask middlewares and decorators
- **`backend/utils/`**: Validation and utility functions

### Tourism AI Modules

- **`tourism_chatbot/agents/`**: LangGraph agent definition and tools
- **`tourism_chatbot/rag/`**: RAG engine for retrieval and generation
- **`tourism_chatbot/database/`**: Database connections and checkpointing
- **`tourism_chatbot/memory/`**: Session and context management
- **`tourism_chatbot/utils/`**: Threading and utility functions

### Data

- **`data/raw/`**: Original data files and crawled images
- **`data/processed/`**: Cleaned and processed location CSV
- **`data/vector_db/`**: ChromaDB persistent vector store

## 🔗 Related Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Guidelines:**
- Follow PEP 8 style guide for Python code
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 👥 Authors & Support

**Maintainer:** [@hienlongg](https://github.com/hienlongg)

**For issues and questions:**
- 🐛 [Report bugs](https://github.com/hienlongg/Tourism-Chatbot/issues)
- 💡 [Request features](https://github.com/hienlongg/Tourism-Chatbot/issues)
- 📧 Contact: your-email@example.com

## 🙏 Acknowledgments

- Google Gemini for LLM capabilities
- LangChain team for the amazing framework
- HuggingFace for embedding models
- ChromaDB for vector storage
- Vietnamese tourism data sources

---

**Last Updated:** December 28, 2025  
**Version:** 2.1.0  
**Python:** 3.11+  
**Status:** ✅ Active Development

**Demo:** [Hugging Face Space](https://huggingface.co/spaces/hienlong/my-tourism-backend)  
**Repository:** [GitHub](https://github.com/hienlongg/Tourism-Chatbot)
