import os
import json
import uuid
import time
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    bot_id: str = "general"

class HealthResponse(BaseModel):
    status: str

# Bot configuration (in production, this would come from a database)
ENABLED_BOTS = {"general"}

def verify_gateway_token(request: Request):
    """Verify the gateway token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    expected_token = os.getenv("GATEWAY_TOKEN")
    
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid gateway token")
    
    return token

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")

@app.post("/v1/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_gateway_token)
):
    """Chat endpoint with streaming OpenAI responses"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Validate bot_id
    if request.bot_id not in ENABLED_BOTS:
        logger.warning(f"Request {request_id}: Disabled bot_id '{request.bot_id}' requested")
        raise HTTPException(
            status_code=501, 
            detail=f"Bot '{request.bot_id}' is not available yet"
        )
    
    try:
        # Prepare messages for OpenAI
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        logger.info(f"Request {request_id}: Processing chat with {len(openai_messages)} messages")
        
        # Create streaming response
        async def generate_response():
            try:
                stream = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=openai_messages,
                    stream=True,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Request {request_id}: OpenAI error: {str(e)}")
                yield f"data: {json.dumps({'error': 'Service temporarily unavailable'})}\n\n"
        
        # Log request completion
        latency = time.time() - start_time
        logger.info(f"Request {request_id}: Completed in {latency:.2f}s")
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request {request_id}: Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
