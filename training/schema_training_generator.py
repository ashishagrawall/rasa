import yaml
import json
from typing import Dict, List, Any
from database.schema_analyzer import SchemaAnalyzer
from database.db_config import db_config
import logging
import random

logger = logging.getLogger(__name__)

class SchemaTrainingGenerator:
    """Generate training data based on actual database schema"""
    
    def __init__(self):
        self.schema_analyzer = SchemaAnalyzer(db_config)
        self.generated_intents = {}
        self.generated_entities = {}
        self.generated_stories = []
        
    def generate_training_data(self) -> Dict[str, Any]:
        """Generate comprehensive training data from database schema"""
        try:
            # Analyze schema
            schema_info = self.schema_analyzer.export_schema_info()
            
            # Generate intents and entities
            self._generate_table_specific_intents(schema_info)
            self._generate_relationship_intents(schema_info)
            self._generate_business_domain_intents(schema_info)
            
            # Generate stories
            self._generate_conversation_stories()
            
            # Generate rules
            rules = self._generate_dynamic_rules()
            
            return {
                'nlu': self._format_nlu_data(),
                'domain': self._format_domain_data(),
                'stories': self._format_stories_data(),
                'rules': rules,
                'schema_info': schema_info
            }
            
        except Exception as e:
            logger.error(f"Error generating training data: {e}")
            return {}
    
    def _generate_table_specific_intents(self, schema_info: Dict):
        """Generate intents specific to each table in the database"""
        tables = schema_info['tables']
        
        for table in tables:
            table_lower = table.lower()
            
            # Get table aliases
            aliases = schema_info['table_aliases'].get(table, [])
            all_names = [table, table_lower] + aliases
            
            # Generate query intents for this table
            intent_name = f"query_{table_lower}"
            examples = []
            
            for name in all_names[:3]:  # Limit to avoid too many variations
                examples.extend([
                    f"show me {name}",
                    f"get all {name}",
                    f"list {name}",
                    f"display {name} data",
                    f"fetch {name} records",
                    f"what's in {name} table",
                    f"give me {name} information"
                ])
            
            self.generated_intents[intent_name] = {
                'examples': examples,
                'table': table
            }
            
            # Generate count intents
            count_intent = f"count_{table_lower}"
            count_examples = []
            
            for name in all_names[:3]:
                count_examples.extend([
                    f"how many {name} are there",
                    f"count {name}",
                    f"total {name}",
                    f"number of {name}",
                    f"{name} count"
                ])
            
            self.generated_intents[count_intent] = {
                'examples': count_examples,
                'table': table
            }
            
            # Generate search intents
            search_intent = f"search_{table_lower}"
            search_examples = []
            
            for name in all_names[:2]:
                search_examples.extend([
                    f"find {name} where",
                    f"search {name} for",
                    f"look for {name} with",
                    f"get {name} that have",
                    f"show {name} containing"
                ])
            
            self.generated_intents[search_intent] = {
                'examples': search_examples,
                'table': table
            }
    
    def _generate_relationship_intents(self, schema_info: Dict):
        """Generate intents for table relationships and joins"""
        relationships = schema_info['relationships']
        
        for table1, connections in relationships.items():
            for table2, relationship_info in connections.items():
                if relationship_info:  # Has actual relationship
                    
                    # Generate join intent
                    join_intent = f"join_{table1.lower()}_{table2.lower()}"
                    join_examples = [
                        f"show {table1} with {table2}",
                        f"get {table1} and their {table2}",
                        f"list {table1} along with {table2}",
                        f"display {table1} including {table2}",
                        f"fetch {table1} with related {table2}",
                        f"combine {table1} and {table2} data"
                    ]
                    
                    self.generated_intents[join_intent] = {
                        'examples': join_examples,
                        'tables': [table1, table2],
                        'type': 'join'
                    }
    
    def _generate_business_domain_intents(self, schema_info: Dict):
        """Generate business domain-specific intents"""
        tables = schema_info['tables']
        
        # Common business scenarios
        business_patterns = {
            'sales_analysis': {
                'keywords': ['sales', 'revenue', 'orders', 'transactions'],
                'examples': [
                    "show me sales data",
                    "what's our revenue",
                    "get sales report",
                    "total sales amount",
                    "sales by month"
                ]
            },
            'customer_analysis': {
                'keywords': ['customers', 'users', 'clients'],
                'examples': [
                    "show customer information",
                    "get customer details",
                    "list all customers",
                    "customer demographics",
                    "active customers"
                ]
            },
            'product_analysis': {
                'keywords': ['products', 'items', 'inventory'],
                'examples': [
                    "show product catalog",
                    "get product information",
                    "list available products",
                    "product inventory",
                    "out of stock products"
                ]
            },
            'financial_analysis': {
                'keywords': ['payments', 'invoices', 'billing'],
                'examples': [
                    "show payment history",
                    "get invoice details",
                    "outstanding payments",
                    "payment status",
                    "billing information"
                ]
            }
        }
        
        # Check which business domains apply to this database
        for domain, pattern_info in business_patterns.items():
            relevant_tables = []
            
            for table in tables:
                table_lower = table.lower()
                if any(keyword in table_lower for keyword in pattern_info['keywords']):
                    relevant_tables.append(table)
            
            if relevant_tables:
                self.generated_intents[domain] = {
                    'examples': pattern_info['examples'],
                    'tables': relevant_tables,
                    'type': 'business_domain'
                }
    
    def _generate_conversation_stories(self):
        """Generate conversation stories based on generated intents"""
        
        # Simple query stories
        for intent_name, intent_info in self.generated_intents.items():
            if 'table' in intent_info:  # Single table intent
                story = {
                    'story': f"{intent_name}_flow",
                    'steps': [
                        {'intent': 'greet'},
                        {'action': 'utter_greet'},
                        {'intent': intent_name},
                        {'action': 'action_process_natural_query'},
                        {'intent': 'goodbye'},
                        {'action': 'utter_goodbye'}
                    ]
                }
                self.generated_stories.append(story)
        
        # Complex multi-turn stories
        complex_stories = [
            {
                'story': 'complex_query_with_clarification',
                'steps': [
                    {'intent': 'greet'},
                    {'action': 'utter_greet'},
                    {'intent': 'ask_database'},
                    {'action': 'action_get_schema_suggestions'},
                    {'intent': 'affirm'},
                    {'action': 'action_process_natural_query'},
                    {'intent': 'goodbye'},
                    {'action': 'utter_goodbye'}
                ]
            },
            {
                'story': 'search_with_refinement',
                'steps': [
                    {'intent': 'greet'},
                    {'action': 'utter_greet'},
                    {'intent': 'search_data'},
                    {'action': 'action_smart_search'},
                    {'intent': 'search_data'},
                    {'action': 'action_process_natural_query'},
                    {'intent': 'goodbye'},
                    {'action': 'utter_goodbye'}
                ]
            }
        ]
        
        self.generated_stories.extend(complex_stories)
    
    def _generate_dynamic_rules(self) -> List[Dict]:
        """Generate rules based on schema analysis"""
        rules = [
            {
                'rule': 'Process any natural language query',
                'steps': [
                    {'intent': 'ask_database'},
                    {'action': 'action_process_natural_query'}
                ]
            },
            {
                'rule': 'Handle search requests',
                'steps': [
                    {'intent': 'search_data'},
                    {'action': 'action_smart_search'}
                ]
            },
            {
                'rule': 'Provide schema suggestions',
                'steps': [
                    {'intent': 'show_tables'},
                    {'action': 'action_get_schema_suggestions'}
                ]
            },
            {
                'rule': 'Explain query processing',
                'steps': [
                    {'intent': 'bot_challenge'},
                    {'action': 'action_explain_query'}
                ]
            }
        ]
        
        # Add table-specific rules
        for intent_name, intent_info in self.generated_intents.items():
            if intent_info.get('type') == 'join':
                rules.append({
                    'rule': f'Handle {intent_name}',
                    'steps': [
                        {'intent': intent_name},
                        {'action': 'action_process_natural_query'}
                    ]
                })
        
        return rules
    
    def _format_nlu_data(self) -> Dict:
        """Format generated intents into NLU YAML format"""
        nlu_data = {
            'version': '3.1',
            'nlu': []
        }
        
        # Add base intents
        base_intents = [
            {
                'intent': 'greet',
                'examples': [
                    'hey', 'hello', 'hi', 'hello there', 'good morning',
                    'good evening', 'hey there', 'good afternoon'
                ]
            },
            {
                'intent': 'goodbye',
                'examples': [
                    'bye', 'goodbye', 'have a nice day', 'see you later',
                    'good night', 'see you around', 'bye bye'
                ]
            },
            {
                'intent': 'affirm',
                'examples': [
                    'yes', 'indeed', 'of course', 'that sounds good',
                    'correct', 'yes please', 'absolutely', 'sure', 'right'
                ]
            },
            {
                'intent': 'deny',
                'examples': [
                    'no', 'never', 'I don\'t think so', 'don\'t like that',
                    'no way', 'not really', 'nope', 'not interested'
                ]
            }
        ]
        
        # Add base intents
        for intent in base_intents:
            nlu_data['nlu'].append({
                'intent': intent['intent'],
                'examples': '|\n    - ' + '\n    - '.join(intent['examples'])
            })
        
        # Add generated intents
        for intent_name, intent_info in self.generated_intents.items():
            examples_text = '|\n    - ' + '\n    - '.join(intent_info['examples'])
            nlu_data['nlu'].append({
                'intent': intent_name,
                'examples': examples_text
            })
        
        return nlu_data
    
    def _format_domain_data(self) -> Dict:
        """Format domain configuration"""
        # Get all intent names
        all_intents = ['greet', 'goodbye', 'affirm', 'deny', 'bot_challenge']
        all_intents.extend(list(self.generated_intents.keys()))
        
        # Get all table names for entities
        schema_info = self.schema_analyzer.export_schema_info()
        tables = schema_info['tables']
        
        domain = {
            'version': '3.1',
            'intents': all_intents,
            'entities': ['table_name', 'column_name', 'search_value', 'record_id'],
            'slots': {
                'table_name': {
                    'type': 'text',
                    'influence_conversation': True,
                    'mappings': [{'type': 'from_entity', 'entity': 'table_name'}]
                },
                'last_query': {
                    'type': 'text',
                    'influence_conversation': False,
                    'mappings': [{'type': 'custom'}]
                },
                'last_sql': {
                    'type': 'text',
                    'influence_conversation': False,
                    'mappings': [{'type': 'custom'}]
                },
                'last_tables': {
                    'type': 'text',
                    'influence_conversation': False,
                    'mappings': [{'type': 'custom'}]
                }
            },
            'responses': {
                'utter_greet': [
                    {'text': 'Hey! I can help you query your database with natural language. What would you like to know?'}
                ],
                'utter_goodbye': [
                    {'text': 'Goodbye! Feel free to ask me about your data anytime.'}
                ],
                'utter_iamabot': [
                    {'text': 'I am an AI assistant that can understand your questions about the database and generate SQL queries automatically.'}
                ]
            },
            'actions': [
                'action_process_natural_query',
                'action_explain_query',
                'action_get_schema_suggestions',
                'action_smart_search'
            ],
            'session_config': {
                'session_expiration_time': 60,
                'carry_over_slots_to_new_session': True
            }
        }
        
        return domain
    
    def _format_stories_data(self) -> Dict:
        """Format stories data"""
        return {
            'version': '3.1',
            'stories': self.generated_stories
        }
    
    def save_training_data(self, output_dir: str = 'training_generated'):
        """Save generated training data to files"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        training_data = self.generate_training_data()
        
        # Save NLU data
        with open(f"{output_dir}/nlu.yml", 'w') as f:
            yaml.dump(training_data['nlu'], f, default_flow_style=False, allow_unicode=True)
        
        # Save domain
        with open(f"{output_dir}/domain.yml", 'w') as f:
            yaml.dump(training_data['domain'], f, default_flow_style=False, allow_unicode=True)
        
        # Save stories
        with open(f"{output_dir}/stories.yml", 'w') as f:
            yaml.dump(training_data['stories'], f, default_flow_style=False, allow_unicode=True)
        
        # Save rules
        rules_data = {'version': '3.1', 'rules': training_data['rules']}
        with open(f"{output_dir}/rules.yml", 'w') as f:
            yaml.dump(rules_data, f, default_flow_style=False, allow_unicode=True)
        
        # Save schema info for reference
        with open(f"{output_dir}/schema_info.json", 'w') as f:
            json.dump(training_data['schema_info'], f, indent=2)
        
        logger.info(f"Training data saved to {output_dir}/")
        
        return {
            'intents_generated': len(self.generated_intents),
            'stories_generated': len(self.generated_stories),
            'tables_analyzed': len(training_data['schema_info']['tables']),
            'output_directory': output_dir
        }
