from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app = FastAPI()

buildings = {}


@app.get("/{building}/feed",response_class=HTMLResponse)
async def feed (building):
    return '''<!DOCTYPE html>
<html>
<head>
<title>HELLO I AM HELLO</title>
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
'''
@app.get("/{building}/alarm")
async def show (
    building
):
    if not building in buildings:
        return {}
    return {}
@app.get("/{building}/count")
async def show (
    building
):
    if not building in buildings:
        return {}
    return buildings[building]
@app.get("/{building}/add/{room}/")
async def add_room (
    building,
    room
):

    if (not building in buildings):
        buildings[building] = {}
    if (not room in buildings[building]):
        buildings[building][room] = 0
@app.get("/{building}/enter/{room_enter}/{person_count}")
async def update_full(
    building,
    room_enter,
    person_count
):
    return update_req(
        building,
        '',
        room_enter,
        person_count
    )
@app.get("/{building}/exit/{room_exit}/{person_count}")
async def update_full(
    building,
    room_exit,
    person_count
):
    return update_req(
        building,
        room_exit,
        '',
        person_count
    )
def update_req(
    building,
    room_leave,
    room_enter,
    person_count
):
    if (not building in buildings):
        buildings[building] = {}
    pcount = int(person_count)
    if room_enter != '':
        if room_enter in buildings[building]:
            buildings[building][room_enter] = buildings[building][room_enter] + pcount
        else:
            buildings[building][room_enter] = 0 + pcount
    if room_leave != '':
        buildings[building][room_leave] = max(buildings[building][room_leave] - pcount,0)
    print(buildings)
    return {}
