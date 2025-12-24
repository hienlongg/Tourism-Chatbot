from tourism_chatbot.rag.rag_engine import (
    initialize_embeddings, 
    load_vector_store,
    semantic_search,
    filter_visited_locations,
    build_context
)
from langchain.tools import tool
import logging
from typing import List, Dict, Tuple

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
def retrieve_context(query: str) -> Tuple[str, Dict]:
    """Retrieve tourism information and build context for LLM.
    
    This tool:
    1. Searches the tourism database semantically
    2. Filters out locations the user has already visited (unless revisiting is allowed)
    3. Builds structured context ready for the LLM
    
    Returns formatted context string and metadata about the results.
    """
    logger.info(f"🔧 [TOOL CALLED] retrieve_context")
    logger.info(f"📝 Query: {query}")
    
    # STEP 1: Semantic Search
    top_k = 5 if _USER_VISITED_IDS and not _ALLOW_REVISIT else 3
    retrieved_docs = semantic_search(vector_store, query, top_k=top_k, verbose=False)
    logger.info(f"📊 Retrieved {len(retrieved_docs)} documents (before filtering)")
    
    # STEP 2: Filter visited locations
    new_places, old_places, filtered_count = filter_visited_locations(
        retrieved_docs,
        _USER_VISITED_IDS,
        allow_revisit=_ALLOW_REVISIT,
        verbose=False
    )
    
    # Log filtering results
    if old_places:
        filtered_names = [doc.metadata.get('TenDiaDanh', 'N/A') for doc in old_places[:3]]
        logger.info(f"🚫 Filtered out {len(old_places)} visited locations: {', '.join(filtered_names)}")
    
    # Determine which places to use for context
    final_places = retrieved_docs if _ALLOW_REVISIT else new_places
    
    logger.info(f"✅ Using {len(final_places)} documents for context building")
    if final_places:
        logger.info(f"📍 Top result: {final_places[0].metadata.get('TenDiaDanh', 'N/A')}")
    
    # Handle case where no places remain
    if not final_places:
        return (
            "Không tìm thấy địa điểm mới phù hợp. Người dùng đã ghé thăm tất cả địa điểm tương tự.",
            {
                'context': "",
                'new_places': [],
                'old_places': old_places,
                'filtered_count': filtered_count,
                'locations_count': 0
            }
        )
    
    # STEP 3: Build context for LLM
    context = build_context(final_places, _USER_VISITED_IDS, _ALLOW_REVISIT, verbose=False)
    
    return (
        context,
        {
            'context': context,
            'new_places': new_places,
            'old_places': old_places,
            'filtered_count': filtered_count,
            'locations_count': len(final_places)
        }
    )