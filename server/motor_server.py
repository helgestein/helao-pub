import sys
sys.path.append(r"../config")
sys.path.append(r"../driver")
from lang_driver import langNet
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json


app = FastAPI(title="Motor driver server V1",
    description="This is a fancy motor driver server",
    version="1.0")

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/motor/connect")
def connect():
    l.connect()
    retc = return_class(
        measurement_type="motor_command",
        parameters={"command": "motor_is_connected"},
        data={'status': True}
        )
    return retc 

@app.get("/motor/disconnecte")
def disconnect():
    l.disconnect()
    retc = return_class(
        measurement_type="motor_command",
        parameters={"command": "motor_is_disconnected"},
        data={'status': True}
        )
    return retc 


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

@app.get("/motor/moveRelZ")
def moveRelZ( dz: float, wait: str=True):
    l.moveRelZ(dz, wait)
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_relative_z", 'dz': dz, 'wait': wait},
    data={'data': None}
    )
    return retc

@app.get("/motor/moveRelXY")
def moveRelXY(dx: float, dy: float, wait: str=True):
    l.moveRelXY(dx, dy, wait)    
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_relative_XY", 'dx': dx, 'dy': dy, 'wait': wait},
    data={'data': None}
    )
    return retc

@app.get("/motor/moveAbsXY")
def moveAbsXY(x: float, y: float, wait: str=True):
    l.moveAbsXY(x, y, wait)
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_absolute_XY", 'x': x, 'y': y, 'wait': wait},
    data={'data': None}
    )
    return retc
 
@app.get("/motor/moveAbsZ")
def moveAbsZ(z: float, wait:str=True):
    l.moveAbsZ(z, wait)
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_absolute_z", 'z': z, 'wait': wait},
    data={'data': None}
    )
    return retc

@app.get("/motor/moveAbsFar")
def moveAbsFar(dx: float, dy: float, dz: float):
    l.moveAbsFar(dx, dy, dz)
    retc = return_class(
    measurement_type="motor_command",
    parameters={"command": "move_absolute_z", 'x': dx, 'y': dy, 'z': dz},
    data={'data': None}
    )
    return retc




if __name__ == "__main__":
    l = langNet()
    uvicorn.run(app, host=config['servers']['motorServer']['host'], port=config['servers']['motorServer']['port'])
    print("instantiated motor")
    