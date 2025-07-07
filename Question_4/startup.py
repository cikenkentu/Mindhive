#!/usr/bin/env python3
"""
Startup script to initialize database and vector store for deployment
"""
import os
import sys
import subprocess

def setup_database():
    """Initialize the outlets database"""
    try:
        print("Setting up outlets database...")
        # Change to the correct directory structure
        script_path = os.path.join(os.path.dirname(__file__), "ingestion", "ingest_outlets.py")
        subprocess.run([sys.executable, script_path], check=True, cwd=os.path.dirname(__file__))
        print("✅ Database setup complete")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Script path: {script_path if 'script_path' in locals() else 'Not set'}")
        return False
    return True

def setup_vector_store():
    """Initialize the vector store"""
    try:
        print("Setting up vector store...")
        # Change to the correct directory structure
        script_path = os.path.join(os.path.dirname(__file__), "ingestion", "ingest_products.py")
        subprocess.run([sys.executable, script_path], check=True, cwd=os.path.dirname(__file__))
        print("✅ Vector store setup complete")
    except Exception as e:
        print(f"❌ Vector store setup failed: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Script path: {script_path if 'script_path' in locals() else 'Not set'}")
        return False
    return True

def main():
    """Main startup function"""
    print("🚀 Starting ZUS Coffee API initialization...")
    
    # Check if already initialized
    if os.path.exists("outlets.db") and os.path.exists("vector_store"):
        print("✅ Already initialized - skipping setup")
        return True
    
    success = True
    
    # Setup database
    if not os.path.exists("outlets.db"):
        if not setup_database():
            success = False
    
    # Setup vector store
    if not os.path.exists("vector_store"):
        if not setup_vector_store():
            success = False
    
    if success:
        print("🎉 Initialization complete!")
    else:
        print("⚠️ Some initialization steps failed")
    
    return success

if __name__ == "__main__":
    main() 