"""
Chat routes for tourism chatbot API.
Provides REST API endpoints for the tourism chatbot functionality.
"""

from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from tourism_chatbot.agents.tools import set_user_context, retrieve_context
from tourism_chatbot.memory import UserContextManager
from tourism_chatbot.rag.rag_engine import slugify
from backend.utils.location_extractor import extract_locations_from_answer
import logging
import json
import re
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# Global references (will be set by init_chatbot)
_AGENT_WITH_MEMORY = None
_VECTOR_STORE = None
_LLM = None


def init_chatbot(agent, vector_store, llm):
    """
    Initialize chatbot components.
    Called from App.py after chatbot system is ready.

    Args:
        agent: The tourism agent with memory
        vector_store: ChromaDB vector store
        llm: LLM instance
    """
    global _AGENT_WITH_MEMORY, _VECTOR_STORE, _LLM
    _AGENT_WITH_MEMORY = agent
    _VECTOR_STORE = vector_store
    _LLM = llm
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


# ============================================================================
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
                    "Tôi sẽ gợi ý cả những địa điểm bạn đã từng đến."
                )
            else:  # disallow
                chat_context["allow_revisit"] = False
                response = (
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

        # Prepare message content
        message_content = user_message

        # Add image context if provided
        if image_url:
            message_content = f"{user_message}\n\n[Image attached: {image_url}]"
            logger.info(f"Image attached to message: {image_url}")

        inputs = {"messages": [("user", message_content)]}

        config = {"configurable": {"thread_id": thread_id}}

        logger.info(f"Processing with agent (thread_id: {thread_id})")

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

        # Extract locations from answer (with lat/lng from CSV)
        try:
            matched_locations = extract_locations_from_answer(response_text)
            logger.info(
                f"📍 Extracted {len(matched_locations)} locations from answer"
            )
        except Exception as e:
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

            # Prepare message content with image if provided
            message_content = [{"type": "text", "text": user_message}]

            if image_url:
                # Handle both absolute and relative URLs
                # If URL starts with http:// or https://, use as-is
                # Otherwise, prepend the frontend base URL
                if image_url.startswith('http://') or image_url.startswith('https://'):
                    full_image_url = image_url
                else:
                    full_image_url = f"http://localhost:5173{image_url}"
                
                message_content.append(
                    {"type": "image", "url": full_image_url}
                )

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
                )
            except Exception as e:
                logger.error(
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
