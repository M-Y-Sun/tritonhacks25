import cv2
import make_requests
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from collections import deque
import platform
import numpy as np
import sys

# === USER CONFIGURABLE SETTINGS ===
ENTRANCE_SIDE = 'left'         # Options: 'left' or 'right'
EXIT_SIDE = 'right'            # Options: 'left' or 'right'
SPEED_THRESHOLD = 15           # Speed threshold in pixels/frame for runners
# ==================================

# Load YOLOv8 model for person detection and door detection
person_model = YOLO('yolov8n.pt')
door_model = YOLO('runs/detect/train10/weights/best.pt')  # Load the trained door model
tracker = DeepSort(max_age=30)

# Initialize webcam capture with avfoundation for macOS
print("📸 Initializing camera...")
if platform.system() == 'Darwin':  # macOS
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print("❌ Could not access webcam using AVFoundation.")
        print("Please check camera permissions in System Settings > Privacy & Security > Camera")
        print("Make sure to grant camera access to your terminal/IDE.")
        sys.exit(1)
else:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not access webcam.")
        sys.exit(1)

# Configure camera settings
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Verify camera is working by reading a test frame
for _ in range(5):  # Try a few times as camera might need to warm up
    ret, test_frame = cap.read()
    if ret:
        break
    print("⚠️ Waiting for camera to initialize...")
    import time
    time.sleep(1)

if not ret:
    print("❌ Camera opened but failed to read frame. Please check camera permissions.")
    sys.exit(1)

print("✅ Camera initialized successfully!")

# Get video properties
FPS = cap.get(cv2.CAP_PROP_FPS)
if FPS == 0 or FPS is None:
    FPS = 30  # fallback if camera doesn't report it
FPS = int(FPS)
MIN_FRAMES_FOR_RUN = int(0.5 * FPS)

# State variables
entered_left = entered_right = 0
exited_left = exited_right = 0
runner_count = 0
id_last_seen_x = {}
id_active = set()
id_entered_side = {}
track_history = {}
counted_runners = set()
door_frame = None
door_center_x = None

# Initialize request object
requester = make_requests.Request(
    'proto_building',
    'B240',
    'hallway',
    'B240-hallway-cam'
)

# Colors for visualization
COLORS = {
    'box': (0, 255, 0),  # Green for bounding boxes
    'text': (255, 255, 255),  # White for text
    'text_bg': (0, 0, 0),  # Black background for text
    'door': (0, 255, 0),  # Green for door frame
    'door_line': (255, 0, 0)  # Red for door center line
}

