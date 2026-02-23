"""
FastAPI application for Canary Islands tourism assistant with Claude AI integration.
"""
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import anthropic

from src.config import settings
from src.rag import TourismRAG
from src.prompts import SYSTEM_PROMPT, REJECTION_PROMPT, get_data_context_prompt


# Pydantic Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "¿Cuántos turistas visitaron Tenerife en enero de 2025?"
            }
        }
    )
    
    message: str = Field(..., description="User message", min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """Chat response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Según los datos disponibles, en enero de 2025..."
            }
        }
    )
    
    response: str = Field(..., description="Assistant response")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None


# Initialize FastAPI
app = FastAPI(
    title="Canarias Tourism AI Assistant API",
    description="API for Canary Islands tourism assistant with AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Initialize RAG system
try:
    rag_system = TourismRAG(settings.DATA_FILE_PATH)
    print(f"✓ RAG system initialized with {len(rag_system.data)} records")
except Exception as e:
    print(f"✗ Error initializing RAG system: {e}")
    rag_system = None


# Dependency to verify API Key
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> bool:
    """
    Verifies that the provided API Key is valid.
    
    Args:
        x_api_key: API Key from header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If API Key is invalid
    """
    if x_api_key != settings.MASTER_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return True


# Function to detect if question is about Canary Islands tourism
def is_canarias_tourism_question(message: str) -> bool:
    """
    Detects if the question is related to Canary Islands tourism.
    Simple system based on keywords.
    
    Args:
        message: User message
        
    Returns:
        True if it appears to be about Canary Islands tourism
    """
    message_lower = message.lower()
    
    # Tourism keywords
    tourism_keywords = [
        "turista", "turismo", "visita", "hotel", "ocupación",
        "viaje", "estancia", "pasajero", "ingreso", "gasto",
        "alojamiento", "estadística", "dato", "cuántos", "cuánto"
    ]
    
    # Canary Islands
    islands_keywords = [
        "canarias", "tenerife", "gran canaria", "lanzarote",
        "fuerteventura", "la palma", "la gomera", "el hierro", "isla"
    ]
    
    has_tourism = any(keyword in message_lower for keyword in tourism_keywords)
    has_canarias = any(keyword in message_lower for keyword in islands_keywords)
    
    # If mentions Canarias or an island, probably relevant
    # If mentions tourism and is a short question, probably relevant
    return has_canarias or (has_tourism and len(message.split()) < 30)


# Endpoints
@app.get("/")
async def root():
    """Root welcome endpoint."""
    return {
        "message": "Canarias Tourism AI Assistant API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "chat": "/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "hola mundo",
        "rag_system": "initialized" if rag_system else "error",
        "data_records": len(rag_system.data) if rag_system else 0
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API Key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def chat(
    request: ChatRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Main chat endpoint with tourism assistant.
    
    Args:
        request: Request with user message
        authenticated: Authentication verification (injected)
        
    Returns:
        ChatResponse with assistant response
        
    Raises:
        HTTPException: If there's any processing error
    """
    try:
        # Validate configuration
        settings.validate()
        
        if not rag_system:
            raise HTTPException(
                status_code=500,
                detail="RAG system not initialized"
            )
        
        user_message = request.message.strip()
        
        # Check if it's a question about Canary Islands tourism
        if not is_canarias_tourism_question(user_message):
            return ChatResponse(response=REJECTION_PROMPT)
        
        # Retrieve relevant data
        relevant_data = rag_system.retrieve_relevant_data(user_message)
        
        # Build messages for Claude
        system_message = SYSTEM_PROMPT
        data_context = get_data_context_prompt(relevant_data)
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Call Claude API
        message = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            system=system_message,
            messages=[
                {
                    "role": "user",
                    "content": f"{data_context}\n\nUSER QUESTION: {user_message}"
                }
            ]
        )
        
        # Extract response
        assistant_response = message.content[0].text
        
        return ChatResponse(response=assistant_response)
        
    except anthropic.APIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude API error: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


# Local development server
if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("\n❌ Error: Dependencies not installed")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt\n")
        exit(1)
    
    # Validate configuration before starting
    try:
        settings.validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nMake sure you have a .env file with:")
        print("  ANTHROPIC_API_KEY=your_key")
        print("  MASTER_API_KEY=your_master_key")
        exit(1)
    
    print("\n🚀 Starting development server...")
    print("📡 API available at: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
