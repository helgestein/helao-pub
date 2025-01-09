import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from ocean_driver import ocean
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]


app = FastAPI(title="ocean driver", 
            description= " this is a fancy ocean optics raman spectrometer driver server",
            version= "1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.on_event("startup")
def startup_event():
    global o
    o = ocean(config[serverkey])

@app.get("/oceanDriver/find")
def findDevice():
    device = o.findDevice()
    retc = return_class(parameters = None,data = {"device" : str(device)})
    return retc

@app.get("/oceanDriver/connect")
def open():
    o.open()
    retc = return_class(parameters = None,data = None)
    return retc

@app.get("/oceanDriver/readSpectrum")
async def readSpectrum(t:int,filename:str):
    data = o.readSpectrum(t,filename)
    retc = return_class(parameters = {"filename" : filename, "t" : t,'units':{'t':'µs'}},data = data)
    return retc

@app.get("/oceanDriver/loadFile")
def loadFile(filename:str):
    data = o.loadFile(filename)
    retc = return_class(parameters = {"filename" : filename},data = data)
    return retc

@app.on_event("shutdown")
def close(self):
    o.close()
    retc = return_class(parameters = None,data = None)
    return retc



if __name__ == "__main__":
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])