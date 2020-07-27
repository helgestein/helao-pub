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

app = FastAPI(title="Mecademic action server V1", 
    description="This is a fancy mecademic action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None


@app.get("/long/moveRel")
def moveRelFar( dx: float, dy: float, dz: float):
    requests.get("{}/motor/moveRelFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(measurement_type='Move_relative', parameters= {"dx": dx, "dy": dy, "dz": dz})
    return retc


@app.get("/long/moveAbs")
def moveAbsFar( dx: float, dy: float, dz: float):
    requests.get("{}/motor/moveAbsFar".format(url), params= {"dx": dx, "dy": dy, "dz": dz}).json()
    retc = return_class(measurement_type='Move_absolut', parameters= {"dx": dx, "dy": dy, "dz": dz})
    return retc


if __name__ == "__main__":

   url = "http://{}:{}".format(config['servers']['motorServer']['host'], config['servers']['motorServer']['port'])
   uvicorn.run(app, host=config['servers']['langServer']['host'], port=config['servers']['langServer']['port'])
   print("instantiated longMotor")
    