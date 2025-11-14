from typing import List, Dict, Any, Optional
from datetime import datetime
from PIL import Image
from calorie_db import CALORIE_DB, canonicalize_class
import logging

logger = logging.getLogger(__name__)

class PredictionHandler:
    """
    Handles food predictions with top-3 recommendations based on confidence scores.
    Supports user confirmation and custom food entry for unidentified items.
    """
    
    def __init__(self, model, confidence_threshold: float = 0.70):
        """
        Initialize prediction handler.
        
        Args:
            model: CalorieModel instance for making predictions
            confidence_threshold: Minimum confidence (0-1) to consider prediction reliable
        """
        self.model = model
        self.confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        
    def get_top_predictions(self, image, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Get top K food predictions with confidence scores and nutritional data.
        
        Args:
            image: PIL Image or image path
            top_k: Number of top predictions to return (default: 3)
            
        Returns:
            List of prediction dictionaries sorted by confidence (highest first)
        """
        # Get predictions from model
        result = self.model.predict(image)
        items = result.get("items", [])
        
        if not items:
            return []
        
        # Sort by confidence and take top K
        sorted_items = sorted(items, key=lambda x: x.get("confidence", 0), reverse=True)
        top_items = sorted_items[:top_k]
        
        # Format predictions with nutritional data
        predictions = []
        for idx, item in enumerate(top_items, 1):
            label = item.get("label", "unknown")
            canonical = item.get("label_canonical", canonicalize_class(label))
            confidence = item.get("confidence", 0.0)
            
            # Get nutritional data from database
            food_data = CALORIE_DB.get(canonical, {})
            if isinstance(food_data, dict):
                calories = food_data.get("calories", 0)
                protein = food_data.get("protein", 0)
                fats = food_data.get("fats", 0)
            else:
                calories = food_data if food_data else 0
                protein = 0
                fats = 0
            
            predictions.append({
                "rank": idx,
                "label": label,
                "label_canonical": canonical,
                "confidence": round(confidence, 4),
                "confidence_percent": round(confidence * 100, 2),
                "calories": calories,
                "protein": protein,
                "fats": fats,
                "box": item.get("box", [])
            })
        
        return predictions
    
    def process_prediction(self, image, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process image and determine if user input is needed based on confidence.
        
        Args:
            image: PIL Image or image path
            session_id: Optional session identifier
            
        Returns:
            Dictionary containing:
                - top_predictions: List of top 3 predictions
                - is_confident: Boolean indicating if top prediction is reliable
                - requires_user_input: Boolean indicating if user confirmation needed
                - recommended_action: String describing next action
                - session_id: Session identifier
        """
        try:
            # Get top 3 predictions
            top_predictions = self.get_top_predictions(image, top_k=3)
            
            if not top_predictions:
                return {
                    "top_predictions": [],
                    "is_confident": False,
                    "requires_user_input": True,
                    "recommended_action": "manual_entry",
                    "message": "No food items detected. Please enter food name manually.",
                    "session_id": session_id
                }
            
            # Check confidence of top prediction
            top_confidence = top_predictions[0]["confidence"]
            is_confident = top_confidence >= self.confidence_threshold
            
            # Determine recommended action
            if is_confident:
                action = "confirm_or_override"
                message = f"Detected '{top_predictions[0]['label']}' with {top_predictions[0]['confidence_percent']}% confidence. Please confirm or select alternative."
            else:
                action = "select_or_manual"
                message = f"Low confidence ({top_predictions[0]['confidence_percent']}%). Please select from suggestions or enter manually."
            
            return {
                "top_predictions": top_predictions,
                "is_confident": is_confident,
                "requires_user_input": not is_confident,
                "recommended_action": action,
                "message": message,
                "confidence_threshold": self.confidence_threshold * 100,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error processing prediction: {e}")
            return {
                "top_predictions": [],
                "is_confident": False,
                "requires_user_input": True,
                "recommended_action": "manual_entry",
                "message": f"Error processing image: {str(e)}",
                "session_id": session_id
            }
    
    def calculate_nutritional_info(self, food_name: str, quantity: float = 1.0) -> Dict[str, Any]:
        """
        Calculate nutritional information for a given food item.
        
        Args:
            food_name: Name of the food item (will be canonicalized)
            quantity: Multiplier for portion size (default: 1.0)
            
        Returns:
            Dictionary with nutritional data
        """
        canonical = canonicalize_class(food_name)
        food_data = CALORIE_DB.get(canonical)
        
        if not food_data:
            return {
                "food_name": food_name,
                "canonical_name": canonical,
                "found_in_database": False,
                "calories": 0,
                "protein": 0,
                "fats": 0,
                "quantity": quantity
            }
        
        if isinstance(food_data, dict):
            calories = food_data.get("calories", 0) * quantity
            protein = food_data.get("protein", 0) * quantity
            fats = food_data.get("fats", 0) * quantity
        else:
            calories = food_data * quantity
            protein = 0
            fats = 0
        
        return {
            "food_name": food_name,
            "canonical_name": canonical,
            "found_in_database": True,
            "calories": round(calories, 2),
            "protein": round(protein, 2),
            "fats": round(fats, 2),
            "quantity": quantity
        }