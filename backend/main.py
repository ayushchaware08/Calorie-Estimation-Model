from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import CalorieModel
from logging_db import PredictionLogger
from prediction_handler import PredictionHandler
from websocket_manager import ConnectionManager
import io
from PIL import Image
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Session storage for predictions (in production, use Redis or similar)
session_predictions = {}

app = FastAPI(title="Calorie Estimation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if ALLOWED_ORIGINS == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class UserConfirmationRequest(BaseModel):
    session_id: str
    selected_option: int  # 1-3 for predictions, 4 for custom
    custom_food_name: Optional[str] = None
    notes: Optional[str] = None

class CustomFoodRequest(BaseModel):
    session_id: str
    food_name: str
    quantity: float = 1.0
    notes: Optional[str] = None

model: CalorieModel | None = None
prediction_logger: PredictionLogger | None = None
prediction_handler: PredictionHandler | None = None
websocket_manager = ConnectionManager()

@app.on_event("startup")
def _startup():
    global model, prediction_logger, prediction_handler
    try:
        model = CalorieModel()
        logger.info("Model loaded successfully")
        
        # Initialize prediction logger
        prediction_logger = PredictionLogger()
        logger.info("Prediction logger initialized successfully")
        
        # Initialize prediction handler with 70% confidence threshold
        prediction_handler = PredictionHandler(model, confidence_threshold=0.70)
        logger.info("Prediction handler initialized successfully")
        
        logger.info("WebSocket manager initialized successfully")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
        model = None
        prediction_logger = None
        prediction_handler = None

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

    # Validate file size
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")
    
    # Add MIME type validation BEFORE reading
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and GIF files are allowed.")

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

@app.post("/predict/top3")
async def predict_with_top3(file: UploadFile = File(...), session_id: Optional[str] = None):
    """
    Get top-3 food predictions with confidence scores.
    Returns recommendations for user to confirm or enter custom food.
    """
    if model is None or prediction_handler is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Validate file size
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")
    
    # Add MIME type validation
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and GIF files are allowed.")

    contents = await file.read()
    start_time = time.time()
    
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_size = image.size
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Invalid image file", "detail": str(e)})

    try:
        # Use prediction handler to get top-3 recommendations
        result = prediction_handler.process_prediction(image, session_id=session_id)
        processing_time_ms = (time.time() - start_time) * 1000
        
        result["processing_time_ms"] = processing_time_ms
        result["image_size"] = f"{image_size[0]}x{image_size[1]}"
        
        # Store predictions in session for later confirmation
        session_predictions[session_id] = {
            "predictions": result.get("top_predictions", []),
            "timestamp": datetime.now().isoformat(),
            "image_size": image_size,
            "confidence_threshold": prediction_handler.confidence_threshold,
            "is_confident": result.get("is_confident", False)
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Prediction failed", "detail": str(e)})

    return result

@app.post("/confirm")
async def confirm_prediction(confirmation: UserConfirmationRequest):
    """
    Log user's confirmation/selection after viewing top-3 predictions.
    Handles acceptance of prediction or custom food entry.
    """
    if prediction_logger is None or prediction_handler is None:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Retrieve stored predictions from session
        session_data = session_predictions.get(confirmation.session_id)
        if not session_data:
            # Session not found, proceed with limited logging
            logger.warning(f"Session {confirmation.session_id} not found in cache")
            top_predictions = []
            was_confident = None
            confidence_threshold = 0.70
        else:
            top_predictions = session_data.get("predictions", [])
            was_confident = session_data.get("is_confident", False)
            confidence_threshold = session_data.get("confidence_threshold", 0.70)
        
        # Determine what the user selected
        is_custom = confirmation.selected_option == 4 or confirmation.custom_food_name is not None
        
        if is_custom and not confirmation.custom_food_name:
            raise HTTPException(status_code=400, detail="Custom food name required when selecting custom option")
        
        # Get nutritional info for the final choice
        if is_custom:
            final_choice = confirmation.custom_food_name
            nutritional_info = prediction_handler.calculate_nutritional_info(final_choice)
        else:
            # User selected one of the top predictions (1-3)
            if not top_predictions:
                raise HTTPException(status_code=400, detail="No predictions found for this session. Please upload an image first.")
            
            if confirmation.selected_option < 1 or confirmation.selected_option > len(top_predictions):
                raise HTTPException(status_code=400, detail=f"Invalid selection. Please select 1-{len(top_predictions)} or 4 for custom.")
            
            selected_prediction = top_predictions[confirmation.selected_option - 1]
            final_choice = selected_prediction.get("label", "unknown")
            nutritional_info = {
                "calories": selected_prediction.get("calories", 0),
                "protein": selected_prediction.get("protein", 0),
                "fats": selected_prediction.get("fats", 0)
            }
        
        # Log the confirmation with all top-3 predictions
        confirmation_id = prediction_logger.log_user_confirmation(
            session_id=confirmation.session_id,
            top_predictions=top_predictions,
            user_selection=confirmation.selected_option,
            final_choice=final_choice,
            is_custom_entry=is_custom,
            custom_food_name=confirmation.custom_food_name if is_custom else None,
            nutritional_info=nutritional_info,
            confidence_threshold=confidence_threshold,
            was_confident=was_confident,
            notes=confirmation.notes
        )
        
        # Clean up session data after confirmation
        if confirmation.session_id in session_predictions:
            del session_predictions[confirmation.session_id]
        
        return {
            "confirmation_id": confirmation_id,
            "session_id": confirmation.session_id,
            "final_choice": final_choice,
            "nutritional_info": nutritional_info,
            "user_selected_option": confirmation.selected_option,
            "top_predictions_logged": len(top_predictions),
            "message": "Confirmation logged successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to log confirmation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log confirmation: {str(e)}")

@app.post("/custom-entry")
async def add_custom_food_entry(request: CustomFoodRequest):
    """
    Record a custom food entry with nutritional information.
    Used when user enters food name manually.
    """
    if prediction_handler is None or prediction_logger is None:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Calculate nutritional info for the custom food
        nutritional_info = prediction_handler.calculate_nutritional_info(
            request.food_name,
            quantity=request.quantity
        )
        
        # Log as custom entry (no predictions available)
        confirmation_id = prediction_logger.log_user_confirmation(
            session_id=request.session_id,
            top_predictions=[],  # No predictions for manual entry
            user_selection=4,  # 4 = custom entry
            final_choice=request.food_name,
            is_custom_entry=True,
            custom_food_name=request.food_name,
            nutritional_info=nutritional_info,
            confidence_threshold=None,
            was_confident=None,
            notes=request.notes
        )
        
        return {
            "confirmation_id": confirmation_id,
            "session_id": request.session_id,
            "food_name": request.food_name,
            "quantity": request.quantity,
            "nutritional_info": nutritional_info,
            "message": "Custom food entry logged successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to log custom entry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log custom entry: {str(e)}")

@app.get("/nutritional-info/{food_name}")
async def get_nutritional_info(food_name: str, quantity: float = Query(1.0, gt=0)):
    """
    Get nutritional information for a specific food item.
    """
    if prediction_handler is None:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        info = prediction_handler.calculate_nutritional_info(food_name, quantity)
        return info
    except Exception as e:
        logger.error(f"Failed to get nutritional info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get nutritional info: {str(e)}")

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

@app.get("/logs/confirmations")
async def get_confirmation_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session_id: Optional[str] = None,
    custom_only: bool = False
):
    """Get user confirmation logs with optional filters"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        logs = prediction_logger.get_user_confirmations(
            limit=limit,
            offset=offset,
            session_id=session_id,
            include_custom_only=custom_only
        )
        return {
            "confirmations": logs,
            "limit": limit,
            "offset": offset,
            "count": len(logs),
            "filters": {
                "session_id": session_id,
                "custom_only": custom_only
            }
        }
    except Exception as e:
        logger.error(f"Failed to retrieve confirmation logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve confirmation logs")

@app.get("/logs/confirmation-stats")
async def get_confirmation_statistics(days: int = Query(7, ge=1, le=365)):
    """Get statistics about user confirmations and model accuracy"""
    if prediction_logger is None:
        raise HTTPException(status_code=503, detail="Logging service not available")
    
    try:
        stats = prediction_logger.get_confirmation_statistics(days=days)
        return {
            "statistics": stats,
            "period_days": days,
            "message": "Confirmation statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to retrieve confirmation statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve confirmation statistics")

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
