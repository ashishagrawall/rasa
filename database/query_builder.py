from sqlalchemy import text
from database.db_config import db_config
import logging

logger = logging.getLogger(__name__)

class QueryBuilder:
    def __init__(self):
        self.db = db_config
    
    def execute_query(self, query, params=None):
        """Execute a raw SQL query safely"""
        session = self.db.get_session()
        try:
            result = session.execute(text(query), params or {})
            if query.strip().upper().startswith('SELECT'):
                return result.fetchall()
            else:
                session.commit()
                return result.rowcount
        except Exception as e:
            session.rollback()
            logger.error(f"Query execution error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_all_records(self, table_name, limit=100):
        """Get all records from a table with optional limit"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT :limit"
            return self.execute_query(query, {'limit': limit})
        except Exception as e:
            logger.error(f"Error getting records from {table_name}: {str(e)}")
            return []
    
    def search_records(self, table_name, column_name, search_value, operator='='):
        """Search records in a table based on column value"""
        try:
            if operator.lower() == 'like':
                query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE :search_value"
                params = {'search_value': f'%{search_value}%'}
            else:
                query = f"SELECT * FROM {table_name} WHERE {column_name} {operator} :search_value"
                params = {'search_value': search_value}
            
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error searching in {table_name}: {str(e)}")
            return []
    
    def count_records(self, table_name, condition=None):
        """Count records in a table with optional condition"""
        try:
            if condition:
                query = f"SELECT COUNT(*) FROM {table_name} WHERE {condition}"
            else:
                query = f"SELECT COUNT(*) FROM {table_name}"
            
            result = self.execute_query(query)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"Error counting records in {table_name}: {str(e)}")
            return 0
    
    def get_record_by_id(self, table_name, record_id, id_column='id'):
        """Get a specific record by ID"""
        try:
            query = f"SELECT * FROM {table_name} WHERE {id_column} = :record_id"
            return self.execute_query(query, {'record_id': record_id})
        except Exception as e:
            logger.error(f"Error getting record {record_id} from {table_name}: {str(e)}")
            return []
    
    def format_results(self, results, table_name):
        """Format query results for display"""
        if not results:
            return "No records found."
        
        # Get column names
        columns = self.db.get_table_columns(table_name)
        
        formatted_results = []
        for row in results[:10]:  # Limit to first 10 results for display
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(columns):
                    row_dict[columns[i]] = value
            formatted_results.append(row_dict)
        
        return formatted_results

# Global query builder instance
query_builder = QueryBuilder()
