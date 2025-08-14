from typing import Dict, Optional, List, AsyncGenerator, Any
import logging
import json
from app.classes.llm import Message, LLM
from app.core import llm_instance, mongodb_instance
from app.schemas.llm import LLMType
from app.services.dto_service import DTOService

logger = logging.getLogger(__name__)


class LLMService:
    """Unified service for LLM interactions and function execution - Singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.llm_instance = llm_instance
            self.mongodb_instance = mongodb_instance
            
            # Function registry
            self.available_functions = {
                "get_car_deals": self._get_car_deals,
                "car_info": self._car_info,
                "evaluate": self._evaluate,
                "general_knowledge": self._general_knowledge,
                "car_comparison": self._car_comparison,
                "analyze_url": self._analyze_url
            }
            self.available_functions_for_streaming = [
                "car_info", "evaluate", "general_knowledge", "car_comparison", "analyze_url"
            ]
            
            self._initialized = True
    
    # ==================== Core LLM Operations ====================
    
    def process_query_with_functions(self, user_query: str) -> Dict:
        """Process user query with LLM and function calling"""
        try:
            messages = [Message(role='user', content=user_query)]
            
            # Get system prompt for deal finder
            system_prompt = """
                You are an intelligent assistant designed to extract structured filters for car search based on user input.
                
                When a user asks for car deals using natural language — including descriptive phrases such as "family SUV", "muscle car", or "offroad vehicle" — your goal is to translate their intent into accurate structured parameters by calling tools with relevant arguments only.
                
                Important guidelines:
                
                - Use tool calls to extract and return structured filters, not to suggest specific car models directly.
                - If the user provides vague or descriptive terms, focus on identifying relevant features (e.g., body style, drivetrain, number of seats) rather than inferring specific makes or models.
                - Do NOT hallucinate or invent any parameters. Only include fields in the tool call if they are explicitly mentioned or can be reasonably inferred from user language.
                - Do NOT add extra filters (e.g., price, mileage, color, year, or location) unless the user clearly specifies them or implies them through well-known phrases.
                - Your primary task is structured interpretation — extract what is needed for filtering, and avoid open-ended recommendations or subjective advice.
                
                Always prioritize precision and minimize assumptions.
            """
            if system_prompt:
                messages.insert(0, Message(role='system', content=system_prompt))
            
            # Generate response with function calling
            response = self.llm_instance.generate_with_functions(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error in process_query_with_functions: {e}")
            raise
    
    # Not used but it's good to have
    # def process_query(self, user_query: str) -> str:
    #     """Process user query without function calling"""
    #     try:
    #         messages = [Message(role='user', content=user_query)]
    #         response = self.llm_instance.generate(messages)
    #         return response
            
    #     except Exception as e:
    #         logger.error(f"Error in process_query: {e}")
    #         raise
    
    # Not used but it's good to have
    # def process_query_stream(self, user_query: str) -> AsyncGenerator[str, None]:
    #     """Process user query with streaming response"""
    #     try:
    #         messages = [Message(role='user', content=user_query)]
            
    #         # Get system prompt for deal finder
    #         system_prompt = self.llm_instance.system_prompts.get("seeze_prompt")
    #         if system_prompt:
    #             messages.insert(0, Message(role='system', content=system_prompt))
            
    #         # Generate streaming response
    #         for chunk in self.llm_instance.generate_stream(messages):
    #             yield chunk
                
    #     except Exception as e:
    #         logger.error(f"Error in process_query_stream: {e}")
    #         yield f"Error: {str(e)}"
    
    # ==================== Function Execution ====================
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function by name with given arguments - /chat/ route"""
        if function_name not in self.available_functions:
            return {
                "error": f"Function {function_name} not found",
                "available_functions": list(self.available_functions.keys())
            }
        
        try:
            result = self.available_functions[function_name](arguments)
            return {
                "success": True,
                "result": result,
                "function_name": function_name
            }
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name
            }
    
    def execute_function_stream(self, function_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Execute a function by name with given arguments but with streaming response - /chat/stream route"""
        if function_name in self.available_functions_for_streaming:
            try:
                for chunk in self.available_functions[function_name](arguments, True):
                    yield chunk
            except Exception as e:
                logger.error(f"Error executing streaming function {function_name}: {e}")
                yield f"Error: {str(e)}"
        else:
            result = self.execute_function(function_name, arguments)
            yield json.dumps(result)
    
    # ==================== Function Definitions ====================
    
    def _get_car_deals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_car_deals function"""
        cars_filter = arguments.get("cars", [])
        
        try:
            # Convert LLM filter to MongoDB filter
            mongo_cars_filter = self.mongodb_instance.convert_filter_to_mongo(cars_filter)

            # Hardcoded
            if mongo_cars_filter:
                # Flatten nested $and operators to avoid double nesting
                if "$and" in mongo_cars_filter:
                    # If the filter already has $and, merge the conditions
                    mongo_cars_filter["$and"].append({"potential_profit_percentage": {'$lt': 30, '$gt': -30}})
                else:
                    # If it's a simple filter, wrap it in $and
                    mongo_cars_filter = {
                        "$and": [
                            mongo_cars_filter,
                            {"potential_profit_percentage": {'$lt': 30, '$gt': -30}}
                        ]
                    }
            print("mongo_cars_filter: ", mongo_cars_filter)
            # Execute query
            raw_cars = self.mongodb_instance.execute_query(mongo_cars_filter, limit=150)
            # raw_cars = []
            
            # Convert to DTO format
            car_deals_dto = DTOService.convert_cars_to_dto_response(raw_cars=raw_cars)
            
            return {
                "mongo_cars_filter": mongo_cars_filter,
                "cars_found": len(raw_cars),
                "cars": car_deals_dto.dict()
            }
        except Exception as e:
            logger.error(f"Error in get_car_deals: {e}")
            car_deals_dto = DTOService.convert_cars_to_dto_response(
                raw_cars=[],
                error=str(e)
            )
            return {
                "mongo_cars_filter": mongo_cars_filter,
                "filter_from_llm": cars_filter,
                "error": str(e),
                "cars": car_deals_dto.dict()
            }
    
    def _car_info(self, arguments: Dict[str, Any], stream: bool = False) -> str | AsyncGenerator[str, None]:
        """Execute car_info function"""
        query = arguments.get("query", "")

        # Get system prompt for car info
        system_prompt = self.llm_instance.system_prompts.get("car_info_prompt", "")

        # Create messages using Message schema
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=query))

        if stream:
            return self.llm_instance.generate_stream(messages)
        else:
            return self.llm_instance.generate(messages)
    
    def _evaluate(self, arguments: Dict[str, Any], stream: bool = False) -> str | AsyncGenerator[str, None]:
        """Execute evaluate function"""
        # Extract required parameters
        make = arguments.get("make")
        model = arguments.get("model")
        year = arguments.get("year")
        mileage = arguments.get("mileage")
        trim = arguments.get("trim")
        
        # Check if required parameters are provided
        if not all([make, model, year, mileage]):
            return "To perform a car evaluation, please provide the make, model, year, and mileage."
        
        # Build the evaluation query
        evaluation_query = f"Please evaluate a {year} {make} {model}"
        if trim:
            evaluation_query += f" {trim}"
        evaluation_query += f" with {mileage:,} miles."
        
        # Get system prompt for evaluation
        system_prompt = self.llm_instance.system_prompts.get("evaluation_prompt", "")
        
        # Create messages using Message schema
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=evaluation_query))

        if stream:
            return self.llm_instance.generate_stream(messages)
        else:
            return self.llm_instance.generate(messages)
    
    def _general_knowledge(self, arguments: Dict[str, Any], stream: bool = False) -> str | AsyncGenerator[str, None]:
        """Execute general_knowledge function"""
        query = arguments.get("query", "")

        # Get system prompt for general knowledge
        system_prompt = self.llm_instance.system_prompts.get("general_knowledge_prompt", "")

        # Create messages using Message schema
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=query))

        if stream:
            return self.llm_instance.generate_stream(messages)
        else:
            return self.llm_instance.generate(messages)
    
    def _car_comparison(self, arguments: Dict[str, Any], stream: bool = False) -> str | AsyncGenerator[str, None]:
        """Execute car_comparison function"""
        query = arguments.get("query", "")
        car_info_list = arguments.get("cars", [])

        # Get system prompt for car comparison
        system_prompt = self.llm_instance.system_prompts.get("car_comparison_prompt", "")
        
        # Format the car info list as JSON string for the prompt
        car_info_json = json.dumps(car_info_list, indent=2)
        
        # Replace the placeholder in the system prompt with actual car data
        formatted_system_prompt = system_prompt.replace("{car_info_list}", car_info_json)

        # Create messages using Message schema
        messages = []
        if formatted_system_prompt:
            messages.append(Message(role="system", content=formatted_system_prompt))
        messages.append(Message(role="user", content=query))

        if stream:
            return self.llm_instance.generate_stream(messages)
        else:
            return self.llm_instance.generate(messages)
    
    def _analyze_url(self, arguments: Dict[str, Any], stream: bool = False) -> str | AsyncGenerator[str, None]:
        """Execute analyze_url function"""
        provided_link = arguments.get("provided_link", "")
        query = arguments.get("query", "")

        # For now, just return the provided link and query as requested
        response = f"URL to analyze: {provided_link}\nQuery: {query}"
        
        if stream:
            return response
        else:
            return response
    
    # ==================== Utility Methods ====================
    
    def get_available_functions(self) -> List[str]:
        """Get list of available functions"""
        return list(self.available_functions.keys())
    
    def get_streaming_functions(self) -> List[str]:
        """Get list of functions that support streaming"""
        return self.available_functions_for_streaming.copy()
    
    def is_function_available(self, function_name: str) -> bool:
        """Check if a function is available"""
        return function_name in self.available_functions
    
    def is_streaming_function(self, function_name: str) -> bool:
        """Check if a function supports streaming"""
        return function_name in self.available_functions_for_streaming