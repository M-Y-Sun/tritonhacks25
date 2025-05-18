from ultralytics import YOLO
import cv2
import numpy as np
import os

# Get absolute path to the model
model_path = os.path.abspath("runs/detect/train10/weights/best.pt")
print(f"Loading model from: {model_path}")

# Load the model with exact path to weights
model = YOLO("runs/detect/train10/weights/best.pt")
print("Model loaded successfully")

print("Initializing camera...")
# Initialize webcam
cap = cv2.VideoCapture(0)

# Wait a bit for the camera to warm up
cv2.waitKey(1000)

# Capture single frame
ret, frame = cap.read()

# Release the camera right away
cap.release()

if ret:
    print("Image captured successfully")
    frame_height, frame_width = frame.shape[:2]

    print("Running prediction...")
    # Run prediction on the frame
    results = model.predict(frame, conf=0.1)
    print(f"Number of detections: {len(results[0].boxes)}")

    # Get the first result
    result = results[0]
    
    # Create a copy of the frame for drawing
    annotated_frame = frame.copy()
    
    # Process each detection
    for box in result.boxes:
        # Get confidence
        conf = float(box.conf)
        print(f"Detection confidence: {conf:.2f}")
        
        # Get coordinates (convert to int)
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        print(f"Door detected at: ({x1}, {y1}, {x2}, {y2})")
        # Draw the box
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add confidence text
        conf_text = f"{conf:.2f}"
        cv2.putText(annotated_frame, conf_text, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Display the frame with boxes
    cv2.imshow('Door Detection', annotated_frame)
    
    # Wait for a key press (0 means wait indefinitely)
    cv2.waitKey(0)

# Close all windows
cv2.destroyAllWindows()