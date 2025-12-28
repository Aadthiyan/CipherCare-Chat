# Embedder Refactoring Complete

## Changes Made

### 1. **Migrated from raw `requests` to `huggingface_hub.InferenceClient`**
   - **File**: `embeddings/embedder.py`
   - **Before**: Using raw HTTP requests with deprecated `api-inference.huggingface.co` endpoint
   - **After**: Using official `InferenceClient` with auto-routing to `router.huggingface.co`
   - **Benefit**: Automatically handles HF API updates, better error handling, official support

### 2. **Configuration-Driven Architecture**
   - Model name: `HUGGINGFACE_MODEL_NAME` env var (default: `sentence-transformers/all-mpnet-base-v2`)
   - Embedding dimension: `EMBEDDING_DIMENSION` env var (default: `768`)
   - API key: `HUGGINGFACE_API_KEY` env var (required)
   - Can override both via constructor parameters

### 3. **Clean Class Hierarchy**
   ```
   EmbeddingService (base class)
   ├── get_embedding()
   ├── get_embeddings_batch()
   └── ClinicalEmbedder (backwards-compatible wrapper)
   ```
   - Methods moved from `ClinicalEmbedder` to base `EmbeddingService`
   - `ClinicalEmbedder` inherits all functionality for backward compatibility
   - Easy to add local model support in the future

### 4. **Improved Error Handling**
   - Detects 410 errors (deprecated endpoint) and logs helpful message
   - Handles 503 (model loading) with automatic retry after 20s
   - Returns zero vectors on failure to prevent crashes
   - Comprehensive logging for debugging

### 5. **Proper Array Handling**
   - Fixed numpy array conversion issues
   - Handles both list and numpy array responses
   - Mean pooling for token embeddings
   - L2 normalization for cosine similarity

## Test Results

All tests passed:
```
[PASS] Import and initialization
[PASS] EmbeddingService initialization
[PASS] ClinicalEmbedder legacy interface
[PASS] Single embedding generation (768-dim vectors)
[PASS] Batch embedding generation
[PASS] Empty text handling
[PASS] Configuration via environment variables
```

### Sample Output
```
[PASS] Generated embedding successfully
  - Embedding dimension: 768
  - First 5 values: [0.000127, -0.00277, -0.0118, 0.0199, 0.0247]
  - L2 Norm: 1.0000
```

## Files Modified

1. **embeddings/embedder.py**
   - Refactored with `InferenceClient`
   - Configuration-driven design
   - Clean class hierarchy
   - ~160 lines (cleaner code)

2. **requirements.txt**
   - Added: `huggingface_hub>=0.16.0`

3. **requirements-render.txt**
   - Added: `huggingface_hub>=0.16.0`

## Migration Notes

### For Existing Code
No changes needed! The refactored code maintains full backward compatibility:
```python
# Old code still works
from embeddings.embedder import ClinicalEmbedder
embedder = ClinicalEmbedder()
embedding = embedder.get_embedding("text")
```

### To Use New EmbeddingService
```python
from embeddings.embedder import EmbeddingService

# Use new base class directly
embedder = EmbeddingService()
# Or with custom config
embedder = EmbeddingService(
    model_name="sentence-transformers/all-mpnet-base-v2",
    embedding_dim=768
)
```

## Environment Variables

```bash
# Required
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx

# Optional (with defaults)
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

## Future Enhancements

The new architecture makes it easy to add local model support:

```python
class LocalEmbeddingService(EmbeddingService):
    """Local model using transformers library"""
    
    def __init__(self, model_name=None, embedding_dim=None):
        # Load model locally instead of using API
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Don't call super().__init__() to skip API client setup
    
    def get_embedding(self, text):
        # Use local model instead of API
        # ... implementation
```

## Comparison: Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **HTTP Library** | `requests.post()` | `InferenceClient` |
| **Endpoint** | Hardcoded deprecated URL | Auto-routed |
| **Config** | Hardcoded defaults | Environment-driven |
| **Error Handling** | Manual status code checks | Built-in, HF-aware |
| **Array Handling** | Basic | Robust (list/array) |
| **Maintainability** | ~165 lines | ~160 lines (cleaner) |
| **Extensibility** | Difficult | Easy inheritance model |

## Testing

To test locally:
```bash
python test_embedder_simple.py
```

To test with actual backend:
```bash
python backend/main.py
# Then in another terminal
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"P123","query":"What conditions?","retrieve_k":5}'
```

Expected: No more 410 errors, embeddings generated successfully!
