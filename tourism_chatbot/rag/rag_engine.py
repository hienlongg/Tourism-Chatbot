"""
RAG Tourism Recommendation Engine

This module contains the core RAG (Retrieval-Augmented Generation) functionality
for Vietnamese tourism recommendations. It handles data loading, document creation,
vector store initialization, and recommendation generation using LangChain and Gemini.

Key Components:
- Data loading and processing from CSV
- Document creation with metadata
- Vector embeddings using HuggingFace
- ChromaDB vector store for semantic search
- LLM-based recommendation generation with Gemini

"""

import pandas as pd
import unicodedata
import re
import os
from typing import List, Dict, Tuple, Optional
import warnings

# LangChain imports
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

# Application imports
from config import Config

warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

# Import configuration from config.py
CSV_PATH = Config.RAG_CSV_PATH
CHROMA_DB_PATH = Config.RAG_CHROMA_DB_PATH
EMBEDDING_MODEL = Config.RAG_EMBEDDING_MODEL
GEMINI_MODEL = Config.RAG_GEMINI_MODEL
TOP_K_RESULTS = Config.RAG_TOP_K_RESULTS
LLM_TEMPERATURE = Config.RAG_LLM_TEMPERATURE
GEMINI_API_KEY = Config.GEMINI_API_KEY


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def slugify(value: str) -> str:
    """
    Convert Vietnamese text with diacritics into a URL-safe slug.
    
    Purpose: Create unique, safe identifiers for each location.
    
    Example:
        "Khu nhà công tử Bạc Liêu" -> "khu_nha_cong_tu_bac_lieu"
        "Thác Khe Vằn" -> "thac_khe_van"
    
    Args:
        value: Vietnamese location name with diacritics
    
    Returns:
        Lowercase slug with underscores (URL-safe)
    """
    # Step 1: Convert Vietnamese 'đ' to 'd' (not handled by NFKD)
    value = str(value).replace("đ", "d").replace("Đ", "D")
    
    # Step 2: Remove Vietnamese diacritics using Unicode normalization
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
    
    # Step 3: Remove special characters, keep only alphanumeric and spaces
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    
    # Step 4: Replace spaces and hyphens with underscores
    value = re.sub(r'[\s-]+', '_', value)
    
    return value


# ============================================================================
# DATA LOADING & PROCESSING
# ============================================================================

def load_csv_data(csv_path: str) -> pd.DataFrame:
    """
    Load tourism location CSV data with loc_id as index.
    
    This is a lightweight version that loads data without printing logs,
    suitable for use in tools and other modules.
    
    Args:
        csv_path: Path to the CSV file
    
    Returns:
        Processed DataFrame with loc_id as index
    """
    df = pd.read_csv(csv_path)
    
    # Generate loc_id using slugify
    df['loc_id'] = df['TenDiaDanh'].apply(slugify)
    
    # Filter: Keep only rows with TenDiaDanh, DiaChi (NoiDung can be null)
    df_filtered = df.dropna(subset=['TenDiaDanh', 'DiaChi']).copy()
    
    # Fill NaN in NoiDung with empty string
    df_filtered['NoiDung'] = df_filtered['NoiDung'].fillna('')
    
    # Set loc_id as index for fast lookup
    df_filtered = df_filtered.set_index('loc_id')
    
    return df_filtered


def load_and_process_data(csv_path: str) -> pd.DataFrame:
    """
    Load tourism location CSV and prepare it for vectorization.
    
    Purpose: 
    - Load raw CSV data
    - Generate loc_id for each location
    - Filter out rows with missing critical fields
    - Set loc_id as index for easy lookup
    
    Args:
        csv_path: Path to the CSV file
    
    Returns:
        Processed DataFrame with loc_id as index
    """
    print("📂 Loading CSV data...")
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} rows")
    
    # Generate loc_id using slugify
    print("🔑 Generating loc_id for each location...")
    df['loc_id'] = df['TenDiaDanh'].apply(slugify)
    
    # Filter: Keep only rows with TenDiaDanh, DiaChi (NoiDung can be null)
    print("🔍 Filtering rows with missing critical data...")
    df_filtered = df.dropna(subset=['TenDiaDanh', 'DiaChi']).copy()
    
    # Fill NaN in NoiDung with empty string
    df_filtered['NoiDung'] = df_filtered['NoiDung'].fillna('')
    
    print(f"   Kept {len(df_filtered)} rows after filtering")
    
    # Set loc_id as index for fast lookup
    df_filtered = df_filtered.set_index('loc_id')
    
    return df_filtered


