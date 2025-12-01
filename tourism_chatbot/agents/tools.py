from tourism_chatbot.rag.rag_engine import initialize_embeddings, load_vector_store
from langchain.tools import tool
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_DB_PATH = 'data/vector_db/chroma_tourism'

embeddings = initialize_embeddings()
vector_store = load_vector_store(embeddings=embeddings, persist_directory=CHROMA_DB_PATH)

# Global state for user context (updated by the chatbot)
_USER_VISITED_IDS: List[str] = []
_ALLOW_REVISIT: bool = False

def set_user_context(visited_ids: List[str], allow_revisit: bool = False):
    """Update the user context for the current session."""
    global _USER_VISITED_IDS, _ALLOW_REVISIT
    _USER_VISITED_IDS = visited_ids
    _ALLOW_REVISIT = allow_revisit
    logger.debug(f"📋 User context updated: {len(visited_ids)} visited locations, allow_revisit={allow_revisit}")

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve tourism information to help answer a query about Vietnamese destinations.
    
    This tool searches the tourism database and automatically filters out locations 
    the user has already visited (unless revisiting is allowed).
    """
    logger.info(f"🔧 [TOOL CALLED] retrieve_context")
    logger.info(f"📝 Query: {query}")
    
    # Retrieve more documents to account for filtering
    k = 5 if _USER_VISITED_IDS and not _ALLOW_REVISIT else 3
    retrieved_docs = vector_store.similarity_search(query, k=k)
    
    logger.info(f"📊 Retrieved {len(retrieved_docs)} documents (before filtering)")
    
    # Filter out visited locations if needed
    filtered_docs = []
    filtered_out = []
    
    for doc in retrieved_docs:
        loc_id = doc.metadata.get('loc_id', '')
        
        if _USER_VISITED_IDS and not _ALLOW_REVISIT and loc_id in _USER_VISITED_IDS:
            filtered_out.append(doc.metadata.get('TenDiaDanh', 'N/A'))
        else:
            filtered_docs.append(doc)
            
        # Stop when we have enough recommendations
        if len(filtered_docs) >= 3:
            break
    
    # Log filtering results
    if filtered_out:
        logger.info(f"🚫 Filtered out {len(filtered_out)} visited locations: {', '.join(filtered_out[:3])}")
    
    logger.info(f"✅ Returning {len(filtered_docs)} documents")
    if filtered_docs:
        logger.info(f"📍 Top result: {filtered_docs[0].metadata.get('TenDiaDanh', 'N/A')}")
    
    # Build serialized response
    if not filtered_docs:
        return "Không tìm thấy địa điểm mới phù hợp. Người dùng đã ghé thăm tất cả địa điểm tương tự.", []
    
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in filtered_docs
    )
    return serialized, filtered_docs