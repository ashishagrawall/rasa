import os
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        self.engine = None
        self.Session = None
        self.metadata = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection based on configuration"""
        try:
            if self.db_type == 'postgresql':
                connection_string = self._get_postgresql_url()
            elif self.db_type == 'mysql':
                connection_string = self._get_mysql_url()
            elif self.db_type == 'sqlite':
                connection_string = self._get_sqlite_url()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            
            self.engine = create_engine(connection_string, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            
            logger.info(f"Database connection established: {self.db_type}")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {str(e)}")
            raise
    
    def _get_postgresql_url(self):
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        db = os.getenv('POSTGRES_DB')
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        
        if not all([db, user, password]):
            raise ValueError("PostgreSQL credentials not properly configured")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def _get_mysql_url(self):
        host = os.getenv('MYSQL_HOST', 'localhost')
        port = os.getenv('MYSQL_PORT', '3306')
        db = os.getenv('MYSQL_DB')
        user = os.getenv('MYSQL_USER')
        password = os.getenv('MYSQL_PASSWORD')
        
        if not all([db, user, password]):
            raise ValueError("MySQL credentials not properly configured")
        
        return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    
    def _get_sqlite_url(self):
        db_path = os.getenv('SQLITE_PATH', './database.db')
        return f"sqlite:///{db_path}"
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def get_table_names(self):
        """Get all table names in the database"""
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error getting table names: {str(e)}")
            return []
    
    def get_table_columns(self, table_name):
        """Get column information for a specific table"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            return [col['name'] for col in columns]
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {str(e)}")
            return []
    
    def get_table_info(self, table_name):
        """Get detailed table information including columns and types"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            return {
                'name': table_name,
                'columns': [{'name': col['name'], 'type': str(col['type'])} for col in columns]
            }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {str(e)}")
            return None

# Global database instance
db_config = DatabaseConfig()
