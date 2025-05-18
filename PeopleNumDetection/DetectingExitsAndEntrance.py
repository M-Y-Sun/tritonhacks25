import cv2
import numpy as np
import make_requests
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from collections import deque
import platform
import sys

# === USER CONFIGURABLE SETTINGS ===
SPEED_THRESHOLD = 15               # Speed threshold in pixels/frame for runners
FPS_FALLBACK = 30
DOOR_CONFIDENCE = 0.3             # Confidence threshold for door detection

# ==================================
# Load YOLOv8 for people and doors, and Deep SORT
person_model = YOLO('yolov8n.pt') # For person detection
door_model = YOLO('runs/detect/train10/weights/best.pt')  # Your trained door model
tracker = DeepSort(max_age=30)

# Camera setup with platform-specific settings
def setup_camera():
    if platform.system() == 'Darwin':  # macOS
        for index in range(2):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                ret, _ = cap.read()
                if ret:
                    return cap
                cap.release()
        print("❌ Could not find a working camera.")
        sys.exit() # Use sys.exit()
    else:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not cap.isOpened():
            print("❌ Could not access webcam.")
            sys.exit() # Use sys.exit()
        return cap

# Open camera
cap = setup_camera()

# Try to get FPS
FPS = cap.get(cv2.CAP_PROP_FPS)
if FPS == 0 or FPS is None:
    FPS = FPS_FALLBACK
FPS = int(FPS)
MIN_FRAMES_FOR_RUN = int(0.5 * FPS)

# State variables for door detection and zones
door_found = False
fixed_door_box = None
BIG_ZONE = []
SMALL_ZONE = []

# State variables for tracking
entered_count = exited_count = runner_count = 0
id_active = set()
track_history = {}
counted_runners = set()
id_status = {}         # Track status: 'outside', 'big_zone', 'small_zone', 'entered', 'exited'
entered_ids = set()
exited_ids = set()
last_seen_frame = {}   # Track last seen frame number per ID
requester = make_requests.Request (
    'CSE',
    'B240',
    'hall',
)
MAX_MISSING_FRAMES = 30  # Frames to assume disappeared inside big zone = entered

frame_count = 0  # global frame counter

# Add after the other state variables
height_history = {}  # Track height changes for each person
HEIGHT_HISTORY_LENGTH = 10  # Number of frames to track height changes
MIN_HEIGHT_CHANGE = 5  # Minimum pixels of height change to consider significant
MIN_FRAMES_FOR_DIRECTION = 5  # Minimum frames needed to determine direction

def calculate_height_trend(heights):
    """
    Calculate if height is generally increasing or decreasing
    Returns: 1 for increasing, -1 for decreasing, 0 for no clear trend
    """
    if len(heights) < MIN_FRAMES_FOR_DIRECTION:
        return 0
        
    # Look at the last MIN_FRAMES_FOR_DIRECTION frames
    recent_heights = list(heights)[-MIN_FRAMES_FOR_DIRECTION:]
    total_change = recent_heights[-1] - recent_heights[0]
    
    if abs(total_change) < MIN_HEIGHT_CHANGE:
        return 0
    return 1 if total_change > 0 else -1

def point_in_polygon(point, polygon):
    if not polygon: # Check if polygon is empty
        return False
    return cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

