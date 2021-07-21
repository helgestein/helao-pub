import sys
sys.path.append(r'../config')
sys.path.append(r'../driver')
sys.path.append(r'../server')
#from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))

config = import_module(sys.argv[1]).config

app = FastAPI(title="LangDriver server V2", 
    description="This is a fancy lang motor action server", 
    version="2.0")


class return_class(BaseModel):
    parameters :dict = None
    data: dict = None


@app.get("/langDriver/getPos")
def getPos():
    res = requests.get("{}/lang/getPos".format(url)).json()
    retc = return_class(parameters= None, data=res)
    return retc

@app.get("/langDriver/moveRel")
def moveRelFar( dx: float, dy: float, dz: float):
    requests.get("{}/lang/moveRelFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(parameters= {"dx": dx, "dy": dy, "dz": dz,'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/langDriver/moveDown") #24 is the maximum amount that it can gp down (24 - 2(initial) = 22)
def moveDown(dz: float,steps: float,maxForce: float, threshold:float=22.6):
    steps = int(steps)
    raw = []
    for i in range(steps):
        forceurl = "http://{}:{}".format(config['servers']['forceDriver']['host'], config['servers']['forceDriver']['port'])
        res = requests.get("{}/forceDriver/read".format(forceurl), params=None).json()
        print(res['data']['data']['value'])
        raw.append(res)
        if dz > threshold:
            if abs(res['data']['data']['value']) > maxForce:
                print('Max force reached!')

            elif not abs(res['data']['data']['value'])> maxForce:
            #requests.get("{}/lang/stopMove".format(url)).json()
                requests.get("{}/lang/moveRelFar".format(url), params= dict(dx = 0, dy = 0, dz = 0)).json()
                moveRelFar(dx= 0, dy=0, dz = threshold)
                print('axis are out of the range')

        else:
            if not abs(res['data']['data']['value'])> maxForce:
                print('Max force not reached ...')
                requests.get("{}/lang/moveRelFar".format(url), params= dict(dx = 0, dy = 0, dz = dz)).json()
            else:
                #requests.get("{}/lang/stopMove".format(url), params= None).json()
                print('Max force reached!')

        pos = requests.get("{}/lang/getPos".format(url)).json()
    retc = return_class(parameters= {"dz": dz,"steps":steps,"maxForce":maxForce,'units':{'dz':'mm','maxforce':'internal units [-1.05,1.05]'}},
                        data= {'raw':raw.append(pos), 'res':{'force_value':res['data']['data']['value'],'pos':pos['data']['pos'],
                              'units':{'force_value':res['data']['data']['units'],'pos':pos['data']['units']}}})
    return retc

@app.get("/langDriver/moveAbs")
def moveAbsFar(dx: float, dy: float, dz: float):
    print("the x and y position of the next point is {} and {}".format(dx, dy))
    print("types are {} and {}".format(type(dx), type(dy))) 
    requests.get("{}/lang/moveAbsFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(parameters= {"dx": dx, "dy": dy, "dz": dz,'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/langDriver/moveHome")
def moveHome():
    res = requests.get("{}/lang/moveAbsFar".format(url), params=dict(dx=config['lang']['safe_home_pos'][0], dy=config['lang']['safe_home_pos'][1], dz=config['lang']['safe_home_pos'][2])).json()
    retc = return_class(parameters=None,data=res)
    return retc

@app.get("/langDriver/moveWaste")
def moveWaste(x: float=0, y: float=0, z: float=0): #these three coordinates define the home position. This helps us to align the positions based on the reference point 
    res = requests.get("{}/lang/moveAbsFar".format(url), params=dict(dx=x+config['lang']['safe_waste_pos'][0], dy=y+config['lang']['safe_waste_pos'][1], dz=z+config['lang']['safe_waste_pos'][2])).json()
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data=res)
    return retc

@app.get("/langDriver/moveSample")
def moveToSample(x: float=0, y: float=0, z: float=0):
    res = requests.get("{}/lang/moveAbsFar".format(url), params=dict(dx=x+config['lang']['safe_sample_pos'][0], dy=y+config['lang']['safe_sample_pos'][1], dz=z+config['lang']['safe_sample_pos'][2])).json()
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data=res)
    return retc

@app.get("/langDriver/RemoveDroplet")
def removeDrop(x: float=0, y: float=0, z: float=0):
    raw = []
    raw.append(requests.get("{}/lang/moveAbsFar".format(url), params= dict(dx = x + config['lang']['safe_waste_pos'][0], dy = y + config['lang']['safe_waste_pos'][1], dz = z + config['lang']['remove_drop'][2])).json()) # because referene will start from 2 
    raw.append(requests.get("{}/lang/moveAbsFar".format(url), params= dict(dx = x + config['lang']['remove_drop'][0], dy = y + config['lang']['remove_drop'][1], dz = z + config['lang']['remove_drop'][2])).json())
    res = requests.get("{}/lang/getPos".format(url)).json()
    raw.append(res)
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data={'raw':raw,'res':res['data']})
    return retc

@app.on_event("shutdown")
def shutDown():
    moveHome()


if __name__ == "__main__":

   url = "http://{}:{}".format(config['servers']['lang']['host'], config['servers']['lang']['port'])
   print('Port of langDriver Server: {}'.format(config['servers']['lang']['port']))
   uvicorn.run(app, host=config['servers']['langDriver']['host'], port=config['servers']['langDriver']['port'])
   print("instantiated langDriver")
    