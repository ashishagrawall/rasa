#!/usr/bin/env python3
"""
Database connection test script
Use this to verify your database configuration before running the bot
"""

import os
from dotenv import load_dotenv
from database.db_config import db_config
from database.query_builder import query_builder

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection...")
    print("=" * 50)
    
    try:
        # Test basic connection
        tables = db_config.get_table_names()
        print(f"✅ Database connection successful!")
        print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        
        if not tables:
            print("⚠️  No tables found in database. Make sure your database has tables.")
            return False
        
        # Test table information
        print("\n📋 Table Details:")
        for table in tables[:5]:  # Show first 5 tables
            columns = db_config.get_table_columns(table)
            print(f"  • {table}: {len(columns)} columns ({', '.join(columns[:3])}{'...' if len(columns) > 3 else ''})")
        
        # Test query execution
        print("\n🔍 Testing Query Execution...")
        first_table = tables[0]
        try:
            count = query_builder.count_records(first_table)
            print(f"✅ Query test successful! Table '{first_table}' has {count} records")
        except Exception as e:
            print(f"⚠️  Query test failed: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your .env file configuration")
        print("2. Verify database server is running")
        print("3. Confirm database credentials are correct")
        print("4. Test connection with a database client")
        return False

def main():
    print("🤖 Database-Integrated Rasa Chatbot - Database Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and configure your database settings")
        return
    
    # Test database connection
    if test_database_connection():
        print("\n🎉 Database test completed successfully!")
        print("Your bot is ready to interact with the database.")
    else:
        print("\n❌ Database test failed!")
        print("Please fix the database configuration before running the bot.")

if __name__ == "__main__":
    main()
