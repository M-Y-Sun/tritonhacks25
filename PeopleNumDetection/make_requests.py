import requests
class Request:
    def __init__(self, building, room_left, room_right, server="http://127.0.0.1:8000"):
        self.building = building
        self.pleft = 0
        self.pright = 0
        self.pcam = 0
        self.room_left = room_left
        self.room_right = room_right
        self.server = server
        try: 
            requests.get(f"{server}/{building}/add/{room_left}")
            requests.get(f"{server}/{building}/add/{room_right}")
            
        except:
            pass
    def update (
        self,
        enter,
        exits
    ):
        pchangeleft = exits - enter - self.pleft        
        pchangeright = enter - exits - self.pright
        if (pchangeleft != 0 or pchangeright != 0): print(pchangeleft,pchangeright)

        if (pchangeleft == 0):
            pass
        elif (pchangeleft < 0):
            requests.get(f"{self.server}/{self.building}/exit/{self.room_left}/{-pchangeleft}",timeout=1)
        else:
            requests.get(f"{self.server}/{self.building}/enter/{self.room_left}/{pchangeleft}",timeout=1)
        self.pleft += pchangeleft
        if (pchangeright == 0):
            pass
        elif (pchangeright < 0):
            requests.get(f"{self.server}/{self.building}/exit/{self.room_right}/{-pchangeright}",timeout=1)
        else:
            requests.get(f"{self.server}/{self.building}/enter/{self.room_right}/{pchangeright}",timeout=1)
        self.pright += pchangeright

