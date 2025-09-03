#!/usr/bin/env python3
"""
Setup script for Database-Integrated Rasa Chatbot
This script helps you set up the environment and train the bot
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_env_file():
    """Check if .env file exists and is configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n⚠️  .env file not found!")
        print("Please copy .env.example to .env and configure your database settings:")
        print("cp .env.example .env")
        return False
    
    print("✅ .env file found")
    return True

def install_dependencies():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def train_model():
    """Train the Rasa model"""
    return run_command("rasa train", "Training Rasa model")

def main():
    print("🤖 Database-Integrated Rasa Chatbot Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("config.yml").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please check your Python environment.")
        sys.exit(1)
    
    # Train model
    if not train_model():
        print("❌ Failed to train model. Please check the configuration files.")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Configure your database in the .env file")
    print("2. Start the action server: rasa run actions")
    print("3. In another terminal, start the bot: rasa shell")
    print("\nFor web interface: rasa run --enable-api --cors '*'")

if __name__ == "__main__":
    main()
