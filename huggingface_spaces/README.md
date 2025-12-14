# HuggingFace Spaces - Embedding API

This directory contains the code to deploy the Vietnamese Tourism Embedding Model on HuggingFace Spaces.

## Quick Overview

This is a **Gradio-based REST API** that exposes the embedding model as endpoints. It runs independently from your main backend on HuggingFace's free infrastructure.

### Why This Setup?

| Component | Before | After |
|-----------|--------|-------|
| Embedding Model | On main backend | 🆓 HF Spaces (16GB free tier) |
| Backend RAM | ~5GB | ~2GB |
| Independent Scaling | ✗ | ✓ |
| Cost | ~$20-30/month | ~$7-10/month |

## What's Included

```
├── app.py              # Gradio web app + REST API
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker deployment option
└── README.md          # This file
```

## Deployment Options

### Option 1: Gradio SDK (Recommended) ⭐

**Steps:**

1. Go to https://huggingface.co/new-space
2. Create a new Space with:
   - **Name:** `tourism-embedding-api`
   - **SDK:** Gradio
   - **License:** OpenRAIL

3. Clone the space:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/tourism-embedding-api
   cd tourism-embedding-api
   ```

4. Copy files from this repo:
   ```bash
   cp app.py requirements.txt .
   ```

5. Push to deploy:
   ```bash
   git add app.py requirements.txt
   git commit -m "Add embedding API"
   git push
   ```

6. Wait 2-5 minutes for deployment. Check status at:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/tourism-embedding-api
   ```

### Option 2: Docker SDK

If you prefer Docker, HF Spaces also supports Docker images:

1. In Space settings, switch to "Docker" SDK
2. Copy `Dockerfile` and `requirements.txt` to space
3. Push and HF will build + deploy automatically

## Using the API

### Endpoints (Automatic REST API)

HuggingFace Spaces automatically exposes Gradio functions as REST API endpoints.

#### 1. Embed Single Text

```bash
curl -X POST https://YOUR_USERNAME-tourism-embedding-api.hf.space/run/embed_text \
  -H "Content-Type: application/json" \
  -d '{"data": ["beautiful mountain resort"]}'
```

**Response:**
```json
{
  "data": [
    [0.123, -0.456, 0.789, ...]
  ]
}
```

#### 2. Embed Multiple Texts

```bash
curl -X POST https://YOUR_USERNAME-tourism-embedding-api.hf.space/run/embed_documents \
  -H "Content-Type: application/json" \
  -d '{"data": ["Doc1\nDoc2\nDoc3"]}'
```

**Response:**
```json
{
  "data": [
    [[0.1, 0.2, ...], [0.3, 0.4, ...], [0.5, 0.6, ...]]
  ]
}
```

#### 3. Similarity Search Demo

```bash
curl -X POST https://YOUR_USERNAME-tourism-embedding-api.hf.space/run/similarity_search \
  -H "Content-Type: application/json" \
  -d '{"data": ["beaches near Hanoi", 5]}'
```

### Python Usage

```python
from tourism_chatbot.clients import RemoteEmbeddingClient

# Initialize
client = RemoteEmbeddingClient(
    space_url="https://YOUR_USERNAME-tourism-embedding-api.hf.space"
)

# Embed query
embedding = client.embed_query("beautiful waterfall")
print(f"Embedding dimension: {len(embedding)}")

# Embed documents
docs = ["Hanoi", "Ho Chi Minh City", "Da Nang"]
embeddings = client.embed_documents(docs)
print(f"Got {len(embeddings)} embeddings")
```

## Integration with Main Backend

See `HF_SPACES_DEPLOYMENT.md` in the main repository for complete integration instructions.

### Quick Integration

1. **Update `.env`:**
   ```bash
   USE_REMOTE_EMBEDDINGS=True
   HF_SPACE_EMBEDDING_URL=https://YOUR_USERNAME-tourism-embedding-api.hf.space
   ```

