# 🔧 Complete Setup, Training & Testing Guide

## 📋 Table of Contents
1. [Initial Setup](#initial-setup)
2. [Database Configuration](#database-configuration)
3. [Training the Bot](#training-the-bot)
4. [Testing & Validation](#testing--validation)
5. [Running the System](#running-the-system)
6. [Integration Examples](#integration-examples)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Initial Setup

### Prerequisites
- Python 3.8+ installed
- Database server running (PostgreSQL/MySQL/SQLite)
- Git (for version control)

### Step 1: Clone & Install
```bash
# Navigate to your project directory
cd /path/to/your/project

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import rasa; print('Rasa installed successfully')"
```

### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your database credentials
nano .env  # or use your preferred editor
```

---

## 🗄️ Database Configuration

### PostgreSQL Example
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=my_company_db
POSTGRES_USER=db_user
POSTGRES_PASSWORD=secure_password123
```

### MySQL Example
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=ecommerce_db
MYSQL_USER=mysql_user
MYSQL_PASSWORD=mysql_pass456
```

### SQLite Example (for development)
```env
DB_TYPE=sqlite
SQLITE_PATH=./sample_database.db
```

### Database Structure Examples

**Sample Tables the Bot Can Work With:**

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150),
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    price DECIMAL(10,2),
    category VARCHAR(50),
    stock_quantity INTEGER,
    supplier_id INTEGER
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    total_amount DECIMAL(10,2),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎓 Training the Bot

### Step 1: Automated Setup & Training
```bash
# Run the complete setup script
python setup.py
```

**What this does:**
- Checks environment configuration
- Installs dependencies
- Trains the Rasa model
- Validates setup

### Step 2: Manual Training (if needed)
```bash
# Train the model manually
rasa train

# Train with specific data
rasa train --data data/ --config config.yml --domain domain.yml
```

### Step 3: Customize Training Data

**Add Your Own Intents** (`data/nlu.yml`):
```yaml
- intent: get_sales_report
  examples: |
    - show me today's sales
    - what are the sales figures
    - generate sales report
    - how much did we sell today

- intent: find_customer_orders
  examples: |
    - show orders for customer [john@email.com](search_value)
    - find all orders by [customer_id](column_name) [123](search_value)
    - get purchase history for [jane](search_value)
```

**Add Custom Entities** (`domain.yml`):
```yaml
entities:
  - table_name
  - column_name
  - search_value
  - date_range
  - customer_id
  - product_category
```

---

## 🧪 Testing & Validation

### Step 1: Test Database Connection
```bash
# Test your database setup
python test_database.py
```

**Expected Output:**
```
🔍 Testing Database Connection...
==================================================
✅ Database connection successful!
📊 Found 3 tables: users, products, orders

📋 Table Details:
  • users: 4 columns (id, name, email...)
  • products: 6 columns (id, name, price...)
  • orders: 6 columns (id, user_id, product_id...)

🔍 Testing Query Execution...
✅ Query test successful! Table 'users' has 150 records

🎉 Database test completed successfully!
```

### Step 2: Test Bot Responses
```bash
# Start interactive testing
rasa shell
```

**Test Conversations:**
```
Your input ->  hi
Hey! How can I help you with your database today?

Your input ->  show me users table
Here are the records from 'users' table:

Record 1:
  id: 1
  name: John Doe
  email: john@company.com
  department: Engineering

Record 2:
  id: 2
  name: Jane Smith
  email: jane@company.com
  department: Marketing

Your input ->  how many products are there?
Table 'products' has 75 records.

Your input ->  find users where department contains engineering
Found 12 record(s) in 'users' where 'department' contains 'engineering':

Record 1:
  id: 1
  name: John Doe
  email: john@company.com
  department: Engineering
```

### Step 3: API Testing
```bash
# Start API server
python start_api.py

# In another terminal, test API endpoints
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all tables", "sender_id": "test_user"}'
```

---

## 🏃‍♂️ Running the System

### Option 1: Full Stack (Recommended)
```bash
# Starts everything: Rasa + Actions + API + Web UI
python start_api.py
```

**Services Started:**
- Rasa Server: `http://localhost:5005`
- Action Server: `http://localhost:5055`
- API Server: `http://localhost:8000`
- Web Interface: Open `web/index.html`

### Option 2: Individual Components
```bash
# Terminal 1: Action Server
rasa run actions

# Terminal 2: Rasa Server
rasa run --enable-api --cors "*"

# Terminal 3: API Server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build
```

---

## 🔌 Integration Examples

### Frontend Integration (JavaScript)
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Database Chat</title>
</head>
<body>
    <div id="chat"></div>
    <input id="message" type="text" placeholder="Ask about your data...">
    <button onclick="sendMessage()">Send</button>

    <script>
        async function sendMessage() {
            const message = document.getElementById('message').value;
            
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: message,
                    sender_id: 'web_user'
                })
            });
            
            const data = await response.json();
            document.getElementById('chat').innerHTML += 
                `<p><strong>You:</strong> ${message}</p>
                 <p><strong>Bot:</strong> ${data[0].response}</p>`;
        }
    </script>
</body>
</html>
```

### Python Integration
```python
import requests

class DatabaseChatbot:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def chat(self, message, user_id="python_client"):
        """Send message to chatbot"""
        response = requests.post(f"{self.api_url}/chat", json={
            "message": message,
            "sender_id": user_id
        })
        return response.json()
    
    def get_tables(self):
        """Get all database tables"""
        response = requests.get(f"{self.api_url}/database/tables")
        return response.json()
    
    def query_table(self, table_name, limit=10):
        """Query specific table"""
        response = requests.post(f"{self.api_url}/database/query", json={
            "table_name": table_name,
            "limit": limit
        })
        return response.json()

# Usage example
bot = DatabaseChatbot()

# Chat with bot
result = bot.chat("How many users do we have?")
print(result[0]['response'])

# Direct database query
tables = bot.get_tables()
print(f"Available tables: {[t['name'] for t in tables['tables']]}")
```

### React Integration
```jsx
import React, { useState } from 'react';

function DatabaseChat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const sendMessage = async () => {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: input,
                sender_id: 'react_user'
            })
        });
        
        const data = await response.json();
        setMessages([...messages, 
            {sender: 'user', text: input},
            {sender: 'bot', text: data[0].response}
        ]);
        setInput('');
    };

    return (
        <div>
            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
            </div>
            <input 
                value={input} 
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
        </div>
    );
}
```

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Failed
```bash
# Test connection
python test_database.py

