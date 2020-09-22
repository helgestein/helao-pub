import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from mischbares_small import config

app = FastAPI(title="Owis action server V1",
    description="This is a very fancy Owis motor server",
    version="1.0")

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/table/activate")
def activate(motor:int=0):
    res = requests.get("{}/owis/activate".format(url),params={"motor":motor}).json()
    retc = return_class(measurement_type='owis',
                        parameters= {'command':'activate','parameters':{"motor": motor}},
                        data = {'data':res})
    return retc

@app.get("/table/configure")
def configure(motor:int=0):
    res = requests.get("{}/owis/configure".format(url),params={"motor":motor}).json()
    retc = return_class(measurement_type='owis',
                        parameters= {'command':'configure','parameters':{"motor": motor}},
                        data = {'data':res})
    return retc


#move. units of loc are mm. if configured properly, valid inputs roughly between 0mm and 96mm
#aiming to write this so that loc can be either a float (when there is only a single motor) or a list of floats
@app.get("/table/move")
def move(loc,absol:bool=True):
    if type(loc) == float or type(loc) == int:
        res = requests.get("{}/owis/move".format(url),params={"count":int(loc*10000),"motor":0,"absol":absol}).json()
    else:
        res = []
        for i,j in zip(range(len(loc)),loc):
            res.append(requests.get("{}/owis/move".format(url),params={"count":int(j*10000),"motor":i,"absol":absol}).json())
    retc = return_class(measurement_type='owis',
                        parameters= {'command':'move','parameters':{"loc": loc,absol:"absol"}},
                        data = {'data':res})
    return retc

@app.get("/table/getPos")
def getPos():
    res = requests.get("{}/owis/getPos".format(url)).json()
    coordinates = res['data']['coordinates']
    loc = None if coordinates == None else coordinates/10000 if type(coordinates) == int else [i/10000 for i in coordinates]
    retc = return_class(measurement_type='owis',
                        parameters= {'command':'getPos','parameters':None},
                        data = {'position': loc, 'meta':res})
    return retc


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['owisServer']['host'], config['servers']['owisServer']['port'])
    uvicorn.run(app, host=config['servers']['tableServer']['host'], 
                     port=config['servers']['tableServer']['port'])