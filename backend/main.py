from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .model import ModelWrapper
from .calorie_db import CALORIE_DB
import io
from PIL import Image

app = FastAPI(title="Calorie Estimation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = ModelWrapper()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Invalid image file", "detail": str(e)})

    try:
        detections = model.predict(image)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Model prediction failed", "detail": str(e)})

    items = []
    total_calories = 0
    for cls_name, conf in detections:
        cal = CALORIE_DB.get(cls_name)
        items.append({"class": cls_name, "confidence": float(conf), "calories": cal})
        if cal:
            total_calories += cal

    return {"items": items, "total_calories": total_calories}
