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
    retc = return_class(measurement_type='position', parameters= None, data={'pos':pos})
    return retc

@app.get("/motor/moveRel")
def moveRelFar( dx: float, dy: float, dz: float):
    requests.get("{}/lang/moveRelFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(measurement_type='Move_relative', parameters= {"dx": dx, "dy": dy, "dz": dz})
    return retc

@app.get("/motor/moveDown") #24 is the maximum amount that it can gp down (24 - 2(initial) = 22)
def moveDown(dz: float,steps: float,maxForce: float, threshold:float=22.6):
    steps = int(steps)
    #threshold = 0.5
    for i in range(steps):
        url_sens = url = "http://{}:{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'])
        res = requests.get("{}/forceAction/read".format(url), params=None).json()
        if dz > threshold:
            if abs(res['data']['data']['data']['value']) > maxForce: 
                print('Max force reached!')

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

        pos = getPos()
    retc = return_class(measurement_type='Move_relative', parameters= {"dz": dz,"steps":steps,"maxForce":maxForce},data={'pos':pos})
    return retc

@app.get("/motor/moveAbs")
def moveAbsFar( dx: float, dy: float, dz: float):
    requests.get("{}/lang/moveAbsFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(measurement_type='Move_absolut', parameters= {"dx": dx, "dy": dy, "dz": dz})
    return retc

@app.get("/motor/moveHome")
def moveHome():
    requests.get("{}/lang/moveToHome".format(url)).json()
    retc = return_class(measurement_type='Move_Home')
    return retc

@app.get("/motor/moveWaste")
def moveWaste():
    requests.get("{}/lang/moveToWaste".format(url)).json()
    retc = return_class(measurement_type='Move_Waste')
    return retc

@app.get("/motor/moveSample")
def moveToSample():
    requests.get("{}/lang/moveToSample".format(url)).json()
    retc = return_class(measurement_type='Move_Sample')
    return retc

@app.get("/motor/RemoveDroplet")
def removeDrop():
    requests.get("{}/lang/removeDrop".format(url)).json()
    retc = return_class(measurement_type='Remove_Droplet')
    return retc



if __name__ == "__main__":

   url = "http://{}:{}".format(config['servers']['langServer']['host'], config['servers']['langServer']['port'])
   print('Port of motor Server: {}'.format(config['servers']['motorServer']['port']))
   uvicorn.run(app, host=config['servers']['motorServer']['host'], port=config['servers']['motorServer']['port'])
   print("instantiated lang motor")
    