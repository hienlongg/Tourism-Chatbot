#!/usr/bin/env python3
"""
Test script to verify database connection and agent setup
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database_connection():
    """Test PostgreSQL connection"""
    print("🔧 Testing database connection...")
    
    try:
        from tourism_chatbot.database import get_connection_pool, initialize_checkpointer
        
        pool = get_connection_pool()
        print("✅ Connection pool created")
        
        checkpointer = initialize_checkpointer(pool, setup_schema=True)
        print("✅ Checkpointer initialized")
        print("✅ Database tables created/verified")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_agent_creation():
    """Test agent with memory creation"""
    print("\n🤖 Testing agent creation...")
    
    try:
        from tourism_chatbot.database import get_connection_pool, initialize_checkpointer
        from tourism_chatbot.memory import create_agent_with_memory
        from tourism_chatbot.agents.tools import retrieve_context
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize database
        pool = get_connection_pool()
        checkpointer = initialize_checkpointer(pool)
        
        # Create model
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
        print("✅ Model created")
        
        # Create agent
        agent = create_agent_with_memory(
            model=model,
            tools=[retrieve_context],
            checkpointer=checkpointer,
            system_prompt="You are a helpful assistant."
        )
        print("✅ Agent with memory created")
        
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_context():
    """Test user context manager"""
    print("\n👤 Testing user context manager...")
    
    try:
        from tourism_chatbot.memory import UserContextManager
        
        context = UserContextManager(user_id="test_user")
        
        # Test operations
        context.add_visited("bai_bien_my_khe")
        context.add_visited("hoi_an_ancient_town")
        context.set_allow_revisit(False)
        
        visited = context.get_visited()
        assert len(visited) == 2
        assert "bai_bien_my_khe" in visited
        
        stats = context.get_stats()
        print(f"✅ Context manager working: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Context manager failed: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from tourism_chatbot.config import config
        
        print("Configuration:")
        config.display()
        
        is_valid = config.validate()
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print("⚠️  Configuration has missing values")
        
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 TOURISM CHATBOT - INTEGRATION TEST")
    print("="*60)
    
    results = {
        "Config": test_config(),
        "Database": test_database_connection(),
        "User Context": test_user_context(),
        "Agent Creation": test_agent_creation(),
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
