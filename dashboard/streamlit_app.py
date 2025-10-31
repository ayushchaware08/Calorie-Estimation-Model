import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Calorie Estimation Dashboard",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .stMetric > div > div > div > div {
        color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def fetch_data(endpoint, params=None):
    """Fetch data from API with error handling"""
    try:
        # Add cache-busting parameter to ensure fresh data
        if params is None:
            params = {}
        params['_t'] = int(time.time())  # Add timestamp to prevent caching
        
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def main():
    # Clear any cached data on page load to ensure fresh data
    st.cache_data.clear()
    
    st.title("🍽️ Calorie Estimation Dashboard")
    st.markdown("Real-time analytics for food recognition and calorie tracking")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Time period selector
    time_periods = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90
    }
    selected_period = st.sidebar.selectbox("Select Time Period", list(time_periods.keys()))
    days = time_periods[selected_period]
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        # Auto refresh every 30 seconds
        time.sleep(0.1)  # Small delay to prevent immediate refresh
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Fetch data
    with st.spinner("Loading dashboard data..."):
        stats = fetch_data("/logs/statistics", {"days": days})
        trends = fetch_data("/logs/trends", {"days": days})
        recent_logs = fetch_data("/logs/recent", {"limit": 10})
    
    if not stats:
        st.error("Unable to connect to the API. Make sure the backend server is running on localhost:8000")
        return
    
    # Key Metrics Row
    st.header("📊 Key Metrics")
    
    stats_data = stats.get("statistics", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_predictions = stats_data.get("total_predictions", 0) or 0
        st.metric(
            label="Total Predictions",
            value=f"{total_predictions:,}",
            delta=f"Last {days} days"
        )
    
    with col2:
        avg_calories = stats_data.get("avg_calories", 0) or 0
        st.metric(
            label="Avg Calories/Meal",
            value=f"{avg_calories:.1f}",
            delta="Per prediction"
        )
    
    with col3:
        total_calories = stats_data.get("total_calories_consumed", 0) or 0
        st.metric(
            label="Total Calories",
            value=f"{total_calories:,.0f}",
            delta="Consumed"
        )
    
    with col4:
        avg_processing = stats_data.get("avg_processing_time", 0) or 0
        st.metric(
            label="Avg Processing Time",
            value=f"{avg_processing:.1f}ms",
            delta="Per prediction"
        )
    
    # Charts Row
    st.header("📈 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Calorie, Fats, and Protein Trends Chart
        if trends and trends.get("trends"):
            st.subheader("Daily Nutrition Trends")
            trends_data = trends["trends"]
            df_trends = pd.DataFrame(trends_data)
            
            if not df_trends.empty:
                fig_trends = go.Figure()
            
                # Add calorie line
                fig_trends.add_trace(go.Scatter(
                    x=df_trends['date'],
                    y=df_trends['total_calories'],
                    mode='lines+markers',
                    name='Calories',
                    line=dict(color='#ff6b6b', width=3),
                    marker=dict(size=6)
                ))
                
                # Add fats line (if available)
                if 'total_fats' in df_trends.columns:
                    fig_trends.add_trace(go.Scatter(
                        x=df_trends['date'],
                        y=df_trends['total_fats'],
                        mode='lines+markers',
                        name='Fats (g)',
                        line=dict(color='#4ecdc4', width=3),
                        marker=dict(size=6),
                        yaxis='y2'
                    ))
                
                # Add protein line (if available)
                if 'total_protein' in df_trends.columns:
                    fig_trends.add_trace(go.Scatter(
                        x=df_trends['date'],
                        y=df_trends['total_protein'],
                        mode='lines+markers',
                        name='Protein (g)',
                        line=dict(color='#45b7d1', width=3),
                        marker=dict(size=6),
                        yaxis='y2'
                    ))
                
                # Update layout for dual y-axis
                fig_trends.update_layout(
                    title="Nutrition Trends Over Time",
                    xaxis_title="Date",
                    yaxis=dict(
                        title="Calories",
                        side="left",
                        color='#ff6b6b'
                    ),
                    yaxis2=dict(
                        title="Grams (Fats & Protein)",
                        side="right",
                        overlaying="y",
                        color='#4ecdc4'
                    ),
                    hovermode='x unified',
                    legend=dict(x=0.01, y=0.99)
                )
                st.plotly_chart(fig_trends, use_container_width=True)
            else:
                st.info("No trend data available for the selected period")
        else:
            st.info("No trend data available")
        
    
    with col2:
        # Top Foods Chart
        if stats_data.get("top_foods"):
            st.subheader("Most Detected Foods")
            top_foods = stats_data["top_foods"][:10]  # Top 10
            df_foods = pd.DataFrame(top_foods)
            
            fig_foods = px.bar(
                df_foods,
                x='count',
                y='label_canonical',
                orientation='h',
                title="Food Detection Frequency",
                color='avg_confidence',
                color_continuous_scale='viridis'
            )
            fig_foods.update_layout(
                xaxis_title="Detection Count",
                yaxis_title="Food Item",
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_foods, use_container_width=True)
        else:
            st.info("No food detection data available")
    
    # Daily Breakdown Section
    st.header("📅 Daily Breakdown")
    
    if stats_data.get("daily_breakdown"):
        daily_data = stats_data["daily_breakdown"]
        df_daily = pd.DataFrame(daily_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily predictions chart
            fig_predictions = px.bar(
                df_daily,
                x='date',
                y='predictions',
                title="Daily Prediction Count"
            )
            st.plotly_chart(fig_predictions, use_container_width=True)
        
        with col2:
            # Daily calories chart
            fig_calories = px.bar(
                df_daily,
                x='date',
                y='calories',
                title="Daily Calorie Consumption",
                color='calories',
                color_continuous_scale='reds'
            )
            st.plotly_chart(fig_calories, use_container_width=True)
    
    # Recent Activity Section
    st.header("🕐 Recent Activity")
    
    if recent_logs and recent_logs.get("logs"):
        recent_data = recent_logs["logs"]
        
        for i, log in enumerate(recent_data[:5]):  # Show top 5 recent
            with st.expander(f"Prediction {log['id']} - {log['timestamp'][:16]}"):
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Items", log.get('total_items', 0))
                    st.metric("Total Calories", f"{log.get('total_calories', 0) or 0:.1f}")
                
                with col2:
                    st.metric("Total Fats", f"{log.get('total_fats', 0) or 0:.1f}g")
                    st.metric("Total Protein", f"{log.get('total_protein', 0) or 0:.1f}g")
                
                with col3:
                    processing_time = log.get('processing_time_ms', 0) or 0
                    st.metric("Processing Time", f"{processing_time:.1f}ms")
                    if log.get('image_size'):
                        st.metric("Image Size", log['image_size'])
                
                # Show detected items
                if log.get('items'):
                    st.subheader("Detected Items:")
                    items_df = pd.DataFrame(log['items'])
                    
                    # Create a nice table
                    display_df = items_df[['label', 'confidence', 'calories']].copy()
                    display_df['confidence'] = display_df['confidence'].round(3)
                    display_df['calories'] = display_df['calories'].fillna(0)
                    
                    st.dataframe(
                        display_df,
                        column_config={
                            "label": "Food Item",
                            "confidence": st.column_config.ProgressColumn(
                                "Confidence",
                                help="Model confidence score",
                                min_value=0,
                                max_value=1,
                            ),
                            "calories": "Calories"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
    else:
        st.info("No recent predictions available")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🔄 Dashboard updates automatically every 30 seconds when auto-refresh is enabled. "
        "| 📡 Connected to API at " + API_BASE_URL
    )

if __name__ == "__main__":
    main()