def create_documents(df: pd.DataFrame) -> List[Document]:
    """
    Convert DataFrame rows into LangChain Document objects.
    
    Purpose:
    - Create rich text content for embedding (TenDiaDanh + NoiDung + DiaChi)
    - Store metadata (loc_id, original columns) for retrieval
    - Each Document will be embedded and stored in ChromaDB
    
    Document Structure:
    - page_content: Combined text for semantic search
    - metadata: All original fields for context generation
    
    Args:
        df: Processed DataFrame with loc_id as index
    
    Returns:
        List of LangChain Document objects
    """
    print("📝 Creating documents for vectorization...")
    documents = []
    
    for loc_id, row in df.iterrows():
        # Build rich content: Title + Description + Location
        # This combined text will be embedded for semantic search
        content_parts = [
            f"Tên địa danh: {row['TenDiaDanh']}",
            f"Địa chỉ: {row['DiaChi']}"
        ]
        
        # Add description if available
        if row['NoiDung'] and str(row['NoiDung']).strip():
            content_parts.append(f"Mô tả: {row['NoiDung']}")
        
        page_content = "\n".join(content_parts)
        
        # Store all metadata for later use in recommendations
        metadata = {
            'loc_id': loc_id,
            'TenDiaDanh': row['TenDiaDanh'],
            'DiaChi': row['DiaChi'],
            'NoiDung': row['NoiDung'] if row['NoiDung'] else '',
            'ImageURL': row.get('ImageURL', ''),
            'DichVu': row.get('DichVu', ''),
            'ThongTinLienHe': row.get('ThongTinLienHe', ''),
            'DanhGia': row.get('DanhGia (Google Map)', '')
        }
        
        documents.append(Document(
            page_content=page_content,
            metadata=metadata
        ))
    
    print(f"   Created {len(documents)} documents")
    return documents


# ============================================================================
# VECTOR STORE INITIALIZATION
# ============================================================================

def initialize_embeddings(
    use_remote: bool = None,
    remote_api_url: str = None,
    timeout: int = 30,
    fallback_to_local: bool = True,
    verbose: bool = False
):
    """
    Initialize embeddings - remote (HF Spaces) or local.
    
    Supports two modes:
    1. Remote: Uses embedding API on HuggingFace Spaces (requires URL)
    2. Local: Uses local HuggingFace embeddings (default, no dependencies)
    
    Args:
        use_remote: If True, use remote embeddings. If None, check config.
        remote_api_url: URL of remote embedding API (required if use_remote=True)
        timeout: Request timeout in seconds (for remote)
        fallback_to_local: If True, fallback to local if remote fails
        verbose: If True, print detailed logs
    
    Returns:
        Embeddings instance (either RemoteEmbeddingsAdapter or HuggingFaceEmbeddings)
    """
    # Use config values if not explicitly provided
    if use_remote is None:
        use_remote = getattr(Config, 'USE_REMOTE_EMBEDDINGS', False)
    
    if remote_api_url is None:
        remote_api_url = getattr(Config, 'REMOTE_EMBEDDING_API_URL', None)
    
    if fallback_to_local is None:
        fallback_to_local = getattr(Config, 'EMBEDDING_API_FALLBACK_LOCAL', True)
    
    if use_remote and remote_api_url:
        print("🌐 Initializing REMOTE embeddings (HuggingFace Spaces)...")
        print(f"   API URL: {remote_api_url}")
        
        try:
            from tourism_chatbot.clients.langchain_embedding_adapter import RemoteEmbeddingsAdapter
            
            embeddings = RemoteEmbeddingsAdapter(
                space_url=remote_api_url,
                timeout=timeout,
                fallback_to_local=fallback_to_local,
                model_name=EMBEDDING_MODEL,
                verbose=verbose
            )
            
            print("✅ Remote embeddings initialized successfully")
            return embeddings
        
        except Exception as e:
            print(f"❌ Failed to initialize remote embeddings: {e}")
            if not fallback_to_local:
                raise
            print("⚠️  Falling back to local embeddings...")
    
    # Local embeddings (default)
    print("🤖 Initializing LOCAL embeddings (HuggingFace)...")
    print(f"   Model: {EMBEDDING_MODEL}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
        encode_kwargs={'normalize_embeddings': True}  # Normalize for cosine similarity
    )
    
    print("✅ Local embeddings initialized successfully")
    return embeddings


