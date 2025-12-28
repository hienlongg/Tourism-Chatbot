"""
Chat routes for tourism chatbot API.
Provides REST API endpoints for the tourism chatbot functionality.
"""

from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from tourism_chatbot.agents.tools import set_user_context, retrieve_context
from tourism_chatbot.memory import UserContextManager
from tourism_chatbot.rag.rag_engine import slugify
from tourism_chatbot.vision import get_image_search_engine
from backend.utils.location_extractor import extract_locations_from_answer
import logging
import json
import re
import os
from typing import List
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# Global references (will be set by init_chatbot)
_AGENT_WITH_MEMORY = None
_VECTOR_STORE = None
_LLM = None
_IMAGE_SEARCH_ENGINE = None


def init_chatbot(agent, vector_store, llm):
    """
    Initialize chatbot components.
    Called from App.py after chatbot system is ready.

    Args:
        agent: The tourism agent with memory
        vector_store: ChromaDB vector store
        llm: LLM instance
    """
    global _AGENT_WITH_MEMORY, _VECTOR_STORE, _LLM, _IMAGE_SEARCH_ENGINE
    _AGENT_WITH_MEMORY = agent
    _VECTOR_STORE = vector_store
    _LLM = llm
    
    # Initialize image search engine
    try:
        _IMAGE_SEARCH_ENGINE = get_image_search_engine()
        logger.info("✅ Image search engine initialized in chat routes")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize image search engine: {e}")
        _IMAGE_SEARCH_ENGINE = None
    
    logger.info("Chat routes initialized with chatbot components")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_user_context_from_session() -> dict:
    """
    Get or create user context from session.

    Returns:
        dict with visited_ids, allow_revisit, and thread_id
    """
    if "chat_context" not in session:
        session["chat_context"] = {
            "visited_ids": [],
            "allow_revisit": False,
        }
    return session["chat_context"]


def get_thread_id(user_id: str) -> str:
    """
    Generate thread ID for conversation memory.

    Args:
        user_id: User identifier

    Returns:
        Thread ID string
    """
    return f"flask_{user_id}"


def detect_visited_command(message: str) -> List[str]:
    """
    Detect if user is reporting visited locations.

    Patterns:
    - "Tôi đã từng đến [place]"
    - "Tôi đã đi [place]"
    - "Đã ghé [place]"

    Args:
        message: User message text

    Returns:
        List of location names mentioned (empty if not a visited command)
    """
    patterns = [
        r"(?:tôi\s+)?đã\s+(?:từng\s+)?(?:đến|đi|ghé|thăm)\s+(.+)",
        r"(?:tôi\s+)?đã\s+(?:từng\s+)?(?:tham quan|viếng)\s+(.+)",
    ]

    message_lower = message.lower().strip()

    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            # Extract location name(s)
            locations_str = match.group(1)
            # Split by common separators
            locations = re.split(r"[,và&]", locations_str)
            return [loc.strip() for loc in locations if loc.strip()]

    return []


def detect_allow_revisit_command(message: str) -> str:
    """
    Detect if user wants to allow/disallow revisit suggestions.

    Args:
        message: User message text

    Returns:
        "allow" | "disallow" | "none"
    """
    message_lower = message.lower().strip()

    # Allow patterns
    allow_patterns = [
        r"cho\s+phép\s+(?:gợi\s+ý\s+)?lại",
        r"được\s+(?:gợi\s+ý\s+)?lại",
        r"có\s+thể\s+(?:gợi\s+ý\s+)?lại",
    ]

    # Disallow patterns
    disallow_patterns = [
        r"không\s+(?:cho\s+phép|được)\s+(?:gợi\s+ý\s+)?lại",
        r"không\s+muốn\s+(?:gợi\s+ý\s+)?lại",
        r"tắt\s+(?:gợi\s+ý\s+)?lại",
    ]

    for pattern in allow_patterns:
        if re.search(pattern, message_lower):
            return "allow"

    for pattern in disallow_patterns:
        if re.search(pattern, message_lower):
            return "disallow"

    return "none"


