import requests
import time
from threading import Lock

class Request:
    """
    A utility class to handle requests to the FastAPI backend
    from the people detection system.
    """
    def __init__(self, building: str, room: str, outside_area: str):
        """
        Initialize the request handler.
        
        Args:
            building: The building identifier (e.g., 'CSE')
            room: The room identifier (e.g., 'B240')
            outside_area: The outside area identifier (e.g., 'hall')
        """
        self.building = building.lower()
        self.room = room
        self.outside_area = outside_area
        self.base_url = "http://localhost:8000"  # FastAPI server
        self.lock = Lock()
        
        # Initialize the room in the backend if it doesn't exist
        self._init_room()
        
        # Track local state to avoid unnecessary requests
        self.entered_count = 0
        self.exited_count = 0
    
    def _init_room(self):
        """Initialize the room in the backend"""
        try:
            url = f"{self.base_url}/{self.building}/add/{self.room}/"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"⚠️ Error initializing room: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error initializing room: {e}")
    
    def update(self, entered_count: int, exited_count: int):
        """
        Update the entered and exited counts.
        
        Args:
            entered_count: The total number of people who have entered
            exited_count: The total number of people who have exited
        """
        with self.lock:
            # Only send requests when the counts change
            if entered_count > self.entered_count:
                people_entering = entered_count - self.entered_count
                self._send_enter_request(people_entering)
                self.entered_count = entered_count
            
            if exited_count > self.exited_count:
                people_exiting = exited_count - self.exited_count
                self._send_exit_request(people_exiting)
                self.exited_count = exited_count
    
    def _send_enter_request(self, count: int):
        """Send request to update enter count"""
        try:
            url = f"{self.base_url}/{self.building}/enter/{self.room}/{count}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"⚠️ Error updating enter count: {response.status_code}")
            else:
                print(f"✅ Updated: {count} people entered {self.building}/{self.room}")
        except Exception as e:
            print(f"⚠️ Error updating enter count: {e}")
    
    def _send_exit_request(self, count: int):
        """Send request to update exit count"""
        try:
            url = f"{self.base_url}/{self.building}/exit/{self.room}/{count}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"⚠️ Error updating exit count: {response.status_code}")
            else:
                print(f"✅ Updated: {count} people exited {self.building}/{self.room}")
        except Exception as e:
            print(f"⚠️ Error updating exit count: {e}")

