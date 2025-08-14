from typing import Dict, Any, AsyncGenerator, Tuple, Optional
import json
from app.services.llm_service import LLMService


class ChatService:
    """Main service for handling chat interactions - Singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.llm_service = LLMService()
            self._initialized = True
    
    def _process_llm_and_parse_function(self, user_query: str) -> Tuple[Dict[str, Any], Optional[str], Optional[Dict[str, Any]]]:
        """Common logic for processing LLM response and parsing function calls"""
        # Step 1: Process query with LLM and function calling
        llm_response = self.llm_service.process_query_with_functions(user_query)

        # Step 2: Check if LLM wants to call a function
        if llm_response.get("function_call"):
            function_call = llm_response["function_call"]
            function_name = function_call.get("name")
            arguments_raw = function_call.get("arguments", {})
            
            # Parse arguments if they're a JSON string
            if isinstance(arguments_raw, str):
                try:
                    arguments = json.loads(arguments_raw)
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = arguments_raw
            
            return llm_response, function_name, arguments
        else:
            return llm_response, None, None
    
    def process_user_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query through the complete pipeline"""
        try:
            llm_response, function_name, arguments = self._process_llm_and_parse_function(user_query)
            
            if function_name:
                # Step 3: Execute the function
                function_result = self.llm_service.execute_function(function_name, arguments)
                
                # Step 4: Return the complete response
                return {
                    "success": True,
                    "user_query": user_query,
                    "llm_response": llm_response,
                    "function_executed": {
                        "name": function_name,
                        "arguments": arguments,
                        "result": function_result
                    }
                }
            else:
                # No function call, just return LLM response
                return {
                    "success": True,
                    "user_query": user_query,
                    "llm_response": llm_response,
                    "function_executed": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_query": user_query
            }
    
    def process_user_query_stream(self, user_query: str) -> AsyncGenerator[str, None]:
        """Process user query with streaming response"""
        try:
            llm_response, function_name, arguments = self._process_llm_and_parse_function(user_query)
            
            if function_name:
                # Step 3: Execute the function with streaming if supported
                if self.llm_service.is_streaming_function(function_name):
                    # Stream LLM response directly for streaming functions
                    for chunk in self.llm_service.execute_function_stream(function_name, arguments):
                        yield chunk
                else:
                    # For non-streaming functions, return the result as JSON
                    function_result = self.llm_service.execute_function(function_name, arguments)
                    yield json.dumps({
                        "success": True,
                        "function_name": function_name,
                        "result": function_result
                    })
            else:
                # No function call, return LLM response as plain text
                content = llm_response.get("content", "")
                if content:
                    yield content
                else:
                    yield "No response generated."
                
        except Exception as e:
            yield f"Error: {str(e)}"