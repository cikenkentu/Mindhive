import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Optional, List, Dict, Any

class LightweightVectorStore:
    """Lightweight vector store replacement for FAISS using scikit-learn"""
    
    def __init__(self, embeddings_function, persist_directory: str):
        self.embeddings_function = embeddings_function
        self.persist_directory = persist_directory
        self.vectors = []
        self.texts = []
        self.metadatas = []
    
    @classmethod
    def from_documents(cls, documents, embeddings_function):
        """Create vector store from documents"""
        store = cls(embeddings_function, "faiss_drinkware_index")
        
        # Extract texts and metadata
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings
        vectors = embeddings_function.embed_documents(texts)
        
        store.vectors = np.array(vectors)
        store.texts = texts
        store.metadatas = metadatas
        
        return store
    
    def save_local(self, path: str):
        """Save vector store to disk"""
        os.makedirs(path, exist_ok=True)
        
        # Save vectors and metadata
        with open(os.path.join(path, "vectors.pkl"), "wb") as f:
            pickle.dump({
                "vectors": self.vectors,
                "texts": self.texts,
                "metadatas": self.metadatas
            }, f)
    
    @classmethod
    def load_local(cls, path: str, embeddings_function, allow_dangerous_deserialization=True):
        """Load vector store from disk"""
        store = cls(embeddings_function, path)
        
        with open(os.path.join(path, "vectors.pkl"), "rb") as f:
            data = pickle.load(f)
            store.vectors = data["vectors"]
            store.texts = data["texts"]
            store.metadatas = data["metadatas"]
        
        return store
    
    def similarity_search(self, query: str, k: int = 3):
        """Perform similarity search"""
        if len(self.vectors) == 0:
            return []
        
        # Get query embedding
        query_vector = self.embeddings_function.embed_query(query)
        query_vector = np.array(query_vector).reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:k]
        
        # Return results
        results = []
        for idx in top_indices:
            # Create document-like object
            doc = type('Document', (), {
                'page_content': self.texts[idx],
                'metadata': self.metadatas[idx]
            })()
            results.append(doc)
        
        return results
    
    def as_retriever(self, search_kwargs: Dict[str, Any] = None):
        """Return a retriever interface"""
        if search_kwargs is None:
            search_kwargs = {"k": 3}
        
        class Retriever:
            def __init__(self, vector_store, search_kwargs):
                self.vector_store = vector_store
                self.search_kwargs = search_kwargs
            
            def get_relevant_documents(self, query: str):
                return self.vector_store.similarity_search(query, **self.search_kwargs)
        
        return Retriever(self, search_kwargs)

class EmbeddingsManager:
    def __init__(self, index_path: str = "faiss_drinkware_index"):
        self.index_path = index_path
        self.embeddings = None
        self.vector_store = None
        self.fallback_mode = False
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize HuggingFace embeddings (local/free)"""
        try:
            print("🔄 Initializing local HuggingFace embeddings...")
            
            # Initialize HuggingFace embeddings with all-MiniLM-L6-v2 model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},  # Use CPU for broader compatibility
                encode_kwargs={'normalize_embeddings': True}  # Normalize for better similarity search
            )
            print("✅ Local HuggingFace embeddings initialized successfully")
            print("✅ Using model: all-MiniLM-L6-v2 (free/local)")
            
        except Exception as e:
            print(f"❌ Error initializing HuggingFace embeddings: {e}")
            print("🔄 Enabling fallback mode")
            self.fallback_mode = True
    
    def load_vector_store(self) -> Optional[LightweightVectorStore]:
        """Load vector store from disk with fallback"""
        if self.fallback_mode:
            print("Running in fallback mode - vector store not available")
            return None
            
        try:
            if not self.embeddings:
                print("Embeddings not initialized")
                return None
                
            if os.path.exists(self.index_path):
                self.vector_store = LightweightVectorStore.load_local(
                    self.index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Vector store loaded from {self.index_path}")
                return self.vector_store
            else:
                print(f"Vector store not found at {self.index_path}")
                print("Please run ingestion/ingest_products.py first")
                print("🔄 Switching to fallback mode")
                self.fallback_mode = True
                return None
        except Exception as e:
            print(f"Error loading vector store: {e}")
            print("🔄 Switching to fallback mode")
            self.fallback_mode = True
            return None
    
    def get_retriever(self, k: int = 3):
        """Get retriever for similarity search with fallback"""
        if self.fallback_mode:
            return None
            
        if not self.vector_store:
            self.load_vector_store()
        
        if self.vector_store:
            return self.vector_store.as_retriever(search_kwargs={"k": k})
        return None
    
    def is_available(self) -> bool:
        """Check if vector store is available"""
        return not self.fallback_mode and self.embeddings is not None

# Global instance
embeddings_manager = EmbeddingsManager() 