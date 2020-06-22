import requests


#dispense a formulation
pumpurl = "http://{}:{}".format("127.0.0.1", "13370")
res = requests.get("{}/pumping/formulation".format(pumpurl), 
                    params={comprel: [0.2,0.2,0.2,0.2,0.2], pumps: [0,1,2,3,4], speed: 1000, totalvol: 1000}).json()