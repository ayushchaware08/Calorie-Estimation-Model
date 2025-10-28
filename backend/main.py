from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from model import CalorieModel
from logging_db import PredictionLogger
from websocket_manager import ConnectionManager
import io
from PIL import Image
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(title="Calorie Estimation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if ALLOWED_ORIGINS == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model: CalorieModel | None = None
prediction_logger: PredictionLogger | None = None
websocket_manager = ConnectionManager()

@app.on_event("startup")
def _startup():
    global model, prediction_logger
    try:
        model = CalorieModel()
        logger.info("Model loaded successfully")
        
        # Initialize prediction logger
        prediction_logger = PredictionLogger()
        logger.info("Prediction logger initialized successfully")
        
        logger.info("WebSocket manager initialized successfully")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
        model = None
        prediction_logger = None

@app.get("/health")
def health():
    ok = model is not None and hasattr(model, "model")
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ok" if ok else "init"})

@app.post("/predict")
async def predict(file: UploadFile = File(...), session_id: Optional[str] = None):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    contents = await file.read()
    start_time = time.time()
    
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_size = image.size
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Invalid image file", "detail": str(e)})

    try:
        result = model.predict(image)
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Log the prediction if logger is available
        if prediction_logger is not None:
            prediction_id = prediction_logger.log_prediction(
                prediction_result=result,
                session_id=session_id,
                processing_time_ms=processing_time_ms,
                image_size=image_size
            )
            result["prediction_id"] = prediction_id
            result["session_id"] = session_id
            result["processing_time_ms"] = processing_time_ms
            
            # Broadcast new prediction to WebSocket clients
            await websocket_manager.send_new_prediction({
                "prediction_id": prediction_id,
                "session_id": session_id,
                "total_calories": result.get("total_calories", 0),
                "total_items": len(result.get("items", [])),
                "processing_time_ms": processing_time_ms,
                "items_summary": [
                    {"label": item.get("label"), "calories": item.get("calories", 0)}
                    for item in result.get("items", [])
                ]
            })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Model prediction failed", "detail": str(e)})

    return result

# Log retrieval endpoints
@app.get("/logs/recent")
async def get_recent_logs(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """Get recent prediction logs with pagination"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        logs = prediction_logger.get_recent_predictions(limit=limit, offset=offset)
        return {"logs": logs, "limit": limit, "offset": offset, "count": len(logs)}
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@app.get("/logs/statistics")
async def get_statistics(days: int = Query(7, ge=1, le=365)):
    """Get prediction statistics for the specified number of days"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        stats = prediction_logger.get_statistics(days=days)
        return {"statistics": stats, "period_days": days}
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/logs/trends")
async def get_calorie_trends(days: int = Query(30, ge=1, le=365)):
    """Get calorie consumption trends over time"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        trends = prediction_logger.get_calorie_trends(days=days)
        return {"trends": trends, "period_days": days}
    except Exception as e:
        logger.error(f"Failed to retrieve trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")

@app.get("/logs/summary")
async def get_summary_stats():
    """Get a comprehensive summary of all logs"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        # Get basic stats
        week_stats = prediction_logger.get_statistics(days=7)
        month_stats = prediction_logger.get_statistics(days=30)
        
        # Get recent predictions count
        recent_logs = prediction_logger.get_recent_predictions(limit=10, offset=0)
        
        return {
            "week_statistics": week_stats,
            "month_statistics": month_stats,
            "recent_predictions_count": len(recent_logs),
            "last_prediction": recent_logs[0] if recent_logs else None
        }
    except Exception as e:
        logger.error(f"Failed to retrieve summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket_manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to Calorie Estimation Dashboard"
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for any message from client (ping/pong, etc.)
            data = await websocket.receive_text()
            
            # Handle client messages if needed
            if data == "ping":
                await websocket_manager.send_personal_message({
                    "type": "pong",
                    "message": "Connection alive"
                }, websocket)
            elif data == "get_stats":
                # Send current statistics
                if prediction_logger is not None:
                    stats = prediction_logger.get_statistics(days=7)
                    await websocket_manager.send_personal_message({
                        "type": "statistics_update",
                        "data": stats
                    }, websocket)
                    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@app.get("/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {"websocket_stats": websocket_manager.get_connection_stats()}
