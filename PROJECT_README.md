# 🍽️ Food Calorie Estimation System with Top-3 Predictions

A comprehensive AI-powered food recognition and calorie estimation system with intelligent user interaction, top-3 recommendations, and real-time analytics dashboard.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ Key Features

### 🎯 Smart Predictions
- **Top-3 Recommendations**: Always shows 3 best predictions
- **Confidence-Based UX**: Adapts UI based on prediction confidence (70% threshold)
- **Manual Entry**: Users can enter food names when model is uncertain
- **Real-time Analysis**: Fast YOLOv8-based food detection

### 📊 Comprehensive Logging
- **User Confirmations**: Tracks all user selections and corrections
- **Prediction History**: Complete log of all predictions
- **Analytics Dashboard**: Real-time statistics and trends
- **Model Accuracy**: Tracks acceptance rates and user behavior

### 🎨 Modern Interface
- **Beautiful UI**: Clean, intuitive design with smooth animations
- **Responsive**: Works on desktop, tablet, and mobile
- **Drag & Drop**: Easy image upload
- **Real-time Feedback**: Instant nutritional information

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Web UI)                     │
│              http://localhost:8080                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI + YOLOv8)                  │
│              http://localhost:8000                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  • PredictionHandler (Top-3 Logic)                │  │
│  │  • CalorieModel (YOLO Detection)                  │  │
│  │  • PredictionLogger (Database)                    │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ API Calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Dashboard (Streamlit Analytics)                │
│              http://localhost:8501                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- 10MB+ free disk space

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/Calorie-Estimation-Model.git
cd Calorie-Estimation-Model
```

2. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Install Dashboard Dependencies**
```bash
cd ../dashboard
pip install -r requirements.txt
```

### Running the System

**Option 1: Automated Launch (Windows)**
```powershell
.\start_all.ps1
```

**Option 2: Manual Start**

Terminal 1 - Backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
python server.py
```

Terminal 3 - Dashboard (Optional):
```bash
cd dashboard
streamlit run streamlit_app.py
```

### Access URLs
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

---

## 📱 Usage Guide

### 1. Upload Food Image
- Open the frontend at http://localhost:8080
- Click "Choose Image" or drag & drop a food photo
- System analyzes the image (1-3 seconds)

### 2. Review Predictions

**High Confidence (≥70%)**
- See detected food with confidence percentage
- View nutritional information (calories, protein, fats)
- Options:
  - ✅ **Accept**: Confirm the prediction
  - 🔄 **See Other Options**: View alternatives
  - ✍️ **Enter Manually**: Type food name

**Low Confidence (<70%)**
- See 3 options with confidence scores
- Each shows nutritional information
- Select any option or enter manually

### 3. Confirm or Enter Custom
- **Accept Prediction**: Click option to confirm
- **Manual Entry**: Type food name, quantity, notes
- System looks up nutritional data

### 4. View Results
- See final nutritional summary
- Add another food
- View analytics dashboard

---

## 📊 Dashboard Features

### Real-time Analytics
- Total predictions
- Average calories per meal
- Processing time statistics
- Most detected foods

### Trends & Charts
- Daily calorie consumption
- Protein and fats tracking
- Detection frequency
- Model accuracy metrics

### User Behavior Insights
- Top prediction acceptance rate
- Alternative selection rate
- Custom entry frequency
- Most commonly misidentified foods

---

## 🛠️ API Endpoints

### Core Prediction Endpoints

**POST /predict/top3**
- Get top-3 predictions with confidence scores
- Returns adaptive UI recommendations

**POST /confirm**
- Log user selection/confirmation
- Track model accuracy

**POST /custom-entry**
- Record manual food entry
- Calculate nutritional information

**GET /nutritional-info/{food_name}**
- Lookup nutritional data
- Support portion sizes

### Analytics Endpoints

**GET /logs/confirmations**
- Retrieve user confirmation history
- Filter by session, custom entries

**GET /logs/confirmation-stats**
- Model accuracy statistics
- User behavior metrics

**GET /logs/statistics**
- General prediction statistics
- Time-based aggregations

See [API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) for complete details.

---

## 📁 Project Structure

```
Calorie-Estimation-Model/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── model.py                     # YOLOv8 model wrapper
│   ├── prediction_handler.py        # Top-3 prediction logic
│   ├── logging_db.py                # Database operations
│   ├── calorie_db.py                # Nutritional database
│   ├── websocket_manager.py         # Real-time updates
│   ├── requirements.txt             # Python dependencies
│   ├── API_DOCUMENTATION.md         # Complete API docs
│   ├── IMPLEMENTATION_SUMMARY.md    # Technical details
│   ├── QUICK_REFERENCE.md           # Quick API reference
│   └── weights/
│       └── yolov8n.pt              # Model weights
│
├── frontend/
│   ├── index.html                   # Main UI
│   ├── styles.css                   # Styling
│   ├── app.js                       # JavaScript logic
│   ├── server.py                    # Development server
│   └── README.md                    # Frontend docs
│
├── dashboard/
│   ├── streamlit_app.py            # Dashboard application
│   ├── requirements.txt            # Dashboard dependencies
│   └── DASHBOARD_README.md         # Dashboard docs
│
├── start_all.ps1                   # Launch script (Windows)
└── STARTUP_GUIDE.md                # Detailed startup guide
```

