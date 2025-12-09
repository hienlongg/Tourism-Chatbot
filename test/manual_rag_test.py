#!/usr/bin/env python3
"""
Manual RAG Testing Script
Run individual tests and explore your RAG system
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def colored(text, color):
    """Print colored text"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['end']}"

def header(title):
    """Print a section header"""
    print(f"\n{colored('=' * 60, 'blue')}")
    print(colored(f"  {title}", 'blue'))
    print(colored('=' * 60, 'blue'), "\n")

def test_slugify():
    """Test the slugify function"""
    header("Test 1: Slugify Function")
    
    from tourism_chatbot.rag.rag_engine import slugify
    
    test_cases = [
        ("Hà Nội", "ha_noi"),
        ("Khu nhà công tử Bạc Liêu", "khu_nha_cong_tu_bac_lieu"),
        ("Thác Khe-Vằn", "thac_khe_van"),
        ("Sài Gòn (TP. Hồ Chí Minh)", "sai_gon_tp_ho_chi_minh"),
    ]
    
    print(f"Testing {len(test_cases)} slugify cases:\n")
    
    passed = 0
    for location, expected in test_cases:
        result = slugify(location)
        status = "✅" if result == expected else "❌"
        print(f"{status} slugify('{location}')")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}\n")
        if result == expected:
            passed += 1
    
    print(colored(f"Results: {passed}/{len(test_cases)} passed", 'green' if passed == len(test_cases) else 'red'))

def test_data_loading():
    """Test data loading from CSV"""
    header("Test 2: Data Loading from CSV")
    
    from tourism_chatbot.rag.rag_engine import load_and_process_data
    from config import Config
    
    try:
        print(f"Loading from: {Config.RAG_CSV_PATH}\n")
        
        df = load_and_process_data(Config.RAG_CSV_PATH)
        
        print(colored(f"✅ Successfully loaded {len(df)} locations", 'green'))
        print(f"\nFirst 5 locations:")
        print("-" * 60)
        
        for i, (loc_id, row) in enumerate(df.head(5).iterrows(), 1):
            print(f"{i}. {row['TenDiaDanh']} ({loc_id})")
            print(f"   Address: {row['DiaChi']}")
            if row.get('NoiDung'):
                print(f"   Desc: {row['NoiDung'][:60]}...")
            print()
        
    except Exception as e:
        print(colored(f"❌ Error loading data: {e}", 'red'))

def test_embeddings():
    """Test embedding generation"""
    header("Test 3: Embeddings Generation")
    
    from tourism_chatbot.rag.rag_engine import initialize_embeddings
    
    try:
        print("Initializing embeddings model...\n")
        embeddings = initialize_embeddings()
        print(colored("✅ Embeddings initialized", 'green'))
        
        test_texts = [
            "Du lịch Việt Nam",
            "Bãi biển đẹp",
            "Thác nước",
        ]
        
        print(f"\nGenerating embeddings for {len(test_texts)} texts:\n")
        
        total_time = 0
        for text in test_texts:
            start = time.time()
            embedding = embeddings.embed_query(text)
            elapsed = time.time() - start
            total_time += elapsed
            
            print(f"✅ '{text}'")
            print(f"   Embedding dim: {len(embedding)}")
            print(f"   Time: {elapsed:.3f}s\n")
        
        print(colored(f"Total time: {total_time:.2f}s", 'yellow'))
        
    except Exception as e:
        print(colored(f"❌ Error generating embeddings: {e}", 'red'))

def test_vector_search():
    """Test vector search in ChromaDB"""
    header("Test 4: Vector Search")
    
    from tourism_chatbot.rag.rag_engine import initialize_rag_system
    
    try:
        print("Initializing RAG system...\n")
        vector_store, llm, embeddings = initialize_rag_system()
        
        print(colored("✅ RAG system initialized", 'green'))
        print(f"\nVector store collection: vietnam_tourism\n")
        
        queries = [
            "bãi biển đẹp",
            "thác nước",
            "danh lam thắng cảnh",
            "lâu đài cổ",
            "yên tĩnh, nhiều cây cối"
        ]
        
        print(f"Testing similarity search with {len(queries)} queries:\n")
        
        for query in queries:
            print(f"Query: '{query}'")
            start = time.time()
            results = vector_store.similarity_search(query, k=3)
            elapsed = time.time() - start
            
            print(f"  ⏱️  Time: {elapsed:.3f}s")
            print(f"  📍 Results:")
            
            for i, doc in enumerate(results, 1):
                print(f"     {i}. {doc.metadata['TenDiaDanh']} - {doc.metadata['DiaChi']}")
            
            print()
        
    except Exception as e:
        print(colored(f"❌ Error during vector search: {e}", 'red'))

