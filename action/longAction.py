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


@app.get("/long/")










@app.get("/motor/moveRelFar")
def moveRelFar(dx: float, dy: float, dz: float):
    l.langNet(dx, dy, dz)
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_relative", 'x': dx, 'y': dy, 'z':dz},
    data={'data': None}
    )
    return retc



@app.get("/motor/getPose")
def getPose():
    data= l.getPose()
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "get_position"},
    data={'data': data}
    )
    return retc









if __name__ == "__main__":

   url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
   uvicorn.run(app, host=config['servers']['movementServer']['host'], port=config['servers']['movementServer']['port'])
   print("instantiated longMotor")
    