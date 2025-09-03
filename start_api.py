#!/usr/bin/env python3
"""
API Server starter script
Runs the FastAPI server with the database chatbot API
"""

import subprocess
import sys
import threading
import time
import os

def run_rasa_server():
    """Run Rasa server in background"""
    print("🤖 Starting Rasa server...")
    try:
        subprocess.run(["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"], 
                      check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Rasa server error: {e}")

def run_action_server():
    """Run Rasa action server in background"""
    print("⚡ Starting Rasa action server...")
    try:
        subprocess.run(["rasa", "run", "actions", "--port", "5055"], 
                      check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Action server error: {e}")

def run_api_server():
    """Run FastAPI server"""
    print("🚀 Starting API server...")
    try:
        subprocess.run(["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], 
                      check=True)
    except KeyboardInterrupt:
        print("\n⏹️  API server stopped")
    except Exception as e:
        print(f"❌ API server error: {e}")

def main():
    print("🌐 Database Chatbot API Stack")
    print("=" * 40)
    print("Starting all services...")
    print("- Rasa Server: http://localhost:5005")
    print("- Action Server: http://localhost:5055") 
    print("- API Server: http://localhost:8000")
    print("- Web Interface: http://localhost:8000/static/index.html")
    print("=" * 40)
    
    # Start Rasa server in background
    rasa_thread = threading.Thread(target=run_rasa_server, daemon=True)
    rasa_thread.start()
    
    # Start action server in background
    action_thread = threading.Thread(target=run_action_server, daemon=True)
    action_thread.start()
    
    # Wait a bit for services to start
    print("⏳ Waiting for services to initialize...")
    time.sleep(5)
    
    # Start API server in main thread
    run_api_server()

if __name__ == "__main__":
    main()
