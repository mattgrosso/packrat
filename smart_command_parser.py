#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from database import WorkshopDatabase

class SmartCommandParser:
    def __init__(self, api_key: str = None, db_path: str = "workshop.db"):
        """
        Smart command parser that gives full database context to GPT-4
        
        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
            db_path: Path to workshop database
        """
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        self.db = WorkshopDatabase(db_path)
        
        # Define available functions for the LLM
        self.functions = [
            {
                "type": "function",
                "function": {
                    "name": "store_item",
                    "description": "Store or update an item's location in the workshop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {
                                "type": "string",
                                "description": "Name of the item to store"
                            },
                            "location": {
                                "type": "string", 
                                "description": "Where the item is stored"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description of the item"
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional category (e.g., 'tool', 'hardware', 'material')"
                            }
                        },
                        "required": ["item_name", "location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_item", 
                    "description": "Remove an item from the workshop inventory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {
                                "type": "string",
                                "description": "Name of the item to delete"
                            }
                        },
                        "required": ["item_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "respond_with_info",
                    "description": "Respond to the user with information about items, locations, or general queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "description": "The response to give to the user"
                            }
                        },
                        "required": ["response"]
                    }
                }
            }
        ]
        
        print("✅ Smart command parser initialized with full database context")
    
    def get_full_database_context(self) -> str:
        """Get the entire database as context for the LLM"""
        try:
            all_items = self.db.list_items()
            
            if not all_items:
                return "The workshop database is currently empty."
            
            # Format items for LLM context
            context_lines = [
                f"WORKSHOP INVENTORY ({len(all_items)} items):",
                "=" * 50
            ]
            
            # Group by category for better organization
            by_category = {}
            for item in all_items:
                category = item.get('category') or 'uncategorized'
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(item)
            
            for category, items in by_category.items():
                context_lines.append(f"\n{category.upper()}:")
                for item in items:
                    name = item['item_name']
                    location = item['location']
                    desc = f" - {item['description']}" if item['description'] else ""
                    context_lines.append(f"  • {name} → {location}{desc}")
            
            # Add location summary
            locations = {}
            for item in all_items:
                loc = item['location']
                if loc not in locations:
                    locations[loc] = []
                locations[loc].append(item['item_name'])
            
            if len(locations) > 1:
                context_lines.extend([
                    f"\nLOCATION SUMMARY:",
                    "-" * 20
                ])
                for location, items in locations.items():
                    items_str = ", ".join(items)
                    context_lines.append(f"  {location}: {items_str}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            return f"Error reading database: {e}"
    
    def execute_function(self, function_name: str, arguments: Dict) -> Dict:
        """Execute a database function and return results"""
        try:
            if function_name == "store_item":
                success = self.db.store_item(
                    item_name=arguments["item_name"],
                    location=arguments["location"],
                    description=arguments.get("description"),
                    category=arguments.get("category")
                )
                return {
                    "success": success,
                    "message": f"Stored {arguments['item_name']} in {arguments['location']}" if success 
                              else f"Failed to store {arguments['item_name']}"
                }
            
            elif function_name == "delete_item":
                success = self.db.delete_item(arguments["item_name"])
                return {
                    "success": success,
                    "message": f"Deleted {arguments['item_name']}" if success 
                              else f"Could not find {arguments['item_name']} to delete"
                }
            
            elif function_name == "respond_with_info":
                return {
                    "success": True,
                    "response": arguments["response"]
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing {function_name}: {str(e)}"
            }
    
    def parse_command(self, command_text: str) -> str:
        """
        Parse a voice command using GPT-4 with full database context
        
        Args:
            command_text: The transcribed voice command
            
        Returns:
            Response text to be spoken back to the user
        """
        try:
            # Get full database context
            db_context = self.get_full_database_context()
            
            # Create enhanced system message with full context
            system_message = f"""
You are a helpful workshop assistant. You help users store and find tools, hardware, and materials in their workshop.

Here is the COMPLETE current workshop inventory:

{db_context}

INSTRUCTIONS:
- For storage commands ("store X in Y", "put X in Y"), use store_item function
- For finding items ("where is X?", "find X"), use the database context above to answer
- For listing items ("what do I have?", "list tools"), use the database context above
- For questions about locations ("what's in the toolbox?"), use the database context above  
- For deleting items ("remove X", "delete X"), use delete_item function
- Be conversational and helpful - you can see EVERYTHING in the workshop
- If an item isn't found, suggest similar items that exist
- You can answer complex queries like "what cutting tools do I have?" or "where are all my screws?"

Use respond_with_info for any query that doesn't require storing/deleting items.

Keep responses brief and natural since they will be spoken aloud.
"""
            
            # Call OpenAI API with function calling
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": command_text}
                ],
                tools=self.functions,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if the model wants to call a function
            if message.tool_calls:
                # Execute the function
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Executing: {function_name}({function_args})")
                
                # Execute the function
                function_result = self.execute_function(function_name, function_args)
                
                # For respond_with_info, return the response directly
                if function_name == "respond_with_info":
                    return function_result["response"]
                
                # For store/delete operations, get a follow-up response
                follow_up_response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": command_text},
                        {"role": "assistant", "content": None, "tool_calls": message.tool_calls},
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(function_result)
                        }
                    ]
                )
                
                return follow_up_response.choices[0].message.content
            
            else:
                # No function call needed, return direct response
                return message.content
                
        except Exception as e:
            print(f"❌ Error parsing command: {e}")
            return "Sorry, I had trouble understanding that command. Could you try rephrasing it?"

def test_smart_parser():
    """Test smart command parser with various queries"""
    print("🧪 Testing Smart Command Parser")
    print("=" * 40)
    
    try:
        parser = SmartCommandParser()
    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test")
        return
    
    # Test commands that show the intelligence
    test_commands = [
        "Store hammer in toolbox drawer three",
        "I put screws in the parts bin",
        "Where is the hammer?",
        "What cutting tools do I have?",
        "What's in the toolbox?",
        "List all my tools",
        "Where did I put those screws?",
        "Do I have any Phillips head screwdrivers?",
        "What's the biggest tool in my workshop?"
    ]
    
    for command in test_commands:
        print(f"\n💬 Command: '{command}'")
        response = parser.parse_command(command)
        print(f"🤖 Response: {response}")
        print("-" * 30)

if __name__ == "__main__":
    test_smart_parser()