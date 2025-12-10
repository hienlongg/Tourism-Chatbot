"""
Shared constants for all APIs.
"""

# API Configuration
API_TIMEOUT = 30  # seconds
MAX_BATCH_SIZE = 100
DEFAULT_MODEL = "intfloat/multilingual-e5-large-instruct"

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 7860

# Response sizes
MAX_RESPONSE_SIZE = 10_000_000  # 10MB
EMBEDDING_DIMENSION = 384
