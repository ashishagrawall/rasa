from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import json
import logging
from database.db_config import db_config
from database.query_builder import query_builder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Database Chatbot API",
    description="REST API for interacting with the database chatbot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    sender_id: Optional[str] = "user"

class ChatResponse(BaseModel):
    response: str
    sender: str = "bot"

class DatabaseQuery(BaseModel):
    table_name: str
    limit: Optional[int] = 10

class SearchQuery(BaseModel):
    table_name: str
    column_name: str
    search_value: str
    operator: Optional[str] = "LIKE"

class RecordQuery(BaseModel):
    table_name: str
    record_id: str
    id_column: Optional[str] = "id"

# Rasa webhook URL
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

@app.get("/")
async def root():
    return {"message": "Database Chatbot API is running", "docs": "/docs"}

@app.post("/chat", response_model=List[ChatResponse])
async def chat_with_bot(message: ChatMessage):
    """Send a message to the Rasa chatbot"""
    try:
        payload = {
            "sender": message.sender_id,
            "message": message.message
        }
        
        response = requests.post(RASA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        rasa_responses = response.json()
        
        if not rasa_responses:
            return [ChatResponse(response="I didn't understand that. Can you try rephrasing?")]
        
        return [ChatResponse(response=msg.get("text", "")) for msg in rasa_responses if msg.get("text")]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with Rasa: {e}")
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/database/tables")
async def get_tables():
    """Get all available tables in the database"""
    try:
        tables = db_config.get_table_names()
        table_info = []
        
        for table in tables:
            columns = db_config.get_table_columns(table)
            count = query_builder.count_records(table)
            table_info.append({
                "name": table,
                "columns": columns,
                "record_count": count
            })
        
        return {"tables": table_info}
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/tables/{table_name}")
async def get_table_info(table_name: str):
    """Get detailed information about a specific table"""
    try:
        tables = db_config.get_table_names()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        columns = db_config.get_table_columns(table_name)
        count = query_builder.count_records(table_name)
        
        return {
            "name": table_name,
            "columns": columns,
            "record_count": count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/query")
async def query_table(query: DatabaseQuery):
    """Query records from a table"""
    try:
        tables = db_config.get_table_names()
        if query.table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{query.table_name}' not found")
        
        results = query_builder.get_all_records(query.table_name, query.limit)
        formatted_results = query_builder.format_results(results, query.table_name)
        
        return {
            "table": query.table_name,
            "records": formatted_results,
            "count": len(results) if results else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying table: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/search")
async def search_records(search: SearchQuery):
    """Search for records in a table"""
    try:
        tables = db_config.get_table_names()
        if search.table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{search.table_name}' not found")
        
        columns = db_config.get_table_columns(search.table_name)
        if search.column_name not in columns:
            raise HTTPException(status_code=404, detail=f"Column '{search.column_name}' not found")
        
        results = query_builder.search_records(
            search.table_name, 
            search.column_name, 
            search.search_value, 
            search.operator
        )
        formatted_results = query_builder.format_results(results, search.table_name)
        
        return {
            "table": search.table_name,
            "column": search.column_name,
            "search_value": search.search_value,
            "records": formatted_results,
            "count": len(results) if results else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/record")
async def get_record(record_query: RecordQuery):
    """Get a specific record by ID"""
    try:
        tables = db_config.get_table_names()
        if record_query.table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{record_query.table_name}' not found")
        
        results = query_builder.get_record_by_id(
            record_query.table_name, 
            record_query.record_id, 
            record_query.id_column
        )
        formatted_results = query_builder.format_results(results, record_query.table_name)
        
        if not formatted_results or formatted_results == "No records found.":
            raise HTTPException(status_code=404, detail=f"Record with ID '{record_query.record_id}' not found")
        
        return {
            "table": record_query.table_name,
            "record_id": record_query.record_id,
            "record": formatted_results[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/count/{table_name}")
async def count_records(table_name: str):
    """Count records in a table"""
    try:
        tables = db_config.get_table_names()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        count = query_builder.count_records(table_name)
        return {
            "table": table_name,
            "count": count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        tables = db_config.get_table_names()
        
        # Test Rasa connection
        rasa_health = True
        try:
            response = requests.get("http://localhost:5005/", timeout=5)
            rasa_health = response.status_code == 200
        except:
            rasa_health = False
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables_count": len(tables),
            "rasa": "connected" if rasa_health else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
