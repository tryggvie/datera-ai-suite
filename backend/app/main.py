import os
import json
import uuid
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()  # Fallback to .env

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Assistant Suite Backend", version="1.0.0")

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
# Add localhost for testing
allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = "dummy-key-for-testing"
    logger.warning("No OPENAI_API_KEY found, using dummy key for testing")

client = openai.OpenAI(api_key=api_key)

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    bot_id: str = "general"
    model: str = "gpt-5"
    verbosity: str = "medium"  # low, medium, high
    reasoning_effort: str = "medium"  # minimal, medium, high

class HealthResponse(BaseModel):
    status: str
    api: str = "gpt-5-responses"

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
    """Chat endpoint using GPT-5 Response API"""
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
        # Prepare messages for OpenAI Response API
        if len(request.messages) == 1:
            # Single message - use as input string
            input_data = request.messages[0].content
        else:
            # Multiple messages - use as input array
            input_data = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Prepare Response API parameters
        response_params = {
            "model": request.model,
            "input": input_data,
            "text": {
                "verbosity": request.verbosity
            },
            "reasoning": {
                "effort": request.reasoning_effort
            }
        }
        
        logger.info(f"Request {request_id}: Processing chat with GPT-5 Response API, verbosity: {request.verbosity}")
        
        # Create streaming response (simulated since Response API doesn't support streaming yet)
        async def generate_response():
            try:
                # Make the API call - try Response API first, fallback to Chat Completions
                try:
                    response = client.responses.create(**response_params)
                except AttributeError:
                    # Fallback to Chat Completions API if Response API not available
                    logger.warning("Response API not available, falling back to Chat Completions")
                    response = client.chat.completions.create(
                        model=request.model,
                        messages=openai_messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    )
                    # Convert to Response API format for consistency
                    class MockResponse:
                        def __init__(self, chat_response):
                            self.output_text = chat_response.choices[0].message.content
                            self.output = [type('obj', (object,), {'content': [type('obj', (object,), {'text': self.output_text})]})()]
                            self.model = chat_response.model
                            self.usage = chat_response.usage
                    response = MockResponse(response)
                
                # Extract the output text
                output_text = ""
                reasoning_summary = None
                
                for item in response.output:
                    if hasattr(item, "content"):
                        for content in item.content:
                            if hasattr(content, "text"):
                                output_text += content.text
                    elif hasattr(item, "summary") and item.summary:
                        reasoning_summary = item.summary[0].text if item.summary else None
                
                # Simulate streaming by sending chunks
                chunk_size = 50
                for i in range(0, len(output_text), chunk_size):
                    chunk = output_text[i:i + chunk_size]
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
                # Send reasoning summary if available
                if reasoning_summary:
                    yield f"data: {json.dumps({'reasoning_summary': reasoning_summary})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Request {request_id}: OpenAI Response API error: {str(e)}")
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