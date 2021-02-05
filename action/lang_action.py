import sys
sys.path.append(r'../config')
sys.path.append(r'../driver')
sys.path.append(r'../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests

app = FastAPI(title="Motor action server V1", 
    description="This is a fancy lang motor action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None


@app.get("/motor/getPos")
def getPos():
    pos = requests.get("{}/lang/getPos".format(url)).json()
    retc = return_class(parameters= None, data=res)
    return retc

@app.get("/motor/moveRel")
def moveRelFar( dx: float, dy: float, dz: float):
    requests.get("{}/lang/moveRelFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc =  return_class(parameters= {"dx": dx, "dy": dy, "dz": dz,'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/motor/moveDown") #24 is the maximum amount that it can gp down (24 - 2(initial) = 22)
def moveDown(dz: float,steps: float,maxForce: float, threshold:float=22.6):
    steps = int(steps)
    force_value = []
    for i in range(steps):
        url_sens = url = "http://{}:{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'])
        res = requests.get("{}/forceAction/read".format(url), params=None).json()
        force_value.append(res)
        if dz > threshold:
            if abs(res['data']['data']['data']['value']) > maxForce:
                print('Max force reached!')

            elif not abs(res['data']['data']['data']['value'])> maxForce:
            #requests.get("{}/lang/stopMove".format(url)).json()
                moveRelFar(dx= 0, dy=0, dz = threshold)
            print('axis are out of the range')

        else:
            if not abs(res['data']['data']['data']['value'])> maxForce:
                print('Max force not reached ...')
                moveRelFar(dx= 0, dy=0, dz = dz)
            else:
                #requests.get("{}/lang/stopMove".format(url), params= None).json()
                print('Max force reached!')

        pos = requests.get("{}/lang/getPos".format(url)).json()
    retc = return_class(parameters= {"dz": dz,"steps":steps,"maxForce":maxForce,'units':{'dz':'mm','maxforce':'internal units [-1.05,1.05]'}},
                        data={'raw':[force_value,pos], 'res':{'force_value':force_value['data']['data']['value'],'pos':pos['data']['pos'],
                              'units':{'force_value':force_value['data']['data']['units'],'pos':pos['data']['units']}}})
    return retc

@app.get("/motor/moveAbs")
def moveAbsFar(dx: float, dy: float, dz: float):
    requests.get("{}/lang/moveAbsFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc =  return_class(parameters= {"dx": dx, "dy": dy, "dz": dz,'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/motor/moveHome")
def moveHome():
    res = moveAbsFar(config['lang']['safe_home_pos'][0], config['lang']['safe_home_pos'][1], config['lang']['safe_home_pos'][2])
    retc = return_class(parameters=None,data=res)
    return retc

@app.get("/motor/moveWaste")
def moveWaste(x: float=0, y: float=0, z: float=0): #these three coordinates define the home position. This helps us to align the positions based on the reference point 
    res = moveAbsFar(x + config['lang']['safe_waste_pos'][0], y + config['lang']['safe_waste_pos'][1], z + config['lang']['safe_waste_pos'][2])
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data=res)
    return retc

@app.get("/motor/moveSample")
def moveToSample(x: float=0, y: float=0, z: float=0):
    res = moveAbsFar(x + config['lang']['safe_sample_pos'][0], y + config['lang']['safe_sample_pos'][1], z + config['lang']['safe_sample_pos'][2])
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data=res)
    return retc

@app.get("/motor/RemoveDroplet")
def removeDrop(x: float=0, y: float=0, z: float=0):
    res = []
    res.append(moveAbsFar(x + config['lang']['safe_waste_pos'][0], y + config['lang']['safe_waste_pos'][1], z + config['lang']['remove_drop'][2])) # because referene will start from 2 
    res.append(moveAbsFar(x + config['lang']['remove_drop'][0], y + config['lang']['remove_drop'][1], z + config['lang']['remove_drop'][2]))
    res.append(getPos())
    retc = return_class(parameters= {"x": x, "y": y, "z": z,'units':{'x':'mm','y':'mm','z':'mm'}},data=res)
    return retc

@app.on_event("shutdown")
def shutDown():
    moveHome()


if __name__ == "__main__":

   url = "http://{}:{}".format(config['servers']['langServer']['host'], config['servers']['langServer']['port'])
   print('Port of motor Server: {}'.format(config['servers']['motorServer']['port']))
   uvicorn.run(app, host=config['servers']['motorServer']['host'], port=config['servers']['motorServer']['port'])
   print("instantiated lang motor")
    