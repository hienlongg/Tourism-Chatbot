"""
Hugging Face Spaces: Vietnamese Tourism Embedding API

This Gradio app exposes the embedding model as a REST API.
Deploy to Hugging Face Spaces to offload embedding computation from your main backend.

Key Features:
- Lightweight Gradio interface (automatic REST API)
- HuggingFace embedding model (multilingual-e5-large-instruct)
- Low latency semantic search
- Scales independently from main backend

Free tier specs: 16GB RAM, 2 vCPUs
Perfect for running the embedding model efficiently.

Usage:
1. Create a Space on HuggingFace with Gradio SDK
2. Upload this file
3. Access API at: https://yourusername-tourism-embedding-api.hf.space/run/embed_text
"""

import gradio as gr
import numpy as np
from typing import List
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy load to optimize startup time
_embeddings = None
_model_name = "intfloat/multilingual-e5-large-instruct"


def get_embeddings():
    """Lazy load HuggingFace embeddings model on first use."""
    global _embeddings
    if _embeddings is None:
        logger.info(f"Loading embedding model: {_model_name}")
        from langchain_huggingface import HuggingFaceEmbeddings
        
        _embeddings = HuggingFaceEmbeddings(
            model_name=_model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("✅ Embedding model loaded successfully")
    
    return _embeddings


def embed_text(text: str) -> List[float]:
    """
    Embed a single text using HuggingFace embeddings.
    
    Args:
        text: Input text to embed
    
    Returns:
        List of floats representing the embedding vector
    """
    logger.info(f"Embedding text: {text[:100]}...")
    
    embeddings = get_embeddings()
    result = embeddings.embed_query(text)
    
    logger.info(f"✅ Embedding generated (dim={len(result)})")
    return result


def embed_documents(texts: str) -> List[List[float]]:
    """
    Embed multiple texts (one per line).
    
    Args:
        texts: Multi-line string where each line is a document to embed
    
    Returns:
        List of embedding vectors (one per document)
    """
    docs = [doc.strip() for doc in texts.split('\n') if doc.strip()]
    
    if not docs:
        return []
    
    logger.info(f"Embedding {len(docs)} documents...")
    
    embeddings = get_embeddings()
    results = embeddings.embed_documents(docs)
    
    logger.info(f"✅ {len(results)} embeddings generated")
    return results


def similarity_search(query: str, num_results: int = 5) -> str:
    """
    Perform similarity search on sample documents.
    
    This is a demo endpoint. In production, your backend will:
    1. Call embed_text(query) to get the query embedding
    2. Use the vector embedding to search ChromaDB
    
    Args:
        query: Search query text
        num_results: Number of results to return
    
    Returns:
        String describing similarity scores
    """
    logger.info(f"Similarity search: {query}")
    
    embeddings = get_embeddings()
    query_embedding = embeddings.embed_query(query)
    
    # This is just a demo response
    # Your backend will handle the actual ChromaDB search
    return f"Query embedded successfully. Vector dimension: {len(query_embedding)}\nUse this embedding to search your ChromaDB instance."

def create_app():
    """Create and return the Gradio Blocks application."""
    
    with gr.Blocks(title="Tourism Embedding API") as demo:
        gr.Markdown(
            """
            # 🇻🇳 Vietnamese Tourism Embedding API
            
            Hosted on Hugging Face Spaces for efficient embedding computation.
            
            ## Available Endpoints:
            - **POST** `/run/embed_text` - Embed single text
            - **POST** `/run/embed_documents` - Embed multiple texts
            - **POST** `/run/similarity_search` - Demo similarity search
            
            ## Usage Example (from your backend):
            ```python
            import requests
            
            HF_SPACE_URL = "https://yourusername-tourism-embedding-api.hf.space"
            
            # Embed a single query
            response = requests.post(
                f"{HF_SPACE_URL}/run/embed_text",
                json={"data": ["beautiful waterfalls"]}
            )
            embedding = response.json()["data"][0]
            ```
            """
        )
        
        # Tab 1: Single Text Embedding
        with gr.Tab("Embed Single Text"):
            text_input = gr.Textbox(
                label="Text to embed",
                placeholder="E.g., 'beautiful mountain resort in Vietnam'",
                lines=3
            )
            embed_btn = gr.Button("Embed", variant="primary")
            output = gr.Textbox(label="Embedding Vector (first 10 dims)", interactive=False)
            
            def show_embedding(text):
                emb = embed_text(text)
                return f"Dimension: {len(emb)}\nFirst 10 values: {emb[:10]}"
            
            embed_btn.click(show_embedding, inputs=text_input, outputs=output)
        
        # Tab 2: Batch Embedding
        with gr.Tab("Embed Documents"):
            docs_input = gr.Textbox(
                label="Documents (one per line)",
                placeholder="Doc 1\nDoc 2\nDoc 3",
                lines=5
            )
            batch_btn = gr.Button("Embed All", variant="primary")
            batch_output = gr.Textbox(label="Results", interactive=False)
            
            def show_batch_embeddings(texts):
                results = embed_documents(texts)
                return f"Generated {len(results)} embeddings\nEach with dimension 384"
            
            batch_btn.click(show_batch_embeddings, inputs=docs_input, outputs=batch_output)
        
        # Tab 3: Similarity Search Demo
        with gr.Tab("Similarity Search Demo"):
            query_input = gr.Textbox(
                label="Search query",
                placeholder="E.g., 'beaches near Hanoi'",
            )
            num_results_input = gr.Slider(
                label="Number of results",
                minimum=1,
                maximum=20,
                value=5,
                step=1
            )
            sim_btn = gr.Button("Search", variant="primary")
            sim_output = gr.Textbox(label="Results", interactive=False)
            
            sim_btn.click(similarity_search, inputs=[query_input, num_results_input], outputs=sim_output)
        
        gr.Markdown(
            """
            ## How to use in production:
            
            1. **Deploy this Space** on Hugging Face (choose Gradio SDK)
            2. **Get your Space URL** (e.g., `https://yourusername-tourism-embedding-api.hf.space`)
            3. **Update your backend** to use the remote embedding API
            
            4. **Keep ChromaDB locally** - only embeddings are offloaded
            5. **Call generate_recommendation()** as before in your backend
            
            ## Benefits:
            - ✅ Free tier: 16GB RAM + 2 vCPUs
            - ✅ Embedding model runs independently
            - ✅ Your main backend stays lightweight
            - ✅ Scales independently from chat logic
            - ✅ Easy zero-downtime updates
            """
        )
    
    return demo


if __name__ == "__main__":
    demo = create_app()
    
    print("\n" + "="*60)
    print("🚀 STARTING EMBEDDING API")
    print("="*60)
    print("\n📍 Available Endpoints:")
    print("   POST /api/embed_text - Embed single text")
    print("   POST /api/embed_documents - Embed multiple documents")
    print("   POST /api/similarity_search - Similarity search demo")
    print("\n🌐 Web UI: http://localhost:7860")
    print("="*60 + "\n")
        
    # Launch Gradio app
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # HF Spaces handles sharing
    )