def create_vector_store(documents: List[Document], embeddings, persist_directory: str) -> Chroma:
    """
    Create new ChromaDB vector store from documents.
    
    Purpose:
    - Convert all documents to vectors
    - Store vectors in ChromaDB for fast similarity search
    - Persist to disk for reuse
    
    Args:
        documents: List of LangChain Documents
        embeddings: Embedding model instance
        persist_directory: Path to store ChromaDB
    
    Returns:
        Initialized Chroma vector store
    """
    print("📦 Creating ChromaDB vector store...")
    print(f"   This may take a few minutes for {len(documents)} documents...")
    
    # Create vector store (embeds all documents)
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="vietnam_tourism"
    )
    
    print(f"   ✅ Vector store created and persisted to: {persist_directory}")
    return vector_store


def load_vector_store(embeddings, persist_directory: str) -> Chroma:
    """
    Load previously created vector store from disk.
    
    Purpose: Skip re-embedding on subsequent runs (saves time)
    
    Args:
        embeddings: Embedding model instance
        persist_directory: Path where ChromaDB was persisted
    
    Returns:
        Loaded Chroma vector store
    """
    print("📂 Loading existing vector store...")
    
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="vietnam_tourism"
    )
    
    print("   ✅ Vector store loaded")
    return vector_store


# ============================================================================
# LLM INITIALIZATION
# ============================================================================

def initialize_llm(api_key: Optional[str] = None, temperature: Optional[float] = None):
    """
    Initialize Google Gemini LLM.
    
    Purpose: Create LLM instance for generating recommendations
    
    Args:
        api_key: Google Gemini API key (optional, will use config if not provided)
        temperature: LLM temperature for creativity (0.0-1.0, optional, will use config if not provided)
    
    Returns:
        ChatGoogleGenerativeAI instance
    """
    print("🤖 Initializing Google Gemini LLM...")
    
    # Use provided API key or fall back to config
    key_to_use = api_key or GEMINI_API_KEY
    if key_to_use:
        os.environ['GOOGLE_API_KEY'] = key_to_use
    
    # Use provided temperature or fall back to config
    temp_to_use = temperature if temperature is not None else LLM_TEMPERATURE
    
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=temp_to_use,
        convert_system_message_to_human=True
    )
    
    print("   ✅ LLM initialized")
    return llm


# ============================================================================
# RAG PIPELINE FUNCTIONS (Modular Design for LangGraph)
# ============================================================================

def semantic_search(
    vector_store: Chroma,
    user_query: str,
    top_k: int = TOP_K_RESULTS,
    verbose: bool = False
) -> List[Document]:
    """
    Step 1: Semantic search to find relevant locations.
    
    Args:
        vector_store: ChromaDB vector store instance
        user_query: Natural language query
        top_k: Number of similar locations to retrieve
        verbose: If True, print logs
    
    Returns:
        List of relevant Document objects
    """
    if verbose:
        print(f"📊 Semantic Search: '{user_query}'")
        print(f"   Searching for top {top_k} locations...")
    
    retrieved_docs = vector_store.similarity_search(user_query, k=top_k)
    
    if verbose:
        print(f"   ✅ Retrieved {len(retrieved_docs)} locations\n")
    
    return retrieved_docs


def filter_visited_locations(
    documents: List[Document],
    user_visited_ids: List[str],
    allow_revisit: bool = False,
    verbose: bool = False
) -> Tuple[List[Document], List[Document], int]:
    """
    Step 2: Filter documents based on visit history.
    
    Args:
        documents: List of retrieved documents
        user_visited_ids: List of loc_ids user has visited
        allow_revisit: If False, exclude visited places
        verbose: If True, print logs
    
    Returns:
        Tuple of (new_places, old_places, filtered_count)
    """
    if verbose:
        print("🔀 History Filtering")
        print(f"   Separating visited vs new places...")
    
    new_places = []
    old_places = []
    
    for doc in documents:
        loc_id = doc.metadata['loc_id']
        if loc_id in user_visited_ids:
            old_places.append(doc)
        else:
            new_places.append(doc)
    
    if verbose:
        print(f"   New places: {len(new_places)}")
        print(f"   Visited places: {len(old_places)}\n")
    
    if allow_revisit:
        final_places = documents
        filtered_count = 0
        if verbose:
            print("   ✅ Including all places (revisit allowed)\n")
    else:
        final_places = new_places
        filtered_count = len(old_places)
        if verbose:
            print(f"   ✅ Excluding {filtered_count} visited places\n")
    
    return new_places, old_places, filtered_count


