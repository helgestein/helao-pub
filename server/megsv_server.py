
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
from megsv_driver import MEGSV


app = FastAPI(title="MEGSV driver", 
            description= " this is a fancy MEGSV driver server",
            version= "1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None



@app.get("/force/connect")
def activate():
    m.activate()
    retc = return_class(parameters=None,data= None)
    return retc

@app.get("/force/read")
def read():
    data = m.read()
    retc = return_class(parameters=None,data= {"value": data, 'units':'internal units [-1.05,1.05]'})
    return retc

@app.get("/force/readBuffer")
def readBuffer():
    data = m.readBuffer()
    retc = return_class(parameters=None,data= {"values": data, 'units':'internal units [-1.05,1.05]'})
    return retc


@app.on_event("shutdown")
def release():
    m.release()
    retc = return_class(parameters=None,data=None)
    return retc


if __name__ == "__main__":
    m = MEGSV(config['megsv'])
    uvicorn.run(app, host=config['servers']['megsvServer']['host'], port=config['servers']['megsvServer']['port'])
    print("instantiated force sensor")
    