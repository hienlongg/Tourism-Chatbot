"""
Agent with memory capabilities
"""

from typing import Optional, List
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


def create_agent_with_memory(
    model: ChatGoogleGenerativeAI,
    tools: List[BaseTool],
    checkpointer: PostgresSaver,
    system_prompt: Optional[str] = None
):
    """
    Create a LangGraph agent with memory capabilities.
    
    Args:
        model: LLM model (e.g., ChatGoogleGenerativeAI)
        tools: List of tools the agent can use
        checkpointer: PostgreSQL checkpointer for state persistence
        system_prompt: Optional system prompt to guide agent behavior
    
    Returns:
        Compiled LangGraph agent with memory
    
    Example:
        >>> from tourism_chatbot.database import get_connection_pool, initialize_checkpointer
        >>> from tourism_chatbot.agents.tools import retrieve_context
        >>> 
        >>> pool = get_connection_pool()
        >>> checkpointer = initialize_checkpointer(pool)
        >>> 
        >>> agent = create_agent_with_memory(
        ...     model=model,
        ...     tools=[retrieve_context],
        ...     checkpointer=checkpointer,
        ...     system_prompt="You are a helpful tourism guide..."
        ... )
        >>> 
        >>> # Use the agent
        >>> config = {"configurable": {"thread_id": "user123"}}
        >>> result = agent.invoke({"messages": [("user", "Hello")]}, config)
    """
    logger.info("Creating agent with memory...")
    logger.info(f"  Tools: {[tool.name for tool in tools]}")
    logger.info(f"  Model: {model.model}")
    logger.info(f"  Checkpointer: {type(checkpointer).__name__}")
    
    agent = create_react_agent(
        model=model,
        tools=tools,
        state_modifier=system_prompt,
        checkpointer=checkpointer
    )
    
    logger.info("Agent with memory created successfully")
    
    return agent


def invoke_agent_with_context(
    agent,
    user_message: str,
    thread_id: str,
    metadata: Optional[dict] = None
) -> dict:
    """
    Invoke agent with conversation context.
    
    Args:
        agent: Compiled LangGraph agent
        user_message: User's message
        thread_id: Conversation thread identifier
        metadata: Optional metadata to attach to this turn
    
    Returns:
        dict: Agent's response with full message history
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    if metadata:
        config["metadata"] = metadata
    
    inputs = {"messages": [("user", user_message)]}
    
    logger.info(f"Invoking agent (thread_id={thread_id})")
    
    result = agent.invoke(inputs, config)
    
    logger.info(f"Agent responded (thread_id={thread_id})")
    
    return result
