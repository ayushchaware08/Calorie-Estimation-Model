# Real-Time Calorie Estimation Dashboard - Technical Architecture Plan

## Overview
This document outlines the technical architecture and implementation plan for building an interactive real-time dashboard that visualizes calorie estimation logs and analytics.

## System Architecture

### 1. Backend Extensions (Already Implemented)
- **Logging Service**: SQLite database with prediction logs, detected items, and nutritional data
- **REST API Endpoints**: 
  - `/logs/recent` - Paginated recent predictions
  - `/logs/statistics` - Statistical aggregations
  - `/logs/trends` - Time-based calorie trends
  - `/logs/summary` - Comprehensive dashboard data

### 2. Frontend Technology Stack (Recommended)

#### Option A: React.js Dashboard (Recommended)
```
Tech Stack:
- React 18+ with TypeScript
- Chart.js or Recharts for visualizations
- Socket.io-client for real-time updates
- Material-UI or Tailwind CSS for UI components
- Axios for API calls
- Date-fns for date manipulation
```

#### Option B: Streamlit Dashboard (Rapid Prototyping)
```
Tech Stack:
- Streamlit for rapid development
- Plotly for interactive charts
- Pandas for data manipulation
- Real-time updates via st.rerun()
```

#### Option C: Next.js Full-Stack (Advanced)
```
Tech Stack:
- Next.js 13+ with App Router
- TypeScript
- Server-Side Rendering
- Built-in API routes
- Vercel deployment ready
```

### 3. Real-Time Features Implementation

#### WebSocket Integration
```python
# Add to backend/main.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Modify predict endpoint to broadcast updates
async def predict(file: UploadFile = File(...), session_id: Optional[str] = None):
    # ... existing code ...
    
    # Broadcast new prediction to connected clients
    if prediction_logger is not None:
        await manager.broadcast({
            "type": "new_prediction",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
    
    return result
```

## Dashboard Components Design

### 1. Real-Time Statistics Cards
```
Components:
- Total Predictions Today
- Average Calories per Meal
- Most Detected Food Item
- Processing Time Average
- Active Sessions Count
```

### 2. Interactive Charts

#### A. Calorie Trends Line Chart
```javascript
// Example with Chart.js
const CalorieTrendsChart = ({ data }) => {
  const chartData = {
    labels: data.map(d => d.date),
    datasets: [{
      label: 'Daily Calories',
      data: data.map(d => d.total_calories),
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  };
  
  return <Line data={chartData} options={chartOptions} />;
};
```

#### B. Food Detection Frequency Bar Chart
```javascript
const FoodFrequencyChart = ({ data }) => {
  const chartData = {
    labels: data.top_foods.map(f => f.label_canonical),
    datasets: [{
      label: 'Detection Count',
      data: data.top_foods.map(f => f.count),
      backgroundColor: 'rgba(54, 162, 235, 0.6)'
    }]
  };
  
  return <Bar data={chartData} />;
};
```

#### C. Nutritional Breakdown Pie Chart
```javascript
const NutritionPieChart = ({ data }) => {
  const chartData = {
    labels: ['Calories', 'Fats', 'Protein'],
    datasets: [{
      data: [data.total_calories, data.total_fats, data.total_protein],
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
    }]
  };
  
  return <Pie data={chartData} />;
};
```

### 3. Real-Time Activity Feed
```javascript
const ActivityFeed = () => {
  const [activities, setActivities] = useState([]);
  
  useEffect(() => {
    const socket = io('ws://localhost:8000');
    
    socket.on('new_prediction', (data) => {
      setActivities(prev => [data, ...prev.slice(0, 49)]); // Keep last 50
    });
    
    return () => socket.disconnect();
  }, []);
  
  return (
    <div className="activity-feed">
      {activities.map(activity => (
        <ActivityItem key={activity.prediction_id} data={activity} />
      ))}
    </div>
  );
};
```