2. **Update `app.py`:**
   ```python
   from config import Config
   
   if Config.USE_REMOTE_EMBEDDINGS:
       from tourism_chatbot.rag.rag_engine_remote import initialize_rag_system
   else:
       from tourism_chatbot.rag.rag_engine import initialize_rag_system
   ```

3. **Initialize RAG:**
   ```python
   vector_store, llm, embeddings = initialize_rag_system(
       use_remote_embeddings=Config.USE_REMOTE_EMBEDDINGS
   )
   ```

## Monitoring & Debugging

### Check Space Status

- **Dashboard:** https://huggingface.co/spaces/YOUR_USERNAME/tourism-embedding-api
- **Logs:** Click "Logs" tab to see startup/runtime logs
- **Status:** Shows if space is Running, Building, Sleeping, or Stopped

### Common Issues

| Issue | Solution |
|-------|----------|
| Space sleeping after 48h inactivity | Access it once to wake up |
| API timeout | Increase timeout in RemoteEmbeddingClient (timeout=60) |
| Connection refused | Check space URL and verify it's Running |
| Out of memory | Should not happen on free tier (16GB available) |

### Test API Connection

```python
import requests

url = "https://YOUR_USERNAME-tourism-embedding-api.hf.space"

# Quick test
try:
    response = requests.get(url, timeout=5)
    print(f"✓ Space is accessible (status: {response.status_code})")
except Exception as e:
    print(f"✗ Cannot reach space: {e}")
```

## Performance Notes

- **First embedding:** ~2-3 seconds (model loading)
- **Subsequent embeddings:** ~0.5-1 second each
- **Batch embedding:** ~0.05s per document

For best performance:
- Batch multiple documents together
- Use connection pooling in your backend
- Monitor HF Space logs for errors

## Model Details

- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimension:** 384
- **Purpose:** Semantic similarity for tourism location search
- **Accuracy:** 71.5% on STSB benchmark

## Specifications

- **HF Space Free Tier:**
  - RAM: 16 GB
  - vCPUs: 2
  - Disk: 50 GB
  - Auto-sleep: After 48h inactivity

- **This App:**
  - Python: 3.11
  - Dependencies: ~800MB
  - Runtime RAM: ~2-3GB (with model)
  - Startup time: ~30-60 seconds

## Production Checklist

- [ ] Space created on HuggingFace
- [ ] `app.py` and `requirements.txt` deployed
- [ ] Space is Running and accessible
- [ ] Test embedding API with curl/Python
- [ ] Update backend `.env` with Space URL
- [ ] Test full RAG pipeline
- [ ] Monitor first few requests in Space logs
- [ ] Set up monitoring/alerting if needed

## Troubleshooting Guide

### Space won't start

**Check:**
1. Syntax errors in `app.py`
2. Missing dependencies in `requirements.txt`
3. View logs on Space page

**Fix:**
```bash
# Test locally first
pip install -r requirements.txt
python app.py
```

### Embedding API returns 500 error

**Likely cause:** Model initialization failed

**Check logs:** Click "Logs" on Space page and look for loading errors

**Fix:**
1. Increase Space startup timeout (might be too slow)
2. Check if disk space available
3. Try recreating Space

### Backend can't connect to Space

**Check:**
1. Space URL is correct (no trailing slash)
2. Space is "Running" (not "Sleeping")
3. Network connectivity from backend to HF

**Test:**
```bash
curl https://YOUR_USERNAME-tourism-embedding-api.hf.space
```

## Support Resources

- **HF Spaces Docs:** https://huggingface.co/docs/hub/spaces
- **Gradio Docs:** https://www.gradio.app/docs/
- **API Reference:** Visit your space URL to see interactive API docs
- **Issues:** Check Space logs first, then HF Spaces community forums

## Next Steps

1. Deploy this Space on HuggingFace
2. Follow integration steps in main README
3. Test with `python test/manual_rag_test.py`
4. Monitor in production

---

**Last Updated:** December 2024