print("✅ Initializing. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame read failed.")
        break

    frame_count += 1
    height, width, _ = frame.shape

    if not door_found:
        cv2.putText(frame, "Searching for door...", (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        door_results_list = door_model(frame, verbose=False) # It's a list
        if door_results_list:
            door_results = door_results_list[0]
            for box in door_results.boxes:
                if box.conf[0] > DOOR_CONFIDENCE: # Access confidence score correctly
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    fixed_door_box = (x1, y1, x2, y2)
                    
                    door_w = x2 - x1
                    door_h = y2 - y1
                    center_x = x1 + door_w / 2
                    center_y = y1 + door_h / 2

                    # Calculate BIG_ZONE (1.4x), ensuring it stays within frame boundaries
                    big_w = door_w * 1.8
                    big_h = door_h * 1.4
                    
                    # Calculate initial coordinates
                    big_x1_ideal = center_x - big_w / 2
                    big_y1_ideal = center_y - big_h / 2
                    big_x2_ideal = center_x + big_w / 2
                    big_y2_ideal = center_y + big_h / 2

                    # Clip to frame boundaries (0, 0, width, height)
                    big_x1 = int(max(0, big_x1_ideal))
                    big_y1 = int(max(0, big_y1_ideal))
                    big_x2 = int(min(width, big_x2_ideal)) # 'width' is frame width
                    big_y2 = int(min(height, big_y2_ideal)) # 'height' is frame height
                    
                    # Recalculate width and height based on clipped coordinates
                    # This maintains the aspect ratio as much as possible if one dimension was heavily clipped
                    # However, perfect 1.4x aspect ratio might be lost if both are heavily clipped against corners
                    final_big_w = big_x2 - big_x1
                    final_big_h = big_y2 - big_y1

                    BIG_ZONE = [(big_x1, big_y1), (big_x2, big_y1), (big_x2, big_y2), (big_x1, big_y2)]

                    # Calculate SMALL_ZONE (0.5x of original door)
                    small_w = door_w * 0.5
                    small_h = door_h * 0.5
                    small_x1 = int(center_x - small_w / 2)
                    small_y1 = int(center_y - small_h / 2)
                    small_x2 = int(center_x + small_w / 2)
                    small_y2 = int(center_y + small_h / 2)
                    SMALL_ZONE = [(small_x1, small_y1), (small_x2, small_y1), (small_x2, small_y2), (small_x1, small_y2)]
                    
                    door_found = True
                    print(f"🚪 Door found at {fixed_door_box}. BIG_ZONE: {BIG_ZONE}, SMALL_ZONE: {SMALL_ZONE}")
                    print("🕵️‍♂️ Starting person tracking with dynamic zones.")
                    break # Found a door, stop searching this frame
        if door_found and fixed_door_box: # Draw original door box if found
             cv2.rectangle(frame, (fixed_door_box[0], fixed_door_box[1]), (fixed_door_box[2], fixed_door_box[3]), (255, 0, 0), 2) # Blue
             cv2.putText(frame, "Detected Door", (fixed_door_box[0], fixed_door_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)


    if door_found:
        # Draw fixed door, BIG_ZONE, and SMALL_ZONE
        if fixed_door_box:
            cv2.rectangle(frame, (fixed_door_box[0], fixed_door_box[1]), (fixed_door_box[2], fixed_door_box[3]), (255, 0, 0), 2) # Blue for original door
            cv2.putText(frame, "Detected Door", (fixed_door_box[0], fixed_door_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        if BIG_ZONE:
            cv2.polylines(frame, [np.array(BIG_ZONE, np.int32)], isClosed=True, color=(255, 255, 0), thickness=2) # Yellow
            cv2.putText(frame, "BIG ZONE", (BIG_ZONE[0][0], BIG_ZONE[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        if SMALL_ZONE:
            cv2.polylines(frame, [np.array(SMALL_ZONE, np.int32)], isClosed=True, color=(0, 255, 255), thickness=2) # Cyan
            cv2.putText(frame, "SMALL ZONE", (SMALL_ZONE[0][0], SMALL_ZONE[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Detect people using person_model
        person_results_list = person_model(frame, verbose=False)
        if person_results_list:
            person_results = person_results_list[0]
            detections = []
            
            for box, conf, cls in zip(person_results.boxes.xywh, person_results.boxes.conf, person_results.boxes.cls):
                if int(cls) == 0:  # person class
                    x_center, y_center, w, h = box
                    x = x_center - w / 2
                    y = y_center - h / 2
                    detections.append(([x, y, w, h], conf.item(), 'person'))
            
            tracks = tracker.update_tracks(detections, frame=frame)
            current_ids = set()
            
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = str(track.track_id)
                box = track.to_ltrb()
                x1_p, y1_p, x2_p, y2_p = map(int, box)
                x_center_p = (x1_p + x2_p) // 2
                y_center_p = (y1_p + y2_p) // 2
                center_point_p = (x_center_p, y_center_p)
                current_ids.add(track_id)

                cv2.rectangle(frame, (x1_p, y1_p), (x2_p, y2_p), (0, 255, 0), 2) # Green for person
                cv2.putText(frame, f'ID {track_id}', (x1_p, y1_p - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # After getting track box coordinates
                person_height = y2_p - y1_p
                
                # Update height history
                if track_id not in height_history:
                    height_history[track_id] = deque(maxlen=HEIGHT_HISTORY_LENGTH)
                height_history[track_id].append(person_height)
                
                # Calculate height trend
                height_trend = calculate_height_trend(height_history[track_id])

                in_big_zone = point_in_polygon(center_point_p, BIG_ZONE)
                in_small_zone = point_in_polygon(center_point_p, SMALL_ZONE)
                prev_status = id_status.get(track_id, 'outside')

                if in_small_zone:
                    id_status[track_id] = 'small_zone'
                elif in_big_zone:
                    id_status[track_id] = 'big_zone'
                else:
                    id_status[track_id] = 'outside'

                # Modified entry/exit detection with height trend
                if prev_status == 'outside' and id_status[track_id] == 'big_zone':
                    pass
                elif (prev_status == 'big_zone' or prev_status == 'outside') and id_status[track_id] == 'small_zone':
                    if track_id not in entered_ids and height_trend == -1:  # Height DECREASING = moving away = entering
                        entered_ids.add(track_id)
                        entered_count += 1
                        id_status[track_id] = 'entered'
                        print(f"🚪 ID {track_id} ENTERED (height trend: decreasing)")

                if prev_status in ['big_zone', 'small_zone', 'entered'] and id_status[track_id] == 'outside':
                    if track_id not in exited_ids and height_trend == 1:  # Height INCREASING = moving closer = exiting
                        exited_ids.add(track_id)
                        exited_count += 1
                        id_status[track_id] = 'exited'
                        print(f"🚪 ID {track_id} EXITED (height trend: increasing)")

                # Optional: Visualize height trend with text
                trend_text = "↑" if height_trend == 1 else "↓" if height_trend == -1 else "-"
                cv2.putText(frame, f'H:{trend_text}', (x1_p, y2_p + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                last_seen_frame[track_id] = frame_count
                history = track_history.get(track_id, deque(maxlen=FPS))
                history.append(x_center_p)
                track_history[track_id] = history

                if len(history) >= MIN_FRAMES_FOR_RUN and track_id not in counted_runners:
                    dx = history[-1] - history[-MIN_FRAMES_FOR_RUN]
                    speed = abs(dx) / MIN_FRAMES_FOR_RUN
                    if speed > SPEED_THRESHOLD:
                        runner_count += 1
                        counted_runners.add(track_id)
                        print(f"🏃 Runner detected! ID {track_id}, Avg Speed: {speed:.2f}")

            disappeared_ids = [tid for tid in last_seen_frame if tid not in current_ids]
            for tid in disappeared_ids:
                if frame_count - last_seen_frame[tid] > MAX_MISSING_FRAMES:
                    status = id_status.get(tid, 'outside')
                    if status == 'big_zone' and tid not in entered_ids: # Assumed entry if lost in BIG_ZONE
                        entered_ids.add(tid)
                        entered_count += 1
                        id_status[tid] = 'entered'
                        print(f"🕵️ Assumed entry (lost in BIG_ZONE): ID {tid}")
                    
                    last_seen_frame.pop(tid, None)
                    id_status.pop(tid, None)
                    track_history.pop(tid, None)
                    counted_runners.discard(tid)
                    id_active.discard(tid)
                    height_history.pop(tid, None)  # Clean up height history

            inactive_ids = list(id_active - current_ids)
            for tid in inactive_ids:
                id_status.pop(tid, None)
                track_history.pop(tid, None)
                counted_runners.discard(tid)
                last_seen_frame.pop(tid, None)
                id_active.discard(tid)
            id_active.update(current_ids)
        
        # Overlay stats
        cv2.putText(frame, f"Entered: {entered_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Exited: {exited_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
        cv2.putText(frame, f"Runners: {runner_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        try:
            requester.update(entered_count, exited_count)
        except Exception as e: # Catch specific exception if known, or general Exception
            # print(f"Error updating requester: {e}") # Optional: log error
            pass

    # Show frame
    cv2.imshow("Real-Time Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
