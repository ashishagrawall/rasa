import openai
import re
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from database.schema_analyzer import SchemaAnalyzer
from database.db_config import db_config
import logging
import json

logger = logging.getLogger(__name__)

class AIQueryGenerator:
    """AI-powered natural language to SQL query generator"""
    
    def __init__(self, schema_analyzer: SchemaAnalyzer, openai_api_key: Optional[str] = None):
        self.schema = schema_analyzer
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Load sentence transformer for semantic similarity
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.sentence_model = None
        
        self.query_patterns = self._load_query_patterns()
        self.intent_keywords = self._build_intent_keywords()
    
    def _load_query_patterns(self) -> Dict:
        """Load common query patterns and templates"""
        return {
            'count': {
                'keywords': ['how many', 'count', 'total', 'number of'],
                'template': 'SELECT COUNT(*) FROM {tables} {joins} {where}'
            },
            'list': {
                'keywords': ['show', 'list', 'get', 'display', 'find'],
                'template': 'SELECT {columns} FROM {tables} {joins} {where} {limit}'
            },
            'aggregate': {
                'keywords': ['sum', 'average', 'max', 'min', 'total'],
                'template': 'SELECT {aggregate}({column}) FROM {tables} {joins} {where}'
            },
            'group_by': {
                'keywords': ['by', 'group', 'each', 'per'],
                'template': 'SELECT {group_columns}, {aggregate} FROM {tables} {joins} {where} GROUP BY {group_columns}'
            },
            'join': {
                'keywords': ['with', 'and', 'related', 'associated'],
                'template': 'SELECT {columns} FROM {tables} {joins} {where}'
            }
        }
    
    def _build_intent_keywords(self) -> Dict:
        """Build keyword mappings for different query intents"""
        return {
            'financial': ['price', 'cost', 'amount', 'revenue', 'sales', 'payment', 'invoice'],
            'temporal': ['date', 'time', 'when', 'created', 'updated', 'recent', 'last'],
            'status': ['active', 'inactive', 'enabled', 'disabled', 'status', 'state'],
            'location': ['address', 'city', 'country', 'location', 'region'],
            'personal': ['name', 'email', 'phone', 'contact', 'customer', 'user'],
            'business': ['order', 'product', 'service', 'company', 'department']
        }
    
    def generate_sql(self, natural_query: str, context: Dict = None) -> Dict:
        """Generate SQL from natural language query"""
        try:
            # Step 1: Analyze the natural language query
            analysis = self._analyze_natural_query(natural_query)
            
            # Step 2: Identify relevant tables
            relevant_tables = self._identify_tables(analysis)
            
            # Step 3: Determine relationships and joins
            joins = self._build_joins(relevant_tables)
            
            # Step 4: Extract columns and conditions
            columns = self._extract_columns(analysis, relevant_tables)
            where_conditions = self._extract_conditions(analysis, relevant_tables)
            
            # Step 5: Generate SQL query
            sql_query = self._construct_sql(
                analysis['intent'],
                relevant_tables,
                columns,
                joins,
                where_conditions,
                analysis
            )
            
            return {
                'sql': sql_query,
                'tables': relevant_tables,
                'analysis': analysis,
                'confidence': analysis.get('confidence', 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return {
                'sql': None,
                'error': str(e),
                'analysis': {'intent': 'unknown'},
                'confidence': 0.0
            }
    
    def _analyze_natural_query(self, query: str) -> Dict:
        """Analyze natural language query to extract intent and entities"""
        query_lower = query.lower()
        analysis = {
            'original_query': query,
            'intent': 'list',  # default
            'entities': [],
            'keywords': [],
            'confidence': 0.5
        }
        
        # Detect intent from patterns
        for intent, pattern_info in self.query_patterns.items():
            for keyword in pattern_info['keywords']:
                if keyword in query_lower:
                    analysis['intent'] = intent
                    analysis['confidence'] += 0.2
                    analysis['keywords'].append(keyword)
        
        # Extract entities (table names, column names, values)
        analysis['entities'] = self._extract_entities(query)
        
        # Detect aggregation functions
        agg_functions = ['count', 'sum', 'avg', 'average', 'max', 'min']
        for func in agg_functions:
            if func in query_lower:
                analysis['aggregation'] = func
                if func in ['sum', 'avg', 'average', 'max', 'min']:
                    analysis['intent'] = 'aggregate'
        
        # Detect grouping
        if any(word in query_lower for word in ['by', 'group', 'each', 'per']):
            analysis['intent'] = 'group_by'
        
        return analysis
    
    def _extract_entities(self, query: str) -> List[Dict]:
        """Extract entities like table names, column names, and values"""
        entities = []
        query_lower = query.lower()
        
        # Extract potential table names
        tables = self.schema.inspector.get_table_names()
        for table in tables:
            # Check direct mentions
            if table.lower() in query_lower:
                entities.append({
                    'type': 'table',
                    'value': table,
                    'original': table,
                    'confidence': 0.9
                })
            
            # Check aliases
            if table in self.schema.table_aliases:
                for alias in self.schema.table_aliases[table]:
                    if alias.lower() in query_lower:
                        entities.append({
                            'type': 'table',
                            'value': table,
                            'original': alias,
                            'confidence': 0.8
                        })
        
        # Extract column names
        for table in tables:
            columns = self.schema.inspector.get_columns(table)
            for col in columns:
                col_name = col['name'].lower()
                if col_name in query_lower:
                    entities.append({
                        'type': 'column',
                        'value': col['name'],
                        'table': table,
                        'confidence': 0.7
                    })
        
        # Extract quoted values and numbers
        quoted_values = re.findall(r"'([^']*)'|\"([^\"]*)\"", query)
        for match in quoted_values:
            value = match[0] or match[1]
            entities.append({
                'type': 'value',
                'value': value,
                'confidence': 0.9
            })
        
        # Extract numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
        for num in numbers:
            entities.append({
                'type': 'number',
                'value': num,
                'confidence': 0.8
            })
        
        return entities
    
    def _identify_tables(self, analysis: Dict) -> List[str]:
        """Identify relevant tables based on query analysis"""
        relevant_tables = []
        
        # Get explicitly mentioned tables
        for entity in analysis['entities']:
            if entity['type'] == 'table':
                relevant_tables.append(entity['value'])
        
        # If no tables mentioned, infer from context
        if not relevant_tables:
            relevant_tables = self._infer_tables_from_context(analysis)
        
        # Add related tables if needed for joins
        if len(relevant_tables) == 1:
            related = self.schema.get_related_tables(relevant_tables[0], max_depth=1)
            # Add directly related tables if query suggests relationships
            if any(word in analysis['original_query'].lower() for word in ['with', 'and', 'related']):
                relevant_tables.extend(related['direct'][:2])  # Limit to avoid too many joins
        
        return list(set(relevant_tables))
    
    def _infer_tables_from_context(self, analysis: Dict) -> List[str]:
        """Infer tables from query context when not explicitly mentioned"""
        query_lower = analysis['original_query'].lower()
        inferred_tables = []
        
        # Business domain keywords to table mapping
        domain_mappings = {
            'customer': ['customers', 'users', 'clients'],
            'order': ['orders', 'purchases', 'transactions'],
            'product': ['products', 'items', 'inventory'],
            'employee': ['employees', 'staff', 'users'],
            'sale': ['sales', 'orders', 'transactions'],
            'payment': ['payments', 'transactions', 'invoices'],
            'invoice': ['invoices', 'bills', 'payments']
        }
        
        tables = self.schema.inspector.get_table_names()
        
        for keyword, potential_tables in domain_mappings.items():
            if keyword in query_lower:
                for pot_table in potential_tables:
                    # Find actual table that matches
                    actual_table = self.schema.find_table_by_alias(pot_table)
                    if actual_table and actual_table in tables:
                        inferred_tables.append(actual_table)
                        break
        
        # If still no tables, use semantic similarity
        if not inferred_tables and self.sentence_model:
            inferred_tables = self._semantic_table_matching(query_lower, tables)
        
        return inferred_tables[:3]  # Limit to 3 tables to avoid complexity
    
    def _semantic_table_matching(self, query: str, tables: List[str]) -> List[str]:
        """Use semantic similarity to match query with table names"""
        try:
            query_embedding = self.sentence_model.encode([query])
            table_embeddings = self.sentence_model.encode(tables)
            
            similarities = np.dot(query_embedding, table_embeddings.T)[0]
            
            # Get top 2 most similar tables
            top_indices = np.argsort(similarities)[-2:][::-1]
            return [tables[i] for i in top_indices if similarities[i] > 0.3]
        except Exception as e:
            logger.error(f"Semantic matching error: {e}")
            return []
    
    def _build_joins(self, tables: List[str]) -> List[str]:
        """Build JOIN clauses for multiple tables"""
        if len(tables) <= 1:
            return []
        
        joins = []
        main_table = tables[0]
        
        for i, table in enumerate(tables[1:], 1):
            relationships = self.schema.find_relationships(main_table, table)
            
            if relationships:
                rel = relationships[0]  # Use first relationship found
                if rel['type'] == 'direct':
                    join_info = rel['join_info']
                    if 'local_columns' in join_info and 'foreign_columns' in join_info:
                        local_col = join_info['local_columns'][0]
                        foreign_col = join_info['foreign_columns'][0]
                        joins.append(f"LEFT JOIN {table} ON {main_table}.{local_col} = {table}.{foreign_col}")
                elif rel['type'] == 'indirect':
                    # Build joins through intermediate tables
                    path = rel['path']
                    for j in range(len(path) - 1):
                        from_table, to_table = path[j], path[j + 1]
                        join_info = rel['join_info'][j]
                        condition = join_info['join_condition']
                        if 'local_columns' in condition and 'foreign_columns' in condition:
                            local_col = condition['local_columns'][0]
                            foreign_col = condition['foreign_columns'][0]
                            joins.append(f"LEFT JOIN {to_table} ON {from_table}.{local_col} = {to_table}.{foreign_col}")
        
        return joins
    
    def _extract_columns(self, analysis: Dict, tables: List[str]) -> List[str]:
        """Extract relevant columns based on query intent and mentioned entities"""
        columns = []
        
        # Get explicitly mentioned columns
        for entity in analysis['entities']:
            if entity['type'] == 'column':
                table = entity.get('table', tables[0] if tables else '')
                columns.append(f"{table}.{entity['value']}")
        
        # If no columns mentioned, suggest based on intent
        if not columns:
            intent = analysis.get('intent', 'list')
            columns = self.schema.suggest_columns_for_query(tables, intent)
        
        # Always include primary keys for joins
        for table in tables:
            table_columns = self.schema.inspector.get_columns(table)
            for col in table_columns:
                if col.get('primary_key') or col['name'].lower() in ['id', 'pk']:
                    pk_col = f"{table}.{col['name']}"
                    if pk_col not in columns:
                        columns.insert(0, pk_col)
                    break
        
        return columns[:10]  # Limit columns to avoid overly wide results
    
    def _extract_conditions(self, analysis: Dict, tables: List[str]) -> List[str]:
        """Extract WHERE conditions from the query"""
        conditions = []
        
        # Extract value-based conditions
        value_entities = [e for e in analysis['entities'] if e['type'] in ['value', 'number']]
        column_entities = [e for e in analysis['entities'] if e['type'] == 'column']
        
        # Match values with columns
        for value_entity in value_entities:
            value = value_entity['value']
            
            # Try to match with mentioned columns
            for col_entity in column_entities:
                table = col_entity.get('table', tables[0] if tables else '')
                column = f"{table}.{col_entity['value']}"
                
                if value_entity['type'] == 'number':
                    conditions.append(f"{column} = {value}")
                else:
                    conditions.append(f"{column} LIKE '%{value}%'")
        
        # Extract comparison operators
        query_lower = analysis['original_query'].lower()
        comparison_patterns = [
            (r'greater than (\d+)', lambda m: f" > {m.group(1)}"),
            (r'less than (\d+)', lambda m: f" < {m.group(1)}"),
            (r'equals? (\d+)', lambda m: f" = {m.group(1)}"),
            (r'between (\d+) and (\d+)', lambda m: f" BETWEEN {m.group(1)} AND {m.group(2)}")
        ]
        
        for pattern, formatter in comparison_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                # Apply to most relevant numeric column
                numeric_columns = self._find_numeric_columns(tables)
                if numeric_columns:
                    conditions.append(f"{numeric_columns[0]}{formatter(match)}")
        
        return conditions
    
    def _find_numeric_columns(self, tables: List[str]) -> List[str]:
        """Find numeric columns in the given tables"""
        numeric_columns = []
        numeric_types = ['INTEGER', 'FLOAT', 'DECIMAL', 'NUMERIC', 'REAL']
        
        for table in tables:
            columns = self.schema.inspector.get_columns(table)
            for col in columns:
                if str(col['type']).upper() in numeric_types:
                    numeric_columns.append(f"{table}.{col['name']}")
        
        return numeric_columns
    
    def _construct_sql(self, intent: str, tables: List[str], columns: List[str], 
                      joins: List[str], conditions: List[str], analysis: Dict) -> str:
        """Construct the final SQL query"""
        if not tables:
            return "SELECT 1"  # Fallback query
        
        # Build SELECT clause
        if intent == 'count':
            select_clause = "SELECT COUNT(*)"
        elif intent == 'aggregate' and 'aggregation' in analysis:
            agg_func = analysis['aggregation']
            numeric_cols = self._find_numeric_columns(tables)
            if numeric_cols:
                select_clause = f"SELECT {agg_func.upper()}({numeric_cols[0]})"
            else:
                select_clause = "SELECT COUNT(*)"
        else:
            if columns:
                select_clause = f"SELECT {', '.join(columns)}"
            else:
                select_clause = f"SELECT {tables[0]}.*"
        
        # Build FROM clause
        from_clause = f"FROM {tables[0]}"
        
        # Add JOINs
        join_clause = " " + " ".join(joins) if joins else ""
        
        # Build WHERE clause
        where_clause = ""
        if conditions:
            where_clause = f" WHERE {' AND '.join(conditions)}"
        
        # Add LIMIT for list queries
        limit_clause = ""
        if intent == 'list' and 'all' not in analysis['original_query'].lower():
            limit_clause = " LIMIT 10"
        
        # Construct final query
        sql = f"{select_clause} {from_clause}{join_clause}{where_clause}{limit_clause}"
        
        return sql.strip()
    
    def generate_with_openai(self, natural_query: str, schema_info: Dict) -> str:
        """Use OpenAI GPT to generate SQL (requires API key)"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required for GPT-based generation")
        
        prompt = self._build_openai_prompt(natural_query, schema_info)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            return sql_query
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _build_openai_prompt(self, query: str, schema_info: Dict) -> str:
        """Build prompt for OpenAI GPT"""
        return f"""
Generate a SQL query for the following natural language request:
"{query}"

Database Schema:
Tables: {', '.join(schema_info.get('tables', []))}
Relationships: {json.dumps(schema_info.get('relationships', {}), indent=2)}

Requirements:
1. Use proper JOIN syntax for related tables
2. Include appropriate WHERE conditions
3. Use LIMIT for large result sets
4. Return only the SQL query, no explanations

SQL Query:
"""
