import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
from pump_driver import pump
serverkey = sys.argv[2]

app = FastAPI(title="PumpDriver server V2",
    description="This is a very fancy pump server",
    version="2.0",)

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/pumpDriver/stopPump")
def stopPump(pump:int,read:bool=False):
    ret = p.stopPump(pump,read)
    retc = return_class(parameters={"pump": pump,"read":read},data={'serial_response':ret})
    return retc

@app.get("/pumpDriver/primePump")
def primePump(pump:int, volume:int, speed:int, direction:int=1, read:bool=False):
    ret = p.primePump(pump, volume, speed, direction, read)
    retc = return_class(parameters={"volume": volume,"speed": speed,"pump": pump,"direction": direction,"read": read,
                                    'units': {'speed':'µl/min','totalvol':'µL'}},
                        data={'serial_response':ret})
    return retc

@app.get("/pumpDriver/runPump")
def runPump(pump:int,read:bool=False):
    ret = p.runPump(pump,read)
    retc = return_class(parameters={"pump":pump,"read":read},data={'serial_response':ret})
    return retc

@app.get("/pumpDriver/readPump")
def readPump(pump:int):
    ret = p.readPump(pump)
    retc = return_class(parameters={"pump": pump},data={'serial_response':ret})
    return retc

@app.get("/pumpDriver/pumpOff")
def pumpOff(pump:int,read:bool=False):
    ret = p.pumpOff(pump,read)
    retc = return_class(parameters={"pump": pump,"read":read},data={'serial_response':ret})
    return retc

@app.get("/pumpDriver/read")
def read():
    ret = p.read()
    retc = return_class(parameters=None,data={'serial_response':ret})
    return retc

@app.on_event("shutdown")
def shutdown():
    p.shutdown()
    retc = return_class(parameters=None,data=None)
    return retc

if __name__ == "__main__":
    p = pump(config[serverkey])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])