def draw_person_box(frame, box, track_id, confidence):
    x1, y1, x2, y2 = map(int, box)
    
    # Check if the box is completely outside the frame
    height, width = frame.shape[:2]
    if (x1 >= width or x2 <= 0 or y1 >= height or y2 <= 0):
        return
    
    # Clip coordinates to frame boundaries
    x1 = max(0, min(x1, width))
    x2 = max(0, min(x2, width))
    y1 = max(0, min(y1, height))
    y2 = max(0, min(y2, height))
    
    # Only draw if the visible area is significant
    visible_width = x2 - x1
    visible_height = y2 - y1
    if visible_width <= 0 or visible_height <= 0:
        return
    
    # Draw the bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS['box'], 2)
    
    # Prepare label text
    label = f"ID: {track_id} ({confidence:.2f})"
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
    )
    
    # Draw background rectangle for text
    cv2.rectangle(
        frame,
        (x1, y1 - text_height - 5),
        (x1 + text_width, y1),
        COLORS['text_bg'],
        -1
    )
    
    # Draw text
    cv2.putText(
        frame, label, (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text'],
        1, cv2.LINE_AA
    )

def detect_door_frame(frame):
    global door_frame, door_center_x
    
    # Use the trained YOLO model to detect doors
    results = door_model.predict(frame, conf=0.3)[0]
    
    # If no doors detected, return False
    if len(results.boxes) == 0:
        return False
        
    # Get the box with highest confidence
    box = results.boxes[0]  # Get first detection
    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get box coordinates
    confidence = float(box.conf[0])
    
    # Only accept high confidence detections
    if confidence < 0.3:
        return False
        
    # Update door frame and center
    door_frame = (x1, y1, x2, y2)
    door_center_x = x1 + (x2 - x1)//2
    
    # Draw the door frame
    cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS['door'], 2)
    cv2.putText(frame, f"Door ({confidence:.2f})", (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['door'], 2)
    
    return True

print("✅ Running real-time tracking. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame read failed. Retrying...")
        # If camera failed, try to reinitialize it
        cap.release()
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            print("❌ Failed to reconnect to camera. Retrying in 3 seconds...")
            import time
            time.sleep(3)
        continue
    
    height, width, _ = frame.shape
    exit_is_right = (EXIT_SIDE == 'right')
    
    # Detect door frame if not already detected
    if door_frame is None:
        detect_door_frame(frame)
    
    # Draw door frame if detected
    if door_frame is not None:
        x1, y1, x2, y2 = door_frame
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS['box'], 2)
        # Draw vertical center line of door
        if door_center_x is not None:
            cv2.line(frame, (door_center_x, y1), (door_center_x, y2), (255, 0, 0), 2)
    
    # Detect people
    results = person_model(frame, verbose=False)[0]
    detections = []
    detection_info = []
    
    for box, conf, cls in zip(results.boxes.xywh, results.boxes.conf, results.boxes.cls):
        if int(cls) == 0 and conf > 0.5:  # person class with confidence threshold
            x_center, y_center, w, h = box
            # Make box tighter by reducing width and height slightly
            w = w * 0.9  # Reduce width by 10%
            h = h * 0.95  # Reduce height by 5%
            x = x_center - w / 2
            y = y_center - h / 2
            detections.append(([x, y, w, h], conf.item(), 'person'))
            detection_info.append({
                'bbox': [float(x), float(y), float(w), float(h)],
                'confidence': float(conf),
                'class': 'person'
            })
    
    # Track people
    tracks = tracker.update_tracks(detections, frame=frame)
    current_ids = set()
    tracked_people = []
    
    for track in tracks:
        if not track.is_confirmed():
            continue
        
        track_id = str(track.track_id)
        box = track.to_ltrb()
        x1, y1, x2, y2 = map(int, box)
        x_center = (x1 + x2) // 2
        current_ids.add(track_id)
        
        # Draw bounding box and ID
        draw_person_box(frame, box, track_id, track.get_det_conf())
        
        # Store tracking info for API
        tracked_people.append({
            'track_id': track_id,
            'bbox': [int(x1), int(y1), int(x2), int(y2)],
            'center': [x_center, (y1 + y2) // 2],
            'confidence': float(track.get_det_conf())
        })
        
        # Only process if we have detected a door
        if door_center_x is not None:
            # Register new person or update existing one
            if track_id not in id_active:
                id_active.add(track_id)
                id_last_seen_x[track_id] = x_center
                id_entered_side[track_id] = 'left' if x_center < door_center_x else 'right'
            else:
                # Check if person crossed the door
                last_x = id_last_seen_x[track_id]
                current_side = 'left' if x_center < door_center_x else 'right'
                last_side = 'left' if last_x < door_center_x else 'right'
                
                if current_side != last_side:  # Person crossed the door
                    if current_side == 'right':  # Moving left to right
                        if id_entered_side[track_id] == 'left':
                            entered_right += 1
                        else:
                            exited_left += 1
                    else:  # Moving right to left
                        if id_entered_side[track_id] == 'right':
                            entered_left += 1
                        else:
                            exited_right += 1
                
                id_last_seen_x[track_id] = x_center
            
            # Track speed for runners only on exit side
            condition = x_center > door_center_x if exit_is_right else x_center < door_center_x
            if condition:
                history = track_history.get(track_id, deque(maxlen=FPS))
                history.append(x_center)
                track_history[track_id] = history
                
                if len(history) >= MIN_FRAMES_FOR_RUN and track_id not in counted_runners:
                    dx = history[-1] - history[-MIN_FRAMES_FOR_RUN]
                    speed = abs(dx) / MIN_FRAMES_FOR_RUN
                    
                    if ((exit_is_right and dx > 0) or (not exit_is_right and dx < 0)) and speed > SPEED_THRESHOLD:
                        runner_count += 1
                        counted_runners.add(track_id)
                        print(f"🏃 Runner detected! ID {track_id}, Avg Speed: {speed:.2f}")
    
    # Clean up tracking data for people who haven't been seen recently
    inactive_ids = list(id_active - current_ids)
    for track_id in inactive_ids:
        track_history.pop(track_id, None)
        counted_runners.discard(track_id)
    
    # Overlay stats
    door_status = "Door Detected" if door_frame is not None else "No Door Detected"
    cv2.putText(frame, f"Status: {door_status} | Exit: {EXIT_SIDE}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    cv2.putText(frame, f"Entered Left: {entered_left}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Entered Right: {entered_right}", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Exited Left: {exited_left}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
    cv2.putText(frame, f"Exited Right: {exited_right}", (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
    cv2.putText(frame, f"Runners {ENTRANCE_SIDE}→{EXIT_SIDE}: {runner_count}", (10, 170),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Update API with detection and tracking info
    requester.update(
        entered_left,
        exited_left,
        entered_right,
        exited_right,
        detections=detection_info,
        tracks=tracked_people,
        door_frame=door_frame,
        door_center=door_center_x
    )
    
    # Show frame
    cv2.imshow("Real-Time Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
