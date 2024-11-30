from uuid import uuid4
from time import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.db import get_redis, create_chat, chat_exists
from app.assistants.assistant import RAGAssistant

class ChatIn(BaseModel):
    message: str

# Get Redis db dependency
async def get_rdb():
    rdb = get_redis()
    try:
        yield rdb
    finally:
        await rdb.aclose()

# Create API router
router = APIRouter()

# Define API routes
# Create a new chat
@router.post('/chats')
async def create_new_chat(rdb = Depends(get_rdb)):
    chat_id = str(uuid4())[:8] # Generate a random chat ID: 8 characters
    created = int(time()) # Get current time in seconds
    
    await create_chat(rdb, chat_id, created)
    
    return {'id': chat_id}

# Chat with an existing chat, using chat_id as reference
@router.post('/chats/{chat_id}')
async def chat(chat_id: str, chat_in: ChatIn):
    rdb = get_redis()
    
    if not await chat_exists(rdb, chat_id):
        raise HTTPException(status_code=404, detail=f'Chat {chat_id} does not exist')
    
    # Create RAGAssistant object: 
    # chat_id is used to identify the chat
    # rdb is the Redis database
    assistant = RAGAssistant(chat_id=chat_id, rdb=rdb)
    
    # Run conversation step
    sse_stream = assistant.run(message=chat_in.message)
    
    return EventSourceResponse(sse_stream, background=rdb.aclose)