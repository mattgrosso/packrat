#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from database import WorkshopDatabase

class CommandParser:
    def __init__(self, api_key: str = None, db_path: str = "workshop.db"):
        """
        Initialize command parser with OpenAI API and database
        
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
                                "description": "Where the item is stored (e.g., 'toolbox drawer 3', 'pegboard', 'shelf A')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description of the item"
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional category (e.g., 'tool', 'hardware', 'material', 'fastener')"
                            }
                        },
                        "required": ["item_name", "location"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "find_item",
                    "description": "Find where an item is stored in the workshop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {
                                "type": "string",
                                "description": "Name of the item to find"
                            }
                        },
                        "required": ["item_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_items",
                    "description": "List items in the workshop, optionally filtered by category or location",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by category (e.g., 'tool', 'hardware')"
                            },
                            "location": {
                                "type": "string",
                                "description": "Filter by location (e.g., 'toolbox', 'pegboard')"
                            }
                        },
                        "required": []
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
            }
        ]
        
        print("✅ Command parser initialized with OpenAI API")
    
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
            
            elif function_name == "find_item":
                item = self.db.find_item(arguments["item_name"])
                if item:
                    return {
                        "success": True,
                        "item": item,
                        "message": f"Found {item['item_name']} in {item['location']}"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I don't have any record of {arguments['item_name']}"
                    }
            
            elif function_name == "list_items":
                items = self.db.list_items(
                    category=arguments.get("category"),
                    location=arguments.get("location")
                )
                return {
                    "success": True,
                    "items": items,
                    "count": len(items),
                    "message": f"Found {len(items)} items"
                }
            
            elif function_name == "delete_item":
                success = self.db.delete_item(arguments["item_name"])
                return {
                    "success": success,
                    "message": f"Deleted {arguments['item_name']}" if success 
                              else f"Could not find {arguments['item_name']} to delete"
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
        Parse a voice command using OpenAI API with function calling
        
        Args:
            command_text: The transcribed voice command
            
        Returns:
            Response text to be spoken back to the user
        """
        try:
            # Create system message for workshop context
            system_message = """
            You are a helpful workshop assistant. Users can tell you where they store tools and hardware, 
            and you can help them find items later. 
            
            Use the provided functions to store, find, list, or delete items from the workshop inventory.
            
            Be conversational and helpful in your responses. Examples:
            - "Got it, I've stored the hammer in toolbox drawer three"
            - "The screwdriver is in the pegboard"
            - "I don't have any record of that item. Would you like to store it somewhere?"
            - "I found 5 tools in your inventory"
            
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
                
                # Get the final response from the model
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
    
    def get_helpful_responses(self) -> Dict[str, str]:
        """Get template responses for common scenarios"""
        return {
            "wake_word_detected": "Yes?",
            "no_audio": "I didn't hear anything. Try again.",
            "unclear_audio": "I couldn't understand that. Please repeat.",
            "error": "Sorry, I had a problem processing that. Please try again.",
            "goodbye": "Goodbye! Let me know if you need help finding anything."
        }

def test_command_parser():
    """Test command parser functionality"""
    print("🧪 Testing Command Parser")
    print("=" * 30)
    
    # Test without API key first
    try:
        parser = CommandParser()
    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test with real API")
        return
    
    # Test commands
    test_commands = [
        "Store hammer in toolbox drawer three",
        "I put the screwdriver on the pegboard", 
        "Where is the hammer?",
        "Find my screwdriver",
        "List all tools",
        "What do I have?"
    ]
    
    for command in test_commands:
        print(f"\n💬 Command: '{command}'")
        response = parser.parse_command(command)
        print(f"🤖 Response: {response}")

if __name__ == "__main__":
    test_command_parser()