import cv2
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from collections import deque

class DoorPersonTracker:
    def __init__(self, person_model_path='yolov8n.pt', door_model_path='runs/detect/train10/weights/best.pt', fps=30):
        
        
        self.person_model = YOLO(person_model_path)
        self.door_model = YOLO(door_model_path)
        self.tracker = DeepSort(max_age=30)

        self.FPS = fps
        self.frame_count = 0

        self.door_found = False
        self.fixed_door_box = None
        self.BIG_ZONE = []
        self.SMALL_ZONE = []

        self.entered_count = 0
        self.exited_count = 0

        self.id_active = set()
        self.track_history = {}
        self.id_status = {}
        self.entered_ids = set()
        self.exited_ids = set()
        self.last_seen_frame = {}
        self.height_history = {}

        self.HEIGHT_HISTORY_LENGTH = 10
        self.MIN_HEIGHT_CHANGE = 5
        self.MIN_FRAMES_FOR_DIRECTION = 5
        self.MAX_MISSING_FRAMES = 30
        self.DOOR_CONFIDENCE = 0.3

    def point_in_polygon(self, point, polygon):
        return polygon and cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

    def calculate_height_trend(self, heights):
        if len(heights) < self.MIN_FRAMES_FOR_DIRECTION:
            return 0
        recent_heights = list(heights)[-self.MIN_FRAMES_FOR_DIRECTION:]
        total_change = recent_heights[-1] - recent_heights[0]
        if abs(total_change) < self.MIN_HEIGHT_CHANGE:
            return 0
        return 1 if total_change > 0 else -1

    def process_frame(self, frame):
        self.frame_count += 1
        height, width, _ = frame.shape

        # Detect door once
        if not self.door_found:
            door_results_list = self.door_model(frame, verbose=False)
            if door_results_list:
                door_results = door_results_list[0]
                for box in door_results.boxes:
                    if box.conf[0] > self.DOOR_CONFIDENCE:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        self.fixed_door_box = (x1, y1, x2, y2)

                        door_w = x2 - x1
                        door_h = y2 - y1
                        center_x = x1 + door_w / 2
                        center_y = y1 + door_h / 2

                        big_w = door_w * 1.8
                        big_h = door_h * 1.4
                        big_x1 = int(max(0, center_x - big_w / 2))
                        big_y1 = int(max(0, center_y - big_h / 2))
                        big_x2 = int(min(width, center_x + big_w / 2))
                        big_y2 = int(min(height, center_y + big_h / 2))
                        self.BIG_ZONE = [(big_x1, big_y1), (big_x2, big_y1), (big_x2, big_y2), (big_x1, big_y2)]

                        small_w = door_w * 0.5
                        small_h = door_h * 0.5
                        small_x1 = int(center_x - small_w / 2)
                        small_y1 = int(center_y - small_h / 2)
                        small_x2 = int(center_x + small_w / 2)
                        small_y2 = int(center_y + small_h / 2)
                        self.SMALL_ZONE = [(small_x1, small_y1), (small_x2, small_y1), (small_x2, small_y2), (small_x1, small_y2)]

                        self.door_found = True
                        break

        # Detect people
        person_results_list = self.person_model(frame, verbose=False)
        if not person_results_list:
            return frame
        person_results = person_results_list[0]
        detections = []

        for box, conf, cls in zip(person_results.boxes.xywh, person_results.boxes.conf, person_results.boxes.cls):
            if int(cls) == 0:  # person class
                x_center, y_center, w, h = box
                x = x_center - w / 2
                y = y_center - h / 2
                detections.append(([x, y, w, h], conf.item(), 'person'))

        tracks = self.tracker.update_tracks(detections, frame=frame)
        current_ids = set()

        for track in tracks:
            if not track.is_confirmed():
                continue

            tid = str(track.track_id)
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            center_point = ((x1 + x2) // 2, (y1 + y2) // 2)
            current_ids.add(tid)

            # Track height trend
            height_val = y2 - y1
            if tid not in self.height_history:
                self.height_history[tid] = deque(maxlen=self.HEIGHT_HISTORY_LENGTH)
            self.height_history[tid].append(height_val)
            trend = self.calculate_height_trend(self.height_history[tid])

            in_big = self.point_in_polygon(center_point, self.BIG_ZONE)
            in_small = self.point_in_polygon(center_point, self.SMALL_ZONE)
            prev_status = self.id_status.get(tid, 'outside')

            if in_small:
                self.id_status[tid] = 'small_zone'
            elif in_big:
                self.id_status[tid] = 'big_zone'
            else:
                self.id_status[tid] = 'outside'

            if prev_status in ['big_zone', 'outside'] and self.id_status[tid] == 'small_zone' and trend == -1:
                if tid not in self.entered_ids:
                    self.entered_ids.add(tid)
                    self.entered_count += 1
                    print(f"ENTERED: {tid}")
                    self.id_status[tid] = 'entered'

            if prev_status in ['big_zone', 'small_zone', 'entered'] and self.id_status[tid] == 'outside' and trend == 1:
                if tid not in self.exited_ids:
                    self.exited_ids.add(tid)
                    self.exited_count += 1
                    print(f"EXITED: {tid}")
                    self.id_status[tid] = 'exited'

            self.last_seen_frame[tid] = self.frame_count
            history = self.track_history.get(tid, deque(maxlen=self.FPS))
            history.append(center_point[0])
            self.track_history[tid] = history

        # Handle disappeared tracks
        disappeared_ids = [tid for tid in self.last_seen_frame if tid not in current_ids]
        for tid in disappeared_ids:
            if self.frame_count - self.last_seen_frame[tid] > self.MAX_MISSING_FRAMES:
                status = self.id_status.get(tid, 'outside')
                if status == 'big_zone' and tid not in self.entered_ids:
                    self.entered_ids.add(tid)
                    self.entered_count += 1
                    print(f"ASSUMED ENTRY: {tid}")
                    self.id_status[tid] = 'entered'
                for d in [self.last_seen_frame, self.track_history, self.id_status, self.height_history]:
                    d.pop(tid, None)
                self.id_active.discard(tid)

        self.id_active.update(current_ids)

        return frame

if __name__ == "__main__":
    # Initialize webcam
    cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        exit()
        
    # Initialize tracker
    tracker = DoorPersonTracker()
    
    print("Starting webcam feed... Press 'q' to quit")
    
    try:
        while True:
            # Read frame from webcam
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
                
            # Process frame and get tracks
            processed_frame = tracker.process_frame(frame)
            
            # Draw door zones if detected
            if tracker.door_found:
                # Draw big zone (blue)
                cv2.polylines(processed_frame, [np.array(tracker.BIG_ZONE, np.int32)], 
                            True, (255, 0, 0), 2)
                # Draw small zone (green)
                cv2.polylines(processed_frame, [np.array(tracker.SMALL_ZONE, np.int32)], 
                            True, (0, 255, 0), 2)
                # Draw door box (red)
                if tracker.fixed_door_box:
                    x1, y1, x2, y2 = tracker.fixed_door_box
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Draw person tracking boxes and IDs
            for track_id in tracker.id_active:
                if track_id in tracker.last_seen_frame and \
                   tracker.frame_count - tracker.last_seen_frame[track_id] <= tracker.MAX_MISSING_FRAMES:
                    
                    # Get status color
                    status = tracker.id_status.get(track_id, 'outside')
                    if status == 'entered':
                        color = (0, 255, 0)  # Green for entered
                    elif status == 'exited':
                        color = (0, 0, 255)  # Red for exited
                    else:
                        color = (255, 255, 0)  # Yellow for tracking
                    
                    # Draw tracking history if available
                    if track_id in tracker.track_history and track_id in tracker.height_history:
                        history = list(tracker.track_history[track_id])
                        heights = list(tracker.height_history[track_id])
                        
                        # Only draw if we have both position and height data
                        min_len = min(len(history), len(heights))
                        for i in range(1, min_len):
                            try:
                                pt1 = (int(history[i-1]), int(heights[i-1]))
                                pt2 = (int(history[i]), int(heights[i]))
                                cv2.line(processed_frame, pt1, pt2, color, 2)
                            except (IndexError, ValueError):
                                continue
                    
                    # Draw person ID and status
                    if track_id in tracker.track_history:
                        x = int(list(tracker.track_history[track_id])[-1])
                        y = int(list(tracker.height_history[track_id])[-1]) if track_id in tracker.height_history else 30
                        label = f"ID: {track_id} ({status})"
                        cv2.putText(processed_frame, label, (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Add counting information
            total_count = max(0, tracker.entered_count - tracker.exited_count)
            cv2.putText(processed_frame, f"Total Count: {total_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(processed_frame, f"Entered: {tracker.entered_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(processed_frame, f"Exited: {tracker.exited_count}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Display frame
            cv2.imshow('DoorPersonTracker', processed_frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("\nCleaned up and exited")
