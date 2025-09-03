from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from database.advanced_query_builder import advanced_query_builder
import logging
import json

logger = logging.getLogger(__name__)

class ActionProcessNaturalQuery(Action):
    """Advanced action that processes complex natural language queries"""
    
    def name(self) -> Text:
        return "action_process_natural_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the user's message
        user_message = tracker.latest_message.get('text', '')
        
        if not user_message:
            dispatcher.utter_message(text="I didn't receive your query. Please try again.")
            return []
        
        try:
            # Process the natural language query
            result = advanced_query_builder.process_natural_query(user_message)
            
            if not result['success']:
                error_msg = result.get('error', 'Unknown error occurred')
                dispatcher.utter_message(
                    text=f"I couldn't process your query: {error_msg}\n\n"
                         f"Try rephrasing your question or being more specific about the tables you want to query."
                )
                return []
            
            # Format and send the response
            response = self._format_response(result, user_message)
            dispatcher.utter_message(text=response)
            
            # Set slots for context
            return [
                SlotSet("last_query", user_message),
                SlotSet("last_sql", result.get('sql_executed', '')),
                SlotSet("last_tables", json.dumps(result.get('tables_involved', [])))
            ]
            
        except Exception as e:
            logger.error(f"Error in ActionProcessNaturalQuery: {e}")
            dispatcher.utter_message(
                text="I encountered an error while processing your query. "
                     "Please try a simpler question or check if your database is accessible."
            )
            return []
    
    def _format_response(self, result: Dict, original_query: str) -> str:
        """Format the query result into a user-friendly response"""
        response = f"**Query:** {original_query}\n\n"
        
        if result['result_type'] == 'data':
            row_count = result['row_count']
            
            if row_count == 0:
                response += "No results found for your query."
            else:
                response += f"**Found {row_count} result(s):**\n\n"
                
                # Display results in a readable format
                data = result['data']
                columns = result['columns']
                
                # Show first 5 results to avoid overwhelming the user
                display_count = min(5, len(data))
                
                for i, row in enumerate(data[:display_count], 1):
                    response += f"**Result {i}:**\n"
                    for col in columns:
                        value = row.get(col, 'N/A')
                        response += f"  • {col}: {value}\n"
                    response += "\n"
                
                if row_count > display_count:
                    response += f"... and {row_count - display_count} more results.\n\n"
                
                # Add confidence and SQL info
                confidence = result.get('confidence', 0)
                if confidence < 0.7:
                    response += f"⚠️ *Confidence: {confidence:.1%} - Results may not be exactly what you're looking for.*\n"
                
                response += f"**SQL executed:** `{result['sql_executed']}`"
        
        else:
            # Modification result
            affected = result.get('affected_rows', 0)
            response += f"Operation completed. {affected} rows affected."
        
        return response

class ActionExplainQuery(Action):
    """Explain how a query would be processed without executing it"""
    
    def name(self) -> Text:
        return "action_explain_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        # Remove "explain" from the message to get the actual query
        query_to_explain = user_message.replace('explain', '').replace('how would you', '').strip()
        
        if not query_to_explain:
            dispatcher.utter_message(
                text="Please provide a query to explain. For example: 'Explain how you would find all customers with orders'"
            )
            return []
        
        try:
            explanation = advanced_query_builder.explain_query(query_to_explain)
            
            if 'error' in explanation:
                dispatcher.utter_message(
                    text=f"I couldn't analyze that query: {explanation['error']}"
                )
                return []
            
            response = f"**Query Analysis:** {query_to_explain}\n\n"
            response += f"**Generated SQL:** `{explanation['generated_sql']}`\n\n"
            response += f"**Confidence:** {explanation['confidence']:.1%}\n\n"
            response += "**Processing Steps:**\n"
            
            for step in explanation['explanation_steps']:
                response += f"{step}\n"
            
            if explanation['tables_involved']:
                response += f"\n**Tables involved:** {', '.join(explanation['tables_involved'])}"
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionExplainQuery: {e}")
            dispatcher.utter_message(text="I couldn't explain that query. Please try again.")
        
        return []

class ActionGetSchemaSuggestions(Action):
    """Get schema-based suggestions for query building"""
    
    def name(self) -> Text:
        return "action_get_schema_suggestions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        try:
            suggestions = advanced_query_builder.get_schema_suggestions(user_message)
            
            response = "**Here are some suggestions based on your database schema:**\n\n"
            
            # Show relevant tables
            if suggestions['tables']:
                response += "**Relevant Tables:**\n"
                for table in suggestions['tables'][:5]:
                    aliases = ', '.join(table['aliases']) if table['aliases'] else 'None'
                    response += f"• **{table['name']}** ({table['row_count']} rows)\n"
                    response += f"  Aliases: {aliases}\n"
                response += "\n"
            
            # Show sample queries
            if suggestions['sample_queries']:
                response += "**Try asking:**\n"
                for query in suggestions['sample_queries'][:5]:
                    response += f"• \"{query}\"\n"
                response += "\n"
            
            # Show relationships
            if suggestions['relationships']:
                response += "**Related Tables:**\n"
                direct = suggestions['relationships'].get('direct', [])
                if direct:
                    response += f"Directly related: {', '.join(direct[:3])}\n"
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionGetSchemaSuggestions: {e}")
            dispatcher.utter_message(text="I couldn't get schema suggestions at the moment.")
        
        return []

class ActionSmartSearch(Action):
    """Smart search that handles fuzzy table/column matching"""
    
    def name(self) -> Text:
        return "action_smart_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        # This action is triggered for queries that mention searching
        # but don't specify exact table names
        
        try:
            # Use the advanced query builder to handle the search
            result = advanced_query_builder.process_natural_query(user_message)
            
            if result['success']:
                response = self._format_search_response(result, user_message)
                dispatcher.utter_message(text=response)
            else:
                # Provide helpful suggestions
                suggestions = advanced_query_builder.get_schema_suggestions(user_message)
                
                response = "I couldn't find exact matches, but here are some suggestions:\n\n"
                
                if suggestions['tables']:
                    response += "**Available tables that might be relevant:**\n"
                    for table in suggestions['tables'][:3]:
                        response += f"• {table['name']}\n"
                    response += "\n"
                
                response += "**Try asking:**\n"
                for query in suggestions['sample_queries'][:3]:
                    response += f"• \"{query}\"\n"
                
                dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionSmartSearch: {e}")
            dispatcher.utter_message(text="I couldn't perform the search. Please try being more specific.")
        
        return []
    
    def _format_search_response(self, result: Dict, original_query: str) -> str:
        """Format search results with emphasis on found matches"""
        if result['row_count'] == 0:
            return f"No matches found for: '{original_query}'\n\nTry using different keywords or check your spelling."
        
        response = f"**Search Results for:** {original_query}\n\n"
        response += f"Found **{result['row_count']} matches** across {len(result['tables_involved'])} table(s)\n\n"
        
        # Show first few results
        for i, row in enumerate(result['data'][:3], 1):
            response += f"**Match {i}:**\n"
            for key, value in row.items():
                if value and str(value).strip():  # Only show non-empty values
                    response += f"  • {key}: {value}\n"
            response += "\n"
        
        if result['row_count'] > 3:
            response += f"... and {result['row_count'] - 3} more matches.\n"
        
        return response
