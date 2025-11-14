# API Documentation - Top-3 Predictions & User Confirmations

## Overview

This API implements a sophisticated food prediction system with top-3 recommendations, confidence-based user interaction, and comprehensive logging of user selections.

## Key Features

- 🎯 **Top-3 Predictions**: Returns top 3 food predictions with confidence scores
- 📊 **Confidence Threshold**: 70% threshold to determine if user confirmation is needed
- ✍️ **Custom Food Entry**: Users can enter food names manually when predictions are uncertain
- 📝 **Comprehensive Logging**: Tracks all predictions, user selections, and custom entries
- 📈 **Analytics**: Provides statistics on prediction accuracy and user behavior

---

## API Endpoints

### 1. Get Top-3 Predictions

**Endpoint**: `POST /predict/top3`

Get top 3 food predictions with confidence scores to show user for confirmation.

**Request**:
```bash
curl -X POST "http://localhost:8000/predict/top3" \
  -F "file=@food_image.jpg" \
  -F "session_id=optional-session-id"
```

**Response**:
```json
{
  "top_predictions": [
    {
      "rank": 1,
      "label": "pizza",
      "label_canonical": "pizza",
      "confidence": 0.8542,
      "confidence_percent": 85.42,
      "calories": 285,
      "protein": 12,
      "fats": 10,
      "box": [100, 150, 400, 500]
    },
    {
      "rank": 2,
      "label": "burger",
      "label_canonical": "burger_beef",
      "confidence": 0.6234,
      "confidence_percent": 62.34,
      "calories": 354,
      "protein": 25,
      "fats": 20,
      "box": [100, 150, 400, 500]
    },
    {
      "rank": 3,
      "label": "sandwich",
      "label_canonical": "sandwich",
      "confidence": 0.4521,
      "confidence_percent": 45.21,
      "calories": 250,
      "protein": 12,
      "fats": 8,
      "box": [100, 150, 400, 500]
    }
  ],
  "is_confident": true,
  "requires_user_input": false,
  "recommended_action": "confirm_or_override",
  "message": "Detected 'pizza' with 85.42% confidence. Please confirm or select alternative.",
  "confidence_threshold": 70.0,
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "processing_time_ms": 234.56,
  "image_size": "1920x1080"
}
```

**Recommended Actions**:
- `confirm_or_override`: High confidence (≥70%) - User should confirm or select alternative
- `select_or_manual`: Low confidence (<70%) - User should select from options or enter manually

---

### 2. Confirm User Selection

**Endpoint**: `POST /confirm`

Log user's final selection after viewing top-3 predictions.

**Request**:
```bash
curl -X POST "http://localhost:8000/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "selected_option": 1,
    "notes": "Looks correct"
  }'
```

**Request Body**:
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "selected_option": 1,  // 1-3 for predictions, 4 for custom
  "custom_food_name": null,  // Required if selected_option = 4
  "notes": "Optional notes"
}
```

**Response**:
```json
{
  "confirmation_id": 42,
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "final_choice": "pizza",
  "nutritional_info": {
    "calories": 285,
    "protein": 12,
    "fats": 10
  },
  "message": "Confirmation logged successfully"
}
```

---

### 3. Custom Food Entry

**Endpoint**: `POST /custom-entry`

Record a custom food entry when user enters food name manually.

**Request**:
```bash
curl -X POST "http://localhost:8000/custom-entry" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "food_name": "biryani",
    "quantity": 1.5,
    "notes": "Chicken biryani"
  }'
```

**Request Body**:
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "food_name": "biryani",
  "quantity": 1.5,
  "notes": "Optional notes"
}
```

**Response**:
```json
{
  "confirmation_id": 43,
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "food_name": "biryani",
  "quantity": 1.5,
  "nutritional_info": {
    "food_name": "biryani",
    "canonical_name": "chicken_briyani",
    "found_in_database": true,
    "calories": 480.0,
    "protein": 27.0,
    "fats": 18.0,
    "quantity": 1.5
  },
  "message": "Custom food entry logged successfully"
}
```

---

### 4. Get Nutritional Information

**Endpoint**: `GET /nutritional-info/{food_name}`

Get nutritional information for a specific food item.

**Request**:
```bash
curl "http://localhost:8000/nutritional-info/pizza?quantity=1.5"
```

**Response**:
```json
{
  "food_name": "pizza",
  "canonical_name": "pizza",
  "found_in_database": true,
  "calories": 427.5,
  "protein": 18.0,
  "fats": 15.0,
  "quantity": 1.5
}
```

---

### 5. Get Confirmation Logs

**Endpoint**: `GET /logs/confirmations`

Retrieve user confirmation logs with optional filters.

**Request**:
```bash
curl "http://localhost:8000/logs/confirmations?limit=50&offset=0&custom_only=false"
```

**Query Parameters**:
- `limit`: Number of records to return (1-1000, default: 100)
- `offset`: Number of records to skip (default: 0)
- `session_id`: Filter by specific session (optional)
- `custom_only`: Show only custom entries (default: false)

