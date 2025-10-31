# Calorie Estimation Dashboard Setup Guide

## Overview
This guide explains how to use the new logging features and interactive real-time dashboard for the Calorie Estimation Model.

## Features Added

### Backend Logging System
- **SQLite Database**: Stores all prediction logs with detailed metadata
- **Automatic Logging**: Every prediction is automatically logged with timestamps
- **REST API Endpoints**: Retrieve logs, statistics, and trends
- **WebSocket Support**: Real-time updates for dashboard
- **Performance Tracking**: Monitors prediction processing time

### Dashboard Features
- **Real-time Activity Feed**: See predictions as they happen
- **Interactive Charts**: Calorie trends, food frequency, daily breakdowns
- **Key Metrics**: Total predictions, average calories, processing times
- **Time-based Filtering**: View data for different time periods
- **Auto-refresh**: Optional automatic updates every 30 seconds

## Quick Start

### 1. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
# From the root directory
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Install Dashboard Dependencies
```bash
cd dashboard
pip install -r requirements.txt
```

### 4. Start the Dashboard
```bash
# From the dashboard directory
streamlit run streamlit_app.py
```

### 5. Access the Dashboard
- Open your browser and go to: `http://localhost:8501`
- The dashboard will automatically connect to the backend API

## API Endpoints

### New Logging Endpoints

#### Get Recent Predictions
```http
GET /logs/recent?limit=100&offset=0
```
Returns paginated list of recent predictions with all detected items.

#### Get Statistics
```http
GET /logs/statistics?days=7
```
Returns aggregated statistics for the specified time period:
- Total predictions
- Average calories per prediction
- Most detected foods
- Processing time statistics

#### Get Calorie Trends
```http
GET /logs/trends?days=30
```
Returns daily calorie consumption trends over time.

#### Get Summary Statistics
```http
GET /logs/summary
```
Returns comprehensive summary including weekly and monthly statistics.

#### WebSocket Connection
```ws
WS /ws
```
Real-time WebSocket connection for live updates.

### Enhanced Predict Endpoint
```http
POST /predict?session_id=optional_session_id
```
Now includes:
- Session ID tracking
- Processing time measurement
- Automatic logging
- Real-time WebSocket broadcasts

## Dashboard Usage

### 1. Key Metrics Section
- **Total Predictions**: Number of predictions in selected time period
- **Avg Calories/Meal**: Average calories per prediction
- **Total Calories**: Sum of all calories detected
- **Avg Processing Time**: Average model processing time

### 2. Analytics Charts
- **Daily Calorie Trends**: Line chart showing calorie consumption over time
- **Most Detected Foods**: Bar chart of frequently detected food items
- **Daily Breakdown**: Prediction count and calorie consumption by day

### 3. Recent Activity
- **Expandable Cards**: Detailed view of recent predictions
- **Detected Items**: Table showing all detected food items with confidence scores
- **Nutritional Info**: Calories, fats, and protein breakdown

### 4. Controls
- **Time Period Selector**: Choose from 7, 30, or 90 days
- **Auto-refresh Toggle**: Enable automatic updates every 30 seconds
- **Manual Refresh**: Force refresh of all data

## Database Schema

### Predictions Table
```sql
CREATE TABLE predictions (
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
);
```

### Detected Items Table
```sql
CREATE TABLE detected_items (
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
);
```

## Testing the Setup

### 1. Test Backend API
```bash
# Check health
curl http://localhost:8000/health

# Test prediction (replace with actual image file)
curl -X POST -F "file=@test_image.jpg" http://localhost:8000/predict

# Check logs
curl http://localhost:8000/logs/statistics
```

### 2. Test WebSocket Connection
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
ws.send('ping');
```

### 3. Generate Test Data
Make several predictions using different food images to populate the dashboard with sample data.

## Customization Options

### Dashboard Themes
You can modify the Streamlit app to add custom themes:
```python
# In streamlit_app.py
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)
```

### API Configuration
Modify the API base URL in the dashboard:
```python
# In streamlit_app.py
API_BASE_URL = "http://your-backend-server:8000"
```

### Database Location
Change the database file location:
```python
# In backend/main.py startup function
prediction_logger = PredictionLogger(db_path="/path/to/your/database.db")
```

## Production Deployment

### Docker Setup
```dockerfile
# Dockerfile for backend
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile for dashboard
FROM python:3.10-slim
WORKDIR /app
COPY dashboard/requirements.txt .
RUN pip install -r requirements.txt
COPY dashboard/ .
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: 
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/prediction_logs.db

  dashboard:
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    ports:
      - "8501:8501"
    depends_on:
      - backend
    environment:
      - API_BASE_URL=http://backend:8000
```

## Troubleshooting

### Common Issues

1. **Dashboard can't connect to API**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify API_BASE_URL in dashboard code

2. **Database errors**
   - Ensure write permissions to database directory
   - Check disk space
   - Verify SQLite installation

3. **WebSocket connection issues**
   - Check if port 8000 supports WebSocket connections
   - Verify CORS settings
   - Test with simple WebSocket client

4. **Performance issues**
   - Monitor database size and optimize if needed
   - Consider pagination for large datasets
   - Enable database indexing

### Performance Optimization

1. **Database Indexing**
   - Indexes are automatically created for common queries
   - Monitor query performance with EXPLAIN QUERY PLAN

2. **Dashboard Caching**
   - Streamlit includes caching decorators for API calls
   - Adjust cache TTL based on your needs

3. **WebSocket Scaling**
   - For high-traffic scenarios, consider Redis for WebSocket management
   - Implement connection pooling for database access

## Next Steps

### Potential Enhancements
1. **User Authentication**: Add user login and session management
2. **Export Features**: PDF reports, CSV downloads
3. **Alerting System**: Notifications for unusual patterns
4. **Mobile App**: React Native or Flutter dashboard
5. **Advanced Analytics**: ML-based insights and predictions
6. **Multi-tenant Support**: Support for multiple users/organizations

### Integration Options
1. **Cloud Storage**: AWS S3, Google Cloud Storage for images
2. **Time Series Database**: InfluxDB for advanced time-series analytics
3. **Message Queue**: Redis/RabbitMQ for background processing
4. **Monitoring**: Prometheus + Grafana for system monitoring

## Support

For issues or questions:
1. Check the logs in both backend and dashboard
2. Verify all dependencies are installed correctly
3. Test API endpoints individually
4. Check the comprehensive architecture plan in `dashboard_architecture_plan.md`

The logging and dashboard system is now fully integrated and ready for use!