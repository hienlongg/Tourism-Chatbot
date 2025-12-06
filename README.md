# Tourism Chatbot - Vietnamese AI Travel Assistant

A conversational AI chatbot for Vietnamese tourism recommendations using RAG (Retrieval-Augmented Generation), LangGraph agents, and Flask backend with session management.

## 📁 Project Structure

```
Tourism-Chatbot/
├── app.py                        # Flask application entry point
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
│
├── backend/
│   ├── models/                   # SQLAlchemy/MongoEngine models
│   │   ├── user.py              # User model
│   │   └── chat.py              # Chat history model
│   ├── routes/
│   │   ├── authentication.py    # Auth endpoints (login, register, logout)
│   │   ├── chat.py              # Chat endpoint integration with tourism agent
│   │   └── upload.py            # File upload handling
│   ├── middlewares/
│   │   └── decorators.py        # Custom middleware/decorators
│   └── utils/
│       └── validators.py        # Input validation utilities
│
├── tourism_chatbot/              # Tourism AI agent system
│   ├── agents/
│   │   ├── tourism_agent.py     # LangGraph tourism agent with tool use
│   │   └── tools.py             # Agent tools (retrieve_context, etc.)
│   ├── rag/
│   │   ├── __init__.py
│   │   └── rag_engine.py        # RAG engine (embeddings, vector store)
│   ├── database/
│   │   ├── connection.py        # Database connections (MongoDB, PostgreSQL)
│   │   └── checkpointer.py      # LangGraph checkpointer for memory
│   ├── memory/
│   │   └── context_manager.py   # User context/session management
│   ├── crawling_data/
│   │   ├── crawl_desinations_description.py
│   │   └── crawl_images.py
│   └── utils/
│       └── thread_utils.py      # Threading utilities
│
├── data/
│   ├── raw/                      # Raw data and images
│   │   ├── danh_sach_dia_danh.txt
│   │   ├── dia_danh_vn.json
│   │   └── crawled_images/       # Tourism location images
│   ├── processed/
│   │   ├── danh_sach_thong_tin_dia_danh_chi_tiet.csv  # Processed locations
│   │   └── manifest.csv
│   └── vector_db/
│       └── chroma_tourism/       # ChromaDB vector store
│
├── test/
│   └── test_integration.py       # Integration tests
│
├── notebooks/                    # Jupyter notebooks for exploration
│   ├── Chatbot.ipynb
│   ├── RAG_Tourism_Recommendation.ipynb
│   ├── CLIP.ipynb
│   └── EDA.ipynb
│
└── uploads/                      # User-uploaded files
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- MongoDB (for session storage)
- PostgreSQL (for LangGraph checkpointing)
- Google Gemini API key

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
# Start MongoDB (if using local installation)
# Or use MongoDB Atlas cloud service
# Update MONGODB_URI in config.py
```

**PostgreSQL:**
```bash
# For LangGraph checkpointing
# Create a database and update DATABASE_URL in config.py
# The schema will be created automatically
```

### 4. Set Environment Variables

Create `.env` file in project root:
```bash
# API Keys
GEMINI_API_KEY="your-google-gemini-api-key"

# Database URLs
MONGODB_URI="mongodb://localhost:27017"
DATABASE_URL="postgresql://user:password@localhost:5432/tourism_chatbot"

# Flask Configuration
FLASK_ENV="development"
SECRET_KEY="your-secret-key"

# CORS allowed origins
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"
```

Get your Google Gemini API key from: https://makersuite.google.com/app/apikey

### 5. Run the Application

```bash
# Start Flask development server
python app.py

# The API will be available at http://localhost:5000
```

## 🎯 Features

### Core Functionality
- **LangGraph Tourism Agent**: Agentic AI using LangChain with tool use and state management
- **Semantic Search**: Find tourism locations using vector similarity (ChromaDB)
- **RAG System**: Retrieval-Augmented Generation for accurate tourist information
- **User Sessions**: Persistent user sessions with visit history tracking
- **History Management**: Remember visited places and filter revisit suggestions
- **Streaming Responses**: Real-time LLM output for better user experience
- **Vietnamese Language**: Full support for Vietnamese text and culture
- **Multi-user Support**: MongoDB-backed session management
- **Conversation Memory**: PostgreSQL-based checkpointing with LangGraph

### REST API Endpoints

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

#### Chat
- `POST /api/chat` - Send message to tourism agent
  - Request: `{"message": "Tìm bãi biển đẹp ở Đà Nẵng", "allow_revisit": false}`
  - Response: `{"response": "...", "visited_locations": [...], "metadata": {...}}`

#### Upload
- `POST /api/upload` - Upload images or documents
  - Returns: File URL and metadata

### User Commands (Examples)

#### 1. Search for Places
```
"Tìm bãi biển đẹp ở miền Trung"
"Tôi muốn đi thác nước hoang sơ"
"Gợi ý chùa chiền cổ kính"
```

#### 2. Report Visited Locations
```
"Tôi đã từng đến Hội An"
"Đã ghé Đà Nẵng và Huế"
"Tôi đã đi Sapa"
```

#### 3. Control Revisit Suggestions
```
"Cho phép gợi ý lại"          # Allow suggesting visited places
"Không cho phép gợi ý lại"    # Only suggest new places
```

## 🏗️ Architecture

### System Flow

```
Client Request
    ↓
Flask Route Handler
    ↓
Session/User Validation
    ↓
LangGraph Tourism Agent
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
gunicorn -w 4 -b 0.0.0.0:5000 app:app
# 4 workers, bind to all interfaces on port 5000
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Set environment
ENV FLASK_ENV=production

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
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
- [Gemini API Documentation](https://ai.google.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

## 📄 License

This project is part of the Tourism Chatbot system.

## 👥 Support

For issues, questions, or feature requests:
1. Check existing GitHub issues
2. Review troubleshooting section
3. Contact the development team

---

**Last Updated**: December 2024
**Version**: 2.0.0
**Python**: 3.10+
**Status**: Active Development
