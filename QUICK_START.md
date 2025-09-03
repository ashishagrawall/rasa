# 🚀 Quick Start Guide

## 1. Setup (5 minutes)

```bash
# 1. Configure database
cp .env.example .env
# Edit .env with your database credentials

# 2. Install and setup
python setup.py

# 3. Test database connection
python test_database.py
```

## 2. Run the Bot

**Option A: Terminal Chat**
```bash
python run_bot.py shell
```

**Option B: Web API**
```bash
python run_bot.py api
# Bot available at http://localhost:5005
```

**Option C: Docker**
```bash
docker-compose up
```

## 3. Example Conversations

```
You: "Hi"
Bot: "Hey! How can I help you with your database today?"

You: "Show me data from users table"
Bot: [Returns first 10 records from users table]

You: "How many records are in products?"
Bot: "Table 'products' has 150 records."

You: "Find records where name contains john"
Bot: [Shows matching records]
```

## 4. Database Configuration Examples

**PostgreSQL:**
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_DB=myapp_db
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypass
```

**MySQL:**
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_DB=myapp_db
MYSQL_USER=myuser
MYSQL_PASSWORD=mypass
```

**SQLite:**
```env
DB_TYPE=sqlite
SQLITE_PATH=./mydata.db
```

## 5. Troubleshooting

**Database connection failed?**
- Run `python test_database.py` to diagnose
- Check database server is running
- Verify credentials in `.env`

**Bot not responding?**
- Ensure both action server and main server are running
- Check port 5055 is available
- Look for error messages in terminal

**Need help?** Check the full README.md for detailed instructions.
