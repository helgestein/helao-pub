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

#issues:
#rate-limiting step is serial read commands. i have serial timeout at .1 right now. .05 and lower do not work.
#this means .1 second between each pump turning on in formulation

#i think my pump primings are loaded incorrectly too, but that does not matter.

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
        res = requests.get("{}/pump/primePump".format(pumpurl), 
                            params={'pump':p,'volume':v,'speed':s,
                                    'direction':1,'read':True}).json()
        retl.append(res)
    for p in pumps:
        res = requests.get("{}/pump/runPump".format(pumpurl),params={'pump':p}).json()
        retl.append(res)
    retl.append(flushSerial()) # need to call a read function regularly to flush things out or it crashes, they seem to slow it down
    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'measure',
                                    'parameters':{'comprel':comprel,'pumps':pumps,'speed':speed,'totalvol':totalvol}},
                        data = {'data':retl})
    return retc

@app.get("/pumping/flushSerial/")
def flushSerial():
    try:
        res = requests.get("{}/pump/read".format(pumpurl)).json()
    except:
        print('read error')
    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'flushSerial','parameters':None},
                        data = {'data':res})
    return retc

@app.get("/pumping/resetPrimings")
def resetPrimings():
    retl = []
    for i in range(14):
        res = requests.get("{}/pump/primePump".format(pumpurl),params={'pump':i,'volume':0,'speed':20,'read':True}).json()
        retl.append(res)
        print('pump '+str(i)+' reset')
        time.sleep(.2) #if you try to send too many serial commands too fast something gets garbled.
    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'resetPrimings','parameters':None},
                        data = {'data':retl})
    return retc

@app.get("/pumping/getPrimings")
def getPrimings():
    res = requests.get("{}/pump/getPrimings".format(pumpurl)).json()
    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'getPrimings','parameters':None},
                        data = {'data':res})
    return retc

@app.get("/pumping/refreshPrimings")
def refreshPrimings():
    res = requests.get("{}/pump/refreshPrimings".format(pumpurl)).json()
    retc = return_class(measurement_type='pumping',
                        parameters= {'command':'refreshPrimings','parameters':None},
                        data = {'data':res})
    return retc


if __name__ == "__main__":
    pumpurl = "http://{}:{}".format(config['servers']['pumpServer']['host'], config['servers']['pumpServer']['port'])
    uvicorn.run(app, host=config['servers']['pumpingServer']['host'], 
                     port=config['servers']['pumpingServer']['port'])