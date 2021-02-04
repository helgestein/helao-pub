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

@app.get("/lang/connect")
def connect():
    l.connect()
    retc = return_class(parameters=None,data=None)
    return retc 

@app.get("/lang/disconnected")
def disconnect():
    l.disconnect()
    retc = return_class(parameters=None,data=None)
    return retc 


@app.get("/lang/moveRelFar")
def moveRelFar(dx: float, dy: float, dz: float):
    l.moveRelFar(dx, dy, dz)
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'dz':dz,
                                    'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/lang/getPos")
def getPos():
    data= l.getPos()
    retc = return_class(parameters=None,data={'pos':data,'units':'mm'})
    return retc

@app.get("/lang/moveRelZ")
def moveRelZ( dz: float, wait: bool=True):
    l.moveRelZ(dz, wait)
    retc = return_class(parameters={'dz': dz, 'wait': wait,'units':{'dz':'mm'}},data=None)
    return retc

@app.get("/lang/moveRelXY")
def moveRelXY(dx: float, dy: float, wait: bool=True):
    l.moveRelXY(dx, dy, wait)    
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'wait': wait,'units':{'dx':'mm','dy':'mm'}},data=None)
    return retc

@app.get("/lang/moveAbsXY")
def moveAbsXY(x: float, y: float, wait: bool=True):
    l.moveAbsXY(x, y, wait)
    retc = return_class(parameters={'x': x, 'y': y, 'wait': wait},data=None)
    return retc
 
@app.get("/lang/moveAbsZ")
def moveAbsZ(z: float, wait: bool=True):
    l.moveAbsZ(z, wait)
    retc = return_class(parameters={'z': z, 'wait': wait,'units':{'z':'mm'}},data=None)
    return retc

@app.get("/lang/moveAbsFar")
def moveAbsFar(dx: float, dy: float, dz: float):
    l.moveAbsFar(dx, dy, dz)
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'dz': dz,
                                    'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/lang/stopMove")
def stopMove():
    l.stopMove()
    retc = return_class(parameters=None,data=None)
    return retc

@app.on_event("shutdown")
def shutDown():
    l.moveToHome()
    l.disconnect()
 
if __name__ == "__main__":
    l = langNet(config['lang'])
    print('Port of lang Server: {}'.format(config['servers']['langServer']['port']))

    uvicorn.run(app, host=config['servers']['langServer']['host'], port=config['servers']['langServer']['port'])
    print("instantiated motor")
    