def build_context(
    documents: List[Document],
    user_visited_ids: List[str] = None,
    allow_revisit: bool = False,
    verbose: bool = False
) -> str:
    """
    Step 3: Build structured context from documents for LLM.
    
    Args:
        documents: List of documents to build context from
        user_visited_ids: List of visited location IDs (for marking)
        allow_revisit: Whether to mark visited locations
        verbose: If True, print logs
    
    Returns:
        Formatted context string for LLM prompt
    """
    if verbose:
        print("📝 Building Context")
    
    if not documents:
        return ""
    
    if user_visited_ids is None:
        user_visited_ids = []
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        meta = doc.metadata
        
        place_info = f"""
Địa điểm {i}:
- Tên: {meta['TenDiaDanh']}
- Địa chỉ: {meta['DiaChi']}
"""
        
        if meta.get('NoiDung') and meta['NoiDung'].strip():
            place_info += f"- Mô tả: {meta['NoiDung']}\n"
        
        if meta.get('DanhGia') and str(meta['DanhGia']).strip() and str(meta['DanhGia']) != 'N/A':
            place_info += f"- Đánh giá: {meta['DanhGia']}\n"
        
        if allow_revisit and meta['loc_id'] in user_visited_ids:
            place_info += "- Trạng thái: Đã ghé thăm\n"
        
        context_parts.append(place_info)
    
    context = "\n".join(context_parts)
    
    if verbose:
        print(f"   ✅ Context built for {len(documents)} places\n")
    
    return context


def generate_recommendation(
    vector_store: Chroma,
    llm: ChatGoogleGenerativeAI,
    user_query: str,
    user_visited_ids: List[str],
    allow_revisit: bool = False,
    top_k: int = TOP_K_RESULTS,
    verbose: bool = False
) -> Dict:
    """
    Generate personalized tourism recommendations using RAG pipeline.
    
    Pipeline:
    1. Vector Search: Find top_k most relevant locations
    2. History Filtering: Separate new vs visited places
    3. Context Building: Prepare information for LLM
    4. LLM Generation: Create human-friendly recommendations
    
    Args:
        vector_store: ChromaDB vector store instance
        llm: LLM instance for generation
        user_query: Natural language query (e.g., "beautiful waterfalls")
        user_visited_ids: List of loc_ids user has visited
        allow_revisit: If False, exclude visited places from recommendations
        top_k: Number of similar locations to retrieve
        verbose: If True, print detailed pipeline logs
    
    Returns:
        Dictionary containing:
        - final_response: LLM-generated recommendation text
        - new_places: List of unvisited locations
        - old_places: List of visited locations
        - filtered_count: Number of places filtered out
    """
    if verbose:
        print(f"\n{'='*60}")
        print("🔍 STARTING RAG RECOMMENDATION PIPELINE")
        print(f"{'='*60}")
        print(f"Query: {user_query}")
        print(f"Visited IDs: {user_visited_ids}")
        print(f"Allow Revisit: {allow_revisit}")
        print(f"{'='*60}\n")
    
    # STEP 1: Semantic Search
    retrieved_docs = semantic_search(vector_store, user_query, top_k, verbose)
    
    # STEP 2: History Filtering
    new_places, old_places, filtered_count = filter_visited_locations(
        retrieved_docs, user_visited_ids, allow_revisit, verbose
    )
    
    # Decide which places to use for context
    final_places = retrieved_docs if allow_revisit else new_places
    
    # Handle case where no places remain after filtering
    if not final_places:
        return {
            'final_response': "Không tìm thấy địa điểm mới phù hợp. Bạn đã ghé thăm tất cả các địa điểm tương tự. Hãy thử tìm kiếm với từ khóa khác hoặc cho phép ghé lại các địa điểm đã thăm.",
            'new_places': [],
            'old_places': old_places,
            'filtered_count': filtered_count
        }
    
    # STEP 3: Context Building
    if verbose:
        print("📝 STEP 3: Building Context for LLM")
    
    context = build_context(final_places, user_visited_ids, allow_revisit, verbose)
    
    # STEP 4: LLM Generation - Create recommendation text
    if verbose:
        print("🤖 STEP 4: Generating LLM Response")
    
    # Create prompt template
    prompt_template = PromptTemplate(
        input_variables=["user_query", "context", "filtered_count"],
        template="""
Bạn là một hướng dẫn viên du lịch Việt Nam chuyên nghiệp và thân thiện.

Người dùng đang tìm kiếm: "{user_query}"

Dựa trên thông tin các địa điểm dưới đây, hãy viết một đoạn giới thiệu hấp dẫn và chi tiết:

{context}

Yêu cầu:
1. Viết bằng tiếng Việt tự nhiên, thân thiện
2. Nêu rõ đặc điểm nổi bật của từng địa điểm
3. Gợi ý lý do nên ghé thăm
4. Sắp xếp theo mức độ phù hợp với yêu cầu
{filter_note}

Hãy viết đoạn giới thiệu:
"""
    )
    
    # Add note about filtered places if applicable
    filter_note = ""
    if filtered_count > 0:
        filter_note = f"\n5. Lưu ý: Đã loại bỏ {filtered_count} địa điểm mà người dùng đã ghé thăm"
    
    # Generate prompt
    prompt = prompt_template.format(
        user_query=user_query,
        context=context,
        filtered_count=filtered_count,
        filter_note=filter_note
    )
    
    if verbose:
        print("   Calling Gemini API...")
    
    # Call LLM
    response = llm.invoke(prompt)
    final_response = response.content
    
    if verbose:
        print("   ✅ Response generated\n")
        print(f"{'='*60}")
        print("✅ PIPELINE COMPLETED")
        print(f"{'='*60}\n")
    
    return {
        'final_response': final_response,
        'new_places': new_places,
        'old_places': old_places,
        'filtered_count': filtered_count
    }


