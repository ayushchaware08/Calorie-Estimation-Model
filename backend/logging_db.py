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
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_session ON predictions(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_prediction ON detected_items(prediction_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_label ON detected_items(label_canonical)")
            
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