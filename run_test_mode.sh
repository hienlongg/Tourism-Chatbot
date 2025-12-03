#!/bin/bash
# Run Chainlit in test mode with predefined user and thread IDs

# Activate virtual environment
source .venv/bin/activate

# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Set test mode environment variables
export CHAINLIT_TEST_MODE=true
export CHAINLIT_TEST_USER_ID="00000000-0000-0000-0000-000000000001"
export CHAINLIT_TEST_THREAD_ID="00000000-0000-0000-0000-000000000002"

# Display configuration
echo "================================"
echo "🧪 CHAINLIT TEST MODE"
echo "================================"
echo "User ID: $CHAINLIT_TEST_USER_ID"
echo "Thread ID: $CHAINLIT_TEST_THREAD_ID"
echo "================================"
echo ""

# Run Chainlit
chainlit run tourism_chatbot/cl_app.py -w --headless
