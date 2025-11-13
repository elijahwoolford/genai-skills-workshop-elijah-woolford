"""FastAPI backend for Alaska Snow Department Agent."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
from google.cloud import logging as cloud_logging
from google.cloud import trace_v1
from .agent import AlaskaSnowAgent
from .config import PROJECT_ID, APP_PORT

# Initialize FastAPI app
app = FastAPI(
    title="Alaska Snow Department Agent API",
    description="AI-powered chatbot for snow services",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Cloud Logging
logging_client = cloud_logging.Client(project=PROJECT_ID)
logger = logging_client.logger("alaska-snow-agent")

# Initialize agent
agent = AlaskaSnowAgent()


class QuestionRequest(BaseModel):
    """Request model for questions."""
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    include_weather: bool = True


class QuestionResponse(BaseModel):
    """Response model for answers."""
    answer: str
    rag_context_used: bool
    weather_data_used: bool
    security_passed: bool
    processing_time_ms: float
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "alaska-snow-agent",
        "version": "1.0.0"
    }


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a user question about Alaska snow services.
    
    Args:
        request: QuestionRequest with query and optional location
    
    Returns:
        QuestionResponse with answer and metadata
    """
    start_time = time.time()
    
    try:
        # Log incoming request
        logger.log_struct({
            "event": "question_received",
            "query": request.query,
            "has_location": request.latitude is not None,
            "timestamp": time.time()
        })
        
        # Get answer from agent
        result = agent.answer_question(
            user_query=request.query,
            latitude=request.latitude,
            longitude=request.longitude,
            include_weather=request.include_weather
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Log response with full prompt and answer
        logger.log_struct({
            "event": "answer_generated",
            "query": request.query,
            "answer": result["answer"],  # Full response text
            "answer_length": len(result["answer"]),
            "functions_called": result.get("functions_called", []),  # Function calls made
            "rag_used": result["rag_context_used"],
            "weather_used": result["weather_data_used"],
            "security_passed": result["security_passed"],
            "processing_time_ms": processing_time,
            "error": result.get("error"),
            "timestamp": time.time()
        })
        
        return QuestionResponse(
            answer=result["answer"],
            rag_context_used=result["rag_context_used"],
            weather_data_used=result["weather_data_used"],
            security_passed=result["security_passed"],
            processing_time_ms=processing_time,
            error=result.get("error")
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        logger.log_struct({
            "event": "error",
            "query": request.query,
            "error": str(e),
            "processing_time_ms": processing_time,
            "timestamp": time.time()
        }, severity="ERROR")
        
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)

