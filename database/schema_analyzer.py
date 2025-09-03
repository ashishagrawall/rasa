from sqlalchemy import inspect, MetaData, Table, ForeignKey
from sqlalchemy.sql import text
import networkx as nx
from typing import Dict, List, Tuple, Optional
import logging
import json
import re

logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    """Advanced database schema analyzer for automatic relationship detection"""
    
    def __init__(self, db_config):
        self.db = db_config
        self.engine = db_config.engine
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.relationship_graph = nx.Graph()
        self.table_aliases = {}
        self.column_synonyms = {}
        self._analyze_schema()
    
    def _analyze_schema(self):
        """Analyze complete database schema and build relationship graph"""
        self._build_relationship_graph()
        self._detect_table_aliases()
        self._detect_column_patterns()
        self._analyze_naming_conventions()
    
    def _build_relationship_graph(self):
        """Build a graph of table relationships using foreign keys"""
        tables = self.inspector.get_table_names()
        
        # Add all tables as nodes
        for table in tables:
            self.relationship_graph.add_node(table)
        
        # Add foreign key relationships as edges
        for table in tables:
            foreign_keys = self.inspector.get_foreign_keys(table)
            for fk in foreign_keys:
                referenced_table = fk['referred_table']
                self.relationship_graph.add_edge(
                    table, 
                    referenced_table,
                    relationship_type='foreign_key',
                    local_columns=fk['constrained_columns'],
                    foreign_columns=fk['referred_columns']
                )
        
        # Detect implicit relationships through naming patterns
        self._detect_implicit_relationships()
    
    def _detect_implicit_relationships(self):
        """Detect relationships through naming conventions (e.g., user_id -> users.id)"""
        tables = self.inspector.get_table_names()
        
        for table in tables:
            columns = self.inspector.get_columns(table)
            for col in columns:
                col_name = col['name'].lower()
                
                # Pattern: table_id -> table.id
                if col_name.endswith('_id'):
                    potential_table = col_name[:-3]
                    # Try plural forms
                    potential_tables = [
                        potential_table,
                        potential_table + 's',
                        potential_table + 'es',
                        potential_table[:-1] + 'ies' if potential_table.endswith('y') else None
                    ]
                    
                    for pot_table in potential_tables:
                        if pot_table and pot_table in tables:
                            if not self.relationship_graph.has_edge(table, pot_table):
                                self.relationship_graph.add_edge(
                                    table,
                                    pot_table,
                                    relationship_type='implicit',
                                    local_columns=[col_name],
                                    foreign_columns=['id']
                                )
                            break
    
    def _detect_table_aliases(self):
        """Detect common table name patterns and aliases"""
        tables = self.inspector.get_table_names()
        
        for table in tables:
            # Common abbreviations
            aliases = []
            
            # Remove common prefixes/suffixes
            clean_name = table.lower()
            if clean_name.startswith('tbl_'):
                clean_name = clean_name[4:]
            if clean_name.endswith('_table'):
                clean_name = clean_name[:-6]
            
            # Generate abbreviations
            if len(clean_name) > 4:
                # First 4 characters
                aliases.append(clean_name[:4])
                # First letter of each word
                words = re.split(r'[_\s]+', clean_name)
                if len(words) > 1:
                    aliases.append(''.join(word[0] for word in words))
            
            # Common business aliases
            business_aliases = {
                'customers': ['cust', 'customer', 'client'],
                'products': ['prod', 'product', 'item'],
                'orders': ['ord', 'order', 'purchase'],
                'employees': ['emp', 'employee', 'staff'],
                'transactions': ['trans', 'transaction', 'txn'],
                'invoices': ['inv', 'invoice', 'bill'],
                'payments': ['pay', 'payment', 'pmt'],
                'addresses': ['addr', 'address', 'location']
            }
            
            for full_name, alias_list in business_aliases.items():
                if full_name in clean_name or clean_name in full_name:
                    aliases.extend(alias_list)
            
            self.table_aliases[table] = list(set(aliases))
    
    def _detect_column_patterns(self):
        """Detect column naming patterns and synonyms"""
        tables = self.inspector.get_table_names()
        
        # Common column synonyms
        column_patterns = {
            'id': ['id', 'pk', 'primary_key', 'key'],
            'name': ['name', 'title', 'label', 'description'],
            'email': ['email', 'email_address', 'mail'],
            'phone': ['phone', 'telephone', 'mobile', 'contact'],
            'address': ['address', 'addr', 'location'],
            'date': ['date', 'created_at', 'updated_at', 'timestamp'],
            'status': ['status', 'state', 'condition'],
            'amount': ['amount', 'price', 'cost', 'value', 'total'],
            'quantity': ['quantity', 'qty', 'count', 'number']
        }
        
        for table in tables:
            columns = self.inspector.get_columns(table)
            for col in columns:
                col_name = col['name'].lower()
                for pattern, synonyms in column_patterns.items():
                    if any(syn in col_name for syn in synonyms):
                        if table not in self.column_synonyms:
                            self.column_synonyms[table] = {}
                        self.column_synonyms[table][col_name] = synonyms
    
    def _analyze_naming_conventions(self):
        """Analyze and learn from existing naming conventions"""
        tables = self.inspector.get_table_names()
        
        # Detect common prefixes/suffixes
        prefixes = {}
        suffixes = {}
        
        for table in tables:
            parts = table.split('_')
            if len(parts) > 1:
                prefix = parts[0]
                suffix = parts[-1]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                suffixes[suffix] = suffixes.get(suffix, 0) + 1
        
        # Store common patterns for future use
        self.naming_patterns = {
            'common_prefixes': [k for k, v in prefixes.items() if v > 1],
            'common_suffixes': [k for k, v in suffixes.items() if v > 1]
        }
    
    def find_table_by_alias(self, alias: str) -> Optional[str]:
        """Find actual table name from alias or partial name"""
        alias = alias.lower().strip()
        
        # Direct match
        tables = self.inspector.get_table_names()
        for table in tables:
            if table.lower() == alias:
                return table
        
        # Check aliases
        for table, aliases in self.table_aliases.items():
            if alias in [a.lower() for a in aliases]:
                return table
        
        # Partial match
        for table in tables:
            if alias in table.lower() or table.lower() in alias:
                return table
        
        return None
    
    def find_relationships(self, table1: str, table2: str) -> List[Dict]:
        """Find all possible relationships between two tables"""
        relationships = []
        
        try:
            # Direct relationship
            if self.relationship_graph.has_edge(table1, table2):
                edge_data = self.relationship_graph.get_edge_data(table1, table2)
                relationships.append({
                    'type': 'direct',
                    'path': [table1, table2],
                    'join_info': edge_data
                })
            
            # Find shortest path through other tables
            try:
                path = nx.shortest_path(self.relationship_graph, table1, table2)
                if len(path) > 2:  # Indirect relationship
                    relationships.append({
                        'type': 'indirect',
                        'path': path,
                        'join_info': self._get_path_join_info(path)
                    })
            except nx.NetworkXNoPath:
                pass
        
        except Exception as e:
            logger.error(f"Error finding relationships between {table1} and {table2}: {e}")
        
        return relationships
    
    def _get_path_join_info(self, path: List[str]) -> List[Dict]:
        """Get join information for a path through multiple tables"""
        join_info = []
        for i in range(len(path) - 1):
            table1, table2 = path[i], path[i + 1]
            if self.relationship_graph.has_edge(table1, table2):
                edge_data = self.relationship_graph.get_edge_data(table1, table2)
                join_info.append({
                    'from_table': table1,
                    'to_table': table2,
                    'join_condition': edge_data
                })
        return join_info
    
    def get_related_tables(self, table: str, max_depth: int = 2) -> Dict[str, List[str]]:
        """Get all tables related to a given table within max_depth"""
        related = {'direct': [], 'indirect': []}
        
        try:
            # Direct relationships
            neighbors = list(self.relationship_graph.neighbors(table))
            related['direct'] = neighbors
            
            # Indirect relationships
            if max_depth > 1:
                for neighbor in neighbors:
                    second_level = list(self.relationship_graph.neighbors(neighbor))
                    for second_table in second_level:
                        if second_table != table and second_table not in related['direct']:
                            related['indirect'].append(second_table)
        
        except Exception as e:
            logger.error(f"Error getting related tables for {table}: {e}")
        
        return related
    
    def suggest_columns_for_query(self, tables: List[str], intent: str) -> List[str]:
        """Suggest relevant columns based on query intent"""
        suggested_columns = []
        
        intent_column_mapping = {
            'count': ['id'],
            'list': ['id', 'name', 'title', 'description'],
            'search': ['name', 'title', 'description', 'email'],
            'financial': ['amount', 'price', 'cost', 'total', 'value'],
            'temporal': ['created_at', 'updated_at', 'date', 'timestamp'],
            'status': ['status', 'state', 'active', 'enabled']
        }
        
        relevant_patterns = intent_column_mapping.get(intent, ['id', 'name'])
        
        for table in tables:
            columns = self.inspector.get_columns(table)
            for col in columns:
                col_name = col['name'].lower()
                for pattern in relevant_patterns:
                    if pattern in col_name:
                        suggested_columns.append(f"{table}.{col['name']}")
        
        return suggested_columns
    
    def export_schema_info(self) -> Dict:
        """Export schema analysis for training data generation"""
        return {
            'tables': self.inspector.get_table_names(),
            'relationships': nx.to_dict_of_dicts(self.relationship_graph),
            'table_aliases': self.table_aliases,
            'column_synonyms': self.column_synonyms,
            'naming_patterns': self.naming_patterns
        }
