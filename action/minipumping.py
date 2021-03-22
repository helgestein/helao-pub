import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
sys.path.append('..')
from util import list_to_dict
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


@app.get("/minipumping/formulation/")
def formulation(speed: int, volume: int, direction: int = 1):
    retl = []
    res = requests.get("{}/minipump/primePump".format(pumpurl), 
                        params={'volume':volume,'speed':speed,
                                'direction': direction,'read':True}).json()
    retl.append(res)
    requests.get("{}/minipump/runPump".format(pumpurl),params=None).json()
    retl.append(flushSerial())    
    print(retl)          #it is good to keep the buffer clean
    retl = list_to_dict(retl)
    retc = return_class(parameters = {'speed':speed,'volume':volume,'direction':direction,
                                      'units':{'volume':'µL','speed':'µL/s'}},data = retl)
    time.sleep(volume/speed)
    return retc

@app.get("/minipumping/flushSerial/")
def flushSerial():
    res = requests.get("{}/minipump/read".format(pumpurl)).json()
    retc = return_class(parameters= None,data = res)
    return retc



if __name__ == "__main__":
    pumpurl = "http://{}:{}".format(config['servers']['minipumpServer']['host'], config['servers']['minipumpServer']['port'])
    uvicorn.run(app, host=config['servers']['minipumpingServer']['host'], 
                     port=config['servers']['minipumpingServer']['port'])