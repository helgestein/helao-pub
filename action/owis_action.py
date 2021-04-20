import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
import numpy
from math import sin,cos
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config


app = FastAPI(title="Owis action server V1",
    description="This is a very fancy Owis motor server",
    version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/table/activate")
def activate(motor:int=0):
    res = requests.get("{}/owis/activate".format(url),params={"motor":motor}).json()
    retc = return_class(parameters= {"motor": motor},data = res)
    return retc

@app.get("/table/configure")
def configure(motor:int=0):
    res = requests.get("{}/owis/configure".format(url),params={"motor":motor}).json()
    retc = return_class(measurement_type='owis',
                        parameters= {"motor": motor},
                        data = res)
    return retc


#move. units of loc are mm. if configured properly, valid inputs roughly between 0mm and 96mm (reading this on 15/04/21, I should qualify that we now have 1 motor which is longer than 96 mm)
#aiming to write this so that loc can be either a float (when there is only a single motor) or a list of floats
@app.get("/table/move")
def move(loc,absol:bool=True):
    loc = json.loads(loc)
    if type(loc) == float or type(loc) == int:
        res = requests.get("{}/owis/move".format(url),params={"count":int(loc*10000),"motor":0,"absol":absol}).json()
    else:
        res = []
        for i,j in zip(range(len(loc)),loc):
            res.append(requests.get("{}/owis/move".format(url),params={"count":int(j*10000),"motor":i,"absol":absol}).json())
    retc = return_class(parameters= {"loc": loc,"absol":absol,'units':{'loc':'mm'}},data = res)
    return retc

@app.get("/table/getPos")
def getPos():
    res = requests.get("{}/owis/getPos".format(url)).json()
    coordinates = res['data']['coordinates']
    loc = None if coordinates == None else coordinates/10000 if type(coordinates) == int else [i/10000 for i in coordinates]
    retc = return_class(parameters= None,data = {'res': {'loc':loc,'units':'mm'}, 'raw':res})
    return retc


@app.on_event("startup")
def memory():
    global height_map
    height_map = None

#3 coordinates which form a right triangle (or a rectangle with the origin included)
#coordinate x should be displaced only in x direction
#coordinate y should be displaced only in y direction
#coordinate m = (x[0],y[1],z) -- between the two
#third component of each coordinate is estimated sample height at that coordinate 'z'
#f is the focal length of the probe used to find optimal height
def set_heights(x,m,y,f=5):
    global height_map
    height_map = lambda c: m[2]-(m[2]-x[2])/(m[1]-x[1])*(m[1]-c[1])-(m[2]-y[2])/(m[0]-y[0])*(m[0]-c[0])-f

#to keep coordinate system right-handed in current configuration, long motor should be x

#x,y,z,theta set that is the motor position at which the center of the probe or whatever would be in contact with the sample stage origin
#theta is angle by which to rotate owis x-y to align it with sample stage x-y
#here we do the inverse of what one would expect, given that, and convert from sample stage coordinates to owis coordinates
def map_coordinates(c,key):
    d = config['owis']['coordinates'][config['owis']['roles'].index(key)]
    return numpy.append(numpy.dot(numpy.array([[cos(d[3]),sin(d[3])],[-sin(d[3]),cos(d[3])]]),numpy.array(c[:2])),c[2])-d[:3]

#believe me, I am not happy about this, but it does not seem prudent right now to continue thinking of a workaround
def calibration(x,m,y,f=5):
    data = requests.get("{}/ocean/readSpectrum".format(url),params={'t':t,'filename':filename}).json()
    #scipy.optimize.minimize_scalar(bracket=(1,f,2*f-1),bounds=(1,2*f-1),)
    set_heights()
    return return_class()

#move table in x-y of sample stage coordinate system
def move_table(pos,key):
    #map x and y
    pos = map_coordinates([pos[0],pos[1],0],key)[:2]
    pos = {config['owis']['roles'].index('x'):pos[0],config['owis']['roles'].index('y'):pos[1]}
    #move
    res = []
    for i,j in pos.items():
        res.append(requests.get("{}/owis/move".format(url),params={"count":int(j*10000),"motor":i}).json())
    retc = return_class(parameters= {"pos": pos,"absol":absol,'units':{'pos':'mm'}},data = res)
    return retc


def move_probe(z,probe):
    d = config['owis']['coordinates'][config['owis']['roles'].index(key)][2]
    res = requests.get("{}/owis/move".format(url),params={"count":int((d+z)*10000),"motor":config['owis']['roles'].index(probe)}).json()
    retc = return_class(parameters= {"z": pos,"probe":probe,'units':{'z':'mm'}},data = res)
    return retc

if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['owisServer']['host'], config['servers']['owisServer']['port'])
    uvicorn.run(app, host=config['servers']['tableServer']['host'], 
                     port=config['servers']['tableServer']['port'])