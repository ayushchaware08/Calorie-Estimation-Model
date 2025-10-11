from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .model import CalorieModel
import io
from PIL import Image
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(title="Calorie Estimation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if ALLOWED_ORIGINS == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model: CalorieModel | None = None

@app.on_event("startup")
def _startup():
    global model
    try:
        model = CalorieModel()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        model = None

@app.get("/health")
def health():
    ok = model is not None and hasattr(model, "model")
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ok" if ok else "init"})

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Invalid image file", "detail": str(e)})

    try:
        result = model.predict(image)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Model prediction failed", "detail": str(e)})

    return result
