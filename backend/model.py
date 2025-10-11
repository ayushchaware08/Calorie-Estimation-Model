from io import BytesIO
import os
from typing import List, Tuple

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

import requests
from PIL import Image


class ModelWrapper:
    """
    Predict returns list[ (class_name: str, confidence: float) ].
    Loading priority:
      1) local YOLO weights (YOLO_WEIGHTS env or default path)
      2) Roboflow hosted model (ROBOFLOW_API_KEY + project info from env)
      3) empty list fallback
    """
    def __init__(self):
        self.model = None
        self.mode = "none"
        self.names = {}
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Try local weights first
        weights = os.getenv("YOLO_WEIGHTS") or os.path.join(os.getcwd(), "runs", "detect", "train8", "weights", "best.pt")
        print(f"[ModelWrapper] Checking local weights: {weights}")
        if YOLO and os.path.isfile(weights):
            try:
                print(f"[ModelWrapper] Loading local YOLO model...")
                self.model = YOLO(weights)
                self.names = getattr(self.model, "names", {})
                self.mode = "local"
                print(f"[ModelWrapper] Local model loaded successfully. Classes: {list(self.names.values())}")
            except Exception as e:
                print(f"[ModelWrapper] Failed to load local model: {e}")
                self.model = None
                self.mode = "none"
        else:
            print(f"[ModelWrapper] Local weights not found or YOLO not available")

        # Roboflow fallback
        if self.mode == "none":
            self.roboflow_api_key = os.getenv("ROBOFLOW_API_KEY")
            workspace = os.getenv("ROBOFLOW_WORKSPACE")
            project = os.getenv("ROBOFLOW_PROJECT") 
            version = os.getenv("ROBOFLOW_VERSION", "1")
            
            print(f"[ModelWrapper] Checking Roboflow: api_key={'***' if self.roboflow_api_key else None}, workspace={workspace}, project={project}, version={version}")
            
            if self.roboflow_api_key and workspace and project:
                # Construct Roboflow URL from env vars
                self.roboflow_url = f"https://detect.roboflow.com/{workspace}/{project}/{version}"
                self.mode = "roboflow"
                print(f"[ModelWrapper] Roboflow mode enabled: {self.roboflow_url}")
            else:
                print(f"[ModelWrapper] Roboflow config incomplete - falling back to empty predictions")
        
        print(f"[ModelWrapper] Initialized in mode: {self.mode}")

    def predict(self, image: Image.Image, conf: float = 0.25) -> List[Tuple[str, float]]:
        results = []
        if self.mode == "local" and self.model is not None:
            # ultralytics model.predict accepts PIL.Image directly
            # set conf via kwargs if supported
            res = self.model.predict(source=image, conf=conf)  # returns list-like
            # parse first (and likely only) batch
            for r in res:
                boxes = getattr(r, "boxes", None)
                if boxes is None:
                    continue
                # boxes.cls and boxes.conf are tensors/arrays
                cls_arr = getattr(boxes, "cls", [])
                conf_arr = getattr(boxes, "conf", [])
                for i in range(len(conf_arr)):
                    try:
                        cls_idx = int(cls_arr[i])
                        cls_name = self.names.get(cls_idx, str(cls_idx))
                        conf_val = float(conf_arr[i])
                        results.append((cls_name, conf_val))
                    except Exception:
                        continue
            return results

        if self.mode == "roboflow":
            # Roboflow hosted inference: POST image bytes to endpoint with api_key query param
            params = {"api_key": self.roboflow_api_key}
            buf = BytesIO()
            image.save(buf, format="JPEG")
            buf.seek(0)
            files = {"file": ("image.jpg", buf, "image/jpeg")}
            try:
                print(f"[ModelWrapper] Sending request to Roboflow: {self.roboflow_url}")
                r = requests.post(self.roboflow_url, params=params, files=files, timeout=30)
                print(f"[ModelWrapper] Roboflow response status: {r.status_code}")
                r.raise_for_status()
                data = r.json()
                print(f"[ModelWrapper] Roboflow response: {data}")
                
                preds = data.get("predictions", [])
                for p in preds:
                    # Roboflow returns 'class' and 'confidence'
                    cls_name = p.get("class") or p.get("label") or ""
                    conf_val = float(p.get("confidence", 0.0))
                    if conf_val >= conf:  # Apply confidence threshold
                        results.append((cls_name, conf_val))
                print(f"[ModelWrapper] Parsed {len(results)} predictions above confidence {conf}")
            except Exception as e:
                print(f"[ModelWrapper] Roboflow request failed: {e}")
                return []
            return results

        # fallback empty
        return []
