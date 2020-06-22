import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI(title="Pump action server V1",
    description="This is a very fancy pump action server",
    version="1.0",)

@app.get("/pumping/formulation_succ/")
def formulation_successive(comprel: list, pumps: list, speed: int, totalvol: int):
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
                            params={'pump':p,'volume':v,'speed':speed,
                                    'direction':1,'read':False,'stage':False}).json()
        retl.append(res)

    retc = return_class(measurement_type='echem_measure',
                        parameters= {'command':'measure',
                                    'parameters':{'comprel':comprel,'pumps':pumps,'speed':speed,'totalvol':totalvol}},
                        data = {'data':retl})
    return retc

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
                            params={'pump':p,'volume':v,'speed':speed,
                                    'direction':1,'read':False,'stage':True}).json()
        retl.append(res)
    retl.append(requests.get("{}/pump/allOn".format(pumpurl), 
                    params={'time':totalvol/speed}).json())

    retc = return_class(measurement_type='echem_measure',
                        parameters= {'command':'measure',
                                    'parameters':{'comprel':comprel,'pumps':pumps,'speed':speed,'totalvol':totalvol}},
                        data = {'data':retl})
    return retc

@app.get("/pumping/flushSerial/")
def formulation():
    res = requests.get("{}/pump/read".format(pumpurl)).json()

    retc = return_class(measurement_type='echem_measure',
                        parameters= {'command':'measure',
                                    'parameters':None},
                        data = {'data':res})
    return retc

if __name__ == "__main__":
    pumpurl = "http://{}:{}".format("127.0.0.1", "13370")
    uvicorn.run(app, host=config['servers']['pumpingServer']['host'], port=config['servers']['pumpingServer']['port'])