async def generate_recommendation_stream(
    vector_store: Chroma,
    llm: ChatGoogleGenerativeAI,
    user_query: str,
    user_visited_ids: List[str],
    allow_revisit: bool = False,
    top_k: int = TOP_K_RESULTS,
    verbose: bool = False
):
    """
    Generate personalized tourism recommendations with streaming support.
    
    This is an async generator that yields tokens from the LLM response,
    allowing for real-time streaming in Chainlit.
    
    Args:
        Same as generate_recommendation()
    
    Yields:
        Tuples of (token, metadata_dict) where:
        - token: String token from LLM
        - metadata_dict: Contains new_places, old_places, filtered_count
    """
    if verbose:
        print(f"\n{'='*60}")
        print("🔍 STARTING RAG RECOMMENDATION PIPELINE (STREAMING)")
        print(f"{'='*60}")
        print(f"Query: {user_query}")
        print(f"Visited IDs: {user_visited_ids}")
        print(f"Allow Revisit: {allow_revisit}")
        print(f"{'='*60}\n")
    
    # STEP 1: RAG Retrieval
    retrieved_docs = vector_store.similarity_search(user_query, k=top_k)
    
    # STEP 2: History Filtering
    new_places = []
    old_places = []
    
    for doc in retrieved_docs:
        loc_id = doc.metadata['loc_id']
        if loc_id in user_visited_ids:
            old_places.append(doc)
        else:
            new_places.append(doc)
    
    # Decide which places to recommend
    if allow_revisit:
        final_places = retrieved_docs
        filtered_count = 0
    else:
        final_places = new_places
        filtered_count = len(old_places)
    
    # Handle case where no places remain
    if not final_places:
        yield ("Không tìm thấy địa điểm mới phù hợp. Bạn đã ghé thăm tất cả các địa điểm tương tự. "
               "Hãy thử tìm kiếm với từ khóa khác hoặc cho phép ghé lại các địa điểm đã thăm.",
               {
                   'new_places': [],
                   'old_places': old_places,
                   'filtered_count': filtered_count
               })
        return
    
    # STEP 3: Build Context
    context_parts = []
    for i, doc in enumerate(final_places, 1):
        meta = doc.metadata
        place_info = f"""
Địa điểm {i}:
- Tên: {meta['TenDiaDanh']}
- Địa chỉ: {meta['DiaChi']}
"""
        if meta.get('NoiDung') and meta['NoiDung'].strip():
            place_info += f"- Mô tả: {meta['NoiDung']}\n"
        
        if meta.get('DanhGia') and str(meta['DanhGia']).strip() and str(meta['DanhGia']) != 'N/A':
            place_info += f"- Đánh giá: {meta['DanhGia']}\n"
        
        if allow_revisit and meta['loc_id'] in user_visited_ids:
            place_info += "- Trạng thái: Đã ghé thăm\n"
        
        context_parts.append(place_info)
    
    context = "\n".join(context_parts)
    
    # STEP 4: Generate prompt
    filter_note = ""
    if filtered_count > 0:
        filter_note = f"\n5. Lưu ý: Đã loại bỏ {filtered_count} địa điểm mà người dùng đã ghé thăm"
    
    prompt = f"""
Bạn là một hướng dẫn viên du lịch Việt Nam chuyên nghiệp và thân thiện.

Người dùng đang tìm kiếm: "{user_query}"

Dựa trên thông tin các địa điểm dưới đây, hãy viết một đoạn giới thiệu hấp dẫn và chi tiết:

{context}

Yêu cầu:
1. Viết bằng tiếng Việt tự nhiên, thân thiện
2. Nêu rõ đặc điểm nổi bật của từng địa điểm
3. Gợi ý lý do nên ghé thăm
4. Sắp xếp theo mức độ phù hợp với yêu cầu
{filter_note}

Hãy viết đoạn giới thiệu:
"""
    
    # STEP 5: Stream LLM response
    metadata = {
        'new_places': new_places,
        'old_places': old_places,
        'filtered_count': filtered_count
    }
    
    async for chunk in llm.astream(prompt):
        yield (chunk.content, metadata)


