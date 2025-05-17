import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO

# Load YOLOv8 and Deep SORT
model = YOLO('yolov8n.pt')
tracker = DeepSort(max_age=30)

# Open video
video_path = 'PeopleDoor.MOV'
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("❌ Could not open video.")
    exit()

# Vertical reference line x-position
LINE_X = 300

# Count trackers
entered_left = 0
entered_right = 0
exited_left = 0
exited_right = 0

# Track state
id_last_seen_x = {}
id_active = set()
id_entered_side = {}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Rotate
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    height, width, _ = frame.shape

    # Draw line
    cv2.line(frame, (LINE_X, 0), (LINE_X, height), (255, 0, 0), 2)

    # Detection
    results = model(frame)[0]
    detections = []
    for box, conf, cls in zip(results.boxes.xywh, results.boxes.conf, results.boxes.cls):
        if int(cls) == 0:
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
        x1, y1, x2, y2 = map(int, track.to_ltrb())
        x_center = (x1 + x2) // 2
        current_ids.add(track_id)

        # Entry
        if track_id not in id_active:
            id_active.add(track_id)
            id_last_seen_x[track_id] = x_center

            if x_center < LINE_X:
                entered_left += 1
                id_entered_side[track_id] = 'left'
            else:
                entered_right += 1
                id_entered_side[track_id] = 'right'

        # Update last seen position
        id_last_seen_x[track_id] = x_center

    # Check for exits
    inactive_ids = list(id_active - current_ids)
    for track_id in inactive_ids:
        last_x = id_last_seen_x.get(track_id)
        side = 'left' if last_x < LINE_X else 'right'
        if id_entered_side.get(track_id) == 'left':
            exited_side = side
            exited_left += 1 if side == 'left' else 0
            exited_right += 1 if side == 'right' else 0
        elif id_entered_side.get(track_id) == 'right':
            exited_side = side
            exited_left += 1 if side == 'left' else 0
            exited_right += 1 if side == 'right' else 0

        # Remove tracked person
        id_active.remove(track_id)
        del id_last_seen_x[track_id]
        del id_entered_side[track_id]

    # Display stats
    cv2.putText(frame, f"Entered Left: {entered_left}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Entered Right: {entered_right}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Exited Left: {exited_left}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
    cv2.putText(frame, f"Exited Right: {exited_right}", (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)

    # Show frame
    cv2.imshow("Tracking Counts", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
