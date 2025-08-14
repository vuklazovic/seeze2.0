import json
import os
import time
from typing import Dict, List, Optional, Union, AsyncGenerator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from openai import OpenAI
from openai import APITimeoutError
import httpx
from app.core import settings
from app.schemas.llm import LLMType


@dataclass
class Message:
    role: str
    content: str

class BaseLLM(ABC):
    """Abstract base class for LLM implementations"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def _retry_with_reinit(self, operation_name: str, operation_func, *args, **kwargs):
        """Retry operation with reinitialization on connection errors"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
                
            except (APITimeoutError, httpx.PoolTimeout, httpx.ConnectError) as e:
                last_exception = e
                print(f"{operation_name} connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    print(f"Reinitializing LLM and retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    
                    # Reinitialize the LLM
                    self._reinitialize()
                    
                    # Increase delay for next retry
                    self.retry_delay *= 2
                else:
                    print(f"All retries failed for {operation_name}")
                    raise ConnectionError(f"LLM service unavailable after {self.max_retries} attempts: {e}")
                    
            except Exception as e:
                # For non-connection errors, don't retry
                print(f"Non-connection error in {operation_name}: {e}")
                raise
        
        # This should never be reached, but just in case
        raise last_exception
    
    def _reinitialize(self):
        """Reinitialize the LLM - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def generate(self, messages: List[Message], **kwargs) -> str:
        """Generate response from messages"""
        pass
    
    @abstractmethod
    def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response from messages"""
        pass
    
    @abstractmethod
    def generate_with_functions(self, messages: List[Message], functions: List[dict], **kwargs) -> Dict:
        """Generate response with function calling"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation"""
    
    def __init__(self, api_key: str, model: str):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        print(f"=== INITIALIZING OPENAI LLM - {self.model}  ====")
        self.client = OpenAI(api_key=self.api_key)
    
    def _reinitialize(self):
        """Reinitialize OpenAI client"""
        print(f"=== REINITIALIZING OPENAI LLM - {self.model}  ====")
        self.client = OpenAI(api_key=self.api_key)
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert Message objects to OpenAI format"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]
    
    def generate(self, messages: List[Message], **kwargs) -> str:
        def _generate():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                **kwargs
            )
            return response.choices[0].message.content
        
        return self._retry_with_reinit("generate", _generate)
    
    def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        def _generate_stream():
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        # For streaming, we need to handle retries differently
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                for chunk in _generate_stream():
                    yield chunk
                return  # Success, exit retry loop
                
            except (APITimeoutError, httpx.PoolTimeout, httpx.ConnectError) as e:
                last_exception = e
                print(f"generate_stream connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    print(f"Reinitializing LLM and retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    self._reinitialize()
                    self.retry_delay *= 2
                else:
                    print(f"All retries failed for generate_stream")
                    yield f"Error: OpenAI service unavailable after {self.max_retries} attempts - {e}"
                    return
                    
            except Exception as e:
                print(f"Non-connection error in generate_stream: {e}")
                yield f"Error: {e}"
                return
    
    def generate_with_functions(self, messages: List[Message], functions: List[dict], **kwargs) -> Dict:
        def _generate_with_functions():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                tools=functions,
                tool_choice="auto",
                **kwargs
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                # Parse arguments if they're a JSON string
                arguments_raw = message.tool_calls[0].function.arguments
                if isinstance(arguments_raw, str):
                    try:
                        arguments = json.loads(arguments_raw)
                    except json.JSONDecodeError:
                        arguments = {}
                else:
                    arguments = arguments_raw
                    
                function_call = {
                    "name": message.tool_calls[0].function.name,
                    "arguments": arguments
                }
            else:
                function_call = None
                
            return {
                "content": message.content,
                "function_call": function_call
            }
        
        return self._retry_with_reinit("generate_with_functions", _generate_with_functions)


class LocalLLM(BaseLLM):
    """Local LLM implementation"""
    
    def __init__(self, api_key: str, api_url: str, model: str):
        super().__init__()
        self.api_key = api_key
        self.api_base = api_url
        self.model = model
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Local LLM client"""
        print(f"=== INITIALIZING LOCAL LLM - {self.model}  ====")
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
    
    def _reinitialize(self):
        """Reinitialize Local LLM client"""
        print(f"=== REINITIALIZING LOCAL LLM - {self.model}  ====")
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert Message objects to local format"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

    def generate(self, messages: List[Message], **kwargs) -> str:
        def _generate():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                extra_body={
                    "repetition_penalty": 1.05,
                    "chat_template_kwargs": {"enable_thinking": False}  # default to True
                },
                **kwargs
            )
            return response.choices[0].message.content
        
        return self._retry_with_reinit("generate", _generate)
    
    def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        def _generate_stream():
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                stream=True,
                extra_body={
                    "repetition_penalty": 1.05,
                    "chat_template_kwargs": {"enable_thinking": False}  # default to True
                },
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        # For streaming, we need to handle retries differently
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                for chunk in _generate_stream():
                    yield chunk
                return  # Success, exit retry loop
                
            except (APITimeoutError, httpx.PoolTimeout, httpx.ConnectError) as e:
                last_exception = e
                print(f"generate_stream connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    print(f"Reinitializing LLM and retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    self._reinitialize()
                    self.retry_delay *= 2
                else:
                    print(f"All retries failed for generate_stream")
                    yield f"Error: Local LLM service unavailable after {self.max_retries} attempts - {e}"
                    return
                    
            except Exception as e:
                print(f"Non-connection error in generate_stream: {e}")
                yield f"Error: {e}"
                return
    
    def generate_with_functions(self, messages: List[Message], functions: List[dict], **kwargs) -> Dict:
        def _generate_with_functions():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._convert_messages(messages),
                tools=functions,
                extra_body={
                    "repetition_penalty": 1.05,
                    "chat_template_kwargs": {"enable_thinking": False}  # default to True
                },
                **kwargs
            )
            
            message = response.choices[0].message

            if message.tool_calls:
                # Parse arguments if they're a JSON string
                arguments_raw = message.tool_calls[0].function.arguments
                if isinstance(arguments_raw, str):
                    try:
                        arguments = json.loads(arguments_raw)
                    except json.JSONDecodeError:
                        arguments = {}
                else:
                    arguments = arguments_raw
                    
                function_call = {
                    "name": message.tool_calls[0].function.name,
                    "arguments": arguments
                }
            else:
                function_call = None

            return {
                "content": message.content,
                "function_call": function_call
            }
        
        return self._retry_with_reinit("generate_with_functions", _generate_with_functions)

class LLM:
    """Universal LLM class with chat functionality"""
    
    def __init__(self, llm_type: Optional[LLMType] = None):
        self.llm_type = llm_type
        self.llm_instance = None
        self.tools = {}
        self.system_prompts = {}
        
        self._load_configuration()
        self._load_jsons()
    
    def _load_configuration(self):
        """Load LLM configuration from environment"""
        if self.llm_type is None:
            # Auto-detect based on environment configuration
            if hasattr(settings, 'LLM_TYPE') and settings.LLM_TYPE:
                try:
                    self.llm_type = LLMType(settings.LLM_TYPE)
                except ValueError:
                    raise ValueError(f"Invalid LLM_TYPE in environment: {settings.LLM_TYPE}")
            else:
                # Default to OpenAI if no LLM_TYPE specified
                self.llm_type = LLMType.LOCAL
        
        # Initialize the appropriate LLM instance
        if self.llm_type == LLMType.OPENAI:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not found in environment")
            api_key = settings.OPENAI_API_KEY
            model = settings.OPENAI_MODEL_NAME
            self.llm_instance = OpenAILLM(api_key, model)
        
        elif self.llm_type == LLMType.LOCAL:
            # Load local LLM configuration from environment
            api_key = settings.LOCAL_LLM_API_KEY
            api_url = settings.LOCAL_LLM_URL
            model = settings.LOCAL_LLM_MODEL_NAME
            self.llm_instance = LocalLLM(api_key, api_url, model)
        
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
    
    def _load_jsons(self):
        """Load tools and system prompts from JSON files"""
        # Load tools JSON
        tools_path = os.path.join(os.path.dirname(__file__), "..", "data", "tools.json")
        if os.path.exists(tools_path):
            with open(tools_path, 'r', encoding='utf-8') as f:
                self.tools = json.load(f)
        
        # Load system prompts JSON
        prompts_path = os.path.join(os.path.dirname(__file__), "..", "data", "system_prompts.json")
        if os.path.exists(prompts_path):
            with open(prompts_path, 'r', encoding='utf-8') as f:
                self.system_prompts = json.load(f)
    
    def generate(self, messages: List[Message], **kwargs) -> str:
        """Generate response from messages"""
        return self.llm_instance.generate(messages, **kwargs)
    
    def generate_stream(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response from messages"""
        for chunk in self.llm_instance.generate_stream(messages, **kwargs):
            yield chunk
    
    def generate_with_functions(self, messages: List[Message], **kwargs) -> Dict:
        """Generate response with function calling"""
        return self.llm_instance.generate_with_functions(messages, self.tools, **kwargs)
    
    # Session functions
    # def create_chat_session(self, system_prompt: Optional[str] = None) -> ChatSession:
    #     """Create a new chat session"""
    #     return ChatSession(system_prompt)
    
    # def chat(self, session: ChatSession, user_message: str, **kwargs) -> str:
    #     """Chat with the user using a session"""
    #     session.add_user_message(user_message)
    #     response = self.generate(session.get_messages(), **kwargs)
    #     session.add_assistant_message(response)
    #     return response
    
    # def chat_stream(self, session: ChatSession, user_message: str, **kwargs) -> AsyncGenerator[str, None]:
    #     """Stream chat with the user using a session"""
    #     session.add_user_message(user_message)
    #     full_response = ""
    #     for chunk in self.generate_stream(session.get_messages(), **kwargs):
    #         full_response += chunk
    #         yield chunk
    #     session.add_assistant_message(full_response)
    
    # def chat_with_functions(self, session: ChatSession, user_message: str, functions: List[dict], **kwargs) -> Dict:
    #     """Chat with function calling"""
    #     session.add_user_message(user_message)
    #     result = self.generate_with_functions(session.get_messages(), functions, **kwargs)
        
    #     if result["function_call"]:
    #         # Add function call to session
    #         session.add_assistant_message("", function_call=result["function_call"])
    #     else:
    #         # Add regular response to session
    #         session.add_assistant_message(result["content"])
        
    #     return result
    
    # def get_tool(self, tool_name: str) -> Optional[Dict]:
    #     """Get tool configuration by name"""
    #     return self.tools.get(tool_name)
    
    # def get_system_prompt(self, prompt_name: str) -> Optional[str]:
    #     """Get system prompt by name"""
    #     return self.system_prompts.get(prompt_name)
    
    # def list_tools(self) -> List[str]:
    #     """List all available tools"""
    #     return list(self.tools.keys())
    
    # def list_system_prompts(self) -> List[str]:
    #     """List all available system prompts"""
    #     return list(self.system_prompts.keys())
