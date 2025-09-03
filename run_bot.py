#!/usr/bin/env python3
"""
Bot runner script for easy deployment
This script provides different ways to run the chatbot
"""

import subprocess
import sys
import threading
import time
import os

def run_action_server():
    """Run the Rasa action server"""
    print("🚀 Starting Rasa Action Server...")
    try:
        subprocess.run(["rasa", "run", "actions"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Action server stopped")
    except Exception as e:
        print(f"❌ Action server error: {e}")

def run_rasa_shell():
    """Run Rasa in shell mode"""
    print("🤖 Starting Rasa Shell...")
    time.sleep(3)  # Wait for action server to start
    try:
        subprocess.run(["rasa", "shell"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Rasa shell stopped")
    except Exception as e:
        print(f"❌ Rasa shell error: {e}")

def run_rasa_api():
    """Run Rasa API server"""
    print("🌐 Starting Rasa API Server...")
    time.sleep(3)  # Wait for action server to start
    try:
        subprocess.run(["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Rasa API server stopped")
    except Exception as e:
        print(f"❌ Rasa API server error: {e}")

def main():
    if len(sys.argv) < 2:
        print("🤖 Database-Integrated Rasa Chatbot Runner")
        print("=" * 50)
        print("Usage:")
        print("  python run_bot.py shell    # Run in terminal shell mode")
        print("  python run_bot.py api      # Run as API server")
        print("  python run_bot.py actions  # Run only action server")
        print("\nFor shell and api modes, both action server and main server will start automatically.")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "actions":
        run_action_server()
    elif mode == "shell":
        # Start action server in background thread
        action_thread = threading.Thread(target=run_action_server, daemon=True)
        action_thread.start()
        
        # Start shell in main thread
        run_rasa_shell()
    elif mode == "api":
        # Start action server in background thread
        action_thread = threading.Thread(target=run_action_server, daemon=True)
        action_thread.start()
        
        # Start API server in main thread
        run_rasa_api()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: shell, api, actions")
        sys.exit(1)

if __name__ == "__main__":
    main()
