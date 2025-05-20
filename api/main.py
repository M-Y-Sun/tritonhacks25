import asyncio
import datetime
import os
import sys
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

import cv2
import numpy as np
from cv2.typing import MatLike
from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from requests.models import HTTPError

from DetectingExitsAndEntrance import DoorPersonTracker
from dispatch.tw_call import call as twilio_call_

# Load environment variables
load_dotenv()

# Add the parent directory of 'api' to the Python path
# This is to ensure that 'dispatch' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dispatch.logger import logger

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ],  # Add all frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def twilio_call(txt: str):
    twilio_call_(
        txt,
        Path("dispatch/caller.txt").read_text(),
        Path("dispatch/reciever.txt").read_text(),
    )


# Global variables for stream management
stream_active = False
current_message = ""
current_university = ""
current_building = ""
video_capture = None
tracker = DoorPersonTracker()

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


class StreamSettings(BaseModel):
    university: str
    building: str
    message: Optional[str] = None


class MessageUpdate(BaseModel):
    message: str


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
    return {"entered": total_people, "exited": 0}  # Placeholder for actual exit count


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

    # Get the current count of people in the building if available
    building_count = 0
    if report.building in buildings:
        building_count = sum(buildings[report.building].values())

    # Get the count from the tracker as well
    tracker_count = max(0, tracker.entered_count - tracker.exited_count)

    # Use the larger of the two counts
    total_count = max(building_count, tracker_count)

    # Construct a message for Twilio
    full_message = f"Emergency at {report.school}, building {report.building} with {total_count} people in it. Message: {report.message}"
    if report.location:
        full_message += f". Location: lat {report.location.latitude}, lon {report.location.longitude}"

    try:
        logger.info(
            f"Number of people using the main door: {tracker.entered_count - tracker.exited_count}"
        )
        # Call the Twilio function
        twilio_call(full_message)
        logger.info("Twilio call initiated successfully.")

        # Store the emergency report
        emergency_reports.append(report)

        return {
            "status": "Emergency report submitted and call initiated",
            "building_count": total_count,
        }
    except Exception as e:
        logger.error(f"Error initiating Twilio call: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate call: {str(e)}"
        )


@app.get("/emergency-reports")
async def get_emergency_reports():
    """Get all emergency reports (admin only endpoint)"""
    return emergency_reports


