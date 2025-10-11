Calorie Estimation Backend
==========================

This folder provides a minimal FastAPI backend for running inference with the YOLO model used in the notebook `Calorie-count-model-final.ipynb`.

Files
- `main.py` - FastAPI app with `/health` and `/predict` endpoints.
- `model.py` - Model wrapper that tries to load `runs/detect/train8/weights/best.pt` or falls back to `yolov8n.pt` if available.
- `calorie_db.py` - Simple mapping of class names to calorie values.
- `requirements.txt` - Minimal dependencies to run the API.

Quick start

1. (Optional) Create a virtual environment and activate it.
2. Install dependencies:

   pip install -r requirements.txt

3. If you want to use the trained model from the notebook, place the `best.pt` model at:

   runs/detect/train8/weights/best.pt

4. Run the server:

   uvicorn backend.main:app --host 0.0.0.0 --port 8000

API
- GET /health - returns {"status": "ok"}
- POST /predict - form upload `file` (image). Returns detected items and estimated calories.

Notes
- Install `ultralytics` only if you need YOLO inference in the backend. The wrapper will work without it but return empty predictions.
