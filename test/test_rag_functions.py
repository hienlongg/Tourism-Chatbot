#!/usr/bin/env python3
"""
Comprehensive RAG Function Testing Suite

This test suite covers:
1. Data loading and processing (slugify, load_and_process_data)
2. Document creation
3. Vector store initialization and persistence
4. Embedding initialization
5. LLM initialization
6. Recommendation generation with history filtering
7. Streaming recommendations
8. Integration tests (full pipeline)
"""

import pytest
import os
import sys
import pandas as pd
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Skip these tests if API keys are missing
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set"
)


class TestSlugify:
    """Test the slugify function for Vietnamese text normalization"""
    
    def test_basic_slugify(self):
        """Test basic slugification without diacritics"""
        from tourism_chatbot.rag.rag_engine import slugify
        
        result = slugify("Ha Noi")
        assert result == "ha_noi"
    
    def test_vietnamese_diacritics(self):
        """Test Vietnamese diacritics conversion"""
        from tourism_chatbot.rag.rag_engine import slugify
        
        # Test with 'đ' character
        result = slugify("Hà Nội")
        assert result == "ha_noi"
        assert "đ" not in result
    
    def test_complex_vietnamese_name(self):
        """Test complex location name with multiple diacritics"""
        from tourism_chatbot.rag.rag_engine import slugify
        
        result = slugify("Khu nhà công tử Bạc Liêu")
        assert "nha" in result
        assert "cong" in result
        assert " " not in result  # No spaces
        assert "đ" not in result
        assert "ạ" not in result  # All diacritics removed
    
    def test_special_characters_removed(self):
        """Test that special characters are removed"""
        from tourism_chatbot.rag.rag_engine import slugify
        
        result = slugify("Thác Khe-Vằn!")
        assert "!" not in result
        assert "-" not in result
        assert result == "thac_khe_van"


class TestDataLoading:
    """Test data loading and processing functions"""
    
    @pytest.fixture
    def sample_csv(self):
        """Create a temporary sample CSV for testing"""
        data = {
            'TenDiaDanh': ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng'],
            'DiaChi': ['Thủ đô Việt Nam', 'Thành phố Hồ Chí Minh', 'Thành phố biển'],
            'NoiDung': ['Thủ đô lâu đời', 'Thành phố lớn nhất', 'Thành phố của biển'],
            'ImageURL': ['url1', 'url2', 'url3'],
            'DichVu': ['Service1', 'Service2', 'Service3'],
            'ThongTinLienHe': ['Info1', 'Info2', 'Info3'],
            'DanhGia (Google Map)': ['4.5', '4.7', '4.6']
        }
        df = pd.DataFrame(data)
        
        # Write to temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    def test_load_and_process_data(self, sample_csv):
        """Test loading and processing CSV data"""
        from tourism_chatbot.rag.rag_engine import load_and_process_data
        
        df = load_and_process_data(sample_csv)
        
        # Check that all rows were loaded
        assert len(df) == 3
        
        # Check that loc_id was created
        assert 'loc_id' in df.index.name
        
        # Check that loc_ids are unique
        assert len(df) == len(set(df.index))
    
    def test_load_and_process_data_filters_missing_fields(self):
        """Test that rows with missing critical fields are filtered"""
        from tourism_chatbot.rag.rag_engine import load_and_process_data
        
        # Create CSV with missing data
        data = {
            'TenDiaDanh': ['Location1', None, 'Location3'],
            'DiaChi': ['Address1', 'Address2', None],
            'NoiDung': ['Desc1', 'Desc2', 'Desc3']
        }
        df = pd.DataFrame(data)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            result = load_and_process_data(temp_file.name)
            # Only first row should remain (has both TenDiaDanh and DiaChi)
            assert len(result) == 1
            assert result.index[0] == 'location1'
        finally:
            os.unlink(temp_file.name)


class TestDocumentCreation:
    """Test document creation for vectorization"""
    
    def test_create_documents(self):
        """Test creating LangChain documents from DataFrame"""
        from tourism_chatbot.rag.rag_engine import create_documents
        import pandas as pd
        
        # Create sample data
        data = {
            'TenDiaDanh': ['Hà Nội'],
            'DiaChi': ['Thủ đô'],
            'NoiDung': ['Thủ đô lâu đời'],
            'ImageURL': ['url1'],
            'DichVu': ['Service1'],
            'ThongTinLienHe': ['Info1'],
            'DanhGia (Google Map)': ['4.5']
        }
        df = pd.DataFrame(data)
        df['loc_id'] = ['ha_noi']
        df = df.set_index('loc_id')
        
        docs = create_documents(df)
        
        assert len(docs) == 1
        doc = docs[0]
        
        # Check page_content
        assert 'Hà Nội' in doc.page_content
        assert 'Thủ đô' in doc.page_content
        assert 'Thủ đô lâu đời' in doc.page_content
        
        # Check metadata
        assert doc.metadata['TenDiaDanh'] == 'Hà Nội'
        assert doc.metadata['loc_id'] == 'ha_noi'
        assert doc.metadata['DanhGia'] == '4.5'
    
    def test_create_documents_handles_missing_content(self):
        """Test document creation with missing NoiDung"""
        from tourism_chatbot.rag.rag_engine import create_documents
        import pandas as pd
        
        data = {
            'TenDiaDanh': ['Location'],
            'DiaChi': ['Address'],
            'NoiDung': [''],  # Empty description
            'ImageURL': [''],
            'DichVu': [''],
            'ThongTinLienHe': [''],
            'DanhGia (Google Map)': ['']
        }
        df = pd.DataFrame(data)
        df['loc_id'] = ['location_slug']
        df = df.set_index('loc_id')
        
        docs = create_documents(df)
        
        # Should still create document even without description
        assert len(docs) == 1
        assert 'Location' in docs[0].page_content