def get_frame():
    """
    Gets a frame from an open cv2 `video_capture`
    """

    global video_capture, tracker
    if video_capture is None or not video_capture.isOpened():
        return None

    success, frame = video_capture.read()
    if not success:
        return None

    # Process frame with tracker
    processed_frame = tracker.process_frame(frame)

    # Draw door zones if detected
    if tracker.door_found:
        # Draw big zone (blue)
        cv2.polylines(
            processed_frame,
            [np.array(tracker.BIG_ZONE, np.int32)],
            True,
            (255, 0, 0),
            2,
        )
        # Draw small zone (green)
        cv2.polylines(
            processed_frame,
            [np.array(tracker.SMALL_ZONE, np.int32)],
            True,
            (0, 255, 0),
            2,
        )
        # Draw door box (red)
        if tracker.fixed_door_box:
            x1, y1, x2, y2 = tracker.fixed_door_box
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Draw person tracking boxes and IDs
    for track_id in tracker.id_active:
        if (
            track_id in tracker.last_seen_frame
            and tracker.frame_count - tracker.last_seen_frame[track_id]
            <= tracker.MAX_MISSING_FRAMES
        ):

            # Get status color
            status = tracker.id_status.get(track_id, "outside")
            if status == "entered":
                color = (0, 255, 0)  # Green for entered
            elif status == "exited":
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
                        pt1 = (int(history[i - 1]), int(heights[i - 1]))
                        pt2 = (int(history[i]), int(heights[i]))
                        cv2.line(processed_frame, pt1, pt2, color, 2)
                    except (IndexError, ValueError):
                        continue

            # Draw person ID and status
            if track_id in tracker.track_history:
                x = int(list(tracker.track_history[track_id])[-1])
                y = (
                    int(list(tracker.height_history[track_id])[-1])
                    if track_id in tracker.height_history
                    else 30
                )
                label = f"ID: {track_id} ({status})"
                cv2.putText(
                    processed_frame,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

    # Add counting information
    total_count = max(0, tracker.entered_count - tracker.exited_count)
    cv2.putText(
        processed_frame,
        f"Total Count: {total_count}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        processed_frame,
        f"Entered: {tracker.entered_count}",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        processed_frame,
        f"Exited: {tracker.exited_count}",
        (10, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
    )

    # Add location information
    cv2.putText(
        processed_frame,
        f"{current_university} - {current_building}",
        (10, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    # Add emergency message if present
    if current_message:
        cv2.putText(
            processed_frame,
            f"Message: {current_message}",
            (10, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )

    return processed_frame


async def generate_frames():
    while stream_active:
        if video_capture is None or not video_capture.isOpened():
            await asyncio.sleep(0.1)
            continue

        frame = get_frame()
        if frame is None:
            await asyncio.sleep(0.1)
            continue

        # Encode frame as JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        # Yield frame in MJPEG format
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

        await asyncio.sleep(0.033)  # ~30 FPS


def cleanup_stream():
    global stream_active, video_capture, current_message, current_university, current_building
    stream_active = False
    if video_capture is not None:
        video_capture.release()
        video_capture = None
    current_message = ""
    current_university = ""
    current_building = ""


@app.post("/start_stream")
async def start_stream(settings: StreamSettings):
    """
    POST request from React frontend server (localhost:3000/video-feed).
    Reqeusted from VideoFeed.jsx
    """

    global stream_active, current_message, current_university, current_building, video_capture, tracker

    # First ensure any existing stream is fully cleaned up
    await stop_stream()

    try:
        # Reset tracker state
        tracker.reset()

        # Initialize video capture
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            raise HTTPException(status_code=500, detail="Could not open video capture")

        # Set video capture properties to ensure fresh start
        video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        video_capture.set(cv2.CAP_PROP_FPS, 30)

        # Clear a few frames to flush any old data
        for _ in range(5):
            video_capture.read()

        stream_active = True
        current_university = settings.university
        current_building = settings.building
        if settings.message:
            current_message = settings.message

        return {"status": "Stream started"}
    except Exception as e:
        if video_capture:
            video_capture.release()
        stream_active = False
        current_message = ""
        current_university = ""
        current_building = ""
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop_stream")
async def stop_stream():
    global stream_active, video_capture, tracker, current_message, current_university, current_building

    try:
        # Reset tracker state
        tracker.reset()

        # Release and cleanup video capture
        if video_capture:
            video_capture.release()
        video_capture = None

        # Reset all stream-related variables
        stream_active = False
        current_message = ""
        current_university = ""
        current_building = ""

        # Small delay to ensure cleanup is complete
        await asyncio.sleep(0.1)

        return {"status": "Stream stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update_message")
async def update_message(message_update: MessageUpdate):
    global current_message
    current_message = message_update.message

    # If there's an active count, include it in the Twilio message
    if tracker is not None:
        total_count = max(0, tracker.entered_count - tracker.exited_count)
        full_message = f"Emergency at {current_university}, {current_building}. {message_update.message}. Current occupancy: {total_count} people."

        try:
            twilio_call(full_message)
            logger.info("Twilio call initiated with updated message and count")
        except Exception as e:
            logger.error(f"Error initiating Twilio call: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to initiate call: {str(e)}"
            )

    return {"status": "Message updated"}


@app.get("/video_feed")
async def video_feed():
    if not stream_active:
        raise HTTPException(status_code=400, detail="Stream not active")

    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    contents = await file.read()  # read bytes
    # Convert bytes to numpy array and decode image
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Process the frame
    tracker.process_frame(img)

    if tracker.entered_count - tracker.exited_count < 0:
        final = 0
    else:
        final = tracker.entered_count - tracker.exited_count

    # You can return info, e.g., counts, or send back an image as bytes
    # Here just return counts for example:
    return {"numberOfPeople": final}


@app.get("/current-count")
async def get_current_count():
    """Get the current count of people from the tracker"""
    if tracker is not None:
        current_count = max(0, tracker.entered_count - tracker.exited_count)
    else:
        current_count = 0

    return {"count": current_count}


@app.get("/get-talking-points")
async def get_talking_points():
    """Get talking points and current building information"""
    # Get current count from tracker
    current_count = (
        max(0, tracker.entered_count - tracker.exited_count) if tracker else 0
    )

    # For demo purposes, using hardcoded location
    # In a real app, this would come from a geocoding service
    location_info = {
        "address": "9500 Gilman Dr, La Jolla, CA 92093"  # Example for UCSD
    }

    # Suggested talking points
    talking_points = [
        "Clearly state the nature of the emergency",
        "Specify if the situation is life-threatening",
        "Report any injuries or immediate dangers",
        "Describe any suspicious individuals or activities",
        "Note any hazardous materials or conditions",
    ]

    return {
        "location": location_info,
        "occupancy_count": current_count,
        "talking_points": talking_points,
    }


sid_frames: dict[int, bool] = {}
connect_sid: int = 0


@app.get("/connect", response_class=HTMLResponse)
async def connect_serve() -> str:
    global connect_sid

    html = (
        Path("../frontend/public/connect.html")
        .read_text()
        .replace("__SERVER_ASSIGN_SID__", str(connect_sid), 1)
    )
    sid_frames.update({connect_sid: False})
    connect_sid += 1

    logger.debug(sid_frames)

    return html


def buffileof(sid: int) -> str:
    return f"ds{sid}buf.png"


class DataURLData(BaseModel):
    sid: int
    dataurl: str


@app.post("/connect")
async def connect_recv(data: DataURLData):
    if data.sid not in sid_frames:
        logger.error("SID not initialized for SID " + str(data.sid))
        raise HTTPException(500, "SID not initialized for SID " + str(data.sid))

    sid_frames[data.sid] = True

    logger.debug(sid_frames)

    response = urlopen(data.dataurl)

    fn = buffileof(data.sid)
    with open("buf/" + fn, "wb") as f:
        f.write(response.file.read())

    logger.info(f"Parsed URL; wrote to file `buf/{fn}'")

    return {
        "status": "Connect POST request received: base64 Data URL",
        "dataurl": data,
    }


class SIDData(BaseModel):
    sid: int


@app.post("/disconnect")
async def disconnect(data: SIDData):
    if data.sid not in sid_frames:
        logger.error("SID not initialized for SID " + str(data.sid))
        raise HTTPException(500, "SID not initialized for SID " + str(data.sid))

    del sid_frames[data.sid]

    logger.debug(sid_frames)

    fn = buffileof(data.sid)

    try:
        os.remove("buf/" + fn)
        logger.info(f"Removed file `buf/{fn}'")
    except FileNotFoundError:
        logger.info(f"No file to delete: `buf/{fn}'")
    except OSError as e:
        logger.error(f"Failed to delete `buf/{fn}'. Error: " + str(e))


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
        print(
            "WARNING: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables not set"
        )

    uvicorn.run(app, host="0.0.0.0", port=8000)
