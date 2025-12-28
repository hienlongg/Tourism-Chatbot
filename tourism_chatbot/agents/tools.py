from tourism_chatbot.rag.rag_engine import (
    initialize_embeddings, 
    load_vector_store,
    semantic_search,
    filter_visited_locations,
    build_context,
    load_csv_data
)
from tourism_chatbot.vision import get_image_search_engine
from langchain.tools import tool
import logging
from typing import List, Dict, Tuple, Union
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_DB_PATH = 'data/vector_db/chroma_tourism'
CSV_PATH = 'data/processed/danh_sach_thong_tin_dia_danh_chi_tiet.csv'

embeddings = initialize_embeddings()
vector_store = load_vector_store(embeddings=embeddings, persist_directory=CHROMA_DB_PATH)

# Initialize image search engine (loaded once at startup)
try:
    image_search_engine = get_image_search_engine()
    logger.info("✅ Image search engine initialized successfully")
except Exception as e:
    logger.warning(f"⚠️  Failed to initialize image search engine: {e}")
    image_search_engine = None

# Load location data for mapping
try:
    location_data = load_csv_data(CSV_PATH)
    logger.info(f"✅ Loaded location data: {len(location_data)} locations")
except Exception as e:
    logger.warning(f"⚠️  Failed to load location data: {e}")
    location_data = None

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


@tool(response_format="content_and_artifact")
def identify_location_from_image(image_path: str) -> Tuple[str, Dict]:
    """Identify Vietnamese tourism location from an uploaded image.
    
    This tool:
    1. Uses ResNet embeddings to find similar images in the database
    2. Identifies the most likely location(s)
    3. Retrieves detailed information about the location from the tourism database
    4. Returns a formatted description of the identified location
    
    Args:
        image_path: Path to the uploaded image file
    
    Returns:
        Tuple of (location description, metadata) with detailed information about the identified place.
    """
    logger.info(f"🔧 [TOOL CALLED] identify_location_from_image")
    logger.info(f"🖼️  Image path: {image_path}")
    
    # Check if image search engine is available
    if image_search_engine is None:
        error_msg = "Xin lỗi, tính năng tìm kiếm bằng hình ảnh hiện không khả dụng."
        return (error_msg, {'error': 'Image search engine not initialized', 'identified_locations': []})
    
    try:
        # Verify image file exists
        if not Path(image_path).exists():
            error_msg = f"Không tìm thấy file hình ảnh: {image_path}"
            logger.error(error_msg)
            return (error_msg, {'error': 'Image file not found', 'image_path': image_path})
        
        # STEP 1: Identify location from image
        logger.info("🔍 Analyzing image to identify location...")
        location_matches = image_search_engine.identify_location(image_path, top_k=5)
        
        if not location_matches:
            error_msg = "Không thể nhận diện địa điểm từ hình ảnh này. Vui lòng thử lại với hình ảnh khác."
            logger.warning("No location matches found")
            return (error_msg, {'identified_locations': []})
        
        # Get top match
        top_match = location_matches[0]
        location_folder_name = top_match['location_name']
        confidence = top_match['confidence']
        
        logger.info(f"🎯 Top match: {location_folder_name} (confidence: {confidence:.4f})")
        
        # STEP 2: Map folder name to location data
        # The folder name is slugified, try to find matching location in database
        matching_location = None
        if location_data is not None:
            for loc_id, row in location_data.iterrows():
                if loc_id == location_folder_name:
                    matching_location = row
                    break
        
        # STEP 3: Build response
        if matching_location is not None:
            # Found exact match in database
            location_name = matching_location['TenDiaDanh']
            address = matching_location['DiaChi']
            description = matching_location['NoiDung']
            
            response_parts = [
                f"📍 **Địa điểm được nhận diện: {location_name}**\n",
                f"🗺️  **Địa chỉ:** {address}\n"
            ]
            
            if description and str(description).strip():
                response_parts.append(f"📝 **Mô tả:** {description}\n")
            
            response_parts.append(f"\n✨ Độ tin cậy: {confidence:.2%}")
            
            # Add alternative matches if confidence is not very high
            if confidence < 0.8 and len(location_matches) > 1:
                response_parts.append("\n\n🤔 **Các địa điểm tương tự khác:**")
                for i, match in enumerate(location_matches[1:4], 1):
                    response_parts.append(f"{i}. {match['location_name']} ({match['confidence']:.2%})")
            
            response = "\n".join(response_parts)
            
        else:
            # No exact match in database, return folder name
            response = f"📍 Hình ảnh này có vẻ liên quan đến: **{location_folder_name}**\n\n"
            response += f"✨ Độ tin cậy: {confidence:.2%}\n\n"
            response += "ℹ️  Tuy nhiên, chúng tôi không tìm thấy thông tin chi tiết về địa điểm này trong cơ sở dữ liệu."
            
            if len(location_matches) > 1:
                response += "\n\n🤔 **Các địa điểm tương tự khác:**"
                for i, match in enumerate(location_matches[1:4], 1):
                    response += f"\n{i}. {match['location_name']} ({match['confidence']:.2%})"
        
        logger.info(f"✅ Successfully identified location: {location_folder_name}")
        
        return (
            response,
            {
                'identified_locations': location_matches,
                'top_location': location_folder_name,
                'confidence': float(confidence),
                'has_database_match': matching_location is not None,
                'image_path': image_path
            }
        )
        
    except Exception as e:
        error_msg = f"Đã xảy ra lỗi khi xử lý hình ảnh: {str(e)}"
        logger.error(f"Error in identify_location_from_image: {e}", exc_info=True)
        return (error_msg, {'error': str(e), 'image_path': image_path})