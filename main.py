from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_query, get_metrics, get_history, clear_history
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ FastAPI App ============

app = FastAPI(
    title="AI Research Agent by NIT Durgapur",
    description="Advanced Multi-Agent Research System with Memory & Analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Request Models ============

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: int  # 1-5
    feedback: str = ""

# ============ Endpoints ============

@app.get("/", response_class=HTMLResponse)
def home():
    """Serve the React frontend"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            """
            <h1>Error: Frontend not found</h1>
            <p>Please ensure static/index.html exists</p>
            <a href="/docs">View API Documentation</a>
            """,
            status_code=404
        )

@app.get("/api/ask")
def ask_get(query: str = Query(..., min_length=3, description="Research question")):
    """Handle GET requests (backward compatible)"""
    return ask_post(QueryRequest(query=query))

@app.post("/api/ask")
def ask_post(request: QueryRequest):
    """Handle POST requests with full query context"""
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")
    
    logger.info(f"📝 Query: {request.query[:100]}...")
    
    try:
        result = run_query(request.query)
        
        if result["success"]:
            logger.info(f"✅ Query completed - {result['metadata'].get('tokens', 0)} tokens")
            return JSONResponse({
                "status": "success",
                "query": request.query,
                "answer": result["answer"],
                "metadata": result["metadata"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.error(f"❌ Query failed: {result['answer']}")
            raise HTTPException(status_code=500, detail=result["answer"])
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
def get_system_metrics():
    """Get system performance metrics"""
    try:
        metrics = get_metrics()
        return JSONResponse({
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_conversation_history():
    """Get conversation history"""
    try:
        history = get_history()
        return JSONResponse({
            "status": "success",
            "history": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/history/clear")
def clear_conversation_history():
    """Clear conversation memory"""
    try:
        result = clear_history()
        logger.info("🗑️ Conversation history cleared")
        return JSONResponse({
            "status": "success",
            "message": "Conversation history cleared",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Collect user feedback"""
    try:
        # In production, save to database
        feedback_data = {
            "query": feedback.query,
            "rating": feedback.rating,
            "feedback": feedback.feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"⭐ Feedback received - Rating: {feedback.rating}/5")
        
        # Here you'd save to DB - for now just log
        with open("feedback.jsonl", "a") as f:
            f.write(json.dumps(feedback_data) + "\n")
        
        return JSONResponse({
            "status": "success",
            "message": "Thank you for your feedback!"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Research Agent",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/export/{format}")
def export_history(format: str):
    """Export conversation history in different formats"""
    if format not in ["json", "txt", "md"]:
        raise HTTPException(status_code=400, detail="Format must be json, txt, or md")
    
    try:
        history = get_history()
        
        if format == "json":
            return JSONResponse({"history": history})
        
        elif format == "txt":
            content = "AI Research Agent - Conversation History\n"
            content += "=" * 50 + "\n\n"
            for msg in history:
                role = "USER" if msg["role"] == "human" else "ASSISTANT"
                content += f"{role}:\n{msg['content']}\n\n"
            
            return HTMLResponse(content=content, media_type="text/plain")
        
        elif format == "md":
            content = "# AI Research Agent - Conversation History\n\n"
            for msg in history:
                role = "**User**" if msg["role"] == "human" else "**Assistant**"
                content += f"{role}:\n\n{msg['content']}\n\n---\n\n"
            
            return HTMLResponse(content=content, media_type="text/markdown")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ Startup/Shutdown Events ============

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Research Agent Starting...")
    logger.info("📚 NIT Durgapur MTech Project")
    logger.info("🔗 Access at: http://localhost:8000")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 AI Research Agent Shutting Down...")

# Mount static files (if you have CSS/JS separately)
# app.mount("/static", StaticFiles(directory="static"), name="static")