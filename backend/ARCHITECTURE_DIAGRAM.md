# System Architecture - Top-3 Predictions Flow

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│  (Web/Mobile App - Dashboard/Frontend)                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ HTTP Requests
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    API ENDPOINTS                                │ │
│  │                                                                  │ │
│  │  POST /predict/top3     ─────►  Get top-3 predictions          │ │
│  │  POST /confirm          ─────►  Log user confirmation          │ │
│  │  POST /custom-entry     ─────►  Record custom food             │ │
│  │  GET  /nutritional-info ─────►  Lookup nutrition data          │ │
│  │  GET  /logs/confirmations ───►  View confirmation logs         │ │
│  │  GET  /logs/confirmation-stats►  Get statistics               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────┬──────────────────────┬───────────────────┬──────────────┘
            │                      │                   │
            ▼                      ▼                   ▼
┌──────────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  PredictionHandler   │  │  CalorieModel   │  │ PredictionLogger│
│  ──────────────────  │  │  ─────────────  │  │  ─────────────  │
│                      │  │                 │  │                 │
│ • Top-3 logic        │  │ • YOLOv8 model  │  │ • Database ops  │
│ • Confidence check   │  │ • Food detect   │  │ • Logging       │
│ • Nutrition calc     │  │ • Predictions   │  │ • Statistics    │
└──────────┬───────────┘  └────────┬────────┘  └────────┬────────┘
           │                       │                    │
           │                       │                    │
           └───────────┬───────────┴────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                     │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐│
│  │   calorie_db.py    │  │  prediction_logs   │  │   YOLOv8       ││
│  │   ──────────────   │  │  ───────────────   │  │   Weights      ││
│  │                    │  │                    │  │                ││
│  │ Food nutrition     │  │ • predictions      │  │ • yolov8n.pt   ││
│  │ database (dict)    │  │ • detected_items   │  │                ││
│  │                    │  │ • user_confirmations│  │                ││
│  └────────────────────┘  └────────────────────┘  └────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Interaction Flow Diagram

### Scenario A: High Confidence (≥70%)

```
┌─────────────┐
│   User      │
│ uploads     │
│  image      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  POST /predict/top3                     │
│  ─────────────────────                  │
│  • Model detects food                   │
│  • Gets top-3 predictions               │
│  • Top confidence: 85%                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  RESPONSE: High Confidence              │
│  ────────────────────────               │
│  {                                      │
│    "top_predictions": [                 │
│      {rank: 1, "pizza", 85.42%},       │
│      {rank: 2, "burger", 62.34%},      │
│      {rank: 3, "sandwich", 45.21%}     │
│    ],                                   │
│    "is_confident": true,                │
│    "recommended_action":                │
│       "confirm_or_override"             │
│  }                                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  USER SEES:                             │
│  ─────────                              │
│  ✓ Detected: Pizza (85%)                │
│  Calories: 285                          │
│                                         │
│  [Accept ✓]  [See Other Options]       │
└──────┬──────────────┬───────────────────┘
       │              │
       │              └──────┐
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│ User clicks │  OR  │ User clicks  │
│  [Accept]   │      │ [See Other]  │
└──────┬──────┘      └──────┬───────┘
       │                    │
       │                    ▼
       │            Shows all 3 options
       │            User selects 2 or 3
       │                    │
       └────────┬───────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  POST /confirm                          │
│  ─────────────                          │
│  {                                      │
│    "session_id": "...",                 │
│    "selected_option": 1,                │
│    "notes": "Correct"                   │
│  }                                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  SYSTEM:                                │
│  • Logs to user_confirmations table     │
│  • Returns nutritional info             │
│  • Updates statistics                   │
└─────────────────────────────────────────┘
```

---

### Scenario B: Low Confidence (<70%)