### 4. Interactive Data Table
```javascript
const PredictionsTable = () => {
  const [predictions, setPredictions] = useState([]);
  const [pagination, setPagination] = useState({ page: 0, limit: 25 });
  
  // Fetch data with pagination
  // Implement sorting, filtering
  
  return (
    <DataTable 
      data={predictions}
      columns={columns}
      pagination={pagination}
      onPageChange={setPagination}
    />
  );
};
```

## Implementation Phases

### Phase 1: Basic Dashboard (Week 1)
- Set up React/Next.js project
- Implement basic API integration
- Create static charts for trends and statistics
- Basic responsive layout

### Phase 2: Real-Time Features (Week 2)
- Implement WebSocket connection
- Add real-time activity feed
- Live updating charts
- Real-time statistics cards

### Phase 3: Advanced Analytics (Week 3)
- Time-based filtering (hourly, daily, weekly, monthly)
- Food detection heatmaps
- Calorie goal tracking
- Export functionality (PDF, CSV)

### Phase 4: Enhanced UX (Week 4)
- Dark/light theme toggle
- Mobile responsiveness
- Interactive tooltips and drill-downs
- Performance optimizations

## Deployment Architecture

### Development Setup
```bash
# Frontend (React)
npx create-react-app calorie-dashboard --template typescript
cd calorie-dashboard
npm install chart.js react-chartjs-2 socket.io-client @mui/material

# Backend (already exists)
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/prediction_logs.db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
```

## Key Features Summary

### Real-Time Dashboard Features:
1. **Live Activity Feed** - Shows predictions as they happen
2. **Dynamic Charts** - Auto-updating visualizations
3. **Statistical Cards** - Key metrics at a glance
4. **Interactive Filters** - Time-based and food-type filtering
5. **Responsive Design** - Works on desktop and mobile
6. **Export Capabilities** - Download reports and charts

### Analytics Capabilities:
1. **Calorie Tracking** - Daily, weekly, monthly trends
2. **Food Recognition Patterns** - Most/least detected foods
3. **Nutritional Analysis** - Breakdown of calories, fats, proteins
4. **Performance Metrics** - Model prediction accuracy and speed
5. **Usage Statistics** - Peak hours, session analysis

### Technical Benefits:
1. **Scalable Architecture** - SQLite for development, PostgreSQL for production
2. **Real-Time Updates** - WebSocket-based live data
3. **API-First Approach** - Separate frontend/backend for flexibility
4. **Type Safety** - TypeScript for robust frontend development
5. **Modern Stack** - Latest React/FastAPI best practices

## Getting Started

### Quick Start (Streamlit Prototype)
```python
# Create dashboard/streamlit_app.py
import streamlit as st
import requests
import plotly.express as px
import pandas as pd

st.title("Calorie Estimation Dashboard")

# Fetch data from API
@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_statistics():
    response = requests.get("http://localhost:8000/logs/statistics")
    return response.json()["statistics"]

@st.cache_data(ttl=30)
def fetch_trends():
    response = requests.get("http://localhost:8000/logs/trends")
    return response.json()["trends"]

# Display charts
stats = fetch_statistics()
trends = fetch_trends()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Predictions", stats.get("total_predictions", 0))
with col2:
    st.metric("Avg Calories", f"{stats.get('avg_calories', 0):.1f}")
with col3:
    st.metric("Avg Processing Time", f"{stats.get('avg_processing_time', 0):.1f}ms")

# Trends chart
if trends:
    df = pd.DataFrame(trends)
    fig = px.line(df, x='date', y='total_calories', title='Daily Calorie Trends')
    st.plotly_chart(fig, use_container_width=True)

# Run with: streamlit run dashboard/streamlit_app.py
```

This architecture provides a solid foundation for building a comprehensive, real-time dashboard that can grow with your needs. The modular approach allows you to start simple and add features incrementally.