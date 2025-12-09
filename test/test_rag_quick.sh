#!/bin/bash

# RAG Testing Quick Start Script
# Usage: ./test_rag_quick.sh [test_type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check if GEMINI_API_KEY is set
check_api_key() {
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  Warning: GEMINI_API_KEY not set${NC}"
        echo "Some tests will be skipped."
        echo "To set it: export GEMINI_API_KEY='your-key-here'"
    fi
}

# Install dependencies
install_deps() {
    print_header "Installing test dependencies..."
    pip install -q pytest pytest-cov pytest-asyncio
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Run unit tests only (fast)
run_unit_tests() {
    print_header "Running Unit Tests (Fast)"
    echo "Testing: slugify, data loading, documents, embeddings, LLM init..."
    
    pytest test/test_rag_functions.py::TestSlugify \
            test/test_rag_functions.py::TestDataLoading \
            test/test_rag_functions.py::TestDocumentCreation \
            test/test_rag_functions.py::TestEmbeddings \
            test/test_rag_functions.py::TestLLMInitialization \
            -v --tb=short
    
    echo -e "\n${GREEN}✅ Unit tests completed${NC}"
}

# Run integration tests (slower)
run_integration_tests() {
    print_header "Running Integration Tests"
    echo "Testing: vector store, recommendation generation..."
    
    pytest test/test_rag_functions.py::TestVectorStoreOperations \
            test/test_rag_functions.py::TestRecommendationGeneration \
            -v -s --tb=short
    
    echo -e "\n${GREEN}✅ Integration tests completed${NC}"
}

# Run all tests with coverage
run_all_with_coverage() {
    print_header "Running All Tests with Coverage Report"
    
    pytest test/test_rag_functions.py \
        --cov=tourism_chatbot.rag \
        --cov=tourism_chatbot.agents \
        --cov-report=term-missing \
        --cov-report=html \
        -v --tb=short
    
    echo -e "\n${GREEN}✅ Coverage report generated${NC}"
    echo -e "${YELLOW}📊 Open htmlcov/index.html to view detailed coverage${NC}"
}

# Run specific test
run_specific_test() {
    local test_name=$1
    print_header "Running Specific Test: $test_name"
    
    pytest "test/test_rag_functions.py::$test_name" -v -s --tb=short
}

# Test recommendation generation (most important)
test_recommendations() {
    print_header "Testing Recommendation Generation"
    echo "This is the core functionality - testing thoroughly..."
    
    pytest test/test_rag_functions.py::TestRecommendationGeneration -v -s
    
    echo -e "\n${GREEN}✅ Recommendation tests passed${NC}"
}

# Quick sanity check
quick_check() {
    print_header "Quick Sanity Check"
    echo "Running basic functionality tests..."
    
    pytest test/test_rag_functions.py::TestSlugify \
            test/test_rag_functions.py::TestEmbeddings \
            -v --tb=short
    
    echo -e "\n${GREEN}✅ Quick check passed${NC}"
}

# Show test categories
show_test_categories() {
    echo -e "\n${BLUE}Available Test Categories:${NC}\n"
    echo "  test_slugify              - Test location name normalization"
    echo "  test_data_loading         - Test CSV loading and filtering"
    echo "  test_documents            - Test document creation"
    echo "  test_embeddings           - Test HuggingFace embeddings"
    echo "  test_llm                  - Test LLM initialization"
    echo "  test_vector_store         - Test ChromaDB operations"
    echo "  test_recommendations      - Test recommendation generation ⭐"
    echo "  test_context              - Test user context management"
    echo ""
}

# Show usage
show_usage() {
    echo -e "${BLUE}RAG Testing Quick Start${NC}\n"
    echo "Usage: ./test_rag_quick.sh [option]\n"
    echo "Options:"
    echo "  install              - Install test dependencies"
    echo "  quick                - Quick sanity check (fastest)"
    echo "  unit                 - Run unit tests only"
    echo "  integration          - Run integration tests"
    echo "  recommend            - Test recommendations (important!)"
    echo "  all                  - Run all tests with coverage"
    echo "  categories           - Show available test categories"
    echo "  <TestClass::method>  - Run specific test (e.g., TestSlugify::test_basic_slugify)"
    echo ""
    echo "Examples:"
    echo "  ./test_rag_quick.sh install"
    echo "  ./test_rag_quick.sh quick"
    echo "  ./test_rag_quick.sh recommend"
    echo "  ./test_rag_quick.sh all"
    echo "  ./test_rag_quick.sh TestRecommendationGeneration::test_generate_recommendation_no_history"
}

# Main
main() {
    check_api_key
    
    case "$1" in
        install)
            install_deps
            ;;
        quick)
            quick_check
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        recommend)
            test_recommendations
            ;;
        all)
            install_deps
            run_all_with_coverage
            ;;
        categories)
            show_test_categories
            ;;
        help|-h|--help)
            show_usage
            ;;
        *)
            if [ -n "$1" ]; then
                # Assume it's a specific test
                run_specific_test "$1"
            else
                show_usage
            fi
            ;;
    esac
}

main "$@"
