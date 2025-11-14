# logging_db.py
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

class PredictionLogger:
    def __init__(self, db_path: str = "prediction_logs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    total_calories REAL,
                    total_fats REAL,
                    total_protein REAL,
                    total_items INTEGER,
                    processing_time_ms REAL,
                    image_size TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create detected_items table for individual food items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detected_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    label TEXT,
                    label_canonical TEXT,
                    confidence REAL,
                    calories REAL,
                    fats REAL,
                    protein REAL,
                    box_coordinates TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES predictions (id)
                )
            """)
            
            # Create user_confirmations table for top-3 predictions and user selections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_confirmations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    top_prediction TEXT,
                    top_confidence REAL,
                    second_prediction TEXT,
                    second_confidence REAL,
                    third_prediction TEXT,
                    third_confidence REAL,
                    user_selected_option INTEGER,
                    user_final_choice TEXT NOT NULL,
                    is_custom_entry BOOLEAN DEFAULT 0,
                    custom_food_name TEXT,
                    final_calories REAL,
                    final_protein REAL,
                    final_fats REAL,
                    confidence_threshold REAL,
                    was_confident BOOLEAN,
                    image_reference TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_session ON predictions(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_prediction ON detected_items(prediction_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_label ON detected_items(label_canonical)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_confirmations_session ON user_confirmations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_confirmations_timestamp ON user_confirmations(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_confirmations_custom ON user_confirmations(is_custom_entry)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def log_prediction(
        self,
        prediction_result: Dict[str, Any],
        session_id: Optional[str] = None,
        processing_time_ms: Optional[float] = None,
        image_size: Optional[tuple] = None
    ) -> int:
        """Log a prediction result to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract summary data
                items = prediction_result.get("items", [])
                total_calories = prediction_result.get("total_calories", 0)
                total_fats = prediction_result.get("total_fats", 0)
                total_protein = prediction_result.get("total_protein", 0)
                total_items = len(items)
                
                image_size_str = f"{image_size[0]}x{image_size[1]}" if image_size else None
                
                # Insert prediction record
                cursor.execute("""
                    INSERT INTO predictions 
                    (session_id, total_calories, total_fats, total_protein, total_items, 
                     processing_time_ms, image_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, total_calories, total_fats, total_protein, total_items,
                      processing_time_ms, image_size_str))
                
                prediction_id = cursor.lastrowid
                
                # Insert detected items
                for item in items:
                    # Get additional nutritional data from calorie_db if available
                    fats = None
                    protein = None
                    if item.get("label_canonical"):
                        from calorie_db import CALORIE_DB
                        food_data = CALORIE_DB.get(item["label_canonical"])
                        if isinstance(food_data, dict):
                            fats = food_data.get("fats")
                            protein = food_data.get("protein")
                    
                    cursor.execute("""
                        INSERT INTO detected_items 
                        (prediction_id, label, label_canonical, confidence, calories, 
                         fats, protein, box_coordinates)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prediction_id,
                        item.get("label"),
                        item.get("label_canonical"),
                        item.get("confidence"),
                        item.get("calories"),
                        fats,
                        protein,
                        json.dumps(item.get("box", []))
                    ))
                
                conn.commit()
                logger.info(f"Logged prediction {prediction_id} with {total_items} items")
                return prediction_id
                
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")
            return -1
    
    def get_recent_predictions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent predictions with their items"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get predictions
                cursor.execute("""
                    SELECT * FROM predictions 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                predictions = []
                for row in cursor.fetchall():
                    prediction = dict(row)
                    
                    # Get items for this prediction
                    cursor.execute("""
                        SELECT * FROM detected_items 
                        WHERE prediction_id = ? 
                        ORDER BY confidence DESC
                    """, (prediction["id"],))
                    
                    items = []
                    for item_row in cursor.fetchall():
                        item = dict(item_row)
                        # Parse box coordinates
                        if item["box_coordinates"]:
                            item["box"] = json.loads(item["box_coordinates"])
                        del item["box_coordinates"]
                        items.append(item)
                    
                    prediction["items"] = items
                    predictions.append(prediction)
                
                return predictions
                
        except Exception as e:
            logger.error(f"Failed to get recent predictions: {e}")
            return []
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get prediction statistics for the last N days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total predictions in period
                cursor.execute("""
                    SELECT COUNT(*) as total_predictions,
                           AVG(total_calories) as avg_calories,
                           SUM(total_calories) as total_calories_consumed,
                           AVG(processing_time_ms) as avg_processing_time
                    FROM predictions 
                    WHERE timestamp > datetime('now', '-{} days')
                """.format(days))
                
                stats = dict(cursor.fetchone())
                
                # Most detected foods
                cursor.execute("""
                    SELECT di.label_canonical, 
                           COUNT(*) as count,
                           AVG(di.confidence) as avg_confidence
                    FROM detected_items di
                    JOIN predictions p ON di.prediction_id = p.id
                    WHERE p.timestamp > datetime('now', '-{} days')
                    GROUP BY di.label_canonical
                    ORDER BY count DESC
                    LIMIT 10
                """.format(days))
                
                top_foods = [dict(row) for row in cursor.fetchall()]
                stats["top_foods"] = top_foods
                
                # Daily breakdown
                cursor.execute("""
                    SELECT DATE(timestamp) as date,
                           COUNT(*) as predictions,
                           SUM(total_calories) as calories
                    FROM predictions 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """.format(days))
                
                daily_stats = [dict(row) for row in cursor.fetchall()]
                stats["daily_breakdown"] = daily_stats
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def get_calorie_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get calorie consumption trends over time"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as prediction_count,
                        SUM(total_calories) as total_calories,
                        AVG(total_calories) as avg_calories_per_prediction,
                        SUM(total_fats) as total_fats,
                        SUM(total_protein) as total_protein
                    FROM predictions 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date ASC
                """.format(days))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get calorie trends: {e}")
            return []
    
    def log_user_confirmation(
        self,
        session_id: str,
        top_predictions: List[Dict[str, Any]],
        user_selection: int,
        final_choice: str,
        is_custom_entry: bool = False,
        custom_food_name: Optional[str] = None,
        nutritional_info: Optional[Dict[str, Any]] = None,
        confidence_threshold: Optional[float] = None,
        was_confident: Optional[bool] = None,
        image_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Log user confirmation/selection after top-3 predictions.
        
        Args:
            session_id: Session identifier
            top_predictions: List of top 3 predictions with confidence scores
            user_selection: Index of selected option (1-3 for predictions, 4 for custom)
            final_choice: Final food name selected/entered by user
            is_custom_entry: Whether user entered custom food name
            custom_food_name: Custom food name if entered
            nutritional_info: Nutritional data for final choice
            confidence_threshold: Threshold used for prediction
            was_confident: Whether top prediction met confidence threshold
            image_reference: Reference to image file
            notes: Additional notes
            
        Returns:
            ID of logged confirmation record
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract top 3 predictions data (pad with None if less than 3)
                top_pred = top_predictions[0] if len(top_predictions) > 0 else {}
                second_pred = top_predictions[1] if len(top_predictions) > 1 else {}
                third_pred = top_predictions[2] if len(top_predictions) > 2 else {}
                
                # Extract nutritional info
                final_calories = nutritional_info.get("calories", 0) if nutritional_info else 0
                final_protein = nutritional_info.get("protein", 0) if nutritional_info else 0
                final_fats = nutritional_info.get("fats", 0) if nutritional_info else 0
                
                cursor.execute("""
                    INSERT INTO user_confirmations 
                    (session_id, top_prediction, top_confidence,
                     second_prediction, second_confidence,
                     third_prediction, third_confidence,
                     user_selected_option, user_final_choice,
                     is_custom_entry, custom_food_name,
                     final_calories, final_protein, final_fats,
                     confidence_threshold, was_confident,
                     image_reference, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    top_pred.get("label"),
                    top_pred.get("confidence"),
                    second_pred.get("label"),
                    second_pred.get("confidence"),
                    third_pred.get("label"),
                    third_pred.get("confidence"),
                    user_selection,
                    final_choice,
                    is_custom_entry,
                    custom_food_name,
                    final_calories,
                    final_protein,
                    final_fats,
                    confidence_threshold,
                    was_confident,
                    image_reference,
                    notes
                ))
                
                confirmation_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Logged user confirmation {confirmation_id} for session {session_id}")
                return confirmation_id
                
        except Exception as e:
            logger.error(f"Failed to log user confirmation: {e}")
            return -1
    
    def get_user_confirmations(
        self,
        limit: int = 100,
        offset: int = 0,
        session_id: Optional[str] = None,
        include_custom_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user confirmation logs with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM user_confirmations WHERE 1=1"
                params = []
                
                if session_id:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if include_custom_only:
                    query += " AND is_custom_entry = 1"
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get user confirmations: {e}")
            return []
    
    def get_confirmation_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics about user confirmations and model accuracy"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_confirmations,
                        SUM(CASE WHEN user_selected_option = 1 THEN 1 ELSE 0 END) as accepted_top_prediction,
                        SUM(CASE WHEN user_selected_option IN (2, 3) THEN 1 ELSE 0 END) as selected_alternative,
                        SUM(CASE WHEN is_custom_entry = 1 THEN 1 ELSE 0 END) as custom_entries,
                        AVG(CASE WHEN user_selected_option = 1 THEN top_confidence ELSE NULL END) as avg_confidence_when_accepted,
                        AVG(top_confidence) as avg_top_confidence,
                        SUM(CASE WHEN was_confident = 1 THEN 1 ELSE 0 END) as high_confidence_predictions,
                        SUM(CASE WHEN was_confident = 0 THEN 1 ELSE 0 END) as low_confidence_predictions
                    FROM user_confirmations 
                    WHERE timestamp > datetime('now', '-{} days')
                """.format(days))
                
                stats = dict(cursor.fetchone())
                
                # Calculate accuracy metrics
                total = stats.get("total_confirmations", 0)
                if total > 0:
                    stats["top_prediction_accuracy"] = round((stats.get("accepted_top_prediction", 0) / total) * 100, 2)
                    stats["alternative_selection_rate"] = round((stats.get("selected_alternative", 0) / total) * 100, 2)
                    stats["custom_entry_rate"] = round((stats.get("custom_entries", 0) / total) * 100, 2)
                else:
                    stats["top_prediction_accuracy"] = 0
                    stats["alternative_selection_rate"] = 0
                    stats["custom_entry_rate"] = 0
                
                # Most commonly custom-entered foods
                cursor.execute("""
                    SELECT custom_food_name, COUNT(*) as count
                    FROM user_confirmations
                    WHERE is_custom_entry = 1 
                    AND timestamp > datetime('now', '-{} days')
                    GROUP BY custom_food_name
                    ORDER BY count DESC
                    LIMIT 10
                """.format(days))
                
                stats["most_custom_entries"] = [dict(row) for row in cursor.fetchall()]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get confirmation statistics: {e}")
            return {}