# ============================================================================
# INITIALIZATION HELPER
# ============================================================================

def initialize_rag_system(
    csv_path: str = CSV_PATH,
    chroma_db_path: str = CHROMA_DB_PATH,
    force_recreate: bool = False,
    api_key: Optional[str] = None,
    use_remote_embeddings: bool = None,
    remote_embedding_url: str = None
) -> Tuple[Chroma, ChatGoogleGenerativeAI]:
    """
    Initialize complete RAG system (one-stop function).
    
    This function handles:
    1. Loading and processing CSV data
    2. Creating or loading vector store
    3. Initializing LLM
    
    Args:
        csv_path: Path to tourism CSV file
        chroma_db_path: Path to ChromaDB storage
        force_recreate: If True, recreate vector store even if exists
        api_key: Google Gemini API key (optional)
        use_remote_embeddings: If True, use remote embedding API from HF Spaces
        remote_embedding_url: URL of remote embedding API
    
    Returns:
        Tuple of (vector_store, llm)
    """
    print("\n" + "="*60)
    print("🚀 INITIALIZING RAG TOURISM SYSTEM")
    print("="*60 + "\n")
    
    # Initialize embeddings (remote or local)
    embeddings = initialize_embeddings(
        use_remote=use_remote_embeddings,
        remote_api_url=remote_embedding_url
    )
    
    # Check if vector store exists
    vector_store_exists = os.path.exists(chroma_db_path)
    
    if vector_store_exists and not force_recreate:
        # Load existing vector store
        print("✅ Found existing vector store")
        vector_store = load_vector_store(embeddings, chroma_db_path)
    else:
        # Create new vector store
        if force_recreate:
            print("🔄 Force recreating vector store...")
        else:
            print("📦 Vector store not found, creating new one...")
        
        # Load and process data
        tourism_df = load_and_process_data(csv_path)
        
        # Create documents
        documents = create_documents(tourism_df)
        
        # Create vector store
        vector_store = create_vector_store(documents, embeddings, chroma_db_path)
    
    # Initialize LLM
    llm = initialize_llm(api_key=api_key)
    
    print("\n" + "="*60)
    print("✅ RAG SYSTEM READY!")
    print("="*60 + "\n")
    
    return vector_store, llm


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'slugify',
    'load_csv_data',
    'load_and_process_data',
    'create_documents',
    'initialize_embeddings',
    'create_vector_store',
    'load_vector_store',
    'initialize_llm',
    'semantic_search',
    'filter_visited_locations',
    'build_context',
    'generate_recommendation',
    'generate_recommendation_stream',
    'initialize_rag_system',
    'CSV_PATH',
    'CHROMA_DB_PATH',
    'EMBEDDING_MODEL',
    'GEMINI_MODEL',
    'TOP_K_RESULTS'
]
