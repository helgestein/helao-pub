import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from mischbares_small import config
import time
import json

app = FastAPI(title="Pump action server V1",
    description="This is a very fancy pump action server",
    version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/pumping/formulation/")
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
            res = requests.get("{}/pump/primePump".format(pumpurl), 
                                params={'pump':p,'volume':v,'speed':s,
                                        'direction': direction,'read':True}).json()
            retl.append(res)
    
    for c,p in zip(comprel,pumps):
        v = int(totalvol*c)
        s = int(speed*c)
        if not v<0.001:
            print(v)
            requests.get("{}/pump/runPump".format(pumpurl),params={'pump':p}).json()
    retl.append(flushSerial()) #it is good to keep the buffer clean
    retc = return_class(parameters= {'comprel':json.dumps(comprel),'pumps':json.dumps(pumps),'speed':speed,'totalvol':totalvol,'direction':direction,
                                     'units': {'speed':'µl/min','totalvol':'µL'}},
                        data = {i:retl[i] for i in range(len(retl))})
    time.sleep(60*totalvol/speed)
    return retc


@app.get("/pumping/flushSerial/")
def flushSerial():
    res = requests.get("{}/pump/read".format(pumpurl)).json()
    retc = return_class(parameters= None,data = res)
    return retc



if __name__ == "__main__":
    pumpurl = "http://{}:{}".format(config['servers']['pumpServer']['host'], config['servers']['pumpServer']['port'])
    uvicorn.run(app, host=config['servers']['pumpingServer']['host'], 
                     port=config['servers']['pumpingServer']['port'])
