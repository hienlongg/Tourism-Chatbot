# Tourism Chatbot - Chainlit Application

A conversational AI chatbot for Vietnamese tourism recommendations using RAG (Retrieval-Augmented Generation).

## 📁 Project Structure

```
tourism_chatbot/
├── cl_app.py              # Main Chainlit application
├── rag/
│   ├── __init__.py        # Package initialization
│   └── rag_engine.py      # Core RAG functionality
├── crawling_data/         # Data scraping utilities
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install chainlit langchain langchain-google-genai langchain-huggingface chromadb pandas
```

### 2. Set API Key

```bash
# Set your Google Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Or add to .env file
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Run the Application

```bash
# Navigate to tourism_chatbot directory
cd /mnt/d/source/AI/SmartTraveling/tourism_chatbot

# Run Chainlit app with watch mode
chainlit run cl_app.py -w
```

The app will start on `http://localhost:8000`

## 🎯 Features

### Core Functionality
- **Semantic Search**: Find tourism locations based on natural language queries
- **Visit History Tracking**: Remember places user has visited
- **Smart Filtering**: Exclude visited places from recommendations (configurable)
- **Streaming Responses**: Real-time LLM output for better UX
- **Vietnamese Language**: Full support for Vietnamese text

### User Commands

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
User Query
    ↓
Command Detection (visited/revisit control)
    ↓
RAG Pipeline:
    1. Vector Similarity Search (ChromaDB)
    2. History Filtering
    3. Context Building
    4. LLM Generation (Gemini)
    ↓
Stream Response to User
```

### Key Components

#### 1. `rag_engine.py` - Core RAG Functionality

**Data Loading**
- Loads CSV with tourism locations
- Generates unique `loc_id` using slugify
- Creates LangChain Documents with metadata

**Vector Store**
- Uses HuggingFace embeddings (`all-MiniLM-L6-v2`)
- Stores in ChromaDB for persistent storage
- Enables semantic similarity search

**Recommendation Generation**
- Retrieves top-K similar locations
- Filters based on visit history
- Generates context for LLM
- Calls Gemini for friendly Vietnamese response

#### 2. `cl_app.py` - Chainlit Application

**Startup Handler** (`@cl.on_chat_start`)
- Initializes RAG system (vector store, LLM, embeddings)
- Sets up user session state
- Sends welcome message

**Message Handler** (`@cl.on_message`)
- Detects special commands
- Updates session state
- Generates recommendations with streaming
- Displays statistics

**Session State Management**
- `visited_ids`: List of location IDs user has visited
- `allow_revisit`: Boolean for revisit control

## 📊 Session State Management

### Per-User Session Variables

```python
cl.user_session.set("visited_ids", [])      # List[str]: Visited location IDs
cl.user_session.set("allow_revisit", False) # bool: Allow revisit suggestions
```

### State Persistence
- Session state is maintained **per browser tab**
- Data is cleared when chat ends (`@cl.on_chat_end`)
- No cross-session persistence (stateless between restarts)

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `CHAINLIT_PORT` | No | 8000 | Port to run app on |

### Model Configuration (in `rag_engine.py`)

```python
CSV_PATH = 'data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv'
CHROMA_DB_PATH = 'data/vector_db/chroma_tourism'
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
GEMINI_MODEL = 'gemini-2.5-flash-lite'
TOP_K_RESULTS = 5  # Number of locations to retrieve
```

## 🧪 Testing

### Manual Testing

1. **Basic Search**
   ```
   User: "Tìm bãi biển đẹp"
   Expected: List of beaches with descriptions
   ```

2. **Visit History**
   ```
   User: "Tôi đã từng đến Đà Nẵng"
   Expected: Confirmation message
   
   User: "Tìm bãi biển đẹp"
   Expected: Excludes Đà Nẵng beaches
   ```

3. **Revisit Control**
   ```
   User: "Cho phép gợi ý lại"
   Expected: Includes visited places
   ```

### CLI Testing (Direct Import)

```python
from rag.rag_engine import initialize_rag_system, generate_recommendation

# Initialize
vector_store, llm, embeddings = initialize_rag_system()

# Test
result = generate_recommendation(
    vector_store=vector_store,
    llm=llm,
    user_query="Tìm thác nước đẹp",
    user_visited_ids=[],
    allow_revisit=False,
    verbose=True
)

print(result['final_response'])
```

## 🔍 How It Works

### 1. Startup Phase
```
User opens chat
    ↓
on_chat_start() triggered
    ↓
Check if RAG system loaded
    ↓
If not loaded:
    - Load CSV data
    - Initialize embeddings model
    - Load/create ChromaDB vector store
    - Initialize Gemini LLM
    ↓
Initialize session state:
    - visited_ids = []
    - allow_revisit = False
    ↓
Send welcome message
```

### 2. Message Processing Phase
```
User sends message
    ↓
on_message() triggered
    ↓
Detect command type:
    - Visited location? → Update visited_ids
    - Revisit control? → Update allow_revisit
    - Regular query? → Generate recommendation
    ↓
If recommendation:
    1. Vector search in ChromaDB
    2. Filter by visit history
    3. Build context for LLM
    4. Stream Gemini response
    5. Display statistics
```

### 3. History Management
```
visited_ids tracking:
    - Stored per session (browser tab)
    - Uses slugified location names as IDs
    - Persists during session lifetime
    - Cleared on chat end

allow_revisit flag:
    - Controls filtering behavior
    - False: Only new places
    - True: Include visited places
```

## 📝 API Key Setup

### Getting Google Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### Setting the API Key

**Option 1: Environment Variable (Linux/Mac)**
```bash
export GEMINI_API_KEY="your-key-here"
```

**Option 2: .env File**
```bash
echo "GEMINI_API_KEY=your-key-here" > .env
```

**Option 3: Direct in Code (Not Recommended)**
```python
import os
os.environ['GEMINI_API_KEY'] = 'your-key-here'
```

## 🐛 Troubleshooting

### Error: "GEMINI_API_KEY not found"
**Solution**: Set the API key using one of the methods above

### Error: "Vector store not found"
**Solution**: Make sure CSV file exists at `data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv`

### Error: "Module 'rag' not found"
**Solution**: Run from `tourism_chatbot/` directory, not from `tourism_chatbot/rag/`

### Slow First Response
**Reason**: First message triggers embedding model loading and vector store initialization
**Solution**: This is normal. Subsequent messages will be faster.

## 🚢 Deployment

### Local Development
```bash
chainlit run cl_app.py -w
```

### Production
```bash
chainlit run cl_app.py --port 8000 --host 0.0.0.0
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["chainlit", "run", "cl_app.py", "--host", "0.0.0.0"]
```

## 📦 Dependencies

```
chainlit>=1.0.0
langchain>=0.1.0
langchain-google-genai>=1.0.0
langchain-huggingface>=0.0.1
chromadb>=0.4.0
pandas>=2.0.0
sentence-transformers>=2.0.0
```

## 🎨 Customization

### Change Number of Results
```python
# In rag_engine.py
TOP_K_RESULTS = 10  # Default: 5
```

### Modify LLM Temperature
```python
# In rag_engine.py, initialize_llm()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.9,  # Higher = more creative (default: 0.7)
)
```

### Change Embedding Model
```python
# In rag_engine.py
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
```

## 📄 License

This project is part of the SmartTraveling system.

## 👥 Support

For issues or questions, contact the development team.
