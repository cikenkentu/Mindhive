#!/usr/bin/env python3
"""
Product ingestion script for ZUS Coffee drinkware.
Crawls product pages and creates FAISS vector store.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

def ingest_drinkware_products():
    """Crawl ZUS drinkware pages and create vector store"""
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    try:
        print("Loading ZUS drinkware pages...")
        
        # URLs to crawl (drinkware collection)
        urls = [
            "https://shop.zuscoffee.com/collections/drinkware",
            # Add specific product pages if needed
        ]
        
        # Load documents
        loader = WebBaseLoader(urls)
        docs = loader.load()
        
        if not docs:
            print("Warning: No documents loaded. Check URLs and connectivity.")
            return False
        
        print(f"Loaded {len(docs)} documents")
        
        # Split long pages into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        chunks = text_splitter.split_documents(docs)
        
        print(f"Split into {len(chunks)} chunks")
        
        # Create embeddings and vector store
        print("Creating embeddings and vector store...")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save to disk
        index_path = "faiss_drinkware_index"
        vector_store.save_local(index_path)
        
        print(f"✅ Vector store saved to {index_path}")
        print(f"✅ Ingestion complete! {len(chunks)} chunks indexed.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return False

def test_vector_store():
    """Test the created vector store"""
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        vector_store = FAISS.load_local(
            "faiss_drinkware_index", 
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Test search
        test_query = "tumbler"
        results = vector_store.similarity_search(test_query, k=2)
        
        print(f"\n🧪 Test search for '{test_query}':")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.page_content[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error testing vector store: {e}")
        return False

if __name__ == "__main__":
    print("ZUS Coffee Drinkware Ingestion")
    print("=" * 40)
    
    success = ingest_drinkware_products()
    
    if success:
        print("\nTesting vector store...")
        test_vector_store()
    else:
        print("❌ Ingestion failed")
        sys.exit(1) 