# Frontend - Food Calorie Estimation

A beautiful, intuitive web interface for the Calorie Estimation Model with top-3 predictions and user confirmation flow.

## 🎨 Features

- **Drag & Drop Upload**: Easy image upload with drag-and-drop support
- **Adaptive UI**: Changes based on prediction confidence
- **Top-3 Recommendations**: Shows alternative predictions
- **Manual Entry**: Users can enter food names when predictions fail
- **Real-time Feedback**: Instant nutritional information
- **Dashboard Integration**: Quick access to analytics dashboard
- **Responsive Design**: Works on desktop, tablet, and mobile

---

## 🚀 Quick Start

### 1. Start Backend Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Start Dashboard (Optional)
```bash
cd dashboard
streamlit run streamlit_app.py
```

### 3. Open Frontend
Simply open `index.html` in your browser, or use a local server:

```bash
# Using Python
cd frontend
python -m http.server 8080

# Using Node.js
npx serve frontend

# Using VS Code Live Server
# Right-click index.html and select "Open with Live Server"
```

Then navigate to: `http://localhost:8080`

---

## 📁 File Structure

```
frontend/
├── index.html       # Main HTML structure
├── styles.css       # Styling and animations
├── app.js          # JavaScript logic and API calls
└── README.md       # This file
```

---

## 🎯 User Flow

### Scenario 1: High Confidence (≥70%)

```
1. User uploads food image
   ↓
2. System: "Detected Pizza with 85% confidence"
   ↓
3. User sees:
   - Food name
   - Confidence bar
   - Nutritional info (calories, protein, fats)
   - Actions: [Accept] [See Other Options] [Enter Manually]
   ↓
4. User clicks [Accept]
   ↓
5. Success screen with final nutritional information
```

### Scenario 2: Low Confidence (<70%)

```
1. User uploads food image
   ↓
2. System: "Low confidence. Please select from options"
   ↓
3. User sees:
   - Top 3 predictions with confidence scores
   - Nutritional info for each option
   - [Enter Food Name Manually] button
   ↓
4. User selects option 2
   ↓
5. Success screen with final nutritional information
```

### Scenario 3: Manual Entry

```
1. User clicks [Enter Manually] from any screen
   ↓
2. Form appears:
   - Food name input
   - Quantity input
   - Notes (optional)
   ↓
3. User enters "chicken biryani" and quantity 1.5
   ↓
4. System looks up nutritional info
   ↓
5. Success screen with adjusted nutritional information
```

---

## 🎨 UI Components

### Upload Section
- Drag-and-drop area
- File browser button
- Visual feedback on hover/drag

### High Confidence View
- Green badge with checkmark
- Large food name display
- Animated confidence bar
- Nutritional summary cards
- Three action buttons

### Low Confidence View
- Yellow warning badge
- List of 3 clickable options
- Each option shows:
  - Food name
  - Confidence percentage
  - Calories, protein, fats
- Manual entry button

### Manual Entry Form
- Text input for food name
- Number input for quantity
- Textarea for notes
- Submit and back buttons

### Success Screen
- Large green checkmark
- Final food name
- Nutritional information grid
- "Add Another" button
- "View Dashboard" button

---

## 🔧 Configuration

### API Endpoints

Edit `app.js` to change API URLs:

```javascript
const API_BASE_URL = 'http://localhost:8000';
const DASHBOARD_URL = 'http://localhost:8501';
```

### Styling

Customize colors in `styles.css`:

```css
:root {
    --primary-color: #4f46e5;
    --secondary-color: #06b6d4;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
}
```

---

## 📱 Responsive Design

The interface is fully responsive and adapts to:

- **Desktop**: Full multi-column layout
- **Tablet**: Adjusted spacing and grid layouts
- **Mobile**: Single column, stacked elements

Breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

---

## 🎬 Animations

- **Fade In**: Smooth section transitions
- **Hover Effects**: Buttons and cards
- **Loading Spinner**: During API calls
- **Confidence Bar**: Animated fill effect
- **Transform Effects**: Subtle lift on hover

---

## 🔌 API Integration

### POST /predict/top3
```javascript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch(`${API_BASE_URL}/predict/top3`, {
    method: 'POST',
    body: formData
});
```

### POST /confirm
```javascript
await fetch(`${API_BASE_URL}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: sessionId,
        selected_option: 1
    })
});
```

### POST /custom-entry
```javascript
await fetch(`${API_BASE_URL}/custom-entry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: sessionId,
        food_name: 'pizza',
        quantity: 1.5
    })
});
```

---

## 🐛 Error Handling

The frontend handles:

- **Network Errors**: Connection issues
- **API Errors**: Backend not running
- **File Validation**: Size and type checks
- **Input Validation**: Required fields
- **Offline Mode**: Network status detection

---

## 🎯 Best Practices

1. **Always show confidence**: Be transparent with users
2. **Provide alternatives**: Let users choose
3. **Easy manual entry**: Don't force wrong predictions
4. **Clear feedback**: Show loading and success states
5. **Accessible**: Keyboard navigation and screen readers

---

## 🔒 Security

- File type validation
- File size limits (10MB)
- Input sanitization
- CORS handling
- No inline scripts

---

## 🚀 Deployment

### Static Hosting (Netlify, Vercel, GitHub Pages)

1. Update API URLs to production endpoints
2. Build/deploy frontend folder
3. Configure CORS on backend

### With Backend

1. Serve frontend from FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

2. Or use Nginx as reverse proxy

---

## 🎨 Customization

### Add New Food Icons
Edit nutrition icons in HTML:
```html
<div class="nutrition-icon">🔥</div> <!-- Calories -->
<div class="nutrition-icon">🥩</div> <!-- Protein -->
<div class="nutrition-icon">🧈</div> <!-- Fats -->
```

### Change Confidence Threshold Display
Edit `app.js`:
```javascript
function showHighConfidenceResult(result) {
    const threshold = 70; // Customize here
    // ... rest of the code
}
```

### Add More Nutritional Info
Extend nutrition grid in `styles.css` and update JavaScript to fetch additional data.

---

## 📊 Performance

- Optimized images
- Minimal dependencies (no frameworks)
- CSS animations (GPU accelerated)
- Lazy loading for images
- Efficient DOM updates

---

## 🔄 Future Enhancements

- [ ] Image preview before upload
- [ ] Multiple food detection in one image
- [ ] Portion size estimation
- [ ] Favorite foods list
- [ ] Meal planning integration
- [ ] Progressive Web App (PWA)
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Voice input for food names
- [ ] Barcode scanning

---

## 🐛 Troubleshooting

### Backend Connection Issues
```
Error: "Failed to analyze image"
Solution: Check if backend is running on localhost:8000
```

### Dashboard Won't Open
```
Error: Dashboard button doesn't work
Solution: Start Streamlit dashboard on port 8501
```

### File Upload Fails
```
Error: "File size must be less than 10MB"
Solution: Compress image before uploading
```

### Predictions Not Showing
```
Error: Blank screen after upload
Solution: Check browser console for errors (F12)
```

---

## 📞 Support

For issues or questions:
1. Check backend logs
2. Open browser console (F12)
3. Verify API is running
4. Check network tab for failed requests

---

## 🎉 Credits

- Font: Inter from Google Fonts
- Icons: Unicode emoji
- Design: Modern minimal UI/UX
- Colors: Tailwind-inspired palette

---

**Built with ❤️ for easy calorie tracking**
