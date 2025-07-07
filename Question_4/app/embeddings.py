import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Optional

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
    
    def load_vector_store(self) -> Optional[FAISS]:
        """Load FAISS vector store from disk with fallback"""
        if self.fallback_mode:
            print("Running in fallback mode - vector store not available")
            return None
            
        try:
            if not self.embeddings:
                print("Embeddings not initialized")
                return None
                
            if os.path.exists(self.index_path):
                self.vector_store = FAISS.load_local(
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