from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import logging
import asyncio
from typing import Dict, Tuple
import time
from .settings import settings
from .agent import get_agent
from .vectorstore import vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LustBot API",
    description="AI Shopping Assistant for Luxury Products",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Request queue management for handling multiple requests properly
user_request_queues: Dict[str, asyncio.Queue] = {}
user_processing_status: Dict[str, bool] = {}
user_last_activity: Dict[str, float] = {}

# Cleanup old user sessions (older than 30 minutes)
CLEANUP_INTERVAL = 1800  # 30 minutes

async def cleanup_old_sessions():
    """Clean up old user sessions periodically"""
    while True:
        current_time = time.time()
        users_to_remove = []
        
        for user_id, last_activity in user_last_activity.items():
            if current_time - last_activity > CLEANUP_INTERVAL:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            if user_id in user_request_queues:
                del user_request_queues[user_id]
            if user_id in user_processing_status:
                del user_processing_status[user_id]
            if user_id in user_last_activity:
                del user_last_activity[user_id]
            logger.info(f"Cleaned up session for user: {user_id}")
        
        await asyncio.sleep(300)  # Check every 5 minutes

async def process_user_queue(user_id: str):
    """Process requests for a specific user in FIFO order"""
    while user_id in user_request_queues and not user_request_queues[user_id].empty():
        try:
            # Get the next request from the queue
            message, future = await user_request_queues[user_id].get()
            
            # Update last activity
            user_last_activity[user_id] = time.time()
            
            # Process the message with the agent
            logger.info(f"Processing message for user {user_id}: {message[:50]}...")
            agent = get_agent(user_id)
            response = agent.run(message, stream=False)
            
            # Set the result for the waiting request
            if not future.cancelled():
                future.set_result(response)
            
            # Mark task as done
            user_request_queues[user_id].task_done()
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            if not future.cancelled():
                future.set_exception(e)
    
    # Mark user as not processing when queue is empty
    user_processing_status[user_id] = False


class ChatMessage(BaseModel):
    message: str
    user_id: str = "anonymous"


class ChatResponse(BaseModel):
    reply: str
    status: str = "success"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please make sure frontend files are in the frontend/ directory</p>",
            status_code=404
        )


@app.post("/lustbot", response_model=ChatResponse)
async def lustbot_chat(request: ChatMessage):
    """
    Main LustBot chat endpoint with FIFO queue processing
    
    Args:
        request: Chat message from user
        
    Returns:
        ChatResponse with bot reply
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        user_id = request.user_id
        logger.info(f"Received message from {user_id}: {request.message[:100]}...")
        
        # Initialize user queue if doesn't exist
        if user_id not in user_request_queues:
            user_request_queues[user_id] = asyncio.Queue()
            user_processing_status[user_id] = False
        
        # Update last activity
        user_last_activity[user_id] = time.time()
        
        # Create a future to wait for the result
        result_future = asyncio.Future()
        
        # Add request to user's queue
        await user_request_queues[user_id].put((request.message, result_future))
        
        # Start processing queue if not already processing
        if not user_processing_status.get(user_id, False):
            user_processing_status[user_id] = True
            asyncio.create_task(process_user_queue(user_id))
        
        # Wait for result with timeout
        try:
            response = await asyncio.wait_for(result_future, timeout=60.0)  # 60 second timeout
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for user {user_id}")
            return ChatResponse(
                reply="מצטער, הבקשה לקחה יותר מדי זמן. אנא נסה שוב.",
                status="error"
            )
        
        # Extract the content from the agno response
        reply = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"Generated reply for {user_id}: {reply[:100]}...")
        
        return ChatResponse(reply=reply, status="success")
        
    except Exception as e:
        logger.error(f"Chat processing failed for {request.user_id}: {e}")
        return ChatResponse(
            reply="מצטער, אני נתקל בבעיה טכנית. אנא נסה שוב מאוחר יותר.",
            status="error"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LustBot",
        "version": "1.0.0"
    }


@app.post("/admin/load-products")
async def load_products():
    """Admin endpoint to reload product database"""
    try:
        success = vector_store.load_products_from_csv()
        if success:
            return {"status": "success", "message": "Products loaded successfully"}
        else:
            return {"status": "error", "message": "Failed to load products"}
    except Exception as e:
        logger.error(f"Product loading failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/agent-reset")
async def reset_agent_endpoint():
    """Admin endpoint to reset agent memory"""
    try:
        from .agent import reset_agent
        reset_agent()
        return {"status": "success", "message": "Agent reset successfully"}
    except Exception as e:
        logger.error(f"Agent reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/queue-status")
async def queue_status():
    """Admin endpoint to check queue status"""
    try:
        status = {}
        for user_id in user_request_queues:
            queue_size = user_request_queues[user_id].qsize()
            is_processing = user_processing_status.get(user_id, False)
            last_activity = user_last_activity.get(user_id, 0)
            status[user_id] = {
                "queue_size": queue_size,
                "is_processing": is_processing,
                "last_activity": last_activity,
                "last_activity_minutes_ago": (time.time() - last_activity) / 60
            }
        
        return {
            "status": "success", 
            "total_users": len(user_request_queues),
            "user_queues": status
        }
    except Exception as e:
        logger.error(f"Queue status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("🚀 Starting LustBot...")
    
    # Initialize vector store with products (optional)
    if settings.pinecone_api_key and settings.pinecone_api_key != "temp-placeholder":
        try:
            success = vector_store.load_products_from_csv()
            if success:
                logger.info("✅ Product database loaded successfully")
            else:
                logger.warning("⚠️ Product database failed to load - Pinecone not available")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load products: {e}")
    else:
        logger.info("ℹ️ Running without Pinecone vector store")
    
    # Initialize agent
    try:
        get_agent("startup_test")
        logger.info("✅ LustBot agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
    
    # Start session cleanup task
    asyncio.create_task(cleanup_old_sessions())
    logger.info("✅ Session cleanup task started")
    
    logger.info(f"🌐 LustBot is running on http://{settings.host}:{settings.port}")
    logger.info(f"📚 API Docs available at http://{settings.host}:{settings.port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("👋 Shutting down LustBot...")


def main():
    """Main entry point"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        access_log=True
    )


if __name__ == "__main__":
    main()
