"""
Chainlit Tourism Chatbot Application

A conversational AI chatbot for Vietnamese tourism recommendations using RAG
(Retrieval-Augmented Generation). The chatbot provides personalized suggestions
based on user queries while tracking visit history and preferences.

Features:
- Semantic search for tourism locations
- Visit history tracking per user session
- Revisit control (allow/disallow suggesting visited places)
- Streaming LLM responses for better UX
- Vietnamese language support

"""

import os
import chainlit as cl
from typing import List, Dict
import re
import logging

# Import RAG engine
from tourism_chatbot.rag.rag_engine import (
    initialize_rag_system,
)

# Import the agent
from tourism_chatbot.agents.tourism_agent import agent
from tourism_chatbot.agents.tools import set_user_context

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE (Initialized at startup)
# ============================================================================

# These will be populated in on_chat_start
VECTOR_STORE = None
LLM = None
EMBEDDINGS = None


# ============================================================================
# STARTUP HANDLER
# ============================================================================

@cl.on_chat_start
async def on_chat_start():
    """
    Initialize the chatbot when a new chat session starts.
    
    This function:
    1. Loads the RAG system (vector store, LLM, embeddings)
    2. Initializes user session state (visited_ids, allow_revisit)
    3. Sends welcome message
    """
    global VECTOR_STORE, LLM, EMBEDDINGS
    
    # Show loading message
    loading_msg = cl.Message(content="")
    await loading_msg.send()
    
    try:
        # Initialize RAG system if not already loaded
        if VECTOR_STORE is None or LLM is None:
            await loading_msg.stream_token("🚀 Đang khởi động hệ thống RAG...\n\n")
            
            # Get API key from environment
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                await loading_msg.stream_token(
                    "⚠️ Cảnh báo: Không tìm thấy GEMINI_API_KEY trong biến môi trường.\n"
                    "Vui lòng thiết lập API key để sử dụng chatbot.\n\n"
                )
                return
            
            await loading_msg.stream_token("📂 Đang tải dữ liệu địa danh...\n")
            await loading_msg.stream_token("🤖 Đang khởi động mô hình embedding...\n")
            await loading_msg.stream_token("🧠 Đang kết nối với Gemini LLM...\n\n")
            
            # Initialize system
            VECTOR_STORE, LLM, EMBEDDINGS = initialize_rag_system(api_key=api_key)
            
            await loading_msg.stream_token("✅ Hệ thống đã sẵn sàng!\n\n")
        
        # Initialize user session state
        cl.user_session.set("visited_ids", [])
        cl.user_session.set("allow_revisit", False)
        cl.user_session.set("message_history", [])
        
        # Send welcome message
        await loading_msg.stream_token(
            "👋 Xin chào! Tôi là trợ lý du lịch thông minh của Việt Nam.\n\n"
            "Tôi có thể giúp bạn:\n"
            "✨ Tìm kiếm địa điểm du lịch phù hợp\n"
            "🗺️ Gợi ý những nơi mới dựa trên sở thích\n"
            "📝 Ghi nhớ những nơi bạn đã đến\n\n"
            "**Cách sử dụng:**\n"
            "- Hỏi tôi về địa điểm: *\"Tìm bãi biển đẹp ở miền Trung\"*\n"
            "- Báo nơi đã đến: *\"Tôi đã từng đến Hội An\"*\n"
            "- Cho phép gợi ý lại: *\"Cho phép gợi ý lại\"*\n"
            "- Không cho phép: *\"Không cho phép gợi ý lại\"*\n\n"
            "Hãy thử hỏi tôi bất cứ điều gì về du lịch Việt Nam! 🇻🇳"
        )
        
        await loading_msg.update()
        
    except Exception as e:
        await loading_msg.stream_token(
            f"❌ Lỗi khi khởi động hệ thống: {str(e)}\n\n"
            "Vui lòng kiểm tra:\n"
            "1. GEMINI_API_KEY đã được thiết lập\n"
            "2. File dữ liệu CSV tồn tại\n"
            "3. Kết nối internet ổn định\n"
        )
        await loading_msg.update()


# ============================================================================
# COMMAND DETECTION
# ============================================================================

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
        r'(?:tôi\s+)?đã\s+(?:từng\s+)?(?:đến|đi|ghé|thăm)\s+(.+)',
        r'(?:tôi\s+)?đã\s+(?:từng\s+)?(?:tham quan|viếng)\s+(.+)',
    ]
    
    message_lower = message.lower().strip()
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            # Extract location name(s)
            locations_str = match.group(1)
            # Split by common separators
            locations = re.split(r'[,và&]', locations_str)
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
        r'cho\s+phép\s+(?:gợi\s+ý\s+)?lại',
        r'được\s+(?:gợi\s+ý\s+)?lại',
        r'có\s+thể\s+(?:gợi\s+ý\s+)?lại',
    ]
    
    # Disallow patterns
    disallow_patterns = [
        r'không\s+(?:cho\s+phép|được)\s+(?:gợi\s+ý\s+)?lại',
        r'không\s+muốn\s+(?:gợi\s+ý\s+)?lại',
        r'tắt\s+(?:gợi\s+ý\s+)?lại',
    ]
    
    for pattern in allow_patterns:
        if re.search(pattern, message_lower):
            return "allow"
    
    for pattern in disallow_patterns:
        if re.search(pattern, message_lower):
            return "disallow"
    
    return "none"


