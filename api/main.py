from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, Any

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    timestamp: str

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
    """Submit an emergency report"""
    emergency_reports.append(report.dict())
    print(f"Emergency report received: {report}")
    # In a real app, this would trigger notifications, alerts, etc.
    return {"success": True, "report_id": len(emergency_reports)}

@app.get("/emergency-reports")
async def get_emergency_reports():
    """Get all emergency reports (admin only endpoint)"""
    return emergency_reports

# Mount the static files directory for serving the React frontend
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")
