# model.py
import os
import io
from typing import Any, Dict, List, Optional, Union
from ultralytics import YOLO
from PIL import Image
from .calorie_db import CALORIE_DB, canonicalize_class

ImageLike = Union[str, bytes, io.BytesIO, Image.Image]

class CalorieModel:
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
        conf: float = 0.25,
        warmup: bool = True,
    ):
        self.model_path = model_path or os.getenv("MODEL_PATH", "yolov8n.pt")
        if not os.path.exists(self.model_path):
            # Try to use a pre-trained YOLOv8 model that will be downloaded automatically
            self.model_path = "weights/yolov8n.pt"
            if not os.path.exists(self.model_path):
                # Fall back to downloading the model automatically
                self.model_path = "yolov8n.pt"
        
        self.device = device
        self.conf = max(0.0, min(1.0, float(conf)))  # Ensure conf is between 0 and 1

        self.model = YOLO(self.model_path)
        self.model.to(self.device)

        self.names: Dict[int, str] = getattr(getattr(self.model, "model", None), "names", None) \
                                     or getattr(self.model, "names", {}) or {}

        if warmup:
            try:
                img = Image.new("RGB", (640, 640), color=(0, 0, 0))
                _ = self.model.predict(img, conf=self.conf, device=self.device, verbose=False)
            except Exception as e:
                print(f"Warmup failed: {e}")
                pass

    def _to_pil(self, image: ImageLike) -> Optional[Image.Image]:
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image)).convert("RGB")
        if isinstance(image, io.BytesIO):
            return Image.open(image).convert("RGB")
        if isinstance(image, str) and os.path.exists(image):
            return Image.open(image).convert("RGB")
        return None

    def predict(
        self,
        image: ImageLike,
        conf: Optional[float] = None,
        classes: Optional[List[int]] = None,
        iou: Optional[float] = None,
        max_det: Optional[int] = None,
    ) -> Dict[str, Any]:
        use_conf = float(conf) if conf is not None else self.conf
        pil = self._to_pil(image)
        src = pil if pil is not None else image

        # Validate parameters to avoid None comparison issues
        predict_kwargs = {
            "source": src,
            "conf": use_conf,
            "device": self.device,
            "verbose": False,
        }
        
        # Only add optional parameters if they are not None
        if classes is not None:
            predict_kwargs["classes"] = classes
        if iou is not None:
            predict_kwargs["iou"] = float(iou)
        if max_det is not None:
            predict_kwargs["max_det"] = int(max_det)

        results = self.model.predict(**predict_kwargs)
        r = results[0]
        names = self.names or getattr(getattr(self.model, "model", None), "names", {}) or getattr(self.model, "names", {})

        items: List[Dict[str, Any]] = []
        if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
            for b in r.boxes:
                try:
                    cls_id = int(b.cls.item()) if b.cls is not None else 0
                    conf_score = float(b.conf.item()) if b.conf is not None else 0.0
                    
                    # Safely handle box coordinates
                    if b.xyxy is not None:
                        box_tensor = b.xyxy.squeeze()
                        if box_tensor.numel() >= 4:  # Ensure we have at least 4 coordinates
                            xyxy = [float(v) for v in box_tensor.tolist()[:4]]
                        else:
                            xyxy = [0.0, 0.0, 0.0, 0.0]
                    else:
                        xyxy = [0.0, 0.0, 0.0, 0.0]
                    
                    raw_label = names.get(cls_id, str(cls_id))
                    canon = canonicalize_class(raw_label)
                    calories = CALORIE_DB.get(canon)
                    
                    items.append({
                        "label": raw_label,
                        "label_canonical": canon,
                        "confidence": conf_score,
                        "box": xyxy,
                        "calories": calories
                    })
                except Exception as e:
                    print(f"Error processing detection box: {e}")
                    continue

        # Calculate total calories, safely handling None values
        total_calories = 0
        for it in items:
            calories = it.get("calories")
            if calories is not None and calories > 0:
                total_calories += float(calories)
        
        return {"items": items, "total_calories": total_calories}