# ============================================================================
# MESSAGE HANDLER
# ============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handle incoming user messages.
    
    Flow:
    1. Detect special commands (visited locations, revisit control)
    2. Update session state accordingly
    3. If not a command, generate recommendation using RAG
    4. Stream response back to user
    """
    global VECTOR_STORE, LLM
    
    user_message = message.content.strip()
    
    # Get session state
    visited_ids = cl.user_session.get("visited_ids")
    allow_revisit = cl.user_session.get("allow_revisit")
    
    # ========================================================================
    # COMMAND DETECTION
    # ========================================================================
    
    # Check for visited location command
    visited_locations = detect_visited_command(user_message)
    if visited_locations:
        # User is reporting visited locations
        from rag.rag_engine import slugify
        
        new_ids = []
        for location in visited_locations:
            loc_id = slugify(location)
            if loc_id not in visited_ids:
                visited_ids.append(loc_id)
                new_ids.append(location)
        
        # Update session
        cl.user_session.set("visited_ids", visited_ids)
        
        # Send confirmation
        if new_ids:
            response = (
                f"✅ Đã ghi nhận! Bạn đã từng đến: **{', '.join(new_ids)}**\n\n"
                f"Tôi sẽ ưu tiên gợi ý những địa điểm mới cho bạn.\n"
                f"(Hiện tại: {len(visited_ids)} địa điểm đã ghé thăm)"
            )
        else:
            response = "📝 Các địa điểm này đã có trong danh sách của bạn rồi!"
        
        await cl.Message(content=response).send()
        return
    
    # Check for allow/disallow revisit command
    revisit_cmd = detect_allow_revisit_command(user_message)
    if revisit_cmd != "none":
        if revisit_cmd == "allow":
            cl.user_session.set("allow_revisit", True)
            response = (
                "✅ Đã bật chế độ cho phép gợi ý lại!\n\n"
                "Tôi sẽ gợi ý cả những địa điểm bạn đã từng đến."
            )
        else:  # disallow
            cl.user_session.set("allow_revisit", False)
            response = (
                "✅ Đã tắt chế độ gợi ý lại!\n\n"
                "Tôi sẽ chỉ gợi ý những địa điểm mới mà bạn chưa đến."
            )
        
        await cl.Message(content=response).send()
        return
    
    # ========================================================================
    # AGENT RECOMMENDATION
    # ========================================================================
    
    # Check if system is ready
    if VECTOR_STORE is None or LLM is None:
        await cl.Message(
            content="❌ Hệ thống chưa sẵn sàng. Vui lòng khởi động lại chat."
        ).send()
        return
    
    # Get or initialize message history
    message_history = cl.user_session.get("message_history")
    if message_history is None:
        message_history = []
        cl.user_session.set("message_history", message_history)
    
    # Add user message to history
    message_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Create streaming message
    response_msg = cl.Message(content="")
    await response_msg.send()
    
    try:
        # Update tool context with user's visited locations
        set_user_context(visited_ids=visited_ids, allow_revisit=allow_revisit)
        
        # Prepare inputs for the agent
        inputs = {
            "messages": [("user", user_message)]
        }
        
        # Configuration for the agent
        config = {
            "configurable": {
                "thread_id": cl.user_session.get("id")
            }
        }
        
        # Stream agent response
        logger.info(f"🤖 [AGENT START] Processing query: {user_message}")
        logger.info(f"📋 User context: {len(visited_ids)} visited locations, allow_revisit={allow_revisit}")
        
        full_response = ""
        tool_calls_count = 0
        
        async for event in agent.astream(inputs, config, stream_mode="values"):
            last_message = event["messages"][-1]
            
            # Log tool calls
            if last_message.type == "tool":
                tool_calls_count += 1
                logger.info(f"🔧 [TOOL CALL #{tool_calls_count}] Agent is calling tool: {last_message.name if hasattr(last_message, 'name') else 'Unknown'}")
            
            if last_message.type == "ai":
                # Log if AI is about to call tools
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        logger.info(f"🔧 [TOOL REQUEST] Agent requesting tool: {tool_call.get('name', 'Unknown')}")
                        logger.info(f"   Args: {tool_call.get('args', {})}")
                
                # Stream content from AI
                if hasattr(last_message, "content") and last_message.content:
                    # Only stream the new part of the content
                    if len(last_message.content) > len(full_response):
                        new_content = last_message.content[len(full_response):]
                        await response_msg.stream_token(new_content)
                        full_response = last_message.content
        
        # Update message history with agent response
        if full_response:
            message_history.append({
                "role": "assistant",
                "content": full_response
            })
            cl.user_session.set("message_history", message_history)
        
        # Update message in UI
        await response_msg.update()
        logger.info(f"✅ [AGENT COMPLETE] Response completed (Tool calls: {tool_calls_count})")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        error_msg = (
            f"❌ Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn.\n\n"
            f"Chi tiết lỗi: {str(e)}\n\n"
            f"Vui lòng thử lại hoặc liên hệ quản trị viên."
        )
        await response_msg.stream_token(error_msg)
        await response_msg.update()

# ============================================================================
# ERROR HANDLER
# ============================================================================

@cl.on_chat_end
async def on_chat_end():
    """
    Print when chat session ends.
    """
    # Clear session state
    print("✅ Chat session ended")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Run the Chainlit app.
    
    Usage:
        chainlit run cl_app.py -w
    
    Environment Variables Required:
        GEMINI_API_KEY: Google Gemini API key
    
    Optional:
        CHAINLIT_PORT: Port to run on (default: 8000)
    """
    print("\n" + "="*60)
    print("🚀 STARTING CHAINLIT TOURISM CHATBOT")
    print("="*60)
    print("\nMake sure you have set the following environment variables:")
    print("  - GEMINI_API_KEY: Your Google Gemini API key")
    print("\nRun with: chainlit run cl_app.py -w")
    print("="*60 + "\n")