import cv2
import make_requests
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from collections import deque

# === USER CONFIGURABLE SETTINGS ===
LINE_X = 300                    # X position of the vertical line
ENTRANCE_SIDE = 'left'         # Options: 'left' or 'right'
EXIT_SIDE = 'right'            # Options: 'left' or 'right'
SPEED_THRESHOLD = 15           # Speed threshold in pixels/frame for runners
# ==================================

# Load YOLOv8 and Deep SORT
model = YOLO('yolov8n.pt')
tracker = DeepSort(max_age=30)

# Camera setup with platform-specific settings
def setup_camera():
    if platform.system() == 'Darwin':  # macOS
        # Try different camera indices
        for index in range(2):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Set camera properties
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                # Attempt to read a frame to verify camera works
                ret, _ = cap.read()
                if ret:
                    return cap
                cap.release()
        print("❌ Could not find a working camera.")
        exit()
    else:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not cap.isOpened():
            print("❌ Could not access webcam.")
            exit()
        return cap

# Open camera
cap = setup_camera()

# Try to get FPS
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
requester = make_requests.Request(
    'proto_building',
    'B240',
    'hallway',
    'B240-hallway-cam'
)
print("✅ Running real-time tracking. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame read failed.")
        break

    height, width, _ = frame.shape
    exit_is_right = (EXIT_SIDE == 'right')

    # Draw vertical reference line
    cv2.line(frame, (LINE_X, 0), (LINE_X, height), (255, 0, 0), 2)

    # Detect people
    results = model(frame, verbose=False)[0]
    detections = []
    for box, conf, cls in zip(results.boxes.xywh, results.boxes.conf, results.boxes.cls):
        if int(cls) == 0:
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
        current_ids.add(track_id)

        # Register new person
        if track_id not in id_active:
            id_active.add(track_id)
            id_last_seen_x[track_id] = x_center
            if x_center < LINE_X:
                entered_left += 1
                id_entered_side[track_id] = 'left'
            else:
                entered_right += 1
                id_entered_side[track_id] = 'right'

        id_last_seen_x[track_id] = x_center

        # Track speed for runners only on exit side
        condition = x_center > LINE_X if exit_is_right else x_center < LINE_X
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

    # Check if people exited
    inactive_ids = list(id_active - current_ids)
    for track_id in inactive_ids:
        last_x = id_last_seen_x.get(track_id)
        side = 'left' if last_x < LINE_X else 'right'

        if id_entered_side.get(track_id) == 'left':
            if side == 'left':
                exited_left += 1
            else:
                exited_right += 1
        elif id_entered_side.get(track_id) == 'right':
            if side == 'left':
                exited_left += 1
            else:
                exited_right += 1

        id_active.remove(track_id)
        id_last_seen_x.pop(track_id, None)
        id_entered_side.pop(track_id, None)
        track_history.pop(track_id, None)
        counted_runners.discard(track_id)

    # Overlay stats
    cv2.putText(frame, f"Line X: {LINE_X} | Exit: {EXIT_SIDE}", (10, 20),
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
    try:
        requests.update (
            enter_left,
            exit_left,
            enter_right,
            exit_right
        )
    except:
        pass
    # Show
    cv2.imshow("Real-Time Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
