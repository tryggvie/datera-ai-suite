import os
import json
import uuid
import time
import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
# httpx import removed - no longer needed for image uploads

# Load environment variables
load_dotenv(".env.local")
load_dotenv()  # Fallback to .env

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info(f"Starting AI Assistant Suite Backend - Log Level: {log_level}")
logger.info(f"OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
logger.info(f"Gateway Token configured: {'Yes' if os.getenv('GATEWAY_TOKEN') else 'No'}")
logger.info(f"Allowed Origins: {os.getenv('ALLOWED_ORIGINS', 'Not set')}")

# Persona system
persona_cache: Dict[str, Dict[str, Any]] = {}

def load_personas():
    """Load persona registry and instructions files into memory"""
    global persona_cache
    persona_cache.clear()
    
    try:
        # Load persona registry - try multiple possible paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "config", "personas.registry.json"),
            os.path.join(os.getcwd(), "config", "personas.registry.json"),
            os.path.join(os.getcwd(), "backend", "config", "personas.registry.json"),
            "config/personas.registry.json",
            "backend/config/personas.registry.json"
        ]
        
        registry_path = None
        for path in possible_paths:
            if os.path.exists(path):
                registry_path = path
                break
        
        if not registry_path:
            logger.error(f"Persona registry not found in any of these locations: {possible_paths}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"__file__ location: {__file__}")
            logger.error(f"Directory listing: {os.listdir('.')}")
            raise FileNotFoundError(f"Persona registry not found in any of these locations: {possible_paths}")
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        logger.info(f"Loading {len(registry['personas'])} personas from registry")
        
        for persona in registry['personas']:
            persona_id = persona['id']
            
            # Load instructions file - try multiple possible paths
            possible_instruction_paths = [
                os.path.join(os.path.dirname(__file__), "..", persona['instructions_path']),
                os.path.join(os.getcwd(), persona['instructions_path']),
                os.path.join(os.getcwd(), "backend", persona['instructions_path']),
                persona['instructions_path']
            ]
            
            instructions_path = None
            for path in possible_instruction_paths:
                if os.path.exists(path):
                    instructions_path = path
                    break
            
            if not instructions_path:
                raise FileNotFoundError(f"Instructions file not found for persona '{persona_id}' in any of these locations: {possible_instruction_paths}")
            try:
                with open(instructions_path, 'r', encoding='utf-8') as f:
                    instructions_text = f.read()
                
                # Compute SHA256 hash
                instructions_sha256 = hashlib.sha256(instructions_text.encode('utf-8')).hexdigest()
                
                # Store in cache
                persona_cache[persona_id] = {
                    'text': instructions_text,
                    'sha256': instructions_sha256,
                    **persona  # Include all registry fields
                }
                
                logger.info(f"Loaded persona '{persona_id}' (v{persona['version']}) - SHA256: {instructions_sha256[:8]}...")
                
            except FileNotFoundError:
                logger.error(f"Instructions file not found for persona '{persona_id}': {instructions_path}")
            except Exception as e:
                logger.error(f"Error loading persona '{persona_id}': {str(e)}")
        
        logger.info(f"Successfully loaded {len(persona_cache)} personas")
        
    except FileNotFoundError:
        logger.error("Persona registry not found, no personas loaded")
    except Exception as e:
        logger.error(f"Error loading persona registry: {str(e)}")

# Load personas on startup
load_personas()

# Initialize FastAPI app
app = FastAPI(title="AI Assistant Suite Backend", version="1.0.0")

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
# Add localhost for testing
allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3002", "http://127.0.0.1:3002"])
# Add production subdomain
allowed_origins.extend(["https://ai.datera.is"])

# Add Vercel pattern matching for dynamic URLs
import re
def is_allowed_origin(origin: str) -> bool:
    if not origin:
        return False
    
    # Check exact matches first
    if origin in [o.strip() for o in allowed_origins if o.strip()]:
        return True
    
    # Check Vercel pattern: https://datera-ai-suite-*.vercel.app
    vercel_pattern = r'^https://datera-ai-suite-[a-zA-Z0-9]+-datera\.vercel\.app$'
    if re.match(vercel_pattern, origin):
        return True
    
    return False

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://datera-ai-suite-.*\.vercel\.app",
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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
    bot_id: str  # Required field
    model: str = "gpt-5"
    verbosity: str = "medium"  # low, medium, high
    reasoning_effort: str = "medium"  # minimal, medium, high
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    format_mode: Optional[str] = None  # "brief" for concise responses
    previous_response_id: Optional[str] = None  # For Responses API conversation state
    image_url: Optional[str] = None  # Optional single image URL for backward compatibility
    image_urls: Optional[List[str]] = None  # Optional array of image URLs for multiple images

class HealthResponse(BaseModel):
    status: str
    api: str = "gpt-5-responses"

class PasscodeRequest(BaseModel):
    passcode: str

class PasscodeResponse(BaseModel):
    valid: bool
    message: str

# ImageUploadResponse model removed - frontend now uploads directly to Vercel Blob

# Bot configuration is now handled by persona system

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

@app.get("/logs")
async def get_logs(lines: int = 50):
    """Get recent logs for debugging"""
    try:
        with open('app.log', 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {"logs": recent_lines, "total_lines": len(all_lines)}
    except FileNotFoundError:
        return {"logs": ["No log file found"], "total_lines": 0}
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return {"error": str(e)}

@app.post("/api/auth/verify", response_model=PasscodeResponse)
async def verify_passcode(request: PasscodeRequest):
    """Verify passcode for frontend authentication"""
    # Get the expected passcode from environment variable
    expected_passcode = os.getenv("FRONTEND_PASSCODE", "datera2024")
    
    if request.passcode == expected_passcode:
        logger.info("Passcode verification successful")
        return PasscodeResponse(valid=True, message="Authentication successful")
    else:
        logger.warning(f"Invalid passcode attempt: {request.passcode[:3]}...")
        return PasscodeResponse(valid=False, message="Invalid passcode")

# Image upload endpoint removed - frontend now uploads directly to Vercel Blob

@app.post("/admin/reload-personas")
async def reload_personas(token: str = Depends(verify_gateway_token)):
    """Hot-reload personas from registry and instructions files"""
    try:
        load_personas()
        return {
            "status": "success",
            "message": f"Reloaded {len(persona_cache)} personas",
            "personas": list(persona_cache.keys())
        }
    except Exception as e:
        logger.error(f"Error reloading personas: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/v1/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_gateway_token)
):
    """Chat endpoint using GPT-5 Response API with persona support"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Debug: Log the incoming request
    logger.info(f"Request {request_id}: Received request - bot_id: {request.bot_id}, image_url: {request.image_url}, image_urls: {request.image_urls}, messages count: {len(request.messages) if request.messages else 0}")
    logger.info(f"Request {request_id}: Raw incoming request body: {request.dict()}")
    
    # Validate bot_id and get persona
    if request.bot_id not in persona_cache:
        logger.warning(f"Request {request_id}: Unknown bot_id '{request.bot_id}' requested")
        raise HTTPException(
            status_code=404, 
            detail=f"Bot '{request.bot_id}' not found"
        )
    
    persona = persona_cache[request.bot_id]
    
    # Check if persona is enabled
    if not persona.get('enabled', False):
        logger.warning(f"Request {request_id}: Disabled bot_id '{request.bot_id}' requested")
        raise HTTPException(
            status_code=501, 
            detail="Bot not enabled"
        )
    
    try:
        logger.info(f"Request {request_id}: Starting persona processing for bot_id: {request.bot_id}")
        
        # Prepare input for OpenAI Response API
        # For Responses API, we need to modify the latest user message to include images
        # and pass the full conversation context
        
        # Get the latest user message
        latest_message = request.messages[-1] if request.messages else None
        if not latest_message:
            input_data = ""
        else:
            # Start with the conversation messages
            input_data = request.messages.copy()
            
            # If we have images, modify the latest user message to include them
            images_to_process = []
            if request.image_urls and len(request.image_urls) > 0:
                images_to_process = request.image_urls
            elif request.image_url:
                images_to_process = [request.image_url]
            
            if images_to_process:
                # Create multimodal content for the latest user message
                if len(images_to_process) == 1:
                    image_prompt = f"I have provided 1 image for you to analyze. Please examine it and respond to my question: {latest_message.content}"
                else:
                    image_prompt = f"I have provided {len(images_to_process)} images for you to analyze. Please examine ALL of them and respond to my question: {latest_message.content}. When referring to specific images, please number them (e.g., 'In the first image...', 'In the second image...', etc.)."
                
                content = [{"type": "input_text", "text": image_prompt}]
                
                # Add all images to the content
                for image_url in images_to_process:
                    content.append({"type": "input_image", "image_url": image_url})
                
                # Replace the latest message with multimodal content
                input_data[-1] = {
                    "role": "user",
                    "content": content
                }
                
                logger.info(f"Request {request_id}: Input data prepared with {len(images_to_process)} images, text length: {len(latest_message.content)}")
                logger.info(f"Request {request_id}: Image URLs: {images_to_process}")
                logger.info(f"Request {request_id}: Full input data: {input_data}")
            else:
                # Text-only input
                logger.info(f"Request {request_id}: Input data prepared, length: {len(str(input_data))}")
        
        # Add format mode instruction if requested
        if request.format_mode == "brief":
            if isinstance(input_data, str):
                input_data = f"For this answer only, keep to concise bullets (≤100 words).\n\n{input_data}"
            else:
                # Add system message for brief mode
                input_data.insert(0, {"role": "system", "content": "For this answer only, keep to concise bullets (≤100 words)."})
        
        # Use persona model and settings
        model_to_use = persona.get('model', request.model)
        fallback_model = persona.get('fallback_model', 'gpt-4o')
        # Prioritize request temperature over persona temperature for mode switching
        # Ensure temperature is always a valid float between 0 and 2
        if request.temperature is not None and request.temperature > 0:
            temperature = request.temperature
        else:
            temperature = persona.get('temperature', 0.7)
        
        # Ensure temperature is within valid range
        temperature = max(0.0, min(2.0, temperature))
        max_tokens = persona.get('max_output_tokens', request.max_tokens)
        
        # Initialize model_to_use for error handling
        final_model_used = model_to_use
        
        logger.info(f"Request {request_id}: Processing chat with persona '{request.bot_id}' (v{persona['version']}) using model {model_to_use}, temperature: {temperature}, verbosity: {request.verbosity}")
        
        # Prepare Response API parameters with persona instructions
        response_params = {
            "model": model_to_use,
            "input": input_data,
            "instructions": persona['text'],  # Full markdown content from persona instructions
            "tools": [{"type": "web_search"}],  # Enable web search
            "store": True,  # Store response for conversation state management
            "text": {
                "verbosity": request.verbosity
            },
            "metadata": {
                "persona_id": request.bot_id,
                "persona_version": persona['version']
            }
        }
        
        # Only add reasoning parameters for models that support them (like gpt-5)
        if model_to_use == "gpt-5":
            response_params["reasoning"] = {
                "effort": request.reasoning_effort
            }
        
        # Add previous_response_id for conversation state management
        if request.previous_response_id:
            response_params["previous_response_id"] = request.previous_response_id
        
        # Add temperature if specified and valid
        if temperature is not None and temperature > 0:
            response_params["temperature"] = temperature
            logger.info(f"Request {request_id}: Added temperature {temperature} to response_params")
        
        # Create streaming response (simulated since Response API doesn't support streaming yet)
        async def generate_response():
            nonlocal final_model_used
            # Use the variables from the outer scope
            current_model = model_to_use
            current_fallback = fallback_model
            current_temperature = temperature
            current_max_tokens = max_tokens
            try:
                # Make the API call - try Response API with primary model first
                logger.info(f"Request {request_id}: About to call OpenAI with params: {response_params}")
                logger.info(f"Request {request_id}: Full input data being sent to OpenAI: {input_data}")
                try:
                    response = client.responses.create(**response_params)
                    final_model_used = current_model
                except (AttributeError, Exception) as e:
                    # Try fallback model within Responses API if primary model fails
                    if current_model != current_fallback:
                        logger.warning(f"Primary model {current_model} failed ({str(e)}), trying fallback model {current_fallback} within Responses API")
                        try:
                            fallback_params = response_params.copy()
                            fallback_params["model"] = current_fallback
                            # Remove reasoning parameters for fallback model if it doesn't support them
                            if current_fallback != "gpt-5" and "reasoning" in fallback_params:
                                del fallback_params["reasoning"]
                            response = client.responses.create(**fallback_params)
                            current_model = current_fallback  # Update for logging
                            final_model_used = current_fallback  # Update final model
                            logger.info(f"Successfully used fallback model {current_fallback} within Responses API")
                        except Exception as e2:
                            logger.error(f"Both primary model {current_model} and fallback model {current_fallback} failed in Responses API: {str(e2)}")
                            raise e2
                    else:
                        logger.error(f"Responses API failed for {current_model} and no fallback model available: {str(e)}")
                        raise e
                
                # Extract the output text
                output_text = ""
                reasoning_summary = None
                
                # Debug: Log response structure
                logger.debug(f"Request {request_id}: Response type: {type(response)}")
                logger.debug(f"Request {request_id}: Response attributes: {dir(response)}")
                
                # Handle both Response API and MockResponse formats
                if hasattr(response, 'output_text'):
                    # Direct access to output_text (MockResponse)
                    output_text = response.output_text or ""
                    logger.info(f"Request {request_id}: Raw response text (MockResponse): {output_text[:200]}...")
                elif hasattr(response, 'output') and response.output:
                    # Response API format
                    for item in response.output:
                        if hasattr(item, "content") and item.content:
                            for content in item.content:
                                if hasattr(content, "text") and content.text:
                                    output_text += content.text
                        elif hasattr(item, "summary") and item.summary:
                            reasoning_summary = item.summary[0].text if item.summary else None
                    logger.info(f"Request {request_id}: Raw response text (Response API): {output_text[:200]}...")
                    logger.info(f"Request {request_id}: Full raw response from OpenAI: {response}")
                else:
                    logger.error(f"Request {request_id}: No valid output found in response")
                    output_text = "Sorry, I couldn't generate a response. Please try again."
                
                # Simulate streaming by sending chunks
                chunk_size = 50
                for i in range(0, len(output_text), chunk_size):
                    chunk = output_text[i:i + chunk_size]
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
                # Send reasoning summary if available
                if reasoning_summary:
                    yield f"data: {json.dumps({'reasoning_summary': reasoning_summary})}\n\n"
                
                # Send response metadata
                metadata = {
                    'persona_id': request.bot_id,
                    'persona_version': persona['version'],
                    'model': final_model_used,
                    'instructions_sha256': persona['sha256']
                }
                logger.info(f"Request {request_id}: Sending response back to frontend - output_text length: {len(output_text)}, metadata: {metadata}")
                
                # Extract response_id from Responses API for conversation state
                response_id = None
                if hasattr(response, 'id'):
                    response_id = response.id
                    metadata['response_id'] = response_id
                    logger.info(f"Request {request_id}: Extracted response_id: {response_id}")
                else:
                    logger.warning(f"Request {request_id}: No response.id found in response object")
                
                yield f"data: {json.dumps({'metadata': metadata})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Request {request_id}: OpenAI API error: {str(e)}", exc_info=True)
                logger.error(f"Request {request_id}: Request details - Model: {request.model}, Messages: {len(request.messages)}")
                yield f"data: {json.dumps({'error': f'Service error: {str(e)}'})}\n\n"
        
        # Log request completion
        latency = time.time() - start_time
        logger.info(f"Request {request_id}: Completed in {latency:.2f}s - Persona: {request.bot_id} (v{persona['version']}), Model: {final_model_used}, SHA256: {persona['sha256'][:8]}...")
        
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