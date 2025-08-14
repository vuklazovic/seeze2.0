# class ChatSession:
#     """Chat session to maintain conversation history"""
    
#     def __init__(self, system_prompt: Optional[str] = None):
#         self.messages: List[Message] = []
#         if system_prompt:
#             self.messages.append(Message(role="system", content=system_prompt))
    
#     def add_message(self, role: str, content: str, name: Optional[str] = None):
#         """Add a message to the conversation"""
#         self.messages.append(Message(role=role, content=content, name=name))
    
#     def add_user_message(self, content: str):
#         """Add a user message"""
#         self.add_message("user", content)
    
#     def add_assistant_message(self, content: str):
#         """Add an assistant message"""
#         self.add_message("assistant", content)
    
#     def add_function_message(self, name: str, content: str):
#         """Add a function message"""
#         self.add_message("function", content, name=name)
    
#     def get_messages(self) -> List[Message]:
#         """Get all messages in the conversation"""
#         return self.messages.copy()
    
#     def clear(self):
#         """Clear conversation history (keeping system prompt if exists)"""
#         system_messages = [msg for msg in self.messages if msg.role == "system"]
#         self.messages = system_messages