# Check if database server is running
# PostgreSQL
sudo systemctl status postgresql

# MySQL
sudo systemctl status mysql
```

**Fix:**
- Verify database credentials in `.env`
- Ensure database server is running
- Check firewall settings
- Test connection with database client

#### 2. Rasa Training Fails
```bash
# Check for syntax errors
rasa data validate

# Train with debug output
rasa train --debug
```

**Fix:**
- Check YAML syntax in `data/` files
- Ensure all intents are defined in `domain.yml`
- Verify training data format

#### 3. Action Server Not Responding
```bash
# Check if action server is running
curl http://localhost:5055/health

# Start with debug logging
rasa run actions --debug
```

**Fix:**
- Ensure port 5055 is available
- Check `endpoints.yml` configuration
- Verify action server dependencies

#### 4. API Server Issues
```bash
# Check API health
curl http://localhost:8000/health

# Start with debug logging
uvicorn api.main:app --log-level debug
```

**Fix:**
- Ensure port 8000 is available
- Check if all dependencies are installed
- Verify database connection

### Debug Commands
```bash
# Check Rasa version
rasa --version

# Validate training data
rasa data validate

# Test specific stories
rasa test

# Check action server
rasa run actions --debug

# Test API endpoints
curl -X GET "http://localhost:8000/health"
```

### Log Files
```bash
# View Rasa logs
tail -f ~/.rasa/logs/rasa.log

# View action server logs
# (logs appear in terminal where you started the action server)

# View API server logs
# (logs appear in terminal where you started uvicorn)
```

---

## 🎯 Production Deployment

### Environment Variables for Production
```env
# Production database
DB_TYPE=postgresql
POSTGRES_HOST=prod-db-server.com
POSTGRES_DB=production_db
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=super_secure_password

# Security
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=production

# Logging
RASA_LOG_LEVEL=INFO
```

### Docker Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  rasa:
    build: .
    environment:
      - ENVIRONMENT=production
      - RASA_LOG_LEVEL=INFO
    ports:
      - "5005:5005"
    restart: unless-stopped

  actions:
    build: .
    environment:
      - ENVIRONMENT=production
    ports:
      - "5055:5055"
    restart: unless-stopped

  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Health Monitoring
```bash
# Setup health checks
curl http://your-domain.com:8000/health

# Monitor logs
docker-compose logs -f
```

---

## 📚 Additional Resources

- **Rasa Documentation**: https://rasa.com/docs/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/

## 🤝 Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review log files for error messages
3. Test individual components separately
4. Verify database connectivity

Your database chatbot is now ready for production use! 🎉
