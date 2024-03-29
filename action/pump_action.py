import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import time
import json
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="Pump action server V2",
    description="This is a very fancy pump action server",
    version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/pump/formulation/")
def formulation(comprel: str, pumps: str, speed: int, totalvol: int, direction: int = 1):
    comprel = json.loads(comprel)
    pumps = json.loads(pumps)
    #make sure the comprel makes sense
    comprel = [i/sum(comprel) for i in comprel]
    retl = []
    for c,p in zip(comprel,pumps):
        v = int(totalvol*c)
        s = int(speed*c)
        if not v==0:
            res = requests.get("{}/pumpDriver/primePump".format(pumpurl), 
                                params={'pump':p,'volume':v,'speed':s,
                                        'direction': direction,'read':True}).json()
            retl.append(res)
    for c,p in zip(comprel,pumps):
        v = int(totalvol*c)
        s = int(speed*c)
        if not v<0.001:
            print(v)
            requests.get("{}/pumpDriver/runPump".format(pumpurl),params={'pump':p}).json()
    retl.append(flushSerial()) #it is good to keep the buffer clean
    retc = return_class(parameters= {'comprel':json.dumps(comprel),'pumps':json.dumps(pumps),'speed':speed,'totalvol':totalvol,'direction':direction,
                                     'units': {'speed':'µl/min','totalvol':'µL'}},
                        data = {i:retl[i] for i in range(len(retl))})
    #this following line needs to change and we need to ask is the RON state is either 0 or 1 for every pump
    #ony when the state is changed we know that it is done solve with while loop
    while True:
        #heck if done state is reached
        #call server driver if done
        #if done:
        reached = True
        if reached:
            break
            
    time.sleep(60*totalvol/speed)
    return retc


@app.get("/pump/flushSerial/")
def flushSerial():
    res = requests.get("{}/pumpDriver/read".format(pumpurl)).json()
    retc = return_class(parameters= None,data = res)
    return retc



if __name__ == "__main__":
    pumpurl = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
