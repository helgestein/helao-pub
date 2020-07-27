import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from mischbares_small import config


app = FastAPI(title="Pump action server V1",
    description="This is a very fancy pump action server",
    version="1.0")

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/pumping/formulation/")
def formulation(comprel: list, pumps: list, speed: int, totalvol: int):
    #make sure the comprel makes sense
    comprel = [i/sum(comprel) for i in comprel]
    retl = []
    for c,p in zip(comprel,pumps):
        #someone check this logic ...
        #we pump at different speeds for formulation in the droplet coming out
        #to make all pumps stop at roughly the same time the volume per pump is also
        #adjusted 
        v = int(totalvol*c)
        s = int(speed*c)
        res = requests.get("{}/pump/dispenseVolume".format(pumpurl), 
                            params={'pump':p,'volume':v,'speed':s,
                                    'direction':1,'read':False,'stage':True}).json()
        retl.append(res)
    retl.append(requests.get("{}/pump/allOn".format(pumpurl), 
                    params={'time':totalvol/speed}).json())

    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'measure',
                                    'parameters':{'comprel':comprel,'pumps':pumps,'speed':speed,'totalvol':totalvol}},
                        data = {'data':retl})
    return retc

@app.get("/pumping/flushSerial/")
def flushSerial():
    res = requests.get("{}/pump/read".format(pumpurl)).json()

    retc = return_class(measurement_type='echem_measure',
                        parameters= {'command':'measure',
                                    'parameters':None},
                        data = {'data':res})
    return retc

if __name__ == "__main__":
    pumpurl = "http://{}:{}".format(config['servers']['pumpServer']['host'], config['servers']['pumpServer']['port'])
    uvicorn.run(app, host=config['servers']['pumpingServer']['host'], 
                     port=config['servers']['pumpingServer']['port'])