import cv2
import numpy as np
import make_requests
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from collections import deque

# === USER CONFIGURABLE SETTINGS ===
SPEED_THRESHOLD = 15               # Speed threshold in pixels/frame for runners
FPS_FALLBACK = 30

# Zones defined as polygons (clockwise points)
BIG_ZONE = [(180, 200), (550, 200), (550, 900), (180, 900)]      # Large entry area
SMALL_ZONE = [(325, 200), (325, 900), (350+40, 900), (350+40, 200)]  # Smaller pass-through area inside big zone

# ==================================

# Load YOLOv8 and Deep SORT
model = YOLO('yolov8n.pt')
tracker = DeepSort(max_age=30)

# Open webcam or video
cap = cv2.VideoCapture("People.MOV")

if not cap.isOpened():
    print("❌ Could not access webcam or video.")
    exit()

# Try to get FPS
FPS = cap.get(cv2.CAP_PROP_FPS)
if FPS == 0 or FPS is None:
    FPS = FPS_FALLBACK
FPS = int(FPS)
MIN_FRAMES_FOR_RUN = int(0.5 * FPS)

# State variables
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

def point_in_polygon(point, polygon):
    return cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

print("✅ Running real-time tracking. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame read failed.")
        break

    frame_count += 1
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    height, width, _ = frame.shape

    # Draw zones
    cv2.polylines(frame, [np.array(BIG_ZONE, np.int32)], isClosed=True, color=(255, 255, 0), thickness=2)
    cv2.putText(frame, "BIG ENTRY ZONE", (BIG_ZONE[0][0], BIG_ZONE[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.polylines(frame, [np.array(SMALL_ZONE, np.int32)], isClosed=True, color=(0, 255, 255), thickness=2)
    cv2.putText(frame, "SMALL CENTER ZONE", (SMALL_ZONE[0][0], SMALL_ZONE[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Detect people
    results = model(frame, verbose=False)[0]
    detections = []
    for box, conf, cls in zip(results.boxes.xywh, results.boxes.conf, results.boxes.cls):
        if int(cls) == 0:  # person class
            x_center, y_center, w, h = box
            x = x_center - w / 2
            y = y_center - h / 2
            detections.append(([x, y, w, h], conf.item(), 'person'))

    # Track people
    tracks = tracker.update_tracks(detections, frame=frame)
    current_ids = set()

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = str(track.track_id)
        x1, y1, x2, y2 = map(int, track.to_ltrb())
        x_center = (x1 + x2) // 2
        y_center = (y1 + y2) // 2
        center_point = (x_center, y_center)
        current_ids.add(track_id)

        # Draw bounding box and ID
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f'ID {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Determine position status inside zones
        in_big_zone = point_in_polygon(center_point, BIG_ZONE)
        in_small_zone = point_in_polygon(center_point, SMALL_ZONE)

        prev_status = id_status.get(track_id, 'outside')

        # Update status based on current position
        if in_small_zone:
            id_status[track_id] = 'small_zone'
        elif in_big_zone:
            id_status[track_id] = 'big_zone'
        else:
            id_status[track_id] = 'outside'

        # Entry detection:
        # From outside → big_zone → small_zone means entered building
        if prev_status == 'outside' and id_status[track_id] == 'big_zone':
            # person just entered big zone
            pass  # can track if needed
        elif (prev_status == 'big_zone' or prev_status == 'outside') and id_status[track_id] == 'small_zone':
            # passed through center small zone → entered building
            if track_id not in entered_ids:
                entered_ids.add(track_id)
                entered_count += 1
                id_status[track_id] = 'entered'
                print(f"🚪 ID {track_id} ENTERED the building")

        # Exit detection:
        # If person was inside and moved outside big zone → exited building
        if prev_status in ['big_zone', 'small_zone', 'entered'] and id_status[track_id] == 'outside':
            if track_id not in exited_ids:
                exited_ids.add(track_id)
                exited_count += 1
                id_status[track_id] = 'exited'
                print(f"🏃 ID {track_id} EXITED the building")

        # Track last seen frame
        last_seen_frame[track_id] = frame_count

        # Track movement history for runner detection
        history = track_history.get(track_id, deque(maxlen=FPS))
        history.append(x_center)
        track_history[track_id] = history

        if len(history) >= MIN_FRAMES_FOR_RUN and track_id not in counted_runners:
            dx = history[-1] - history[-MIN_FRAMES_FOR_RUN]
            speed = abs(dx) / MIN_FRAMES_FOR_RUN
            if speed > SPEED_THRESHOLD:
                runner_count += 1
                counted_runners.add(track_id)
                print(f"🏃 Runner detected! ID {track_id}, Avg Speed: {speed:.2f}")

    # Check disappeared IDs for assumed entry (inside big zone but lost)
    disappeared_ids = [tid for tid in last_seen_frame if tid not in current_ids]
    for tid in disappeared_ids:
        if frame_count - last_seen_frame[tid] > MAX_MISSING_FRAMES:
            status = id_status.get(tid, 'outside')
            if status == 'big_zone' and tid not in entered_ids:
                entered_ids.add(tid)
                entered_count += 1
                id_status[tid] = 'entered'
                print(f"🕵️ Assumed entry (lost inside big zone): ID {tid}")
            # Cleanup
            last_seen_frame.pop(tid, None)
            id_status.pop(tid, None)
            track_history.pop(tid, None)
            counted_runners.discard(tid)
            id_active.discard(tid)

    # Cleanup inactive IDs (ids that disappeared not yet removed)
    inactive_ids = list(id_active - current_ids)
    for tid in inactive_ids:
        id_origin = None  # you may have id_origin in your original code
        id_status.pop(tid, None)
        track_history.pop(tid, None)
        counted_runners.discard(tid)
        last_seen_frame.pop(tid, None)
        id_active.discard(tid)

    id_active.update(current_ids)

    # Overlay stats
    cv2.putText(frame, f"Entered: {entered_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Exited: {exited_count}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
    cv2.putText(frame, f"Runners: {runner_count}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    try:
        requester.update(
            entered_count,
            exited_count        
        )
    except:
        pass
    # Show frame
    cv2.imshow("Real-Time Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