```
┌─────────────┐
│   User      │
│ uploads     │
│  image      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  POST /predict/top3                     │
│  ─────────────────────                  │
│  • Model detects food                   │
│  • Gets top-3 predictions               │
│  • Top confidence: 55% ⚠️               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  RESPONSE: Low Confidence               │
│  ───────────────────────                │
│  {                                      │
│    "top_predictions": [                 │
│      {rank: 1, "pizza", 55.23%},       │
│      {rank: 2, "burger", 48.12%},      │
│      {rank: 3, "sandwich", 42.87%}     │
│    ],                                   │
│    "is_confident": false,               │
│    "requires_user_input": true,         │
│    "recommended_action":                │
│       "select_or_manual"                │
│  }                                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  USER SEES:                             │
│  ─────────                              │
│  ⚠️ Low confidence (55%)                │
│  Please select the food:                │
│                                         │
│  ○ Pizza (55%)     285 cal              │
│  ○ Burger (48%)    354 cal              │
│  ○ Sandwich (43%)  250 cal              │
│                                         │
│  [Enter Food Name Manually...]          │
└──────┬───────────────────┬──────────────┘
       │                   │
       │                   │
       ▼                   ▼
┌─────────────┐    ┌──────────────────┐
│ User selects│ OR │ User clicks      │
│ option 1-3  │    │ [Enter Manually] │
└──────┬──────┘    └────────┬─────────┘
       │                    │
       │                    ▼
       │            ┌───────────────────┐
       │            │ User types:       │
       │            │ "chicken biryani" │
       │            └────────┬──────────┘
       │                     │
       │                     ▼
       │            ┌─────────────────────────┐
       │            │ POST /custom-entry      │
       │            │ ─────────────────       │
       │            │ {                       │
       │            │   "food_name":          │
       │            │     "chicken biryani",  │
       │            │   "quantity": 1.0       │
       │            │ }                       │
       │            └────────┬────────────────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  SYSTEM:                                │
│  • Logs to user_confirmations table     │
│  • Looks up nutrition in calorie_db     │
│  • Returns nutritional info             │
│  • Flags as custom entry                │
└─────────────────────────────────────────┘
```

---

## 🗄️ Database Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE OPERATIONS                       │
└─────────────────────────────────────────────────────────────┘

User Confirmation Logging:
───────────────────────────

┌─────────────────┐
│ User confirms   │
│ or enters food  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ log_user_confirmation()                 │
│ ──────────────────────                  │
│ Stores in user_confirmations table:     │
│                                         │
│ • session_id                            │
│ • top_prediction + confidence           │
│ • second_prediction + confidence        │
│ • third_prediction + confidence         │
│ • user_selected_option (1-4)            │
│ • user_final_choice                     │
│ • is_custom_entry (boolean)             │
│ • custom_food_name                      │
│ • final_calories, protein, fats         │
│ • confidence_threshold                  │
│ • was_confident                         │
│ • timestamp                             │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Data Available For:                     │
│ ──────────────────                      │
│ • Analytics dashboard                   │
│ • Model performance metrics             │
│ • User behavior analysis                │
│ • Food database expansion               │
│ • Model retraining data                 │
└─────────────────────────────────────────┘
```

---

## 📊 Statistics Generation Flow

```
┌─────────────────────────────────────────┐
│ GET /logs/confirmation-stats?days=7     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ get_confirmation_statistics()           │
│ ────────────────────────────            │
│ Analyzes user_confirmations table:      │
│                                         │
│ SELECT queries calculate:               │
│ • Total confirmations                   │
│ • Accepted top predictions              │
│ • Alternative selections                │
│ • Custom entries                        │
│ • Average confidences                   │
│ • Most custom-entered foods             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ RETURNS:                                │
│ ───────                                 │
│ {                                       │
│   "total_confirmations": 150,           │
│   "top_prediction_accuracy": 80.0%,     │
│   "alternative_selection_rate": 13.3%,  │
│   "custom_entry_rate": 6.7%,            │
│   "most_custom_entries": [...]          │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## 🔧 Component Dependencies

```
main.py (API Layer)
    │
    ├──► PredictionHandler
    │        │
    │        ├──► CalorieModel (YOLOv8)
    │        └──► calorie_db.py
    │
    └──► PredictionLogger
             │
             └──► SQLite Database
                      │
                      ├──► predictions table
                      ├──► detected_items table
                      └──► user_confirmations table
```

---

## 📈 Data Flow Summary

```
Image Upload
    ↓
Model Prediction (YOLO)
    ↓
Top-3 Extraction (PredictionHandler)
    ↓
Confidence Analysis (threshold: 70%)
    ↓
User Interface (dynamic based on confidence)
    ↓
User Selection (1-3 or custom)
    ↓
Database Logging (user_confirmations)
    ↓
Nutritional Info Response
    ↓
Analytics & Statistics
```

---

## 🎯 Key Decision Points

```
                    ┌─────────────┐
                    │  Confidence │
                    │   Check     │
                    └──────┬──────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
          ≥ 70%                       < 70%
             │                           │
             ▼                           ▼
    ┌────────────────┐         ┌────────────────┐
    │ confirm_or_    │         │ select_or_     │
    │ override       │         │ manual         │
    └────────────────┘         └────────────────┘
             │                           │
             ▼                           ▼
    Show top prediction        Show all 3 options
    with [Accept] button       + manual entry
```

---

This visual guide helps understand how all components work together to provide an intelligent, user-friendly food prediction system!
