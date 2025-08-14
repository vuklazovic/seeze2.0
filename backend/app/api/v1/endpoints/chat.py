from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import chat as schemas
from app.services.chat_service import ChatService

router = APIRouter()

# Global singleton instance
chat_service = ChatService()


@router.post("/", response_model=schemas.ChatResponse)
def chat(request: schemas.UserQuery):
    """Process user query with LLM and function calling"""
    try:
        result = chat_service.process_user_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: schemas.UserQuery):
    """Process user query with LLM and function calling with streaming response"""
    try:
        def generate():
            for chunk in chat_service.process_user_query_stream(request.query):
                # Follow SSE standard: data: <content>
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))