from sqlalchemy import text, inspect
from database.db_config import db_config
from database.schema_analyzer import SchemaAnalyzer
from database.ai_query_generator import AIQueryGenerator
from typing import Dict, List, Optional, Any
import logging
import json
import re

logger = logging.getLogger(__name__)

class AdvancedQueryBuilder:
    """Advanced query builder with AI-powered natural language processing"""
    
    def __init__(self):
        self.db = db_config
        self.schema_analyzer = SchemaAnalyzer(db_config)
        self.ai_generator = AIQueryGenerator(self.schema_analyzer)
        self.query_cache = {}
        self.execution_stats = {}
    
    def process_natural_query(self, natural_query: str, user_context: Dict = None) -> Dict:
        """Process natural language query and return results"""
        try:
            # Generate SQL using AI
            query_result = self.ai_generator.generate_sql(natural_query, user_context)
            
            if not query_result['sql']:
                return {
                    'success': False,
                    'error': query_result.get('error', 'Could not generate SQL'),
                    'natural_query': natural_query
                }
            
            # Execute the generated SQL
            execution_result = self.execute_generated_sql(
                query_result['sql'], 
                query_result.get('tables', [])
            )
            
            # Format results for user
            formatted_result = self.format_query_results(
                execution_result,
                query_result,
                natural_query
            )
            
            # Cache successful queries
            if formatted_result['success']:
                self._cache_query(natural_query, query_result['sql'], formatted_result)
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error processing natural query: {e}")
            return {
                'success': False,
                'error': str(e),
                'natural_query': natural_query
            }
    
    def execute_generated_sql(self, sql_query: str, involved_tables: List[str]) -> Dict:
        """Execute AI-generated SQL with safety checks"""
        try:
            # Validate SQL safety
            if not self._is_safe_query(sql_query):
                return {
                    'success': False,
                    'error': 'Query contains potentially unsafe operations'
                }
            
            # Optimize query if needed
            optimized_sql = self._optimize_query(sql_query, involved_tables)
            
            # Execute query
            session = self.db.get_session()
            try:
                result = session.execute(text(optimized_sql))
                
                if optimized_sql.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    columns = list(result.keys()) if hasattr(result, 'keys') else []
                    
                    return {
                        'success': True,
                        'data': rows,
                        'columns': columns,
                        'row_count': len(rows),
                        'sql_executed': optimized_sql
                    }
                else:
                    session.commit()
                    return {
                        'success': True,
                        'affected_rows': result.rowcount,
                        'sql_executed': optimized_sql
                    }
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'sql_attempted': sql_query
            }
    
    def _is_safe_query(self, sql: str) -> bool:
        """Check if SQL query is safe to execute"""
        sql_upper = sql.upper().strip()
        
        # Block dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False
        
        return True
    
    def _optimize_query(self, sql: str, tables: List[str]) -> str:
        """Optimize SQL query for better performance"""
        optimized = sql
        
        # Add LIMIT if not present and query might return many rows
        if 'LIMIT' not in sql.upper() and 'COUNT(' not in sql.upper():
            # Check if tables are large (simple heuristic)
            large_tables = self._identify_large_tables(tables)
            if large_tables:
                optimized += ' LIMIT 100'
        
        # Add proper indexing hints if available
        optimized = self._add_index_hints(optimized, tables)
        
        return optimized
    
    def _identify_large_tables(self, tables: List[str]) -> List[str]:
        """Identify potentially large tables"""
        large_tables = []
        
        for table in tables:
            try:
                count_query = f"SELECT COUNT(*) FROM {table}"
                session = self.db.get_session()
                result = session.execute(text(count_query))
                count = result.scalar()
                session.close()
                
                if count > 10000:  # Consider large if > 10k rows
                    large_tables.append(table)
                    
            except Exception as e:
                logger.warning(f"Could not check size of table {table}: {e}")
        
        return large_tables
    
    def _add_index_hints(self, sql: str, tables: List[str]) -> str:
        """Add database-specific index hints if beneficial"""
        # This is database-specific and would need implementation
        # for each database type (PostgreSQL, MySQL, etc.)
        return sql
    
    def format_query_results(self, execution_result: Dict, query_info: Dict, 
                           natural_query: str) -> Dict:
        """Format query results for user presentation"""
        if not execution_result['success']:
            return {
                'success': False,
                'error': execution_result['error'],
                'natural_query': natural_query,
                'sql_attempted': execution_result.get('sql_attempted')
            }
        
        formatted = {
            'success': True,
            'natural_query': natural_query,
            'sql_executed': execution_result['sql_executed'],
            'confidence': query_info.get('confidence', 0.5),
            'tables_involved': query_info.get('tables', []),
            'analysis': query_info.get('analysis', {})
        }
        
        if 'data' in execution_result:
            # Format SELECT results
            formatted.update({
                'result_type': 'data',
                'row_count': execution_result['row_count'],
                'columns': execution_result['columns'],
                'data': self._format_data_rows(
                    execution_result['data'], 
                    execution_result['columns']
                ),
                'summary': self._generate_result_summary(
                    execution_result, 
                    natural_query
                )
            })
        else:
            # Format modification results
            formatted.update({
                'result_type': 'modification',
                'affected_rows': execution_result['affected_rows']
            })
        
        return formatted
    
    def _format_data_rows(self, rows: List, columns: List[str]) -> List[Dict]:
        """Convert raw rows to list of dictionaries"""
        formatted_rows = []
        
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(columns):
                    # Handle different data types
                    if value is None:
                        row_dict[columns[i]] = None
                    elif isinstance(value, (int, float)):
                        row_dict[columns[i]] = value
                    else:
                        row_dict[columns[i]] = str(value)
                        
            formatted_rows.append(row_dict)
        
        return formatted_rows
    
    def _generate_result_summary(self, execution_result: Dict, natural_query: str) -> str:
        """Generate human-readable summary of results"""
        row_count = execution_result['row_count']
        
        if row_count == 0:
            return "No results found for your query."
        elif row_count == 1:
            return "Found 1 result matching your query."
        else:
            return f"Found {row_count} results matching your query."
    
    def _cache_query(self, natural_query: str, sql: str, result: Dict):
        """Cache successful queries for faster future execution"""
        cache_key = natural_query.lower().strip()
        self.query_cache[cache_key] = {
            'sql': sql,
            'timestamp': self._get_timestamp(),
            'success_count': self.query_cache.get(cache_key, {}).get('success_count', 0) + 1
        }
        
        # Limit cache size
        if len(self.query_cache) > 100:
            oldest_key = min(self.query_cache.keys(), 
                           key=lambda k: self.query_cache[k]['timestamp'])
            del self.query_cache[oldest_key]
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def get_schema_suggestions(self, partial_query: str) -> Dict:
        """Get schema-based suggestions for partial queries"""
        suggestions = {
            'tables': [],
            'columns': [],
            'relationships': [],
            'sample_queries': []
        }
        
        partial_lower = partial_query.lower()
        
        # Suggest tables
        tables = self.schema_analyzer.inspector.get_table_names()
        for table in tables:
            if partial_lower in table.lower() or table.lower() in partial_lower:
                suggestions['tables'].append({
                    'name': table,
                    'aliases': self.schema_analyzer.table_aliases.get(table, []),
                    'row_count': self._get_table_row_count(table)
                })
        
        # Suggest columns from relevant tables
        for table_info in suggestions['tables']:
            table = table_info['name']
            columns = self.schema_analyzer.inspector.get_columns(table)
            for col in columns[:5]:  # Limit to first 5 columns
                suggestions['columns'].append({
                    'name': col['name'],
                    'table': table,
                    'type': str(col['type'])
                })
        
        # Suggest relationships
        if suggestions['tables']:
            main_table = suggestions['tables'][0]['name']
            related = self.schema_analyzer.get_related_tables(main_table)
            suggestions['relationships'] = related
        
        # Generate sample queries
        suggestions['sample_queries'] = self._generate_sample_queries(suggestions['tables'])
        
        return suggestions
    
    def _get_table_row_count(self, table: str) -> int:
        """Get approximate row count for a table"""
        try:
            session = self.db.get_session()
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            session.close()
            return count
        except:
            return 0
    
    def _generate_sample_queries(self, tables: List[Dict]) -> List[str]:
        """Generate sample natural language queries for given tables"""
        samples = []
        
        for table_info in tables[:3]:  # Limit to first 3 tables
            table = table_info['name']
            
            # Basic queries
            samples.extend([
                f"Show me all {table}",
                f"How many {table} are there?",
                f"Get the latest {table}",
            ])
            
            # Relationship queries if related tables exist
            related = self.schema_analyzer.get_related_tables(table)
            if related['direct']:
                related_table = related['direct'][0]
                samples.append(f"Show {table} with their {related_table}")
        
        return samples[:10]  # Limit to 10 samples
    
    def explain_query(self, natural_query: str) -> Dict:
        """Explain how a natural language query would be processed"""
        try:
            # Analyze without executing
            query_result = self.ai_generator.generate_sql(natural_query)
            
            explanation = {
                'natural_query': natural_query,
                'generated_sql': query_result.get('sql'),
                'confidence': query_result.get('confidence', 0),
                'analysis': query_result.get('analysis', {}),
                'tables_involved': query_result.get('tables', []),
                'explanation_steps': []
            }
            
            # Add step-by-step explanation
            analysis = query_result.get('analysis', {})
            
            explanation['explanation_steps'] = [
                f"1. Detected intent: {analysis.get('intent', 'unknown')}",
                f"2. Identified tables: {', '.join(query_result.get('tables', []))}",
                f"3. Generated SQL: {query_result.get('sql', 'None')}",
                f"4. Confidence level: {query_result.get('confidence', 0):.1%}"
            ]
            
            return explanation
            
        except Exception as e:
            return {
                'error': str(e),
                'natural_query': natural_query
            }

# Global instance
advanced_query_builder = AdvancedQueryBuilder()
