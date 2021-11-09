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
from owis_driver import owis
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]


app = FastAPI(title="owis driver", 
            description= " this is a fancy owis driver server",
            version= "1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/owisDriver/activate")
def activate(motor:int=0):
    o.activate(motor)
    retc = return_class(parameters={"motor": motor},data= None)
    return retc

@app.get("/owisDriver/configure")
def configure(motor:int=0,ref:int=6):
    o.configure(motor,ref)
    retc = return_class(parameters={"motor": motor},data=None)
    return retc

@app.get("/owisDriver/move")
def move(count:int,motor:int=0,absol:bool=True):
    o.move(count,motor,absol)
    retc = return_class(parameters={"count": count, "motor": motor, "absol": absol,'units':{'count':'microsteps (about .0001mm)'}},data= None)
    return retc

@app.get("/owisDriver/getPos")
def getPos():
    ret = o.getPos()
    retc = return_class(parameters=None,data={"coordinates": ret,'units':{'coordinates':'microsteps (about .0001mm)'}})
    return retc

@app.get("/owisDriver/setCurrent")
def setCurrent(dri:int,hol:int,amp:int,motor:int=0):
    o.setCurrent(dri,hol,amp,motor)
    retc = return_class(parameters={"dri":dri,"hol":hol,"amp":amp,"motor":motor},data=None)
    return retc


if __name__ == "__main__":
    o = owis(config[serverkey])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("instantiated owis motor")
    