def test_recommendations():
    """Test recommendation generation"""
    header("Test 5: Recommendation Generation")
    
    from tourism_chatbot.rag.rag_engine import initialize_rag_system, generate_recommendation
    
    try:
        print("Initializing RAG system...\n")
        vector_store, llm, embeddings = initialize_rag_system()
        print(colored("✅ RAG system initialized\n", 'green'))
        
        # Test 1: No history
        print("Test 5a: Generate recommendations (no visit history)")
        print("-" * 60)
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="du lịch Việt Nam",
            user_visited_ids=[],
            allow_revisit=False,
            top_k=3,
            verbose=False
        )
        
        print(f"✅ Generated {len(result['new_places'])} recommendations")
        print(f"   New places: {len(result['new_places'])}")
        print(f"   Old places: {len(result['old_places'])}")
        print(f"   Filtered out: {result['filtered_count']}\n")
        
        # Test 2: With history, no revisit
        print("Test 5b: With visit history (no revisit)")
        print("-" * 60)
        
        visited = ['ha_noi', 'ho_chi_minh']
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="thành phố Việt Nam",
            user_visited_ids=visited,
            allow_revisit=False,
            top_k=5,
            verbose=False
        )
        
        print(f"📋 Visited locations: {', '.join(visited)}")
        print(f"✅ Generated {len(result['new_places'])} new recommendations")
        print(f"   New places: {len(result['new_places'])}")
        print(f"   Filtered (visited): {result['filtered_count']}\n")
        
        if result['new_places']:
            print("New recommendations:")
            for place in result['new_places'][:3]:
                print(f"  - {place.metadata['TenDiaDanh']}")
        
        # Test 3: Allow revisit
        print("\nTest 5c: Allow revisit")
        print("-" * 60)
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="thành phố Việt Nam",
            user_visited_ids=visited,
            allow_revisit=True,
            top_k=3,
            verbose=False
        )
        
        print(f"✅ Generated {len(result['new_places']) + len(result['old_places'])} recommendations")
        print(f"   New places: {len(result['new_places'])}")
        print(f"   Old places (revisit): {len(result['old_places'])}")
        print(f"   Filtered out: {result['filtered_count']}\n")
        
    except Exception as e:
        print(colored(f"❌ Error during recommendation: {e}", 'red'))

def test_retrieve_context_tool():
    """Test the retrieve_context tool"""
    header("Test 6: Retrieve Context Tool")
    
    from tourism_chatbot.agents.tools import set_user_context, retrieve_context
    
    try:
        print("Test 6a: Basic retrieve_context call")
        print("-" * 60)
        
        result, docs = retrieve_context("du lịch Việt Nam")
        
        print(f"✅ Retrieved {len(docs)} documents\n")
        print("Top results:")
        for i, doc in enumerate(docs[:3], 1):
            print(f"{i}. {doc.metadata['TenDiaDanh']} - {doc.metadata['DiaChi']}")
        
        # Test with user context
        print("\n\nTest 6b: With user visit history")
        print("-" * 60)
        
        visited = ['ha_noi', 'ba_na_nui_chua']
        set_user_context(visited, allow_revisit=False)
        
        print(f"📋 Setting user context: {len(visited)} visited locations")
        
        result, docs = retrieve_context("danh lam thắng cảnh")
        
        print(f"✅ Retrieved {len(docs)} documents (after filtering)\n")
        print("Recommendations (excluding visited):")
        for i, doc in enumerate(docs[:3], 1):
            print(f"{i}. {doc.metadata['TenDiaDanh']}")
        
    except Exception as e:
        print(colored(f"❌ Error with retrieve_context: {e}", 'red'))

def show_menu():
    """Show interactive menu"""
    print(f"\n{colored('RAG Manual Testing Script', 'blue')}\n")
    print("Available tests:")
    print("  1. Slugify function")
    print("  2. Data loading from CSV")
    print("  3. Embeddings generation")
    print("  4. Vector similarity search")
    print("  5. Recommendation generation")
    print("  6. Retrieve context tool")
    print("  7. Run all tests")
    print("  0. Exit")
    print()

def run_all_tests():
    """Run all tests"""
    test_slugify()
    test_data_loading()
    test_embeddings()
    test_vector_search()
    test_recommendations()
    test_retrieve_context_tool()
    
    print(f"\n{colored('All tests completed!', 'green')}\n")

def main():
    """Main interactive loop"""
    
    if len(sys.argv) > 1:
        # Run specific test from command line
        choice = sys.argv[1]
    else:
        # Interactive mode
        show_menu()
        choice = input("Enter test number: ").strip()
    
    tests = {
        '1': test_slugify,
        '2': test_data_loading,
        '3': test_embeddings,
        '4': test_vector_search,
        '5': test_recommendations,
        '6': test_retrieve_context_tool,
        '7': run_all_tests,
    }
    
    if choice in tests:
        try:
            tests[choice]()
        except Exception as e:
            print(colored(f"\n❌ Unexpected error: {e}", 'red'))
            import traceback
            traceback.print_exc()
    elif choice == '0':
        print("Exiting...")
        sys.exit(0)
    else:
        print(colored("Invalid choice", 'red'))

if __name__ == "__main__":
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print(colored("⚠️  Warning: GEMINI_API_KEY not set", 'yellow'))
        print("Some tests may fail. Set it with: export GEMINI_API_KEY='your-key'\n")
    
    main()