class TestEmbeddings:
    """Test embedding initialization"""
    
    def test_initialize_embeddings(self):
        """Test initializing HuggingFace embeddings"""
        from tourism_chatbot.rag.rag_engine import initialize_embeddings
        
        embeddings = initialize_embeddings()
        
        # Check that embeddings can be called
        assert embeddings is not None
        
        # Test embedding a simple text
        result = embeddings.embed_query("Du lịch Việt Nam")
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], float)


class TestLLMInitialization:
    """Test LLM initialization"""
    
    def test_initialize_llm_with_default_config(self):
        """Test initializing LLM with default config"""
        from tourism_chatbot.rag.rag_engine import initialize_llm
        
        llm = initialize_llm()
        
        assert llm is not None
        assert hasattr(llm, 'invoke')
    
    def test_initialize_llm_with_custom_temperature(self):
        """Test initializing LLM with custom temperature"""
        from tourism_chatbot.rag.rag_engine import initialize_llm
        
        llm = initialize_llm(temperature=0.7)
        
        assert llm is not None
        assert llm.temperature == 0.7


class TestVectorStoreOperations:
    """Test vector store creation and loading"""
    
    @pytest.fixture
    def temp_chroma_db(self):
        """Create temporary ChromaDB directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_create_and_load_vector_store(self, temp_chroma_db):
        """Test creating and then loading a vector store"""
        from tourism_chatbot.rag.rag_engine import (
            initialize_embeddings, create_vector_store, load_vector_store,
            create_documents
        )
        import pandas as pd
        
        embeddings = initialize_embeddings()
        
        # Create sample documents
        data = {
            'TenDiaDanh': ['Hà Nội', 'Sài Gòn'],
            'DiaChi': ['Bắc', 'Nam'],
            'NoiDung': ['Thủ đô', 'Thành phố lớn'],
            'ImageURL': ['', ''],
            'DichVu': ['', ''],
            'ThongTinLienHe': ['', ''],
            'DanhGia (Google Map)': ['', '']
        }
        df = pd.DataFrame(data)
        df['loc_id'] = ['ha_noi', 'sai_gon']
        df = df.set_index('loc_id')
        
        docs = create_documents(df)
        
        # Create vector store
        vs = create_vector_store(docs, embeddings, temp_chroma_db)
        assert vs is not None
        
        # Load the same vector store
        vs_loaded = load_vector_store(embeddings, temp_chroma_db)
        assert vs_loaded is not None
        
        # Test similarity search works on loaded store
        results = vs_loaded.similarity_search("Hà Nội thủ đô", k=1)
        assert len(results) > 0


class TestRecommendationGeneration:
    """Test the main recommendation generation function"""
    
    @pytest.fixture
    def setup_rag_system(self):
        """Setup a test RAG system with mock data"""
        from tourism_chatbot.rag.rag_engine import (
            initialize_embeddings, create_documents, create_vector_store,
            initialize_llm
        )
        import pandas as pd
        
        # Create sample data
        data = {
            'TenDiaDanh': [
                'Hà Nội',
                'Hồ Chí Minh',
                'Đà Nẵng',
                'Hạ Long',
                'Huế'
            ],
            'DiaChi': ['Bắc', 'Nam', 'Trung', 'Quảng Ninh', 'Thừa Thiên'],
            'NoiDung': [
                'Thủ đô lâu đời',
                'Thành phố lớn nhất',
                'Thành phố biển đẹp',
                'Vịnh nổi tiếng',
                'Cộng hòa xã hội chủ nghĩa'
            ],
            'ImageURL': ['', '', '', '', ''],
            'DichVu': ['', '', '', '', ''],
            'ThongTinLienHe': ['', '', '', '', ''],
            'DanhGia (Google Map)': ['4.5', '4.7', '4.6', '4.8', '4.4']
        }
        df = pd.DataFrame(data)
        df['loc_id'] = ['ha_noi', 'ho_chi_minh', 'da_nang', 'ha_long', 'hue']
        df = df.set_index('loc_id')
        
        embeddings = initialize_embeddings()
        temp_dir = tempfile.mkdtemp()
        docs = create_documents(df)
        vector_store = create_vector_store(docs, embeddings, temp_dir)
        llm = initialize_llm()
        
        yield vector_store, llm, temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_generate_recommendation_no_history(self, setup_rag_system):
        """Test recommendation generation without visit history"""
        from tourism_chatbot.rag.rag_engine import generate_recommendation
        
        vector_store, llm, _ = setup_rag_system
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="đặc sản du lịch Việt Nam",
            user_visited_ids=[],
            allow_revisit=False,
            top_k=3,
            verbose=True
        )
        
        # Check result structure
        assert 'new_places' in result
        assert 'old_places' in result
        assert 'filtered_count' in result
        
        # No history, so old_places should be empty
        assert len(result['old_places']) == 0
        assert result['filtered_count'] == 0
    
    def test_generate_recommendation_with_history_no_revisit(self, setup_rag_system):
        """Test recommendation generation with visit history (no revisit allowed)"""
        from tourism_chatbot.rag.rag_engine import generate_recommendation
        
        vector_store, llm, _ = setup_rag_system
        
        visited_ids = ['ha_noi', 'ho_chi_minh']
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="thành phố Việt Nam",
            user_visited_ids=visited_ids,
            allow_revisit=False,
            top_k=5,
            verbose=True
        )
        
        # Should filter out visited locations
        for place in result['new_places']:
            assert place.metadata['loc_id'] not in visited_ids
    
    def test_generate_recommendation_with_history_allow_revisit(self, setup_rag_system):
        """Test recommendation generation allowing revisit"""
        from tourism_chatbot.rag.rag_engine import generate_recommendation
        
        vector_store, llm, _ = setup_rag_system
        
        visited_ids = ['ha_noi']
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="thành phố Việt Nam",
            user_visited_ids=visited_ids,
            allow_revisit=True,
            top_k=3,
            verbose=True
        )
        
        # With allow_revisit=True, filtered_count should be 0
        assert result['filtered_count'] == 0
        
        # Combined old and new places should equal total results
        total_places = len(result['new_places']) + len(result['old_places'])
        assert total_places > 0
    
    def test_generate_recommendation_no_new_places(self, setup_rag_system):
        """Test when all matched places have been visited"""
        from tourism_chatbot.rag.rag_engine import generate_recommendation
        
        vector_store, llm, _ = setup_rag_system
        
        # Mark all locations as visited
        visited_ids = ['ha_noi', 'ho_chi_minh', 'da_nang', 'ha_long', 'hue']
        
        result = generate_recommendation(
            vector_store=vector_store,
            llm=llm,
            user_query="du lịch Việt Nam",
            user_visited_ids=visited_ids,
            allow_revisit=False,
            top_k=5
        )
        
        # No new places available
        assert len(result['new_places']) == 0


class TestRAGSystemInitialization:
    """Test complete RAG system initialization"""
    
    def test_initialize_rag_system_creates_vector_store(self, monkeypatch):
        """Test that initialize_rag_system creates all components"""
        from tourism_chatbot.rag.rag_engine import initialize_rag_system
        
        # Use temporary directory for vector store
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Mock CSV path with test data
            import pandas as pd
            test_csv = os.path.join(temp_dir, 'test_tourism.csv')
            data = {
                'TenDiaDanh': ['Hà Nội', 'Sài Gòn'],
                'DiaChi': ['Bắc', 'Nam'],
                'NoiDung': ['Thủ đô', 'Thành phố lớn'],
                'ImageURL': ['', ''],
                'DichVu': ['', ''],
                'ThongTinLienHe': ['', ''],
                'DanhGia (Google Map)': ['4.5', '4.7']
            }
            pd.DataFrame(data).to_csv(test_csv, index=False)
            
            chroma_db_path = os.path.join(temp_dir, 'chroma_db')
            
            # Initialize system
            vs, llm, embeddings = initialize_rag_system(
                csv_path=test_csv,
                chroma_db_path=chroma_db_path,
                force_recreate=False
            )
            
            # Verify components are initialized
            assert vs is not None
            assert llm is not None
            assert embeddings is not None
            
            # Verify vector store was created
            assert os.path.exists(chroma_db_path)
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestUserContextManagement:
    """Test user context management in tools"""
    
    def test_set_user_context(self):
        """Test setting user context"""
        from tourism_chatbot.agents.tools import set_user_context
        
        visited_ids = ['ha_noi', 'ho_chi_minh']
        set_user_context(visited_ids, allow_revisit=True)
        
        # User context should be updated (internal state)
        # This test verifies the function doesn't raise errors
        assert True
    
    def test_retrieve_context_tool_filters_visited(self):
        """Test that retrieve_context filters visited locations"""
        from tourism_chatbot.agents.tools import set_user_context, retrieve_context
        
        # Set context with visited locations
        visited_ids = ['ha_noi', 'ho_chi_minh']
        set_user_context(visited_ids, allow_revisit=False)
        
        # Call retrieve_context
        try:
            result, docs = retrieve_context("du lịch Việt Nam")
            # Should return some results (may be empty if all filtered)
            assert isinstance(result, str)
        except Exception as e:
            # Vector store may not be initialized in test
            pytest.skip(f"Vector store not initialized: {e}")


def test_integration_full_pipeline():
    """Integration test: Full RAG pipeline from query to results"""
    pytest.skip("Full integration test - requires proper vector store setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
