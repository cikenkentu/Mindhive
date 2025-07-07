import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from typing import Optional

class EmbeddingsManager:
    def __init__(self, index_path: str = "faiss_drinkware_index"):
        self.index_path = index_path
        self.embeddings = None
        self.vector_store = None
        self.fallback_mode = False
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize OpenAI embeddings with fallback mode"""
        try:
            # Check for API key
            if not os.getenv("OPENAI_API_KEY"):
                print("Warning: OPENAI_API_KEY environment variable not set")
                self.fallback_mode = True
                return
            
            # Try to initialize embeddings - if it fails, use fallback mode
            try:
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-ada-002"
                )
                print("✅ OpenAI embeddings initialized successfully")
            except Exception as embed_error:
                print(f"Warning: OpenAI embeddings failed: {embed_error}")
                print("🔄 Falling back to mock mode for demo purposes")
                self.fallback_mode = True
                
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI embeddings: {e}")
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