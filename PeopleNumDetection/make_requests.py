import requests
class Request:
    def __init__(self, building_name, room_number, room_type, camera_id):
        self.building_name = building_name
        self.room_number = room_number
        self.room_type = room_type
        self.camera_id = camera_id
        self.base_url = "http://localhost:8000"  # FastAPI endpoint

    def update(self, entered_left, exited_left, entered_right, exited_right, 
               detections=None, tracks=None, door_frame=None, door_center=None):
        """
        Send an update to the FastAPI endpoint with detection and tracking information
        """
        data = {
            "building_name": self.building_name,
            "room_number": self.room_number,
            "room_type": self.room_type,
            "camera_id": self.camera_id,
            "counts": {
                "entered_left": entered_left,
                "exited_left": exited_left,
                "entered_right": entered_right,
                "exited_right": exited_right
            },
            "detections": detections or [],
            "tracks": tracks or [],
            "door": {
                "frame": list(door_frame) if door_frame else None,
                "center": door_center
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/update", json=data)
            if response.status_code != 200:
                print(f"⚠️ API request failed with status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Failed to send API request: {str(e)}")