---

## 🎯 User Interaction Flow

```
┌─────────────┐
│ Upload Image│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Model Analyzes      │
│ Returns Top-3       │
└──────┬──────────────┘
       │
       ├─── Confidence ≥ 70% ───┐
       │                         │
       │                         ▼
       │              ┌──────────────────┐
       │              │ Show Top Result  │
       │              │ + Alternatives   │
       │              └────────┬─────────┘
       │                       │
       │                       ├─ Accept → Log
       │                       ├─ Select Alt → Log
       │                       └─ Manual Entry
       │
       └─── Confidence < 70% ───┐
                                 │
                                 ▼
                      ┌──────────────────┐
                      │ Show All 3       │
                      │ + Manual Option  │
                      └────────┬─────────┘
                               │
                               ├─ Select → Log
                               └─ Manual Entry
                                       │
                                       ▼
                              ┌────────────────┐
                              │ Success Screen │
                              │ + Nutrition    │
                              └────────────────┘
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python test_top3_predictions.py
```

### Manual Testing
1. Start all services
2. Upload test images
3. Verify predictions
4. Check dashboard updates
5. Test manual entry

### API Testing
```bash
# Test health
curl http://localhost:8000/health

# Test prediction
curl -X POST "http://localhost:8000/predict/top3" \
  -F "file=@test_image.jpg"
```

---

## 🎨 Customization

### Adjust Confidence Threshold
Edit `backend/main.py`:
```python
prediction_handler = PredictionHandler(model, confidence_threshold=0.75)
```

### Add Food Items
Edit `backend/calorie_db.py`:
```python
CALORIE_DB = {
    "new_food": {"calories": 200, "protein": 10, "fats": 5},
    # ... existing items
}
```

### Customize UI Colors
Edit `frontend/styles.css`:
```css
:root {
    --primary-color: #4f46e5;
    --success-color: #10b981;
    /* ... other colors */
}
```

---

## 📈 Performance

- **Prediction Speed**: 1-3 seconds per image
- **Model Size**: ~6MB (YOLOv8n)
- **Accuracy**: Depends on training data
- **Concurrent Users**: Supports multiple simultaneous requests

---

## 🔒 Security

- File size validation (10MB limit)
- MIME type checking
- SQL injection prevention
- CORS configuration
- Input sanitization

---

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
- Check if port 8000 is available
- Verify model weights exist
- Install all dependencies

**Frontend shows errors**
- Verify backend is running
- Check browser console (F12)
- Confirm API_BASE_URL is correct

**Dashboard is blank**
- Ensure backend is running
- Check Streamlit logs
- Verify API connection

See [STARTUP_GUIDE.md](STARTUP_GUIDE.md) for detailed troubleshooting.

---

## 🔄 Future Enhancements

- [ ] Multi-food detection in single image
- [ ] Portion size estimation
- [ ] Mobile app (React Native)
- [ ] Voice input for food names
- [ ] Meal planning integration
- [ ] Barcode scanning
- [ ] Recipe suggestions
- [ ] Export nutrition logs
- [ ] Multi-language support
- [ ] Dark mode

---

## 📚 Documentation

- [API Documentation](backend/API_DOCUMENTATION.md) - Complete API reference
- [Implementation Summary](backend/IMPLEMENTATION_SUMMARY.md) - Technical details
- [Quick Reference](backend/QUICK_REFERENCE.md) - Quick API guide
- [Startup Guide](STARTUP_GUIDE.md) - Detailed startup instructions
- [Frontend README](frontend/README.md) - Frontend documentation
- [Dashboard README](dashboard/DASHBOARD_README.md) - Dashboard guide

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- FastAPI framework
- Streamlit for dashboards
- Google Fonts (Inter)

---

## 📞 Support

For issues or questions:
- Check documentation
- Review troubleshooting guide
- Open an issue on GitHub
- Check API logs

---

## 🎉 Success Metrics

The system tracks:
- ✅ Top prediction acceptance rate: Target >80%
- 🔄 Alternative selection rate
- ✍️ Custom entry rate: Lower is better
- ⏱️ Average processing time
- 📊 User satisfaction

---

## 🌟 Highlights

- **Intelligent UX**: Adapts to prediction confidence
- **Complete Logging**: Tracks everything for improvement
- **Beautiful Design**: Modern, responsive interface
- **Real-time Analytics**: Instant insights
- **Production Ready**: Comprehensive error handling

---

**Built with ❤️ for healthy eating and calorie tracking**

🍽️ Happy tracking! 🥗
