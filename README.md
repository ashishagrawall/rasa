# Database-Integrated Rasa Chatbot

A streamlined Rasa chatbot that can interact with your database tables, views, and relationships. This bot allows users to query, search, and retrieve data through natural language conversations.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd personal-website

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` file with your database credentials:

**For PostgreSQL:**
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

**For MySQL:**
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
```

**For SQLite:**
```env
DB_TYPE=sqlite
SQLITE_PATH=./your_database.db
```

### 3. Training the Bot

```bash
# Train the Rasa model
rasa train

# This will create a models/ directory with your trained model
```

### 4. Running the Bot

**Terminal 1 - Start Action Server:**
```bash
rasa run actions
```

**Terminal 2 - Start Rasa Server:**
```bash
rasa shell
```

Or for web interface:
```bash
rasa run --enable-api --cors "*"
```

## 📊 Database Integration

### Supported Databases
- **PostgreSQL** - Production-ready, supports complex queries
- **MySQL** - Popular choice, good performance
- **SQLite** - Perfect for development and small applications

### How It Works

1. **Automatic Table Discovery**: The bot automatically discovers all tables in your database
2. **Dynamic Column Mapping**: Columns are mapped dynamically for each table
3. **Safe Query Execution**: All queries use parameterized statements to prevent SQL injection
4. **Error Handling**: Comprehensive error handling with user-friendly messages

### Database Structure Mapping

The bot works with any database structure. Here's how to map your data:

#### Tables
- The bot automatically detects all tables in your database
- No manual configuration needed for basic table access

#### Views
- Database views are treated like tables
- The bot can query views just like regular tables

#### Relationships
- Foreign key relationships are automatically detected
- You can query related data by specifying table and column names

## 🗣️ User Interaction Examples

### Basic Queries
```
User: "Show me data from users table"
Bot: Returns first 10 records from users table

User: "How many records are in the products table?"
Bot: Returns count of records

User: "Get record with id 123 from orders table"
Bot: Returns specific record
```

### Search Operations
```
User: "Find records where name contains john"
Bot: Searches across specified column

User: "Search for email containing gmail in users table"
Bot: Performs LIKE search on email column
```

### Table Information
```
User: "What tables are available?"
Bot: Lists all tables with their columns

User: "Show me table structure"
Bot: Displays table names and column information
```

## 🛠️ Customization

### Adding New Intents

1. **Edit `data/nlu.yml`** - Add new intent examples:
```yaml
- intent: your_new_intent
  examples: |
    - your example phrase
    - another example
```

2. **Edit `domain.yml`** - Add the new intent:
```yaml
intents:
  - your_new_intent
```

3. **Create Custom Action** in `actions/actions.py`:
```python
class ActionYourNewAction(Action):
    def name(self) -> Text:
        return "action_your_new_action"
    
    def run(self, dispatcher, tracker, domain):
        # Your custom logic here
        return []
```

### Database Query Customization

Edit `database/query_builder.py` to add custom query methods:

```python
def your_custom_query(self, table_name, custom_params):
    """Your custom database operation"""
    query = "SELECT * FROM {} WHERE custom_condition = :param"
    return self.execute_query(query.format(table_name), {'param': custom_params})
```

### Adding New Database Types

1. **Edit `database/db_config.py`**
2. **Add new connection method**:
```python
def _get_your_db_url(self):
    # Your database connection logic
    return "your_db_connection_string"
```

## 📁 Project Structure

```
personal-website/
├── actions/                 # Custom Rasa actions
│   ├── __init__.py
│   └── actions.py          # Database interaction actions
├── data/                   # Training data
│   ├── nlu.yml            # Natural language understanding
│   ├── rules.yml          # Conversation rules
│   └── stories.yml        # Training stories
├── database/              # Database integration
│   ├── __init__.py
│   ├── db_config.py       # Database configuration
│   └── query_builder.py   # Query execution
├── models/                # Trained models (created after training)
├── .env.example          # Environment template
├── config.yml            # Rasa configuration
├── domain.yml            # Bot domain definition
├── endpoints.yml         # Action server endpoint
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration Files

### `config.yml`
- Defines the NLP pipeline and policies
- Optimized for database interactions
- Uses DIET classifier for intent recognition

### `domain.yml`
- Defines intents, entities, slots, and responses
- Contains all database-related intents
- Configures conversation flow

### `endpoints.yml`
- Configures action server endpoint
- Points to localhost:5055 by default

## 🚨 Security Considerations

1. **Environment Variables**: Never commit `.env` file to version control
2. **SQL Injection**: All queries use parameterized statements
3. **Database Permissions**: Use read-only database users when possible
4. **Rate Limiting**: Consider implementing rate limiting for production

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed:**
- Check your `.env` file configuration
- Verify database server is running
- Test connection with database client

**No Tables Found:**
- Ensure database user has proper permissions
- Check if database name is correct
- Verify tables exist in the specified database

**Action Server Not Responding:**
- Make sure action server is running (`rasa run actions`)
- Check if port 5055 is available
- Verify endpoints.yml configuration

### Logs and Debugging

Enable debug logging by adding to your environment:
```env
RASA_LOG_LEVEL=DEBUG
```

## 📈 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN rasa train

EXPOSE 5005 5055

CMD ["rasa", "run", "--enable-api", "--cors", "*"]
```

### Environment Setup
- Use production database credentials
- Set up proper logging
- Configure CORS for web integration
- Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Test thoroughly
5. Submit pull request

## 📝 License

This project is open source and available under the MIT License.

---

**Ready to use!** Your database-integrated Rasa chatbot is now configured and ready for training and deployment.