def prepare_message_for_checkpointer(message_content):
    """
    Remove image URLs from message content before saving to checkpointer.
    Keep only text content to avoid storing large image URLs in database.
    
    Args:
        message_content: Message content with potential images
        
    Returns:
        Cleaned message content with only text
    """
    if isinstance(message_content, list):
        # Filter to only keep text content
        return [item for item in message_content if item.get("type") == "text"]
    return message_content


def process_image_for_location(image_url: str) -> dict:
    """
    Process an image URL to identify the location using vision model.
    
    Args:
        image_url: URL or path to the image
        
    Returns:
        dict with success status, location description, and metadata
    """
    if not _IMAGE_SEARCH_ENGINE:
        return {
            "success": False,
            "error": "Image search engine not available",
            "description": ""
        }
    
    try:
        # Convert URL to file path
        # Extract image filename from URL
        if image_url.startswith("http"):
            # Extract filename from full URL (e.g., http://localhost:8080//api/upload/image/image_20251228_142917_fbb3e3e7.jpg)
            image_filename = image_url.split("/")[-1]
            file_path = os.path.join("uploads", image_filename)
        else:
            # Relative path already provided
            file_path = os.path.join(os.getcwd(), image_url.lstrip("/"))
        # Ensure the file exists
        if not os.path.exists(file_path):
            logger.error(f"Image file not found: {file_path}")
            return {
                "success": False,
                "error": f"Image file not found at path: {file_path}",
                "description": ""
            }
        
        logger.info(f"🔍 Identifying location from image: {file_path}")
        
        # Use vision model to identify location
        location_matches = _IMAGE_SEARCH_ENGINE.identify_location(file_path, top_k=3)
        
        if not location_matches:
            return {
                "success": False,
                "error": "Could not identify location from image",
                "description": ""
            }
        
        # Get top match
        top_match = location_matches[0]
        location_name = top_match['location_name']
        confidence = top_match['confidence']
        
        logger.info(f"🎯 Identified location: {location_name} (confidence: {confidence:.2%})")
        
        # Build description for chatbot
        description = f"Người dùng đã gửi một hình ảnh. Địa điểm trong hình được nhận diện là: {location_name} (độ tin cậy: {confidence:.0%})."
        
        # Add alternatives if confidence is low
        if confidence < 0.8 and len(location_matches) > 1:
            alternatives = [match['location_name'] for match in location_matches[1:3]]
            description += f" Các địa điểm tương tự khác: {', '.join(alternatives)}."
        
        return {
            "success": True,
            "location_name": location_name,
            "confidence": confidence,
            "description": description,
            "matches": location_matches
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "description": ""
        }


# API ENDPOINTS
# ============================================================================


