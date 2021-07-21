import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
from lang_driver import langNet
serverkey = sys.argv[2]

app = FastAPI(title="Lang server V2",
    description="This is a fancy motor driver server",
    version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/langDriver/connect")
def connect():
    l.connect()
    retc = return_class(parameters=None,data=None)
    return retc 

@app.get("/langDriver/disconnected")
def disconnect():
    l.disconnect()
    retc = return_class(parameters=None,data=None)
    return retc 


@app.get("/langDriver/moveRelFar")
def moveRelFar(dx: float, dy: float, dz: float):
    l.moveRelFar(dx, dy, dz)
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'dz':dz,
                                    'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/langDriver/getPos")
def getPos():
    data= l.getPos()
    retc = return_class(parameters=None,data={'pos':data,'units':'mm'})
    return retc

@app.get("/langDriver/moveRelZ")
def moveRelZ( dz: float, wait: bool=True):
    l.moveRelZ(dz, wait)
    retc = return_class(parameters={'dz': dz, 'wait': wait,'units':{'dz':'mm'}},data=None)
    return retc

@app.get("/langDriver/moveRelXY")
def moveRelXY(dx: float, dy: float, wait: bool=True):
    l.moveRelXY(dx, dy, wait)    
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'wait': wait,'units':{'dx':'mm','dy':'mm'}},data=None)
    return retc

@app.get("/langDriver/moveAbsXY")
def moveAbsXY(x: float, y: float, wait: bool=True):
    l.moveAbsXY(x, y, wait)
    retc = return_class(parameters={'x': x, 'y': y, 'wait': wait},data=None)
    return retc
 
@app.get("/langDriver/moveAbsZ")
def moveAbsZ(z: float, wait: bool=True):
    l.moveAbsZ(z, wait)
    retc = return_class(parameters={'z': z, 'wait': wait,'units':{'z':'mm'}},data=None)
    return retc

@app.get("/langDriver/moveAbsFar")
def moveAbsFar(dx: float, dy: float, dz: float):
    l.moveAbsFar(dx, dy, dz)
    retc = return_class(parameters={'dx': dx, 'dy': dy, 'dz': dz,
                                    'units':{'dx':'mm','dy':'mm','dz':'mm'}},data=None)
    return retc

@app.get("/langDriver/stopMove")
def stopMove():
    l.stopMove()
    retc = return_class(parameters=None,data=None)
    return retc

@app.on_event("shutdown")
def shutDown():
    l.disconnect()
 
if __name__ == "__main__":
    l = langNet(config[serverkey])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("instantiated motor")
    