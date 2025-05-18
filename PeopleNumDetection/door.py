from ultralytics import YOLO
import cv2
import numpy as np

# Load your trained model
model = YOLO("runs/detect/train10/weights/best.pt")

# Initialize webcam
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        break

    # Run prediction on the frame
    results = model.predict(frame, conf=0.3)

    # Get the first result (since we only have one frame)
    result = results[0]

    # Draw boxes on the frame
    annotated_frame = result.plot()

    # Display the frame
    cv2.imshow("Door Detection", annotated_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()