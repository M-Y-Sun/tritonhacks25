import requests
class Request:
    def __init__(self, building, room_left, room_right, cam, server="http://127.0.0.1:8000"):
        self.building = building
        self.pleft = 0
        self.pright = 0
        self.pcam = 0
        self.room_left = room_left
        self.room_right = room_right
        self.server = server
        self.cam = cam
        try: 
            requests.get(f"{server}/{building}/add/{room_left}")
            requests.get(f"{server}/{building}/add/{room_right}")
        except:
            pass
    def update (
        self,
        enter_left,
        exit_left,
        enter_right,
        exit_right
    ):
        pchangeleft = exit_left - enter_left - self.pleft
        if (pchangeleft == 0):
            pass
        elif (pchangeleft < 0):
            requests.get(f"{self.server}/{self.building}/exit/{self.room_left}/{-pchangeleft}")
        else:
            requests.get(f"{self.server}/{self.building}/enter/{self.room_left}/{pchangeleft}")
        pchangeright = exit_right - enter_right - self.pright
        if (pchangeright == 0):
            pass
        elif (pchangeright < 0):
            requests.get(f"{self.server}/{self.building}/exit/{self.room_right}/{-pchangeright}")
        else:
            requests.get(f"{self.server}/{self.building}/enter/{self.room_right}/{pchangeright}")
        pchangecam = enter_left + enter_right - exit_left - exit_right - self.pcam
        if (pchangecam == 0):
            pass
        elif (pchangecam < 0):
            requests.get(f"{self.server}/{self.building}/exit/{self.cam}/{-pchangecam}")
        else:
            requests.get(f"{self.server}/{self.building}/enter/{self.cam}/{pchangecam}")
        self.pleft += pchangeleft
        self.pright += pchangeright
        self.pcam += pchangecam


