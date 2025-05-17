from fastapi import FastAPI

app = FastAPI()

buildings = {}


@app.get("/{building}/count")
async def show (
    building
):
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
