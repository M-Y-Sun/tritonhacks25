import kagglehub
import os

# Download latest version of the dataset
path = kagglehub.dataset_download("sayedmohamed1/doors-detection")
print("Path to dataset files:", path)

from ultralytics import YOLO

# Load the pretrained nano model (smaller parameters)
model = YOLO("yolov8n.pt")

# Train the model using our local data.yaml with updated parameters
current_dir = os.path.dirname(os.path.abspath(__file__))
data_yaml = os.path.join(current_dir, "data.yaml")
model.train(data=data_yaml, epochs=30, imgsz=640, batch=32, half=True, cache=True, plots=True, patience=10, workers=8)

# Load the best model from the training run
weights_path = os.path.join(current_dir, "runs/detect/train/weights/best.pt")
model = YOLO(weights_path)

# Test the model on a sample image
test_image = os.path.join(path, "images/test/test.jpg")  # Adjust path if needed
results = model.predict(test_image, save=True, conf=0.3)