@chat_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for chatbot service.
    """
    return jsonify(
        {
            "status": "healthy",
            "agent_ready": _AGENT_WITH_MEMORY is not None,
            "vector_store_ready": _VECTOR_STORE is not None,
        }
    ), 200


@chat_bp.route("/message", methods=["POST"])
def send_message():
    """
    Send a message to the chatbot and get a response.

    Request body:
        {
            "message": "User's message",
            "imageUrl": "/uploads/image_filename.jpg" (optional)
        }

    Response:
        {
            "success": true,
            "response": "Chatbot response",
            "type": "recommendation" | "command" | "error",
            "metadata": {
                "visited_count": 0,
                "allow_revisit": false,
                "has_image": false
            },
            "locations": [
                { name, address, lat, lng, ... }
            ]
        }
    """
    # Check if chatbot is initialized
    if _AGENT_WITH_MEMORY is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Chatbot system is not initialized",
                    "type": "error",
                }
            ),
            503,
        )

    # Get request data
    data = request.get_json()
    if not data or "message" not in data:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Message is required",
                    "type": "error",
                }
            ),
            400,
        )

    user_message = data["message"].strip()
    if not user_message:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Message cannot be empty",
                    "type": "error",
                }
            ),
            400,
        )

    # Get optional image URL
    image_url = (
        data.get("imageUrl", "").strip()
        if isinstance(data.get("imageUrl"), str)
        else ""
    )

    # Get user info from session
    user_id = session.get("user_id", "anonymous")
    chat_context = get_user_context_from_session()
    visited_ids = chat_context.get("visited_ids", [])
    allow_revisit = chat_context.get("allow_revisit", False)
    thread_id = get_thread_id(user_id)

    logger.info(f"Message from user {user_id}: {user_message[:50]}...")
    logger.info(f"Message from user {user_id}: {user_message[:50]}...")

    try:
        # Check for visited location command
        visited_locations = detect_visited_command(user_message)
        if visited_locations:
            new_ids = []
            for location in visited_locations:
                loc_id = slugify(location)
                if loc_id not in visited_ids:
                    visited_ids.append(loc_id)
                    new_ids.append(location)

            # Update session
            chat_context["visited_ids"] = visited_ids
            session["chat_context"] = chat_context
            session.modified = True

            if new_ids:
                response = (
                    f"Đã ghi nhận! Bạn đã từng đến: **{', '.join(new_ids)}**\n\n"
                    f"Đã ghi nhận! Bạn đã từng đến: **{', '.join(new_ids)}**\n\n"
                    f"Tôi sẽ ưu tiên gợi ý những địa điểm mới cho bạn.\n"
                    f"(Hiện tại: {len(visited_ids)} địa điểm đã ghé thăm)"
                )
            else:
                response = "📝 Các địa điểm này đã có trong danh sách của bạn rồi!"

            return (
                jsonify(
                    {
                        "success": True,
                        "response": response,
                        "type": "command",
                        "metadata": {
                            "visited_count": len(visited_ids),
                            "allow_revisit": allow_revisit,
                        },
                        "locations": [],
                    }
                ),
                200,
            )

        # Check for allow/disallow revisit command
        revisit_cmd = detect_allow_revisit_command(user_message)
        if revisit_cmd != "none":
            if revisit_cmd == "allow":
                chat_context["allow_revisit"] = True
                response = (
                    "Đã bật chế độ cho phép gợi ý lại!\n\n"
                    "Đã bật chế độ cho phép gợi ý lại!\n\n"
                    "Tôi sẽ gợi ý cả những địa điểm bạn đã từng đến."
                )
            else:  # disallow
                chat_context["allow_revisit"] = False
                response = (
                    "Đã tắt chế độ gợi ý lại!\n\n"
                    "Đã tắt chế độ gợi ý lại!\n\n"
                    "Tôi sẽ chỉ gợi ý những địa điểm mới mà bạn chưa đến."
                )

            # Update session
            session["chat_context"] = chat_context
            session.modified = True

            return (
                jsonify(
                    {
                        "success": True,
                        "response": response,
                        "type": "command",
                        "metadata": {
                            "visited_count": len(visited_ids),
                            "allow_revisit": chat_context["allow_revisit"],
                        },
                        "locations": [],
                    }
                ),
                200,
            )

        # Process with agent
        set_user_context(visited_ids=visited_ids, allow_revisit=allow_revisit)

        # Process image if provided
        image_context = None
        if image_url:
            logger.info(f"📸 Processing image: {image_url}")
            image_result = process_image_for_location(image_url)
            
            if image_result['success']:
                image_context = image_result['description']
                logger.info(f"✅ Location identified: {image_result.get('location_name', 'Unknown')}")
            else:
                logger.warning(f"⚠️  Image processing failed: {image_result.get('error', 'Unknown error')}")
                # Return error response
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": image_result.get('error', 'Failed to process image'),
                            "type": "error",
                        }
                    ),
                    400,
                )

        # Prepare message content - combine user message with image context
        if image_context:
            # Prepend image context to user message
            message_content = f"{image_context}\n\nNgười dùng hỏi: {user_message}"
        else:
            message_content = user_message

        inputs = {"messages": [("user", message_content)]}

        config = {"configurable": {"thread_id": thread_id}}

        logger.info(f"🤖 Processing with agent (thread_id: {thread_id})")

        # Invoke agent (synchronous)
        result = _AGENT_WITH_MEMORY.invoke(inputs, config)

        # Extract response from result
        last_message = result["messages"][-1]
        response_text = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        logger.info(f"Agent response generated for user {user_id}")
        logger.info(f"Agent response generated for user {user_id}")

        # Extract locations from answer (with lat/lng from CSV)
        try:
            matched_locations = extract_locations_from_answer(response_text)
            logger.info(
                f"📍 Extracted {len(matched_locations)} locations from answer"
            )
        except Exception as e:
            logger.error(f"Error extracting locations: {str(e)}")
            logger.error(f"Error extracting locations: {str(e)}")
            matched_locations = []

        return (
            jsonify(
                {
                    "success": True,
                    "response": response_text,
                    "type": "recommendation",
                    "metadata": {
                        "visited_count": len(visited_ids),
                        "allow_revisit": allow_revisit,
                        "has_image": bool(image_url),
                    },
                    "locations": matched_locations,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(f"Error processing message: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Error processing message: {str(e)}",
                    "type": "error",
                }
            ),
            500,
        )


@chat_bp.route("/message/stream", methods=["POST"])
def send_message_stream():
    """
    Send a message to the chatbot and get a streaming response.
    Uses Server-Sent Events (SSE) for real-time streaming.

    Request body:
        {
            "message": "User's message",
            "imageUrl": "/uploads/image_filename.jpg" (optional)
        }

    Response: SSE stream with JSON data
    """
    # Check if chatbot is initialized
    if _AGENT_WITH_MEMORY is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Chatbot system is not initialized",
                    "type": "error",
                }
            ),
            503,
        )

    # Get request data
    data = request.get_json()
    if not data or "message" not in data:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Message is required",
                    "type": "error",
                }
            ),
            400,
        )

    user_message = data["message"].strip()
    if not user_message:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Message cannot be empty",
                    "type": "error",
                }
            ),
            400,
        )

    # Get optional image URL
    image_url = (
        data.get("imageUrl", "").strip()
        if isinstance(data.get("imageUrl"), str)
        else ""
    )

    # Get user info from session
    user_id = session.get("user_id", "anonymous")
    chat_context = get_user_context_from_session()
    visited_ids = chat_context.get("visited_ids", [])
    allow_revisit = chat_context.get("allow_revisit", False)
    thread_id = get_thread_id(user_id)

    def generate():
        """Generator for SSE streaming."""
        try:
            # Set user context for tools
            set_user_context(
                visited_ids=visited_ids, allow_revisit=allow_revisit
            )

            # Process image if provided
            image_context = None
            if image_url:
                logger.info(f"📸 Processing image for streaming: {image_url}")
                image_result = process_image_for_location(image_url)
                
                if image_result['success']:
                    image_context = image_result['description']
                    logger.info(f"✅ Location identified: {image_result.get('location_name', 'Unknown')}")
                else:
                    logger.warning(f"⚠️  Image processing failed: {image_result.get('error', 'Unknown error')}")
                    # Send error event
                    yield (
                        "data: "
                        + json.dumps(
                            {"error": image_result.get('error', 'Failed to process image')},
                            ensure_ascii=False,
                        )
                        + "\n\n"
                    )
                    return

            # Prepare message content - combine user message with image context
            if image_context:
                message_content = f"{image_context}\n\nNgười dùng hỏi: {user_message}"
            else:
                message_content = user_message

            inputs = {"messages": [("user", message_content)]}

            config = {"configurable": {"thread_id": thread_id}}

            full_response = ""

            # Stream from agent with default stream mode
            for event in _AGENT_WITH_MEMORY.stream(inputs, config):
                # Extract messages from the event
                if "model" in event:
                    messages = event["model"]["messages"]
                    if messages:
                        last_message = messages[-1]

                        if last_message.type == "ai":
                            if (
                                hasattr(last_message, "content")
                                and last_message.content
                            ):
                                if len(last_message.content) > len(
                                    full_response
                                ):
                                    new_content = last_message.content[
                                        len(full_response) :
                                    ]
                                    full_response = last_message.content

                                    # Send SSE event: new token
                                    yield (
                                        "data: "
                                        + json.dumps(
                                            {"token": new_content},
                                            ensure_ascii=False,
                                        )
                                        + "\n\n"
                                    )

            # Extract locations after full streamed answer ===
            try:
                matched_locations = extract_locations_from_answer(
                    full_response
                )
                logger.info(
                    f"Extracted {len(matched_locations)} locations from streamed answer"
                    f"Extracted {len(matched_locations)} locations from streamed answer"
                )
            except Exception as e:
                logger.error(
                    f"Error extracting locations (stream): {str(e)}"
                    f"Error extracting locations (stream): {str(e)}"
                )
                matched_locations = []

            # Send completion event (done + metadata + locations)
            done_payload = {
                "done": True,
                "metadata": {
                    "visited_count": len(visited_ids),
                    "allow_revisit": allow_revisit,
                    "has_image": bool(image_url),
                },
                "locations": matched_locations,
            }
            yield (
                "data: "
                + json.dumps(done_payload, ensure_ascii=False)
                + "\n\n"
            )

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            logger.error(f"Streaming error: {str(e)}")
            yield (
                "data: "
                + json.dumps({"error": str(e)}, ensure_ascii=False)
                + "\n\n"
            )

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_bp.route("/context", methods=["GET"])
def get_context():
    """
    Get current user's chat context (visited locations, preferences).

    Response:
        {
            "success": true,
            "context": {
                "visited_ids": [],
                "allow_revisit": false
            }
        }
    """
    chat_context = get_user_context_from_session()

    return jsonify({"success": True, "context": chat_context}), 200


@chat_bp.route("/context/visited", methods=["POST"])
def add_visited_location():
    """
    Add a visited location to user's context.

    Request body:
        {
            "location": "Location name" | "loc_id"
        }

    Response:
        {
            "success": true,
            "visited_ids": [...],
            "message": "Location added"
        }
    """
    data = request.get_json()
    if not data or "location" not in data:
        return (
            jsonify(
                {"success": False, "error": "Location is required"}
            ),
            400,
        )

    location = data["location"].strip()
    loc_id = slugify(location)

    chat_context = get_user_context_from_session()
    visited_ids = chat_context.get("visited_ids", [])

    if loc_id not in visited_ids:
        visited_ids.append(loc_id)
        chat_context["visited_ids"] = visited_ids
        session["chat_context"] = chat_context
        session.modified = True

        return (
            jsonify(
                {
                    "success": True,
                    "visited_ids": visited_ids,
                    "message": f"Added {location} to visited list",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "success": True,
                    "visited_ids": visited_ids,
                    "message": "Location already in visited list",
                }
            ),
            200,
        )


@chat_bp.route("/context/visited", methods=["DELETE"])
def remove_visited_location():
    """
    Remove a visited location from user's context.

    Request body:
        {
            "location": "Location name" | "loc_id"
        }

    Response:
        {
            "success": true,
            "visited_ids": [...],
            "message": "Location removed"
        }
    """
    data = request.get_json()
    if not data or "location" not in data:
        return (
            jsonify(
                {"success": False, "error": "Location is required"}
            ),
            400,
        )

    location = data["location"].strip()
    loc_id = slugify(location)

    chat_context = get_user_context_from_session()
    visited_ids = chat_context.get("visited_ids", [])

    if loc_id in visited_ids:
        visited_ids.remove(loc_id)
        chat_context["visited_ids"] = visited_ids
        session["chat_context"] = chat_context
        session.modified = True

        return (
            jsonify(
                {
                    "success": True,
                    "visited_ids": visited_ids,
                    "message": f"Removed {location} from visited list",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "success": True,
                    "visited_ids": visited_ids,
                    "message": "Location not in visited list",
                }
            ),
            200,
        )


@chat_bp.route("/context/revisit", methods=["PUT"])
def set_revisit_preference():
    """
    Set allow_revisit preference.

    Request body:
        {
            "allow_revisit": true | false
        }

    Response:
        {
            "success": true,
            "allow_revisit": true | false
        }
    """
    data = request.get_json()
    if data is None or "allow_revisit" not in data:
        return (
            jsonify(
                {"success": False, "error": "allow_revisit is required"}
            ),
            400,
        )

    allow_revisit = bool(data["allow_revisit"])

    chat_context = get_user_context_from_session()
    chat_context["allow_revisit"] = allow_revisit
    session["chat_context"] = chat_context
    session.modified = True

    return (
        jsonify({"success": True, "allow_revisit": allow_revisit}),
        200,
    )


@chat_bp.route("/context/clear", methods=["POST"])
def clear_context():
    """
    Clear user's chat context (reset visited locations and preferences).

    Response:
        {
            "success": true,
            "message": "Context cleared"
        }
    """
    session["chat_context"] = {
        "visited_ids": [],
        "allow_revisit": False,
    }
    session.modified = True

    return (
        jsonify(
            {"success": True, "message": "Chat context cleared"}
        ),
        200,
    )