**Response**:
```json
{
  "confirmations": [
    {
      "id": 1,
      "session_id": "123e4567-e89b-12d3-a456-426614174000",
      "timestamp": "2025-11-15T10:30:00",
      "top_prediction": "pizza",
      "top_confidence": 0.8542,
      "second_prediction": "burger",
      "second_confidence": 0.6234,
      "third_prediction": "sandwich",
      "third_confidence": 0.4521,
      "user_selected_option": 1,
      "user_final_choice": "pizza",
      "is_custom_entry": false,
      "custom_food_name": null,
      "final_calories": 285,
      "final_protein": 12,
      "final_fats": 10,
      "confidence_threshold": 0.70,
      "was_confident": true,
      "notes": "Looks correct"
    }
  ],
  "limit": 50,
  "offset": 0,
  "count": 1,
  "filters": {
    "session_id": null,
    "custom_only": false
  }
}
```

---

### 6. Get Confirmation Statistics

**Endpoint**: `GET /logs/confirmation-stats`

Get statistics about user confirmations and model accuracy.

**Request**:
```bash
curl "http://localhost:8000/logs/confirmation-stats?days=7"
```

**Query Parameters**:
- `days`: Number of days to analyze (1-365, default: 7)

**Response**:
```json
{
  "statistics": {
    "total_confirmations": 150,
    "accepted_top_prediction": 120,
    "selected_alternative": 20,
    "custom_entries": 10,
    "avg_confidence_when_accepted": 0.8234,
    "avg_top_confidence": 0.7456,
    "high_confidence_predictions": 130,
    "low_confidence_predictions": 20,
    "top_prediction_accuracy": 80.0,
    "alternative_selection_rate": 13.33,
    "custom_entry_rate": 6.67,
    "most_custom_entries": [
      {
        "custom_food_name": "biryani",
        "count": 5
      }
    ]
  },
  "period_days": 7,
  "message": "Confirmation statistics retrieved successfully"
}
```

---

## User Interaction Flow

### High Confidence Scenario (≥70%)

```
1. User uploads image
   ↓
2. System returns top-3 predictions with confidence ≥70%
   ↓
3. User sees: "Detected 'pizza' with 85% confidence"
   Options: [Accept] [Select Alternative] [Enter Manually]
   ↓
4a. User accepts → POST /confirm with selected_option=1
4b. User selects alternative → POST /confirm with selected_option=2 or 3
4c. User enters manually → POST /custom-entry with food_name
   ↓
5. System logs confirmation and returns nutritional info
```

### Low Confidence Scenario (<70%)

```
1. User uploads image
   ↓
2. System returns top-3 predictions with confidence <70%
   ↓
3. User sees: "Low confidence (65%). Please select or enter manually"
   Shows: Top 3 suggestions + [Enter Manually] option
   ↓
4a. User selects suggestion → POST /confirm with selected_option=1-3
4b. User enters manually → POST /custom-entry with food_name
   ↓
5. System logs confirmation and returns nutritional info
```

---

## Database Schema

### user_confirmations Table

```sql
CREATE TABLE user_confirmations (
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
);
```

---

## Configuration

### Confidence Threshold

The default confidence threshold is **70%** (0.70). You can adjust this in the `PredictionHandler` initialization:

```python
prediction_handler = PredictionHandler(model, confidence_threshold=0.75)
```

### Session Management

- Sessions are identified by `session_id` (UUID v4)
- If not provided, the system generates one automatically
- Sessions track the complete user interaction flow

---

## Analytics Metrics

The system tracks:

- ✅ **Top Prediction Accuracy**: % of times users accept the #1 prediction
- 🔄 **Alternative Selection Rate**: % of times users choose options #2 or #3
- ✍️ **Custom Entry Rate**: % of times users enter food manually
- 📊 **Average Confidence**: Mean confidence of accepted predictions
- 🎯 **High/Low Confidence Split**: Distribution of predictions by confidence

---

## Example Client Implementation

### Frontend Flow (JavaScript)

```javascript
// Step 1: Upload image and get top-3 predictions
async function getPredictions(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch('/predict/top3', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Step 2: Show UI based on confidence
function displayPredictions(result) {
  if (result.is_confident) {
    // Show: "Detected X with Y% confidence"
    // Buttons: [Accept] [See Alternatives] [Enter Manually]
  } else {
    // Show: "Low confidence. Please select or enter:"
    // List all 3 options + [Enter Manually]
  }
}

// Step 3: Handle user selection
async function confirmSelection(sessionId, selectedOption, customName = null) {
  if (customName) {
    // Custom entry
    await fetch('/custom-entry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        food_name: customName,
        quantity: 1.0
      })
    });
  } else {
    // Accept prediction
    await fetch('/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        selected_option: selectedOption
      })
    });
  }
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid input)
- `413`: File too large
- `500`: Server error
- `503`: Service not available (model not loaded)

**Error Response Format**:
```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

---

## Best Practices

1. **Always use session IDs** to track complete user interactions
2. **Store predictions temporarily** before user confirmation (use Redis/cache)
3. **Provide clear UI feedback** about confidence levels
4. **Allow easy manual entry** when predictions fail
5. **Log everything** for model improvement
6. **Monitor accuracy metrics** to tune confidence threshold

---

## Future Enhancements

- [ ] Session-based storage (Redis) for temporary predictions
- [ ] User feedback loop for model retraining
- [ ] Batch prediction support
- [ ] Food portion size estimation
- [ ] Multi-language support for food names
- [ ] Integration with nutrition APIs for unknown foods

---

## Support

For questions or issues, please refer to the main README.md or create an issue in the repository.
