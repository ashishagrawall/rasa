# 🌐 API Documentation

## Overview

The Database Chatbot provides both conversational AI and direct REST API endpoints for interacting with your database. You can use either approach depending on your needs.

## 🚀 Quick Start

### Start All Services
```bash
python start_api.py
```

This starts:
- **Rasa Server**: `http://localhost:5005` (Chatbot AI)
- **Action Server**: `http://localhost:5055` (Database actions)
- **API Server**: `http://localhost:8000` (REST endpoints)
- **Web Interface**: `http://localhost:8000/docs` (Interactive docs)

### Web Interface
Open `web/index.html` in your browser for a beautiful chat interface.

## 📡 API Endpoints

### Base URL: `http://localhost:8000`

### 1. Chat with Bot
**POST** `/chat`

Send natural language messages to the chatbot.

```json
{
  "message": "Show me data from users table",
  "sender_id": "user123"
}
```

**Response:**
```json
[
  {
    "response": "Here are the records from 'users' table:\n\nRecord 1:\n  id: 1\n  name: John Doe\n  email: john@example.com",
    "sender": "bot"
  }
]
```

### 2. Get All Tables
**GET** `/database/tables`

Returns all available tables with their structure and record counts.

**Response:**
```json
{
  "tables": [
    {
      "name": "users",
      "columns": ["id", "name", "email", "created_at"],
      "record_count": 150
    },
    {
      "name": "products",
      "columns": ["id", "name", "price", "category"],
      "record_count": 75
    }
  ]
}
```

### 3. Get Table Information
**GET** `/database/tables/{table_name}`

Get detailed information about a specific table.

**Response:**
```json
{
  "name": "users",
  "columns": ["id", "name", "email", "created_at"],
  "record_count": 150
}
```

### 4. Query Table Records
**POST** `/database/query`

Retrieve records from a table.

```json
{
  "table_name": "users",
  "limit": 10
}
```

**Response:**
```json
{
  "table": "users",
  "records": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01"
    }
  ],
  "count": 10
}
```

### 5. Search Records
**POST** `/database/search`

Search for specific records in a table.

```json
{
  "table_name": "users",
  "column_name": "name",
  "search_value": "john",
  "operator": "LIKE"
}
```

**Response:**
```json
{
  "table": "users",
  "column": "name",
  "search_value": "john",
  "records": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "count": 1
}
```

### 6. Get Specific Record
**POST** `/database/record`

Get a record by its ID.

```json
{
  "table_name": "users",
  "record_id": "123",
  "id_column": "id"
}
```

**Response:**
```json
{
  "table": "users",
  "record_id": "123",
  "record": {
    "id": 123,
    "name": "Jane Smith",
    "email": "jane@example.com"
  }
}
```

### 7. Count Records
**GET** `/database/count/{table_name}`

Count total records in a table.

**Response:**
```json
{
  "table": "users",
  "count": 150
}
```

### 8. Health Check
**GET** `/health`

Check the status of all services.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "tables_count": 5,
  "rasa": "connected"
}
```

## 🔧 Integration Examples

### JavaScript/Frontend
```javascript
// Chat with bot
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Show me all tables',
    sender_id: 'web_user'
  })
});

// Get tables directly
const tables = await fetch('http://localhost:8000/database/tables');
const data = await tables.json();
```

### Python
```python
import requests

# Chat with bot
response = requests.post('http://localhost:8000/chat', json={
    'message': 'How many users are there?',
    'sender_id': 'python_client'
})

# Direct database query
tables = requests.get('http://localhost:8000/database/tables')
print(tables.json())
```

### cURL
```bash
# Chat with bot
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me products table", "sender_id": "curl_user"}'

# Get table info
curl "http://localhost:8000/database/tables/users"
```

## 🎯 Use Cases

### 1. **Conversational Interface**
Use `/chat` endpoint for natural language queries:
- "Show me all users"
- "How many products do we have?"
- "Find customers in New York"

### 2. **Direct Database Access**
Use specific endpoints for programmatic access:
- Build dashboards with `/database/tables`
- Create search interfaces with `/database/search`
- Integrate with existing applications

### 3. **Hybrid Approach**
Combine both:
- Use chat for complex queries
- Use direct endpoints for structured data

## 🔒 Security Features

- **CORS enabled** for web integration
- **Parameterized queries** prevent SQL injection
- **Input validation** on all endpoints
- **Error handling** with appropriate HTTP status codes

## 📊 Response Formats

All endpoints return JSON with consistent error handling:

**Success Response:**
```json
{
  "data": "...",
  "status": "success"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🚨 Error Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (table/record doesn't exist)
- **500**: Internal Server Error
- **503**: Service Unavailable (Rasa not running)

## 🔧 Configuration

The API automatically detects your database configuration from the `.env` file. No additional setup required beyond the initial database configuration.

## 📱 Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with Swagger UI where you can test all endpoints directly in your browser.
