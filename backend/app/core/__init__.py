# Core package
from .config import settings

# Initialize LLM globally
from app.classes.llm import LLM
from app.schemas.llm import LLMType
# Global LLM instance
llm_instance = LLM(llm_type=LLMType.LOCAL) # LOCAL | OPENAI 

# Initialize MongoDB globally
from app.classes.mongodb import MongoDB
# Global MongoDB instance
mongodb_instance = MongoDB()

# Initialize Chat globally
from app.services.chat_service import ChatService
# Global ChatService instance
chat_service = ChatService()