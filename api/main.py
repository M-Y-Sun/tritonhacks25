from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from dispatch.tw_call import call as twilio_call
from dotenv import load_dotenv
import os
import datetime
import sys

# Load environment variables
load_dotenv()

# Add the parent directory of 'api' to the Python path
# This is to ensure that 'dispatch' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import logger

app = FastAPI()

# CORS Configuration
# Origins that are allowed to make cross-origin requests.
# You might want to restrict this to your frontend's URL in production.
origins = [
    "http://localhost",        # For local development if frontend is served from root
    "http://localhost:3000",   # Common port for React dev server
    "http://localhost:3001",   # Another common port
    "http://localhost:5173",   # Common port for Vite dev server
    # Add other origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Buildings data structure
buildings = {}

# Emergency reports storage
emergency_reports = []

class LocationData(BaseModel):
    latitude: float
    longitude: float

class EmergencyReport(BaseModel):
    school: str
    building: str
    message: str
    location: Optional[LocationData] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

@app.get("/{building}/feed", response_class=HTMLResponse)
async def feed(building):
    return """<!DOCTYPE html>
<html>
<head>
<title>Building Monitor</title>
<script>
    async function alarm () {
        req = await fetch('alarm')
    }
    async function run () {
        req = await fetch('count')
        rooms = await req.json()
        for (const room in rooms) {
            document.body.insertAdjacentHTML("afterbegin", `<p>Room ${room} has ${rooms[room]} people in it</p>`)
        }
    }
</script>
</head>
<body onload='run()'>
    <button onclick='alarm()'>
        Alarm authorities?
    </button>
</body>
</html>
"""

@app.get("/{building}/count")
async def show(building):
    if not building in buildings:
        # Return empty object if building not found
        return {}

    return buildings[building]

@app.get("/{building}/stats")
async def building_stats(building):
    """Return aggregated statistics for a building"""
    if not building in buildings:
        return {"entered": 0, "exited": 0}
    
    rooms = buildings[building]
    total_people = sum(rooms.values())
    
    # For now, we're estimating exited count
    # In a real app, you would track this from DetectingExitsAndEntrance.py
    return {
        "entered": total_people,
        "exited": 0  # Placeholder for actual exit count
    }

@app.get("/{building}/add/{room}/")
async def add_room(building, room):
    if not building in buildings:
        buildings[building] = {}
    if not room in buildings[building]:
        buildings[building][room] = 0

@app.get("/{building}/enter/{room_enter}/{person_count}")
async def update_full_enter(building, room_enter, person_count):
    return update_req(building, "", room_enter, person_count)

@app.get("/{building}/exit/{room_exit}/{person_count}")
async def update_full_exit(building, room_exit, person_count):
    return update_req(building, room_exit, "", person_count)

def update_req(building, room_leave, room_enter, person_count):
    if not building in buildings:
        buildings[building] = {}
    pcount = int(person_count)
    if room_enter != "":
        if room_enter in buildings[building]:
            buildings[building][room_enter] = buildings[building][room_enter] + pcount
        else:
            buildings[building][room_enter] = 0 + pcount
    if room_leave != "":
        buildings[building][room_leave] = max(
            buildings[building][room_leave] - pcount, 0
        )
    print(buildings)
    return {}

@app.post("/submit-emergency")
async def submit_emergency(report: EmergencyReport):
    logger.info(f"Received emergency report: {report.model_dump_json()}")
    
    # Construct a message for Twilio. You might want to customize this further.
    full_message = f"Emergency at {report.school}, building {report.building}. Message: {report.message}"
    if report.location:
        full_message += f". Location: lat {report.location.latitude}, lon {report.location.longitude}"
        
    try:
        # Call the Twilio function
        # Ensure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set as environment variables
        twilio_call(text=full_message)
        logger.info("Twilio call initiated successfully.")
        return {"status": "Emergency report submitted and call initiated"}
    except Exception as e:
        logger.error(f"Error initiating Twilio call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.get("/emergency-reports")
async def get_emergency_reports():
    """Get all emergency reports (admin only endpoint)"""
    return emergency_reports

# Mount the static files directory for serving the React frontend
app.mount("/static", StaticFiles(directory="../frontend/public"), name="static")

# Mount the frontend build directory as the root
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Ensure environment variables are loaded if you're using a .env file
    # from dotenv import load_dotenv
    # load_dotenv()
    
    # Check if Twilio credentials are set
    if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
        print("ERROR: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables must be set.")
        # logger.error("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables must be set.")
        # sys.exit(1) # Exit if credentials are not set

    uvicorn.run(app, host="0.0.0.0", port=8000)

