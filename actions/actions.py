from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from database.query_builder import query_builder
from database.db_config import db_config
import logging
import json

logger = logging.getLogger(__name__)

class ActionQueryDatabase(Action):
    def name(self) -> Text:
        return "action_query_database"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        table_name = tracker.get_slot("table_name")
        
        if not table_name:
            dispatcher.utter_message(text="Please specify which table you'd like to query.")
            return []
        
        try:
            # Check if table exists
            available_tables = db_config.get_table_names()
            if table_name not in available_tables:
                dispatcher.utter_message(
                    text=f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}"
                )
                return []
            
            # Get records from the table
            results = query_builder.get_all_records(table_name, limit=10)
            formatted_results = query_builder.format_results(results, table_name)
            
            if formatted_results == "No records found.":
                dispatcher.utter_message(text=f"No records found in table '{table_name}'.")
            else:
                response = f"Here are the records from '{table_name}' table:\n\n"
                for i, record in enumerate(formatted_results, 1):
                    response += f"Record {i}:\n"
                    for key, value in record.items():
                        response += f"  {key}: {value}\n"
                    response += "\n"
                
                dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionQueryDatabase: {str(e)}")
            dispatcher.utter_message(text="I encountered an error while querying the database. Please try again.")
        
        return []

class ActionGetTableInfo(Action):
    def name(self) -> Text:
        return "action_get_table_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            tables = db_config.get_table_names()
            if not tables:
                dispatcher.utter_message(text="No tables found in the database.")
                return []
            
            response = "Available tables in your database:\n\n"
            for table in tables:
                columns = db_config.get_table_columns(table)
                response += f"📊 **{table}**\n"
                response += f"   Columns: {', '.join(columns)}\n\n"
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionGetTableInfo: {str(e)}")
            dispatcher.utter_message(text="I encountered an error while getting table information.")
        
        return []

class ActionSearchRecords(Action):
    def name(self) -> Text:
        return "action_search_records"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        table_name = tracker.get_slot("table_name")
        column_name = tracker.get_slot("column_name")
        search_value = tracker.get_slot("search_value")
        
        if not all([table_name, column_name, search_value]):
            dispatcher.utter_message(text="Please specify the table, column, and search value.")
            return []
        
        try:
            # Check if table exists
            available_tables = db_config.get_table_names()
            if table_name not in available_tables:
                dispatcher.utter_message(
                    text=f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}"
                )
                return []
            
            # Check if column exists
            columns = db_config.get_table_columns(table_name)
            if column_name not in columns:
                dispatcher.utter_message(
                    text=f"Column '{column_name}' not found in table '{table_name}'. Available columns: {', '.join(columns)}"
                )
                return []
            
            # Search for records
            results = query_builder.search_records(table_name, column_name, search_value, operator='LIKE')
            formatted_results = query_builder.format_results(results, table_name)
            
            if formatted_results == "No records found.":
                dispatcher.utter_message(
                    text=f"No records found in '{table_name}' where '{column_name}' contains '{search_value}'."
                )
            else:
                response = f"Found {len(results)} record(s) in '{table_name}' where '{column_name}' contains '{search_value}':\n\n"
                for i, record in enumerate(formatted_results, 1):
                    response += f"Record {i}:\n"
                    for key, value in record.items():
                        response += f"  {key}: {value}\n"
                    response += "\n"
                
                dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionSearchRecords: {str(e)}")
            dispatcher.utter_message(text="I encountered an error while searching the database.")
        
        return []

class ActionCountRecords(Action):
    def name(self) -> Text:
        return "action_count_records"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        table_name = tracker.get_slot("table_name")
        
        if not table_name:
            # If no specific table, count all tables
            try:
                tables = db_config.get_table_names()
                response = "Record counts for all tables:\n\n"
                for table in tables:
                    count = query_builder.count_records(table)
                    response += f"📊 {table}: {count} records\n"
                
                dispatcher.utter_message(text=response)
                
            except Exception as e:
                logger.error(f"Error counting all tables: {str(e)}")
                dispatcher.utter_message(text="I encountered an error while counting records.")
        else:
            try:
                # Check if table exists
                available_tables = db_config.get_table_names()
                if table_name not in available_tables:
                    dispatcher.utter_message(
                        text=f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}"
                    )
                    return []
                
                count = query_builder.count_records(table_name)
                dispatcher.utter_message(text=f"Table '{table_name}' has {count} records.")
                
            except Exception as e:
                logger.error(f"Error counting records in {table_name}: {str(e)}")
                dispatcher.utter_message(text="I encountered an error while counting records.")
        
        return []

class ActionGetSpecificRecord(Action):
    def name(self) -> Text:
        return "action_get_specific_record"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        table_name = tracker.get_slot("table_name")
        record_id = tracker.get_slot("record_id")
        
        if not all([table_name, record_id]):
            dispatcher.utter_message(text="Please specify both the table name and record ID.")
            return []
        
        try:
            # Check if table exists
            available_tables = db_config.get_table_names()
            if table_name not in available_tables:
                dispatcher.utter_message(
                    text=f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}"
                )
                return []
            
            # Get the specific record
            results = query_builder.get_record_by_id(table_name, record_id)
            formatted_results = query_builder.format_results(results, table_name)
            
            if formatted_results == "No records found.":
                dispatcher.utter_message(text=f"No record found with ID '{record_id}' in table '{table_name}'.")
            else:
                record = formatted_results[0]
                response = f"Record with ID '{record_id}' from table '{table_name}':\n\n"
                for key, value in record.items():
                    response += f"  {key}: {value}\n"
                
                dispatcher.utter_message(text=response)
            
        except Exception as e:
            logger.error(f"Error in ActionGetSpecificRecord: {str(e)}")
            dispatcher.utter_message(text="I encountered an error while retrieving the record.")
        
        return []
