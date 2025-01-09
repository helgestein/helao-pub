
import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../driver')
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
#from sdc_1 import config
from force_driver import GSV3USB
serverkey = sys.argv[2]
#serverkey = 'forceDriver'

app = FastAPI(title="Force driver new one", 
            description= " this is a fancy force driver server",
            version= "2.0")
            
class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/forceDriver/setoffset")
def set_offset():
    g.set_offset()
    retc = return_class(parameters=None,data= None)
    return retc

@app.get("/forceDriver/setzero")
def set_zero():
    g.set_zero()
    retc = return_class(parameters=None, data=None)
    return retc

@app.get("/forceDriver/read")
def read_value():
    data = g.read_value()
    retc = return_class(parameters=None,data= {"value": data, 'units':'internal units [500mN]'})
    return retc


if __name__ == "__main__":
    g = GSV3USB(config['forceDriver']['com_port']) #config[serverkey] 
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("Terminated forcDriver sensor")
    
