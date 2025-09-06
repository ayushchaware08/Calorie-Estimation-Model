#  Calorie Estimation Model

## 🎬 DEMO

<video controls src="Screen Recording 2025-09-07 020911.mp4" title="Calorie Estimation Demo"></video>

## Results
![alt text](results-1.jpeg)
![alt text](image-1.png)
## 🚀 Features

- **Real-time Food Detection**: Uses YOLOv8 to identify multiple food items in a single image
- **Calorie Estimation**: Provides caloric content for detected food items
- **Multi-Class Detection**: Trained to recognize various food categories:
  - Burgers (Beef & Chicken)
  - French Fries
  - Pizza
  - Fried Chicken
  - Chow Mein
  - Fruits (Apple, Watermelon, Tomato)
  - Boiled Eggs
  - And more...
- **Nutritional Information**: Beyond calories - get protein, fats, and fiber content
- **High Accuracy**: Model trained on diverse food dataset
- **Fast Inference**: Real-time detection capabilities

## 📋 Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended)
- Required packages:
  ```
  ultralytics==8.2.103
  roboflow==1.1.48
  PIL
  numpy
  ```

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Kyvra-Labs-Pvt-Ltd/Calorie-Estimation-Model.git
   cd Calorie-Estimation-Model
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Download the trained model**
   ```python
   from roboflow import Roboflow
   rf = Roboflow(api_key="YOUR_API_KEY")
   project = rf.workspace("ayush-trial-workspace").project("calorie-detection-iweay-czyjv")
   dataset = project.version(1).download("yolov8")
   ```

## 💻 Usage

### Training the Model

```python
# Train YOLOv8 model
!yolo task=detect mode=train model=yolov8s.pt data=data.yaml epochs=25 imgsz=800 plots=True
```

### Inference

```python
from ultralytics import YOLO
from PIL import Image

# Load the model
model = YOLO('runs/detect/train/weights/best.pt')

# Perform inference
results = model.predict(source='your_image.jpg', conf=0.25)

# Process results
for r in results:
    im_array = r.plot()
    im = Image.fromarray(im_array[..., ::-1])
    im.save('results.jpg')
```

## 📊 Model Performance

- **Training Results**: View training metrics in `runs/detect/train/results.png`
- **Confusion Matrix**: Available in `runs/detect/train/confusion_matrix.png`
- **Validation Results**: Check validation performance in `runs/detect/train/val_batch0_pred.jpg`

## 🎯 Results

The model achieves:

- High accuracy in food item detection
- Reliable calorie estimation
- Real-time processing capabilities

## 📁 Project Structure

```
calorie-estimation-model/
├── Calorie-count-model-final.ipynb  # Main notebook
├── data/                           # Dataset directory
│   ├── train/
│   ├── valid/
│   └── test/
├── runs/                           # Training outputs
├── models/                         # Saved models
└── sample_images/                  # Example images
```

## 🔧 Custom Training

1. **Prepare your dataset**

   - Use Roboflow to annotate images
   - Export in YOLOv8 format

2. **Modify data.yaml**

   - Update class names
   - Adjust paths

3. **Train the model**
   - Adjust epochs and image size
   - Monitor training metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Dataset from Roboflow Universe
- YOLOv8 by Ultralytics
- Nutritional database sources
